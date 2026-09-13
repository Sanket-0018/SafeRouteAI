"""
SafeRoute AI — OpenStreetMap Road Context Integration Tests
Validates physical road attribute schemas, missing attribute preservation,
corridor association, hazard-level road context enrichment, and zero-synthetic integrity.
"""

from __future__ import annotations

import pytest
from src.journey.journey_analyzer import analyze_journey_safety
from src.journey.road_context import (
    extract_road_context,
    match_hazard_road_context,
    CORRIDOR_INFRASTRUCTURE_METADATA,
)
from src.journey.router import get_route_geometry
from src.journey.schemas import (
    HazardRoadContext,
    JourneyHazard,
    JourneyRequest,
    RoadContextSummary,
    RouteGeometry,
)


def test_corridor_infrastructure_metadata_valid():
    assert len(CORRIDOR_INFRASTRUCTURE_METADATA) >= 5
    for c in CORRIDOR_INFRASTRUCTURE_METADATA:
        assert "highway_ref" in c
        assert "highway_class" in c
        assert "lanes" in c and c["lanes"] >= 2
        assert "maxspeed_kmh" in c and c["maxspeed_kmh"] > 0
        assert "lat_min" in c and "lat_max" in c


def test_match_hazard_road_context_pune_urban():
    ctx = match_hazard_road_context(
        hazard_lat=18.5204,
        hazard_lon=73.8567,
        hazard_highway="Pune Arterial",
        hazard_name="Pune Sector 363 (Pune)",
    )
    assert isinstance(ctx, HazardRoadContext)
    assert ctx.highway_class == "primary"
    assert ctx.lanes == 4
    assert ctx.is_lit is True
    assert ctx.maxspeed_kmh == 50
    assert "urban arterial" in ctx.context_summary.lower()


def test_match_hazard_road_context_expressway_tunnel():
    ctx = match_hazard_road_context(
        hazard_lat=18.8890,
        hazard_lon=73.1850,
        hazard_highway="Mumbai–Pune Expressway",
        hazard_name="Bhatan Tunnel Approach (Panvel end)",
    )
    assert isinstance(ctx, HazardRoadContext)
    assert ctx.highway_class == "motorway"
    assert ctx.lanes == 6
    assert ctx.is_tunnel is True
    assert ctx.maxspeed_kmh == 100
    assert ctx.surface == "concrete"


def test_extract_road_context_on_pune_nagpur():
    req = JourneyRequest(
        origin="Pune, Maharashtra",
        destination="Nagpur, Maharashtra",
        departure_datetime="2026-08-30T20:00:00",
    )
    assessment = analyze_journey_safety(req)

    assert assessment.road_context_summary is not None
    assert isinstance(assessment.road_context_summary, RoadContextSummary)
    assert len(assessment.road_context_summary.major_highways) > 0
    assert assessment.road_context_summary.source_provenance.startswith("OpenStreetMap")

    # Check notable segments
    assert len(assessment.notable_segments) > 0
    seg_names = [s.name for s in assessment.notable_segments]
    assert any("Samruddhi" in n or "Shikrapur" in n for n in seg_names)

    # Check hazards road context
    for h in assessment.hazards:
        assert h.road_context is not None
        assert isinstance(h.road_context, HazardRoadContext)
        assert h.road_context.context_summary != ""
        assert h.road_context.lanes is not None


def test_road_context_responsible_ai_disclaimer_present():
    req = JourneyRequest(
        origin="Mumbai, Maharashtra",
        destination="Pune, Maharashtra",
        departure_datetime="2026-08-30T08:00:00",
    )
    assessment = analyze_journey_safety(req)
    assert "OpenStreetMap" in assessment.responsible_ai_disclaimer
    assert "infrastructure characteristics" in assessment.responsible_ai_disclaimer.lower()


def test_zero_fake_probabilities_with_road_context():
    req = JourneyRequest(
        origin="Pune, Maharashtra",
        destination="Kolhapur, Maharashtra",
        departure_datetime="2026-08-30T14:00:00",
    )
    assessment = analyze_journey_safety(req)
    for h in assessment.hazards:
        if h.hazard_type == "OFFICIAL_BLACKSPOT":
            assert h.risk_probability is None
            assert h.contributing_factors is None
            assert h.road_context is not None
            assert "Road Context" not in h.reason  # Reason is why flagged, context is separate
