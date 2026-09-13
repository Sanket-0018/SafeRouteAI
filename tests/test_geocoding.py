"""
SafeRoute AI — Place Search & Geocoding Autocomplete Tests
Tests query normalization, empty/short query handling, local indexing,
OSM Nominatim fallback, coordinate validity, deduplication, and caching.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from api.main import app
from src.journey.geocoding import PlaceItem, search_places

client = TestClient(app)


def test_autocomplete_endpoint_status():
    resp = client.get("/places/autocomplete?q=Pune")
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "count" in data
    assert "results" in data
    assert data["count"] > 0


def test_empty_query_handled_correctly():
    resp = client.get("/places/autocomplete?q=")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_short_query_handled_correctly():
    resp = client.get("/places/autocomplete?q=a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_pune_search():
    resp = client.get("/places/autocomplete?q=Pune")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    names = [r["display_name"].lower() for r in data["results"]]
    assert any("pune" in n for n in names)
    # Check that coordinate is around Pune (18.5N, 73.8E)
    first = data["results"][0]
    assert 18.0 <= first["latitude"] <= 19.0
    assert 73.0 <= first["longitude"] <= 74.5


def test_nagpur_search():
    resp = client.get("/places/autocomplete?q=Nag")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    names = [r["display_name"].lower() for r in data["results"]]
    assert any("nagpur" in n for n in names)
    first = next(r for r in data["results"] if "nagpur" in r["display_name"].lower())
    assert 20.5 <= first["latitude"] <= 21.5
    assert 78.5 <= first["longitude"] <= 79.5


def test_nashik_search():
    resp = client.get("/places/autocomplete?q=Nashik")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    names = [r["display_name"].lower() for r in data["results"]]
    assert any("nashik" in n for n in names)


def test_sambhajinagar_search():
    resp = client.get("/places/autocomplete?q=Sambhajinagar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    names = [r["display_name"].lower() for r in data["results"]]
    assert any("sambhajinagar" in n or "aurangabad" in n for n in names)


def test_unknown_place_handled_gracefully():
    resp = client.get("/places/autocomplete?q=xyz123fakeplace999notexist")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_results_contain_valid_coordinates_and_schema():
    resp = client.get("/places/autocomplete?q=Mumbai")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    for item in data["results"]:
        assert isinstance(item["latitude"], float)
        assert isinstance(item["longitude"], float)
        assert -90.0 <= item["latitude"] <= 90.0
        assert -180.0 <= item["longitude"] <= 180.0
        assert "display_name" in item and item["display_name"] != ""
        assert "place_type" in item


def test_duplicate_places_removed():
    results = search_places("Pune", limit=10)
    seen = set()
    for r in results:
        key = r.display_name.lower().strip()
        assert key not in seen, f"Duplicate place detected: {key}"
        seen.add(key)


def test_backend_never_exposes_raw_provider_errors():
    # Pass special characters or weird input; should always return 200 with clean response
    resp = client.get("/places/autocomplete?q=???&&&%%%")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_geocoding_caching():
    # Perform search twice; verify second search returns successfully
    res1 = search_places("Solapur", limit=5)
    res2 = search_places("Solapur", limit=5)
    assert len(res1) > 0
    assert len(res2) > 0
    assert res1[0].display_name == res2[0].display_name
