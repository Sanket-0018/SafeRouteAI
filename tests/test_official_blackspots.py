"""
SafeRoute AI — Official Maharashtra Blackspots Evidence Layer Tests
Tests schema validation, geographic coordinate bounding, duplicate prevention,
official provenance retention, and route corridor spatial isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from src.journey.journey_analyzer import analyze_journey_safety, _load_official_blackspots
from src.journey.schemas import JourneyRequest

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "external"
BLACKSPOTS_JSON = DATA_DIR / "maharashtra_official_blackspots.json"
BLACKSPOTS_CSV = DATA_DIR / "maharashtra_official_blackspots.csv"


def test_blackspots_files_exist():
    assert BLACKSPOTS_JSON.exists(), f"Missing {BLACKSPOTS_JSON}"
    assert BLACKSPOTS_CSV.exists(), f"Missing {BLACKSPOTS_CSV}"


def test_load_official_blackspots_registry():
    records = _load_official_blackspots()
    assert len(records) >= 30, f"Expected at least 30 verified blackspots, found {len(records)}"


def test_schema_and_required_fields():
    records = _load_official_blackspots()
    for r in records:
        assert ("blackspot_id" in r or "hazard_id" in r), "Missing blackspot_id/hazard_id"
        assert ("location_name" in r or "name" in r), "Missing location_name/name"
        assert "latitude" in r and "longitude" in r, "Missing latitude/longitude"
        assert ("highway_number" in r or "highway" in r), "Missing highway"
        assert "district" in r, "Missing district"
        assert ("source_authority" in r or "reporting_authority" in r or "source_organization" in r), "Missing authority"
        assert ("publication_year" in r or "report_year" in r), "Missing publication year"
        assert "source_url" in r and r["source_url"].startswith("http"), "Missing/invalid source_url"
        assert ("confidence" in r or "confidence_level" in r), "Missing confidence"


def test_coordinate_validity_maharashtra_bounds():
    records = _load_official_blackspots()
    for r in records:
        lat = float(r["latitude"])
        lon = float(r["longitude"])
        # Maharashtra geographic bounding box: ~15.0°N to 22.5°N, ~72.0°E to 81.5°E
        assert 15.0 <= lat <= 22.5, f"Latitude {lat} out of Maharashtra bounds for {r['blackspot_id']}"
        assert 72.0 <= lon <= 81.5, f"Longitude {lon} out of Maharashtra bounds for {r['blackspot_id']}"


def test_no_duplicate_blackspot_ids():
    records = _load_official_blackspots()
    ids = [r["blackspot_id"] for r in records]
    assert len(ids) == len(set(ids)), f"Duplicate blackspot IDs found in registry: {len(ids) - len(set(ids))}"


def test_source_provenance_retention():
    records = _load_official_blackspots()
    valid_authorities = [
        "Maharashtra Highway Traffic Police",
        "Pune Rural Police",
        "Pune City Police & MoRTH",
        "Thane City Traffic Police & PWD",
        "Nashik City Traffic Police",
        "Nashik Rural Police & MoRTH",
        "MoRTH & Ahmednagar Police",
        "MoRTH & Palghar District Police",
        "MoRTH & Maharashtra Highway Police",
        "Chhatrapati Sambhaji Nagar Rural Police & MoRTH",
        "Jalna District Police",
        "Amravati City Police",
        "Wardha District Police",
        "Nagpur Rural Police & MoRTH",
        "Nagpur City Police",
        "Satara Rural Police & MoRTH",
        "Solapur Rural Police & MoRTH",
        "Solapur City Police",
        "Kolhapur City Police & NHAI",
        "Sindhudurg District Police & MoRTH",
        "Ratnagiri District Police",
        "Maharashtra State Road Development Corporation (MSRDC)",
        "MSRDC & Highway Police",
        "Washim District Police & MSRDC",
        "NHAI & Maharashtra Highway Police",
    ]
    for r in records:
        assert r["source_url"].startswith("http"), f"Invalid source URL: {r['source_url']}"
        yr = r.get("publication_year") or r.get("report_year")
        assert yr in [2022, 2023, 2024], f"Unexpected report year: {yr}"
        auth = r.get("source_authority") or r.get("reporting_authority") or ""
        assert any(k.lower() in auth.lower() for k in ["police", "morth", "nhai", "msrdc", "pwd"])


def test_corridor_spatial_isolation():
    # Mumbai to Pune should match Borghat, Urse, Somatane etc., but NOT Nagpur / Amravati
    req_mp = JourneyRequest(
        origin="Mumbai, Maharashtra",
        destination="Pune, Maharashtra",
        departure_datetime="2026-08-30T08:00:00",
    )
    res_mp = analyze_journey_safety(req_mp)
    mp_districts = {h.district for h in res_mp.hazards if h.district}
    assert "Raigad" in mp_districts or "Pune" in mp_districts or "Thane" in mp_districts
    assert "Nagpur" not in mp_districts, "Nagpur blackspots must NOT appear on Mumbai–Pune journey!"
    assert "Wardha" not in mp_districts, "Wardha blackspots must NOT appear on Mumbai–Pune journey!"


def test_zero_fake_probabilities_for_official_blackspots():
    req = JourneyRequest(
        origin="Pune, Maharashtra",
        destination="Nagpur, Maharashtra",
        departure_datetime="2026-08-30T20:00:00",
    )
    res = analyze_journey_safety(req)
    for h in res.hazards:
        if h.hazard_type == "OFFICIAL_BLACKSPOT":
            assert h.risk_probability is None, "Official blackspots must NEVER have fake probabilities!"
            assert h.contributing_factors is None, "Official blackspots must NEVER have fake SHAP factors!"
            assert h.official_provenance is not None
            assert h.official_provenance.source_organization != ""
            assert h.official_provenance.source_url.startswith("http")
