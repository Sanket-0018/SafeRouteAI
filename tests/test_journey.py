"""
SafeRoute AI — Journey Road-Safety Assessment Test Suite
Tests corridor spatial matching, arrival time sequencing, hazard deduplication,
and strict distinction between ML hotspots and official Maharashtra blackspots.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.journey.corridor_matcher import deduplicate_hazards, match_hazard_to_route
from src.journey.journey_analyzer import analyze_journey_safety
from src.journey.router import get_route_geometry
from src.journey.schemas import JourneyRequest, JourneySafetyAssessment

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Router & Route Geometry Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_router_pune_nagpur_geometry():
    geom = get_route_geometry("Pune, Maharashtra", "Nagpur, Maharashtra")
    assert geom.distance_km > 500.0  # Approx 680-730 km
    assert geom.duration_hours > 5.0
    assert len(geom.coordinates) > 10
    # Coordinates in [[lon, lat], ...] order
    p0 = geom.coordinates[0]
    assert 73.0 <= p0[0] <= 75.0  # Pune longitude
    assert 18.0 <= p0[1] <= 19.5  # Pune latitude


def test_router_custom_coordinates():
    geom = get_route_geometry(
        origin_name="Custom Start",
        destination_name="Custom End",
        origin_lat=18.5204,
        origin_lon=73.8567,
        dest_lat=19.0760,
        dest_lon=72.8777,
    )
    assert geom.distance_km > 100.0
    assert len(geom.coordinates) > 0


# ──────────────────────────────────────────────────────────────────────────────
# 2. Corridor Spatial Matching Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_match_hazard_on_corridor():
    # Route: Pune to Ahmednagar
    route_coords = [[73.8567, 18.5204], [74.7480, 19.0952]]
    # Point near Shikrapur (on route)
    h_lat, h_lon = 18.6942, 74.1258
    res = match_hazard_to_route(h_lat, h_lon, route_coords, total_route_distance_km=120.0)
    assert res is not None
    dist_to_corridor, dist_along_route = res
    assert dist_to_corridor < 15.0
    assert 10.0 < dist_along_route < 60.0


def test_match_hazard_far_from_corridor():
    # Route: Pune to Ahmednagar
    route_coords = [[73.8567, 18.5204], [74.7480, 19.0952]]
    # Chennai coordinates (thousands of km away)
    h_lat, h_lon = 13.0827, 80.2707
    res = match_hazard_to_route(h_lat, h_lon, route_coords, total_route_distance_km=120.0)
    assert res is not None
    dist_to_corridor, _ = res
    assert dist_to_corridor > 500.0  # Far away


# ──────────────────────────────────────────────────────────────────────────────
# 3. Hazard Deduplication & Sequencing Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_deduplicate_close_hazards():
    raw = [
        {"distance_from_origin_km": 10.0, "hazard_type": "OFFICIAL_BLACKSPOT", "risk_probability": None},
        {"distance_from_origin_km": 11.5, "hazard_type": "ML_PREDICTED_HOTSPOT", "risk_probability": 0.85},
        {"distance_from_origin_km": 50.0, "hazard_type": "OFFICIAL_BLACKSPOT", "risk_probability": None},
    ]
    deduped = deduplicate_hazards(raw, min_spacing_km=4.0)
    assert len(deduped) == 2
    assert deduped[0]["distance_from_origin_km"] in [10.0, 11.5]
    assert deduped[1]["distance_from_origin_km"] == 50.0


# ──────────────────────────────────────────────────────────────────────────────
# 4. End-to-End Pune → Nagpur Assessment Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_pune_nagpur_journey_assessment():
    req = JourneyRequest(
        origin="Pune, Maharashtra",
        destination="Nagpur, Maharashtra",
        departure_datetime="2026-08-30T20:00:00",
    )
    assessment = analyze_journey_safety(req)

    assert isinstance(assessment, JourneySafetyAssessment)
    assert assessment.origin == "Pune, Maharashtra"
    assert assessment.destination == "Nagpur, Maharashtra"
    assert assessment.total_distance_km > 600.0
    assert assessment.total_hazards_count > 5
    assert assessment.ml_hotspots_count >= 1
    assert assessment.official_blackspots_count >= 5

    # Verify chronological sequence
    distances = [h.distance_from_origin_km for h in assessment.hazards]
    assert distances == sorted(distances), "Hazards must be chronologically sequenced along the route"

    for idx, h in enumerate(assessment.hazards, start=1):
        assert h.sequence == idx
        assert h.distance_from_origin_km >= 0.0
        assert h.expected_arrival_time != ""
        assert h.expected_arrival_window != ""

        if h.hazard_type == "ML_PREDICTED_HOTSPOT":
            # ML hotspots must have valid probability and SHAP factors
            assert h.risk_probability is not None
            assert 0.0 <= h.risk_probability <= 1.0
            assert h.contributing_factors is not None
            assert len(h.contributing_factors) > 0

        elif h.hazard_type == "OFFICIAL_BLACKSPOT":
            # STRICT: Official blackspots must NEVER have fake probabilities or fake SHAP
            assert h.risk_probability is None, "Official blackspots must NOT have fake probabilities"
            assert h.contributing_factors is None, "Official blackspots must NOT have fake SHAP factors"
            assert h.official_provenance is not None
            assert h.official_provenance.source_organization != ""
            assert h.official_provenance.source_url.startswith("http")


# ──────────────────────────────────────────────────────────────────────────────
# 5. API POST /journey/analyze Endpoint Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_api_journey_analyze_success():
    payload = {
        "origin": "Pune, Maharashtra",
        "destination": "Nagpur, Maharashtra",
        "departure_datetime": "2026-08-30T20:00:00",
    }
    resp = client.post("/journey/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["origin"] == "Pune, Maharashtra"
    assert data["destination"] == "Nagpur, Maharashtra"
    assert "total_distance_km" in data
    assert "estimated_duration_formatted" in data
    assert "hazards" in data
    assert len(data["hazards"]) > 0

    first_hazard = data["hazards"][0]
    assert "sequence" in first_hazard
    assert "hazard_type" in first_hazard
    assert "location_name" in first_hazard
    assert "expected_arrival_time" in first_hazard
    assert "risk_tier" in first_hazard
    assert "safety_guidance" in first_hazard


def test_api_journey_mumbai_pune():
    payload = {
        "origin": "Mumbai, Maharashtra",
        "destination": "Pune, Maharashtra",
        "departure_datetime": "2026-08-30T08:00:00",
    }
    resp = client.post("/journey/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_distance_km"] > 100.0
    assert len(data["hazards"]) > 0


def test_api_journey_missing_required_fields():
    resp = client.post("/journey/analyze", json={"origin": "Pune"})
    assert resp.status_code == 422  # Unprocessable Entity (missing destination)
