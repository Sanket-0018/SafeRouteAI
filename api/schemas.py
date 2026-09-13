"""
SafeRoute AI — FastAPI Backend
Pydantic response schemas for all API endpoints.
"""

from __future__ import annotations
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Sub-models mirroring the hotspot_intelligence.json structure
# ──────────────────────────────────────────────────────────────────────────────

class Location(BaseModel):
    city: str
    zone_id: int
    latitude: float
    longitude: float
    cluster_radius_km: float
    area_name: Optional[str] = Field(None, description="Human-readable corridor or landmark name")


class Temporal(BaseModel):
    target_month: str
    target_start_date: str
    time_window: str
    is_peak_window: bool


class Prediction(BaseModel):
    risk_tier: str = Field(..., description="Predicted risk tier: HIGH, MEDIUM, or LOW")
    high_probability: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Model-estimated probability of HIGH risk. Historical base rate is ~6.5%.",
    )
    actual_risk_tier: Optional[str] = Field(
        None,
        description="Actual observed risk tier (from historical test-period data). "
                    "Only available for out-of-time test predictions.",
    )


class ContributingFactor(BaseModel):
    feature: str = Field(..., description="Human-readable description of the predictive feature")
    feature_code: str = Field(..., description="Machine-readable feature identifier")
    value: float = Field(..., description="Observed feature value for this hotspot/window")
    contribution: float = Field(
        ...,
        description=(
            "SHAP contribution to the HIGH-risk prediction. "
            "Positive values increase predicted probability. "
            "This reflects statistical model sensitivity, NOT proven causation."
        ),
    )


class SafetyGuidance(BaseModel):
    rank: int
    chunk_id: str
    title: str
    organization: str
    topic: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    source_url: str
    document_type: str
    content_excerpt: str


# ──────────────────────────────────────────────────────────────────────────────
# Top-level Hotspot Intelligence record
# ──────────────────────────────────────────────────────────────────────────────

class HotspotIntelligence(BaseModel):
    rank: int
    location: Location
    temporal: Temporal
    prediction: Prediction
    contributing_factors: List[ContributingFactor]
    retrieval_query: str = Field(
        ...,
        description=(
            "Semantic query constructed from SHAP factors used to retrieve "
            "authoritative safety guidance. For transparency only."
        ),
    )
    safety_guidance: List[SafetyGuidance]


# ──────────────────────────────────────────────────────────────────────────────
# User-Centric Risk Check Request & Response
# ──────────────────────────────────────────────────────────────────────────────

class CheckRiskRequest(BaseModel):
    latitude: float = Field(..., description="Target latitude coordinate")
    longitude: float = Field(..., description="Target longitude coordinate")
    location_name: Optional[str] = Field(None, description="User-supplied or geocoded location name")
    travel_time: Optional[str] = Field(None, description="Planned travel time (e.g. '19:30' or '21:00')")
    travel_date: Optional[str] = Field(None, description="Planned travel date (e.g. '2025-03-15')")


class CheckRiskResponse(BaseModel):
    covered: bool = Field(..., description="True if location falls within evaluated training coverage")
    location_name: str = Field(..., description="Human-readable location label")
    latitude: float
    longitude: float
    time_window: str = Field(..., description="Mapped 4-hour travel risk window")
    message: str = Field(..., description="Status or coverage explanation")
    distance_km: Optional[float] = Field(None, description="Distance in km to nearest evaluated corridor")
    nearest_supported_city: Optional[str] = Field(None, description="Nearest evaluated city")
    intelligence: Optional[HotspotIntelligence] = Field(
        None, description="Full risk intelligence object if location is covered"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Summary / list response models
# ──────────────────────────────────────────────────────────────────────────────

class HotspotSummary(BaseModel):
    """Lightweight record for list endpoints (avoids sending full guidance text)."""
    rank: int
    city: str
    zone_id: int
    area_name: Optional[str] = None
    latitude: float
    longitude: float
    target_month: str
    time_window: str
    is_peak_window: bool
    risk_tier: str
    high_probability: float
    top_factor: str
    top_guidance_title: str
    top_guidance_organization: str
    top_guidance_url: str


class HotspotsResponse(BaseModel):
    total: int
    filtered: int
    results: List[HotspotSummary]


class CitiesResponse(BaseModel):
    cities: List[str]
    count: int


class StatsResponse(BaseModel):
    total_hotspot_records: int
    cities_covered: List[str]
    risk_tier_breakdown: dict
    probability_stats: dict
    data_period: dict
    responsible_ai_notice: str


class HealthResponse(BaseModel):
    status: str
    data_file_loaded: bool
    record_count: int
    api_version: str


class RootResponse(BaseModel):
    name: str
    version: str
    description: str
    endpoints: dict
    responsible_ai_notice: str


# ──────────────────────────────────────────────────────────────────────────────
# Journey & Geocoding Schemas (re-exported for API use)
# ──────────────────────────────────────────────────────────────────────────────
from src.journey.geocoding import PlaceItem
from src.journey.schemas import (
    JourneyHazard,
    JourneyRequest,
    JourneySafetyAssessment,
    RouteGeometry,
)


class PlacesAutocompleteResponse(BaseModel):
    query: str
    count: int
    results: List[PlaceItem]


# ──────────────────────────────────────────────────────────────────────────────
# IBM Bob AI Journey Brief Schemas
# ──────────────────────────────────────────────────────────────────────────────

class HazardBriefItem(BaseModel):
    type: str = Field(..., description="Hazard type (e.g. 'ML hotspot' or 'Official blackspot')")
    name: str = Field(..., description="Location name or road description")
    distance_km: float = Field(..., description="Distance in km from origin")
    eta: Optional[str] = Field(None, description="Expected arrival time (e.g. '20:12')")
    risk_tier: Optional[str] = Field(None, description="Risk tier")


class JourneyAiBriefRequest(BaseModel):
    route: str = Field(..., description="Route corridor string (e.g. 'Pune → Nagpur')")
    distance_km: float = Field(..., description="Total driving distance in km")
    duration: str = Field(..., description="Estimated travel duration formatted (e.g. '8h 17m')")
    departure: Optional[str] = Field(None, description="Departure datetime or time")
    risk_window: Optional[str] = Field(None, description="Elevated risk window")
    hazards: List[HazardBriefItem] = Field(default_factory=list, description="Top identified hazards along route")


class JourneyAiBriefResponse(BaseModel):
    brief: str = Field(..., description="Concise AI-generated safety briefing from IBM Bob")
    model: str = Field(default="IBM Bob (premium-ide)", description="Generative AI model used")
    disclaimer: str = Field(
        default="AI-generated decision support based on available historical and official evidence. It does not guarantee safety.",
        description="Responsible AI disclaimer"
    )
