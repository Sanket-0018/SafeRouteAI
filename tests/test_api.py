"""
tests/test_api.py — FastAPI endpoint tests for SafeRoute AI backend.

Tests every required endpoint using FastAPI's TestClient (no running server needed).
"""

import sys
from pathlib import Path

# Add project root to path (conftest.py also does this, but be explicit here)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# 1. GET /
# ──────────────────────────────────────────────────────────────────────────────

def test_root_status():
    resp = client.get("/")
    assert resp.status_code == 200


def test_root_structure():
    resp = client.get("/")
    data = resp.json()
    assert data["name"] == "SafeRoute AI"
    assert "endpoints" in data
    assert "responsible_ai_notice" in data
    assert "version" in data


# ──────────────────────────────────────────────────────────────────────────────
# 2. GET /health
# ──────────────────────────────────────────────────────────────────────────────

def test_health_status():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_loaded():
    resp = client.get("/health")
    data = resp.json()
    assert data["data_file_loaded"] is True
    assert data["status"] == "ok"
    assert data["record_count"] > 0
    assert "api_version" in data


# ──────────────────────────────────────────────────────────────────────────────
# 3. GET /hotspots (bare)
# ──────────────────────────────────────────────────────────────────────────────

def test_hotspots_returns_200():
    resp = client.get("/hotspots")
    assert resp.status_code == 200


def test_hotspots_structure():
    resp = client.get("/hotspots")
    data = resp.json()
    assert "total" in data
    assert "filtered" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_hotspots_default_limit():
    resp = client.get("/hotspots")
    data = resp.json()
    assert len(data["results"]) <= 20


def test_hotspots_result_fields():
    resp = client.get("/hotspots")
    data = resp.json()
    first = data["results"][0]
    required = [
        "rank", "city", "zone_id", "latitude", "longitude",
        "target_month", "time_window", "is_peak_window",
        "risk_tier", "high_probability", "top_factor",
        "top_guidance_title", "top_guidance_organization", "top_guidance_url",
    ]
    for field in required:
        assert field in first, f"Missing field: {field}"


# ──────────────────────────────────────────────────────────────────────────────
# 4. City filtering
# ──────────────────────────────────────────────────────────────────────────────

def test_city_filter_pune():
    resp = client.get("/hotspots?city=Pune")
    assert resp.status_code == 200
    data = resp.json()
    assert data["filtered"] > 0
    for r in data["results"]:
        assert r["city"] == "Pune"


def test_city_filter_case_insensitive():
    resp = client.get("/hotspots?city=pune")
    assert resp.status_code == 200
    data = resp.json()
    for r in data["results"]:
        assert r["city"] == "Pune"


def test_city_filter_unknown():
    resp = client.get("/hotspots?city=Atlantis")
    assert resp.status_code == 400
    assert "detail" in resp.json()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Risk-tier filtering
# ──────────────────────────────────────────────────────────────────────────────

def test_risk_tier_high():
    resp = client.get("/hotspots?risk_tier=HIGH")
    assert resp.status_code == 200
    data = resp.json()
    for r in data["results"]:
        assert r["risk_tier"] == "HIGH"


def test_risk_tier_invalid():
    resp = client.get("/hotspots?risk_tier=EXTREME")
    assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 6. Limit parameter
# ──────────────────────────────────────────────────────────────────────────────

def test_limit_5():
    resp = client.get("/hotspots?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 5


def test_limit_combined_with_city():
    resp = client.get("/hotspots?city=Pune&limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) <= 3


def test_limit_zero_invalid():
    resp = client.get("/hotspots?limit=0")
    assert resp.status_code == 422  # FastAPI Query validation


def test_limit_too_large_invalid():
    resp = client.get("/hotspots?limit=999")
    assert resp.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# 7. GET /hotspots/{rank}
# ──────────────────────────────────────────────────────────────────────────────

def test_hotspot_rank_1():
    resp = client.get("/hotspots/1")
    assert resp.status_code == 200


def test_hotspot_rank_1_full_structure():
    resp = client.get("/hotspots/1")
    data = resp.json()
    assert "rank" in data
    assert "location" in data
    assert "temporal" in data
    assert "prediction" in data
    assert "contributing_factors" in data
    assert "safety_guidance" in data
    assert "retrieval_query" in data


def test_hotspot_rank_1_location():
    resp = client.get("/hotspots/1")
    data = resp.json()
    loc = data["location"]
    assert "city" in loc
    assert "zone_id" in loc
    assert "latitude" in loc
    assert "longitude" in loc
    assert "cluster_radius_km" in loc


def test_hotspot_rank_1_contributing_factors():
    resp = client.get("/hotspots/1")
    data = resp.json()
    factors = data["contributing_factors"]
    assert len(factors) > 0
    f = factors[0]
    assert "feature" in f
    assert "feature_code" in f
    assert "value" in f
    assert "contribution" in f


def test_hotspot_rank_1_safety_guidance():
    resp = client.get("/hotspots/1")
    data = resp.json()
    guidance = data["safety_guidance"]
    assert len(guidance) > 0
    g = guidance[0]
    assert "title" in g
    assert "organization" in g
    assert "relevance_score" in g
    assert "source_url" in g
    # Verify URL is a real URL, not empty
    assert g["source_url"].startswith("http")


def test_hotspot_rank_5():
    resp = client.get("/hotspots/5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rank"] == 5


# ──────────────────────────────────────────────────────────────────────────────
# 8. Invalid rank
# ──────────────────────────────────────────────────────────────────────────────

def test_hotspot_rank_0_invalid():
    resp = client.get("/hotspots/0")
    assert resp.status_code == 404


def test_hotspot_rank_999_invalid():
    resp = client.get("/hotspots/999")
    assert resp.status_code == 404


def test_hotspot_rank_negative_invalid():
    resp = client.get("/hotspots/-1")
    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────────────────
# 9. GET /cities
# ──────────────────────────────────────────────────────────────────────────────

def test_cities_status():
    resp = client.get("/cities")
    assert resp.status_code == 200


def test_cities_structure():
    resp = client.get("/cities")
    data = resp.json()
    assert "cities" in data
    assert "count" in data
    assert isinstance(data["cities"], list)
    assert data["count"] == len(data["cities"])


def test_cities_content():
    resp = client.get("/cities")
    data = resp.json()
    # At minimum these Indian cities should be present
    expected = {"Pune", "Chandigarh"}
    actual = set(data["cities"])
    assert expected.issubset(actual), f"Expected cities {expected} not all in {actual}"


def test_cities_sorted():
    resp = client.get("/cities")
    data = resp.json()
    assert data["cities"] == sorted(data["cities"])


# ──────────────────────────────────────────────────────────────────────────────
# 10. GET /stats
# ──────────────────────────────────────────────────────────────────────────────

def test_stats_status():
    resp = client.get("/stats")
    assert resp.status_code == 200


def test_stats_structure():
    resp = client.get("/stats")
    data = resp.json()
    required = [
        "total_hotspot_records",
        "cities_covered",
        "risk_tier_breakdown",
        "probability_stats",
        "data_period",
        "responsible_ai_notice",
    ]
    for field in required:
        assert field in data, f"Missing stats field: {field}"


def test_stats_values():
    resp = client.get("/stats")
    data = resp.json()
    assert data["total_hotspot_records"] == 100
    assert data["probability_stats"]["min"] >= 0.0
    assert data["probability_stats"]["max"] <= 1.0
    assert data["probability_stats"]["max"] >= data["probability_stats"]["min"]
    assert "HIGH" in data["risk_tier_breakdown"]


def test_stats_responsible_ai_notice():
    resp = client.get("/stats")
    data = resp.json()
    notice = data["responsible_ai_notice"]
    assert len(notice) > 50
    # Must NOT contain overconfident language
    assert "will happen" not in notice.lower()
    assert "guaranteed" not in notice.lower()


# ──────────────────────────────────────────────────────────────────────────────
# 11. POST & GET /check-risk (Location Risk Lookup & Coverage Boundary)
# ──────────────────────────────────────────────────────────────────────────────

def test_check_risk_covered_pune():
    # Pune Hadapsar corridor coordinates (18.4966, 73.8833)
    resp = client.post(
        "/check-risk",
        json={
            "latitude": 18.4966,
            "longitude": 73.8833,
            "location_name": "Hadapsar, Pune",
            "travel_time": "19:30",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["covered"] is True
    assert "intelligence" in data and data["intelligence"] is not None
    assert data["intelligence"]["prediction"]["risk_tier"] == "HIGH"
    assert data["intelligence"]["location"]["city"] == "Pune"
    assert len(data["intelligence"]["contributing_factors"]) > 0
    assert len(data["intelligence"]["safety_guidance"]) > 0


def test_check_risk_unsupported_nagpur():
    # Nagpur coordinates (21.1458, 79.0882) - outside model training coverage
    resp = client.post(
        "/check-risk",
        json={
            "latitude": 21.1458,
            "longitude": 79.0882,
            "location_name": "Nagpur, Maharashtra",
            "travel_time": "20:00",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["covered"] is False
    assert data["intelligence"] is None
    assert "sufficient trained accident data" in data["message"].lower()
    assert data["distance_km"] > 50.0  # Far away from evaluated corridors


def test_check_risk_get_endpoint():
    resp = client.get("/check-risk?lat=18.4966&lon=73.8833&name=Pune&time=02:00")
    assert resp.status_code == 200
    data = resp.json()
    assert data["covered"] is True
    assert "Late Night" in data["time_window"]
