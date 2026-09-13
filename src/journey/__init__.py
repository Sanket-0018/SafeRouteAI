"""
SafeRoute AI — Journey Road-Safety Assessment Module
Spatially and temporally matches user journeys to ML urban hotspots and official highway blackspots.
"""

from src.journey.schemas import (
    JourneyHazard,
    JourneyRequest,
    JourneySafetyAssessment,
    RouteGeometry,
)
from src.journey.journey_analyzer import analyze_journey_safety

__all__ = [
    "JourneyRequest",
    "JourneyHazard",
    "JourneySafetyAssessment",
    "RouteGeometry",
    "analyze_journey_safety",
]
