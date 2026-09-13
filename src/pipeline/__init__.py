"""
SafeRoute AI — Pipeline Package

Unified analytical pipeline integrating ML prediction, SHAP explanation,
and RAG knowledge retrieval into structured Hotspot Intelligence objects.
"""

from src.pipeline.hotspot_intelligence import (
    build_single_intelligence_record,
    generate_all_hotspot_intelligence,
    get_hotspot_intelligence,
    format_hotspot_intelligence_summary,
    parse_contributing_factor,
)

__all__ = [
    "build_single_intelligence_record",
    "generate_all_hotspot_intelligence",
    "get_hotspot_intelligence",
    "format_hotspot_intelligence_summary",
    "parse_contributing_factor",
]
