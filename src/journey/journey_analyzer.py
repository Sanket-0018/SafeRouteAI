"""
SafeRoute AI — Journey Safety Analyzer Engine
Combines ML urban hotspot predictions and official highway blackspots along an OSM journey path.
Calculates expected milestone arrival times and produces evidence-grounded risk assessments.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.journey.corridor_matcher import deduplicate_hazards, match_hazard_to_route
from src.journey.geocoding import search_places
from src.journey.road_context import extract_road_context
from src.journey.router import get_route_geometry
from src.journey.schemas import (
    ContributingFactorSummary,
    JourneyHazard,
    JourneyRequest,
    JourneySafetyAssessment,
    OfficialProvenance,
    RouteGeometry,
    SafetyGuidanceSummary,
)

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
INTELLIGENCE_JSON_PATH = _PROJECT_ROOT / "outputs" / "reports" / "hotspot_intelligence.json"
OFFICIAL_BLACKSPOTS_JSON_PATH = _PROJECT_ROOT / "data" / "external" / "maharashtra_official_blackspots.json"
FALLBACK_BLACKSPOTS_JSON_PATH = _PROJECT_ROOT / "data" / "external" / "maharashtra_highway_blackspots.json"

CORRIDOR_BUFFER_KM = 12.0  # Max distance from route centerline to consider a hazard on-corridor


def _load_ml_intelligence() -> List[Dict[str, Any]]:
    if not INTELLIGENCE_JSON_PATH.exists():
        return []
    try:
        with open(INTELLIGENCE_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load ML intelligence: {e}")
        return []


def _load_official_blackspots() -> List[Dict[str, Any]]:
    target_path = OFFICIAL_BLACKSPOTS_JSON_PATH if OFFICIAL_BLACKSPOTS_JSON_PATH.exists() else FALLBACK_BLACKSPOTS_JSON_PATH
    if not target_path.exists():
        return []
    try:
        with open(target_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load official blackspots from {target_path}: {e}")
        return []


def _parse_departure_dt(dep_str: Optional[str]) -> datetime:
    """Parses ISO string, various date/time formats, or defaults to 20:00 today."""
    now = datetime.now()
    if not dep_str:
        return now.replace(hour=20, minute=0, second=0, microsecond=0)

    clean_str = dep_str.strip()

    # 1. Try ISO format (e.g. 2026-08-30T20:00:00 or 2026-08-30 20:00:00)
    try:
        return datetime.fromisoformat(clean_str.replace("Z", ""))
    except Exception:
        pass

    # 2. Try common date-time patterns
    date_patterns = [
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %I:%M %p",
        "%d/%m/%Y %I:%M %p",
        "%Y-%m-%d %I:%M %p",
    ]
    for pattern in date_patterns:
        try:
            return datetime.strptime(clean_str, pattern)
        except Exception:
            pass

    # 3. Try time-only parsing
    try:
        clean_time = clean_str.lower()
        if "pm" in clean_time or "am" in clean_time:
            is_pm = "pm" in clean_time
            clean_time = clean_time.replace("pm", "").replace("am", "").strip()
            parts = clean_time.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            if is_pm and h < 12:
                h += 12
            elif not is_pm and h == 12:
                h = 0
            return now.replace(hour=h, minute=m, second=0, microsecond=0)
        elif ":" in clean_time:
            parts = clean_time.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            return now.replace(hour=h, minute=m, second=0, microsecond=0)
    except Exception:
        pass

    return now.replace(hour=20, minute=0, second=0, microsecond=0)


def _map_hour_to_window(hour: int) -> str:
    if 0 <= hour < 4:
        return "00:00 - 03:59 (Late Night)"
    elif 4 <= hour < 8:
        return "04:00 - 07:59 (Early Morning)"
    elif 8 <= hour < 12:
        return "08:00 - 11:59 (Morning Rush)"
    elif 12 <= hour < 16:
        return "12:00 - 15:59 (Afternoon)"
    elif 16 <= hour < 20:
        return "16:00 - 19:59 (Evening Rush)"
    else:
        return "20:00 - 23:59 (Night)"


def analyze_journey_safety(request: JourneyRequest) -> JourneySafetyAssessment:
    """
    Executes end-to-end journey safety assessment for an Origin -> Destination query.
    1. Fetches OSRM route geometry.
    2. Spatially matches ML hotspots and official blackspots to the corridor.
    3. Calculates milestone arrival times and maps to temporal risk windows.
    4. Attaches SHAP factors (ML) or official provenance (Blackspots) and RAG guidance.
    """
    route_geom = get_route_geometry(
        origin_name=request.origin,
        destination_name=request.destination,
        origin_lat=request.origin_lat,
        origin_lon=request.origin_lon,
        dest_lat=request.dest_lat,
        dest_lon=request.dest_lon,
    )

    dep_dt = _parse_departure_dt(request.departure_datetime)
    total_km = route_geom.distance_km
    total_duration_hours = route_geom.duration_hours
    avg_speed_kmh = max(30.0, total_km / max(0.5, total_duration_hours))

    raw_matched_hazards: List[Dict[str, Any]] = []

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Match ML Predicted Hotspots
    # ──────────────────────────────────────────────────────────────────────────
    ml_records = _load_ml_intelligence()
    # Group ML records by (city, zone_id) to avoid duplicates per zone
    unique_zones: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for r in ml_records:
        key = (r["location"]["city"], r["location"]["zone_id"])
        if key not in unique_zones or r["prediction"]["high_probability"] > unique_zones[key]["prediction"]["high_probability"]:
            unique_zones[key] = r

    for (city, zid), r in unique_zones.items():
        h_lat = r["location"]["latitude"]
        h_lon = r["location"]["longitude"]

        match_res = match_hazard_to_route(h_lat, h_lon, route_geom.coordinates, total_km)
        if match_res is not None:
            dist_to_corridor, dist_from_orig = match_res
            if dist_to_corridor <= CORRIDOR_BUFFER_KM:
                # Calculate expected arrival time
                elapsed_hours = dist_from_orig / avg_speed_kmh
                arr_dt = dep_dt + timedelta(hours=elapsed_hours)
                arr_time_str = arr_dt.strftime("%H:%M")
                arr_window = _map_hour_to_window(arr_dt.hour)

                # Format SHAP contributing factors
                shap_factors = [
                    ContributingFactorSummary(
                        feature=f["feature"],
                        contribution=f["contribution"],
                        value=f["value"],
                    )
                    for f in r.get("contributing_factors", [])[:3]
                ]

                # Format RAG guidance
                guidance_list = [
                    SafetyGuidanceSummary(
                        title=g["title"],
                        organization=g["organization"],
                        content_excerpt=g["content_excerpt"],
                        source_url=g["source_url"],
                    )
                    for g in r.get("safety_guidance", [])[:2]
                ]

                area_name = r["location"].get("area_name") or f"{city} Sector {zid}"

                raw_matched_hazards.append({
                    "hazard_type": "ML_PREDICTED_HOTSPOT",
                    "location_name": f"{area_name} ({city})",
                    "district": city,
                    "highway": "Urban Highway Arterial",
                    "latitude": h_lat,
                    "longitude": h_lon,
                    "distance_from_origin_km": dist_from_orig,
                    "expected_arrival_time": arr_time_str,
                    "expected_arrival_window": arr_window,
                    "risk_tier": r["prediction"]["risk_tier"],
                    "risk_probability": r["prediction"]["high_probability"],
                    "reason": f"Predicted elevated accident risk ({round(r['prediction']['high_probability']*100, 1)}% probability) driven by historical crash concentration and shift severity.",
                    "contributing_factors": shap_factors,
                    "safety_guidance": guidance_list,
                    "official_provenance": None,
                })

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Match Official Maharashtra Highway Blackspots
    # ──────────────────────────────────────────────────────────────────────────
    blackspots = _load_official_blackspots()
    for b in blackspots:
        b_lat = b["latitude"]
        b_lon = b["longitude"]

        match_res = match_hazard_to_route(b_lat, b_lon, route_geom.coordinates, total_km)
        if match_res is not None:
            dist_to_corridor, dist_from_orig = match_res
            if dist_to_corridor <= CORRIDOR_BUFFER_KM:
                elapsed_hours = dist_from_orig / avg_speed_kmh
                arr_dt = dep_dt + timedelta(hours=elapsed_hours)
                arr_time_str = arr_dt.strftime("%H:%M")
                arr_window = _map_hour_to_window(arr_dt.hour)

                source_org = b.get("source_authority") or b.get("source_organization") or b.get("reporting_authority") or "Maharashtra Highway Police"
                countermeasures = b.get("countermeasures") or b.get("official_countermeasure") or "Enforce speed calming, junction lighting, and IRC geometry improvements."
                reason = b.get("primary_factors") or b.get("hazard_description") or b.get("reason") or "Officially designated government high-severity accident blackspot."
                loc_name = b.get("location_name") or b.get("name") or "Highway Blackspot"
                highway = b.get("highway_number") or b.get("highway") or "National Highway"
                f_crashes = b.get("fatal_crashes") if b.get("fatal_crashes") is not None else b.get("fatal_crashes_3yr")
                f_fatalities = b.get("fatalities") if b.get("fatalities") is not None else b.get("total_fatalities_3yr")
                f_crashes_total = b.get("crash_count") if b.get("crash_count") is not None else b.get("grievous_injuries_3yr")
                bs_id = b.get("blackspot_id") or b.get("hazard_id") or "MH-BS-000"

                prov = OfficialProvenance(
                    source_organization=source_org,
                    source_url=b.get("source_url", "https://highwaypolice.maharashtra.gov.in"),
                    report_year=int(b.get("publication_year") or b.get("report_year") or 2024),
                    blackspot_id=bs_id,
                    chainage_km=b.get("chainage_km"),
                    fatal_crashes_3yr=f_crashes,
                    total_fatalities_3yr=f_fatalities,
                    grievous_injuries_3yr=f_crashes_total,
                )

                # Official blackspot guidance
                guidance_list = [
                    SafetyGuidanceSummary(
                        title=f"MoRTH & Police Blackspot Protocol ({bs_id})",
                        organization=source_org,
                        content_excerpt=countermeasures,
                        source_url=b.get("source_url", "https://highwaypolice.maharashtra.gov.in"),
                    )
                ]

                raw_matched_hazards.append({
                    "hazard_type": "OFFICIAL_BLACKSPOT",
                    "location_name": loc_name,
                    "district": b.get("district", "Maharashtra"),
                    "highway": highway,
                    "latitude": b_lat,
                    "longitude": b_lon,
                    "distance_from_origin_km": dist_from_orig,
                    "expected_arrival_time": arr_time_str,
                    "expected_arrival_window": arr_window,
                    "risk_tier": "OFFICIAL_HIGH_SEVERITY",
                    "risk_probability": None,  # STRICT: Zero fake probabilities
                    "reason": reason,
                    "contributing_factors": None,  # STRICT: Zero fake SHAP
                    "safety_guidance": guidance_list,
                    "official_provenance": prov,
                })

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Deduplicate and Chronologically Sequence
    # ──────────────────────────────────────────────────────────────────────────
    deduped = deduplicate_hazards(raw_matched_hazards, min_spacing_km=4.0)

    final_hazards: List[JourneyHazard] = []
    ml_count = 0
    official_count = 0

    for idx, h in enumerate(deduped, start=1):
        if h["hazard_type"] == "ML_PREDICTED_HOTSPOT":
            ml_count += 1
        else:
            official_count += 1

        final_hazards.append(JourneyHazard(
            sequence=idx,
            hazard_type=h["hazard_type"],
            location_name=h["location_name"],
            district=h.get("district"),
            highway=h.get("highway"),
            latitude=h["latitude"],
            longitude=h["longitude"],
            distance_from_origin_km=h["distance_from_origin_km"],
            expected_arrival_time=h["expected_arrival_time"],
            expected_arrival_window=h["expected_arrival_window"],
            risk_tier=h["risk_tier"],
            risk_probability=h.get("risk_probability"),
            reason=h["reason"],
            contributing_factors=h.get("contributing_factors"),
            safety_guidance=h.get("safety_guidance", []),
            official_provenance=h.get("official_provenance"),
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Enrich with Physical OpenStreetMap Road Context
    # ──────────────────────────────────────────────────────────────────────────
    road_summary, notable_segs, enriched_hazards = extract_road_context(route_geom, final_hazards)

    # Identify most critical time window
    peak_windows = [h.expected_arrival_window for h in enriched_hazards if "Late Night" in h.expected_arrival_window or "Evening Rush" in h.expected_arrival_window]
    highest_risk_window = peak_windows[0] if peak_windows else (enriched_hazards[0].expected_arrival_window if enriched_hazards else "00:00 - 03:59 (Late Night)")

    return JourneySafetyAssessment(
        origin=request.origin,
        destination=request.destination,
        departure_datetime=dep_dt.isoformat(),
        total_distance_km=total_km,
        estimated_duration_hours=total_duration_hours,
        estimated_duration_formatted=route_geom.estimated_duration_formatted,
        total_hazards_count=len(enriched_hazards),
        ml_hotspots_count=ml_count,
        official_blackspots_count=official_count,
        highest_risk_time_window=highest_risk_window,
        hazards=enriched_hazards,
        route_geometry=route_geom,
        road_context_summary=road_summary,
        notable_segments=notable_segs,
    )
