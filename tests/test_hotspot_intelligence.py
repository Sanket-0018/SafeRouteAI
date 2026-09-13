"""
test_hotspot_intelligence.py — Automated Tests for SafeRoute AI Unified Pipeline

Tests:
1. Hotspot matching integrity (zone_id, target_month, time_window)
2. SHAP factor parsing and attribution matching
3. RAG retrieval connectivity and relevance score calculation
4. Required output fields in both dict and flat representations
5. Source provenance retention (title, organization, URL, retrieval date)
6. JSON serialization validation
"""

import os
import json
import pytest
import pandas as pd

from src.pipeline.hotspot_intelligence import (
    build_single_intelligence_record,
    flatten_intelligence_for_csv,
    parse_contributing_factor,
    get_hotspot_intelligence,
    DEFAULT_RANKED_PATH,
    DEFAULT_EXPLANATIONS_PATH,
    DEFAULT_CHROMA_DIR,
)


@pytest.fixture
def ranked_df():
    return pd.read_csv(DEFAULT_RANKED_PATH)


@pytest.fixture
def expl_df():
    return pd.read_csv(DEFAULT_EXPLANATIONS_PATH)


def test_contributing_factor_parsing():
    """Test 2: SHAP factor parsing into structured representation."""
    sample_str = "Persistent accident history in prior 180 days (value: 38.00, impact: +0.452)"
    parsed = parse_contributing_factor(sample_str)
    
    assert parsed is not None
    assert parsed["feature"] == "Persistent accident history in prior 180 days"
    assert parsed["feature_code"] == "lag_accidents_180d"
    assert parsed["value"] == 38.00
    assert parsed["contribution"] == 0.452


def test_hotspot_and_shap_matching(ranked_df, expl_df):
    """Test 1 & 2: Verify hotspot records correctly match their corresponding SHAP explanations."""
    top_ranked = ranked_df.iloc[0]
    
    # Exact key match
    match = expl_df[
        (expl_df["zone_id"] == top_ranked["zone_id"]) &
        (expl_df["target_month"] == top_ranked["target_month"]) &
        (expl_df["time_window_label"] == top_ranked["time_window_label"])
    ]
    
    assert len(match) == 1
    expl_row = match.iloc[0]
    
    assert expl_row["city"] == top_ranked["city"]
    assert round(expl_row["predicted_high_probability"], 4) == round(top_ranked["predicted_high_probability"], 4)
    assert expl_row["predicted_risk_tier"] == top_ranked["predicted_risk_tier"]


def test_rag_retrieval_connection(ranked_df, expl_df):
    """Test 3: Verify RAG vector store connects and retrieves top-k safety guidance."""
    top_ranked = ranked_df.iloc[0]
    expl_row = expl_df.iloc[0]
    
    record = build_single_intelligence_record(
        ranked_row=top_ranked,
        expl_row=expl_row,
        chroma_dir=DEFAULT_CHROMA_DIR,
        top_k_rag=3,
        rank=1,
    )
    
    assert "safety_guidance" in record
    assert len(record["safety_guidance"]) == 3
    
    # Check retrieval relevance scores are within valid cosine bounds [0, 1]
    for g in record["safety_guidance"]:
        assert 0.0 <= g["relevance_score"] <= 1.0


def test_required_output_fields(ranked_df, expl_df):
    """Test 4: Verify all mandatory fields exist in both structured and flat records."""
    record = build_single_intelligence_record(
        ranked_row=ranked_df.iloc[0],
        expl_row=expl_df.iloc[0],
        chroma_dir=DEFAULT_CHROMA_DIR,
        top_k_rag=3,
        rank=1,
    )
    
    # Structured object schema checks
    assert "rank" in record
    assert "location" in record
    assert all(k in record["location"] for k in ["city", "zone_id", "latitude", "longitude"])
    assert "temporal" in record
    assert all(k in record["temporal"] for k in ["target_month", "time_window"])
    assert "prediction" in record
    assert all(k in record["prediction"] for k in ["risk_tier", "high_probability"])
    assert "contributing_factors" in record
    assert "safety_guidance" in record
    
    # Flat CSV row schema checks
    flat = flatten_intelligence_for_csv(record)
    required_flat_keys = [
        "rank", "city", "zone_id", "latitude", "longitude", "target_month",
        "target_start_date", "time_window", "predicted_risk_tier",
        "predicted_high_probability", "top_shap_factors", "factor_contributions",
        "retrieved_guidance", "source_organization", "source_title", "source_url",
        "retrieval_score"
    ]
    for k in required_flat_keys:
        assert k in flat, f"Missing required flat field: {k}"


def test_source_provenance_retention(ranked_df, expl_df):
    """Test 5: Verify source provenance (title, organization, URL) is retained without fabrication."""
    record = build_single_intelligence_record(
        ranked_row=ranked_df.iloc[0],
        expl_row=expl_df.iloc[0],
        chroma_dir=DEFAULT_CHROMA_DIR,
        top_k_rag=3,
        rank=1,
    )
    
    for g in record["safety_guidance"]:
        assert len(g["title"]) > 0
        assert len(g["organization"]) > 0
        assert g["source_url"].startswith("http")
        assert g["chunk_id"] != ""


def test_json_serialization(ranked_df, expl_df):
    """Test 6: Verify intelligence object can be serialized to JSON and deserialized identically."""
    record = build_single_intelligence_record(
        ranked_row=ranked_df.iloc[0],
        expl_row=expl_df.iloc[0],
        chroma_dir=DEFAULT_CHROMA_DIR,
        top_k_rag=3,
        rank=1,
    )
    
    json_str = json.dumps(record, ensure_ascii=False)
    assert len(json_str) > 0
    
    deserialized = json.loads(json_str)
    assert deserialized["rank"] == record["rank"]
    assert deserialized["location"]["city"] == record["location"]["city"]
    assert deserialized["prediction"]["high_probability"] == record["prediction"]["high_probability"]


def test_query_helper_function():
    """Test callable helper function get_hotspot_intelligence."""
    # Query by rank
    record = get_hotspot_intelligence(rank=1)
    assert record is not None
    assert record["rank"] == 1
    assert record["location"]["city"] == "Pune"
    
    # Query by city + zone_id
    record_zone = get_hotspot_intelligence(city="Pune", zone_id=363)
    assert record_zone is not None
    assert record_zone["location"]["zone_id"] == 363
