"""
SafeRoute AI — Journey Assessment Data Schemas
Defines structured Pydantic models for journey hazard analysis,
including OpenStreetMap physical road-network context models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class RouteGeometry(BaseModel):
    coordinates: List[List[float]] = Field(
        ...,
        description="GeoJSON coordinates array in [[longitude, latitude], ...] order",
    )
    distance_km: float = Field(..., description="Total driving distance in km")
    duration_hours: float = Field(..., description="Estimated travel duration in decimal hours")
    estimated_duration_formatted: str = Field(
        ..., description="Human-readable duration (e.g. '10h 45m')"
    )


class ContributingFactorSummary(BaseModel):
    feature: str
    contribution: float
    value: float


class SafetyGuidanceSummary(BaseModel):
    title: str
    organization: str
    content_excerpt: str
    source_url: str


class OfficialProvenance(BaseModel):
    source_organization: str
    source_url: str
    report_year: int
    blackspot_id: str
    chainage_km: Optional[str] = None
    fatal_crashes_3yr: Optional[int] = None
    total_fatalities_3yr: Optional[int] = None
    grievous_injuries_3yr: Optional[int] = None


class HazardRoadContext(BaseModel):
    highway_class: Optional[str] = Field(None, description="OSM highway classification (motorway, trunk, primary, secondary)")
    lanes: Optional[int] = Field(None, description="Number of carriageway travel lanes")
    maxspeed_kmh: Optional[int] = Field(None, description="Official legal speed limit in km/h")
    surface: Optional[str] = Field(None, description="Road surface material (e.g. asphalt, concrete)")
    is_lit: Optional[bool] = Field(None, description="Whether the road section has functional street lighting")
    is_bridge: bool = Field(False, description="Whether the location is on or immediately approaching a bridge")
    is_tunnel: bool = Field(False, description="Whether the location is in or approaching a tunnel portal")
    is_junction: bool = Field(False, description="Whether the location is an intersection, roundabout, or interchange")
    is_divided: Optional[bool] = Field(None, description="Whether physical median separates opposing traffic directions")
    road_name_or_ref: Optional[str] = Field(None, description="Road name or national/state highway reference code")
    context_summary: str = Field(..., description="Human-readable physical road infrastructure context description")


class JourneyHazard(BaseModel):
    sequence: int = Field(..., description="Chronological milestone order along the journey (1, 2, ...)")
    hazard_type: Literal["ML_PREDICTED_HOTSPOT", "OFFICIAL_BLACKSPOT"] = Field(
        ..., description="Type of hazard: ML model prediction or official government blackspot"
    )
    location_name: str
    district: Optional[str] = None
    highway: Optional[str] = None
    latitude: float
    longitude: float
    distance_from_origin_km: float = Field(
        ..., description="Driving distance in km from journey origin to this hazard"
    )
    expected_arrival_time: str = Field(
        ..., description="Projected local clock arrival time (e.g. '21:15' or '02:40')"
    )
    expected_arrival_window: str = Field(
        ..., description="Corresponding 4-hour temporal shift window"
    )
    risk_tier: str = Field(
        ..., description="Risk tier: HIGH, MEDIUM, LOW, or OFFICIAL_HIGH_SEVERITY"
    )
    risk_probability: Optional[float] = Field(
        None,
        description=(
            "Model-estimated probability of HIGH risk. "
            "STRICT RULE: None for official blackspots (no fake probabilities)."
        ),
    )
    reason: str = Field(..., description="Summary explanation of why this location is hazardous")
    contributing_factors: Optional[List[ContributingFactorSummary]] = Field(
        None, description="SHAP feature contributions for ML hotspots. None for official blackspots."
    )
    road_context: Optional[HazardRoadContext] = Field(
        None,
        description="Physical road-network context from OpenStreetMap (NOT accident causality).",
    )
    safety_guidance: List[SafetyGuidanceSummary] = Field(
        default_factory=list,
        description="Evidence-based prevention countermeasures from authoritative road safety literature",
    )
    official_provenance: Optional[OfficialProvenance] = Field(
        None, description="Government registry documentation for official blackspots"
    )


class NotableRoadSegment(BaseModel):
    segment_id: str
    name: str
    highway_class: str
    start_km: float
    end_km: float
    notable_feature: str
    lanes: Optional[int] = None
    speed_limit_kmh: Optional[int] = None


class RoadContextSummary(BaseModel):
    major_highways: List[str] = Field(default_factory=list)
    road_classes: List[str] = Field(default_factory=list)
    lit_coverage_pct: Optional[float] = None
    divided_carriageway_pct: Optional[float] = None
    lane_distribution: Dict[str, float] = Field(default_factory=dict)
    speed_limit_distribution: Dict[str, float] = Field(default_factory=dict)
    total_bridges: int = 0
    total_tunnels: int = 0
    total_major_junctions: int = 0
    source_provenance: str = "OpenStreetMap Contributors (ODbL) / Overpass Infrastructure Layer"


class JourneyRequest(BaseModel):
    origin: str = Field(..., description="Journey origin city/address (e.g. 'Pune, Maharashtra')")
    destination: str = Field(..., description="Journey destination city/address (e.g. 'Nagpur, Maharashtra')")
    departure_datetime: Optional[str] = Field(
        None, description="ISO format departure datetime (e.g. '2026-08-30T20:00:00') or time ('20:00')"
    )
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None


class JourneySafetyAssessment(BaseModel):
    origin: str
    destination: str
    departure_datetime: str
    total_distance_km: float
    estimated_duration_hours: float
    estimated_duration_formatted: str
    total_hazards_count: int
    ml_hotspots_count: int
    official_blackspots_count: int
    highest_risk_time_window: str
    hazards: List[JourneyHazard]
    route_geometry: RouteGeometry
    road_context_summary: Optional[RoadContextSummary] = Field(
        None,
        description="Aggregate physical road infrastructure summary along the journey corridor",
    )
    notable_segments: List[NotableRoadSegment] = Field(
        default_factory=list,
        description="Notable physical infrastructure segments (ghats, bridges, tunnels, bottlenecks)",
    )
    responsible_ai_disclaimer: str = Field(
        default=(
            "SafeRoute AI provides pre-travel road-safety hazard assessments based on historical "
            "accident patterns and official government blackspot registries. It does NOT provide "
            "turn-by-turn navigation, route steering, or guarantee zero-accident conditions. "
            "OpenStreetMap physical road attributes describe infrastructure characteristics and "
            "do not imply direct crash causation. Drivers must follow official speed limits, road signs, "
            "and traffic police directives."
        )
    )
