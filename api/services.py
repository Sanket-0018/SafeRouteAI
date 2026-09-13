"""
SafeRoute AI — API Data Service Layer
Loads and serves hotspot intelligence from pre-computed JSON output.
Includes spatial coverage evaluation for arbitrary user location & time queries.
"""

from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from api.schemas import (
    CheckRiskRequest,
    CheckRiskResponse,
    HotspotIntelligence,
    HotspotSummary,
    HotspotsResponse,
    Location,
    StatsResponse,
)

# Resolve path relative to project root (two levels up from api/)
_API_DIR = Path(__file__).parent
_PROJECT_ROOT = _API_DIR.parent
INTELLIGENCE_JSON_PATH = _PROJECT_ROOT / "outputs" / "reports" / "hotspot_intelligence.json"

VALID_RISK_TIERS = {"HIGH", "MEDIUM", "LOW"}
API_VERSION = "1.0.0"
MAX_COVERAGE_DISTANCE_KM = 25.0  # Max distance to consider a location within monitored corridor coverage

# Human-readable landmark / corridor descriptions for known zones
ZONE_LANDMARK_NAMES: Dict[Tuple[str, int], str] = {
    ("Pune", 363): "Hadapsar / Magarpatta / Solapur Road corridor",
    ("Pune", 379): "Wakad / Hinjewadi / Pimpri corridor",
    ("Chandigarh", 97): "Zirakpur / Mohali / Chandigarh Highway corridor",
    ("Hyderabad", 233): "Shamshabad / Airport Highway corridor",
    ("Hyderabad", 223): "Gachibowli / Financial District corridor",
    ("Hyderabad", 248): "Secunderabad / Begumpet corridor",
    ("Hyderabad", 240): "LB Nagar / Hayathnagar corridor",
    ("Bangalore", 51): "Yelahanka / Hebbal / Airport Road corridor",
    ("Chennai", 138): "Ambattur / Avadi Industrial corridor",
    ("Kolkata", 273): "Howrah / Central Kolkata corridor",
    ("Kolkata", 283): "Salt Lake / New Town corridor",
    ("Mumbai", 319): "JNPT / Navi Mumbai / Uran corridor",
}


# ──────────────────────────────────────────────────────────────────────────────
# Data loading (cached for the process lifetime)
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_raw_records() -> List[dict]:
    """Load and cache all intelligence records from JSON. Raises on missing file."""
    if not INTELLIGENCE_JSON_PATH.exists():
        raise FileNotFoundError(
            f"hotspot_intelligence.json not found at {INTELLIGENCE_JSON_PATH}. "
            "Run the pipeline first: python -m src.pipeline.hotspot_intelligence"
        )
    with open(INTELLIGENCE_JSON_PATH, encoding="utf-8") as f:
        records = json.load(f)

    # Attach human-readable area names to location metadata
    for r in records:
        city = r["location"]["city"]
        zid = r["location"]["zone_id"]
        r["location"]["area_name"] = ZONE_LANDMARK_NAMES.get((city, zid), f"{city} Sector {zid}")

    return records


def get_all_records() -> List[dict]:
    return _load_raw_records()


def is_data_loaded() -> bool:
    try:
        _load_raw_records()
        return True
    except Exception:
        return False


def get_record_count() -> int:
    try:
        return len(_load_raw_records())
    except Exception:
        return 0


# ──────────────────────────────────────────────────────────────────────────────
# Spatial & Temporal Helpers
# ──────────────────────────────────────────────────────────────────────────────

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in km between two lat/lon coordinates."""
    r = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def map_time_to_window(travel_time: Optional[str]) -> Tuple[str, str]:
    """
    Map an input time string (e.g. '19:30', '7:30 PM', '21:00') to 4-hour window label.
    Defaults to Late Night window if time is omitted or unparseable.
    """
    if not travel_time:
        return "00:00 - 03:59 (Late Night)", "Late Night"

    hour = 0
    try:
        clean = travel_time.strip().lower()
        if "pm" in clean or "am" in clean:
            is_pm = "pm" in clean
            clean = clean.replace("pm", "").replace("am", "").strip()
            parts = clean.split(":")
            hour = int(parts[0])
            if is_pm and hour < 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
        elif ":" in clean:
            parts = clean.split(":")
            hour = int(parts[0])
        else:
            hour = int(clean)
    except Exception:
        hour = 0

    if 0 <= hour < 4:
        return "00:00 - 03:59 (Late Night)", "Late Night"
    elif 4 <= hour < 8:
        return "04:00 - 07:59 (Early Morning)", "Early Morning"
    elif 8 <= hour < 12:
        return "08:00 - 11:59 (Morning Rush)", "Morning Rush"
    elif 12 <= hour < 16:
        return "12:00 - 15:59 (Afternoon)", "Afternoon"
    elif 16 <= hour < 20:
        return "16:00 - 19:59 (Evening Rush)", "Evening Rush"
    else:
        return "20:00 - 23:59 (Night)", "Night"


# ──────────────────────────────────────────────────────────────────────────────
# Check Risk Service
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_location_risk(
    latitude: float,
    longitude: float,
    location_name: Optional[str] = None,
    travel_time: Optional[str] = None,
    travel_date: Optional[str] = None,
) -> CheckRiskResponse:
    """
    Evaluates whether a given latitude/longitude coordinate falls within evaluated
    accident hotspot coverage and returns the corresponding risk prediction.
    """
    records = get_all_records()
    mapped_window, shift_label = map_time_to_window(travel_time)

    display_name = location_name or f"{latitude:.4f}°N, {longitude:.4f}°E"

    # Find closest hotspot in the database
    best_dist = float("inf")
    best_record = None
    nearest_city = "Pune"

    for r in records:
        h_lat = r["location"]["latitude"]
        h_lon = r["location"]["longitude"]
        dist = haversine_distance_km(latitude, longitude, h_lat, h_lon)
        if dist < best_dist:
            best_dist = dist
            best_record = r
            nearest_city = r["location"]["city"]

    # Check if within valid coverage threshold
    if best_dist > MAX_COVERAGE_DISTANCE_KM or best_record is None:
        return CheckRiskResponse(
            covered=False,
            location_name=display_name,
            latitude=latitude,
            longitude=longitude,
            time_window=mapped_window,
            distance_km=round(best_dist, 1) if best_dist != float("inf") else None,
            nearest_supported_city=nearest_city,
            message=(
                "SafeRoute AI does not currently have sufficient trained accident data for "
                f"this area to provide a reliable risk prediction. Coverage is currently active for "
                f"evaluated metropolitan corridors (nearest: {nearest_city}, {best_dist:.1f} km away)."
            ),
            intelligence=None,
        )

    # Location IS covered! Now search for matching time window for that same zone/corridor
    target_zone = best_record["location"]["zone_id"]
    target_city = best_record["location"]["city"]

    # Match exact zone + window if possible
    window_match = next(
        (
            r
            for r in records
            if r["location"]["zone_id"] == target_zone
            and r["location"]["city"] == target_city
            and r["temporal"]["time_window"] == mapped_window
        ),
        None,
    )

    matched_record = window_match if window_match is not None else best_record
    full_intelligence = HotspotIntelligence(**matched_record)

    area_name = matched_record["location"].get("area_name", f"{target_city} Corridor")

    return CheckRiskResponse(
        covered=True,
        location_name=f"{display_name} ({area_name})",
        latitude=latitude,
        longitude=longitude,
        time_window=matched_record["temporal"]["time_window"],
        distance_km=round(best_dist, 2),
        nearest_supported_city=target_city,
        message=f"Elevated road-safety risk profile evaluated for {area_name}, {target_city}.",
        intelligence=full_intelligence,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Conversion helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_summary(r: dict) -> HotspotSummary:
    loc = r["location"]
    temp = r["temporal"]
    pred = r["prediction"]
    factors = r.get("contributing_factors", [])
    guidance = r.get("safety_guidance", [])

    top_factor = factors[0]["feature"] if factors else "N/A"
    top_g = guidance[0] if guidance else {}

    return HotspotSummary(
        rank=r["rank"],
        city=loc["city"],
        zone_id=loc["zone_id"],
        area_name=loc.get("area_name"),
        latitude=loc["latitude"],
        longitude=loc["longitude"],
        target_month=temp["target_month"],
        time_window=temp["time_window"],
        is_peak_window=temp["is_peak_window"],
        risk_tier=pred["risk_tier"],
        high_probability=pred["high_probability"],
        top_factor=top_factor,
        top_guidance_title=top_g.get("title", "N/A"),
        top_guidance_organization=top_g.get("organization", "N/A"),
        top_guidance_url=top_g.get("source_url", ""),
    )


def _to_full(r: dict) -> HotspotIntelligence:
    return HotspotIntelligence(**r)


# ──────────────────────────────────────────────────────────────────────────────
# Query functions
# ──────────────────────────────────────────────────────────────────────────────

def query_hotspots(
    city: Optional[str] = None,
    risk_tier: Optional[str] = None,
    limit: int = 20,
) -> HotspotsResponse:
    """
    Filter and return hotspot summaries.
    Raises ValueError on invalid filter values.
    """
    if risk_tier is not None and risk_tier.upper() not in VALID_RISK_TIERS:
        raise ValueError(f"Invalid risk_tier '{risk_tier}'. Must be one of: HIGH, MEDIUM, LOW")

    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")

    records = get_all_records()
    all_cities = {r["location"]["city"].lower() for r in records}

    if city is not None and city.lower() not in all_cities:
        raise ValueError(
            f"Unknown city '{city}'. Available cities: "
            + ", ".join(sorted(r["location"]["city"] for r in records if True))
        )

    filtered = records
    if city is not None:
        filtered = [r for r in filtered if r["location"]["city"].lower() == city.lower()]
    if risk_tier is not None:
        filtered = [r for r in filtered if r["prediction"]["risk_tier"] == risk_tier.upper()]

    limited = filtered[:limit]

    return HotspotsResponse(
        total=len(records),
        filtered=len(filtered),
        results=[_to_summary(r) for r in limited],
    )


def get_hotspot_by_rank(rank: int) -> HotspotIntelligence:
    """Return full intelligence record by rank. Raises ValueError if not found."""
    records = get_all_records()
    if rank < 1 or rank > len(records):
        raise ValueError(f"Rank {rank} out of range. Valid range: 1–{len(records)}")
    match = next((r for r in records if r["rank"] == rank), None)
    if match is None:
        raise ValueError(f"No record found for rank {rank}")
    return _to_full(match)


def get_cities() -> List[str]:
    records = get_all_records()
    return sorted(set(r["location"]["city"] for r in records))


def get_stats() -> StatsResponse:
    records = get_all_records()
    probs = [r["prediction"]["high_probability"] for r in records]
    tier_counts: Dict[str, int] = {}
    for r in records:
        t = r["prediction"]["risk_tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

    months = sorted(set(r["temporal"]["target_month"] for r in records))
    cities = sorted(set(r["location"]["city"] for r in records))

    return StatsResponse(
        total_hotspot_records=len(records),
        cities_covered=cities,
        risk_tier_breakdown=tier_counts,
        probability_stats={
            "min": round(min(probs), 4),
            "max": round(max(probs), 4),
            "mean": round(sum(probs) / len(probs), 4),
        },
        data_period={
            "earliest_month": months[0] if months else "N/A",
            "latest_month": months[-1] if months else "N/A",
            "months_count": len(months),
        },
        responsible_ai_notice=(
            "SafeRoute AI identifies historically high-risk location + time combinations "
            "based on accident patterns. Predictions indicate elevated historical risk — "
            "they do not guarantee future accidents. SHAP values reflect model feature "
            "sensitivity, not verified causation. Safety guidance is retrieved from "
            "authoritative sources (MoRTH, IRC, WHO) to support engineering decisions."
        ),
    )
