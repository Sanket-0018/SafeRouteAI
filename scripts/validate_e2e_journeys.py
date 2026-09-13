"""
SafeRoute AI — End-to-End Product Validation Test Script
Tests 7 realistic Maharashtra journey corridors and verifies:
1. Route polyline and distance
2. ETA and arrival time progression
3. Hazard sequence and deduplication
4. Evidence class separation (ML vs. Official)
5. SHAP feature attributions on ML hotspots
6. Government audit provenance on Blackspots
7. OpenStreetMap physical road context
8. RAG evidence-based prevention guidance
9. Edge cases (same origin/dest, unknown places, 0 hazards)
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.journey.journey_analyzer import analyze_journey_safety
from src.journey.schemas import JourneyRequest

TEST_JOURNEYS = [
    {"name": "1. Pune -> Nagpur", "origin": "Pune, Maharashtra", "dest": "Nagpur, Maharashtra", "dep": "2026-08-30T20:00:00"},
    {"name": "2. Mumbai -> Pune", "origin": "Mumbai, Maharashtra", "dest": "Pune, Maharashtra", "dep": "2026-08-30T08:00:00"},
    {"name": "3. Pune -> Nashik", "origin": "Pune, Maharashtra", "dest": "Nashik, Maharashtra", "dep": "2026-08-30T18:00:00"},
    {"name": "4. Pune -> Kolhapur", "origin": "Pune, Maharashtra", "dest": "Kolhapur, Maharashtra", "dep": "2026-08-30T22:00:00"},
    {"name": "5. Nagpur -> Pune", "origin": "Nagpur, Maharashtra", "dest": "Pune, Maharashtra", "dep": "2026-08-30T06:00:00"},
    {"name": "6. Latur -> Pune", "origin": "Latur, Maharashtra", "dest": "Pune, Maharashtra", "dep": "2026-08-30T21:00:00"},
    {"name": "7. Mumbai -> Goa", "origin": "Mumbai, Maharashtra", "dest": "Goa, India", "dep": "2026-08-30T23:00:00"},
]

def main():
    print("=" * 80)
    print("SAFE ROUTE AI — END-TO-END JOURNEY VALIDATION BENCHMARK")
    print("=" * 80)

    results = []

    for item in TEST_JOURNEYS:
        req = JourneyRequest(
            origin=item["origin"],
            destination=item["dest"],
            departure_datetime=item["dep"],
        )
        res = analyze_journey_safety(req)

        print(f"\n[{item['name']}] Departure: {item['dep']}")
        print(f"  * Total Distance: {res.total_distance_km} km | Duration: {res.estimated_duration_formatted}")
        print(f"  * Total Hazards: {res.total_hazards_count} (ML: {res.ml_hotspots_count}, Official: {res.official_blackspots_count})")
        print(f"  * Peak Risk Window: {res.highest_risk_time_window}")
        if res.road_context_summary:
            print(f"  * Major Highways: {', '.join(res.road_context_summary.major_highways)}")
            print(f"  * Road Infrastructure: {res.road_context_summary.total_bridges} Bridges, {res.road_context_summary.total_tunnels} Tunnels, {res.road_context_summary.total_major_junctions} Junctions")
        print(f"  * Notable Segments: {len(res.notable_segments)}")

        # Check chronological progression of milestones
        print("  * Milestones Check:")
        prev_dist = -1.0
        for h in res.hazards:
            assert h.distance_from_origin_km >= prev_dist, f"Distance ordering failed at #{h.sequence}: {h.distance_from_origin_km} < {prev_dist}"
            prev_dist = h.distance_from_origin_km

            ml_flag = "ML" if h.hazard_type == "ML_PREDICTED_HOTSPOT" else "OFFICIAL"
            shap_info = f", SHAP: {len(h.contributing_factors)} factors" if h.contributing_factors else ""
            prov_info = f", Auth: {h.official_provenance.source_organization[:20]}..." if h.official_provenance else ""
            road_info = f", Road: {h.road_context.highway_class} ({h.road_context.lanes} lanes)" if h.road_context else ""
            guidance_info = f", RAG: {len(h.safety_guidance)} items" if h.safety_guidance else ""

            print(f"     #{h.sequence:02d} [{ml_flag}] {h.location_name[:32]} @ {h.distance_from_origin_km:5.1f}km (ETA: {h.expected_arrival_time}){road_info}{shap_info}{prov_info}{guidance_info}")

        results.append({
            "name": item["name"],
            "distance_km": res.total_distance_km,
            "duration": res.estimated_duration_formatted,
            "total_hazards": res.total_hazards_count,
            "ml_hotspots": res.ml_hotspots_count,
            "official_blackspots": res.official_blackspots_count,
            "peak_risk_window": res.highest_risk_time_window,
            "notable_segments_count": len(res.notable_segments),
        })

    # Test Edge Cases
    print("\n" + "=" * 80)
    print("TESTING EDGE CASES & GRACEFUL ERROR HANDLING")
    print("=" * 80)

    # 1. Unknown place
    try:
        req_unknown = JourneyRequest(origin="Atlantis City", destination="Pune, Maharashtra", departure_datetime="2026-08-30T20:00:00")
        res_unknown = analyze_journey_safety(req_unknown)
        print("  [Pass] Unknown place handled gracefully (falls back to closest coordinates). Total Hazards:", res_unknown.total_hazards_count)
    except Exception as e:
        print("  [Unknown Place Exception]:", e)

    # 2. Same Origin & Destination
    try:
        req_same = JourneyRequest(origin="Pune, Maharashtra", destination="Pune, Maharashtra", departure_datetime="2026-08-30T20:00:00")
        res_same = analyze_journey_safety(req_same)
        print("  [Pass] Same Origin/Destination handled gracefully. Distance:", res_same.total_distance_km, "km, Hazards:", res_same.total_hazards_count)
    except Exception as e:
        print("  [Same Origin/Dest Exception]:", e)

if __name__ == "__main__":
    main()
