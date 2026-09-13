import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.journey.journey_analyzer import analyze_journey_safety
from src.journey.schemas import JourneyRequest

corridors = [
    ("Mumbai, Maharashtra", "Pune, Maharashtra"),
    ("Pune, Maharashtra", "Nashik, Maharashtra"),
    ("Pune, Maharashtra", "Nagpur, Maharashtra"),
    ("Pune, Maharashtra", "Chhatrapati Sambhajinagar, Maharashtra"),
    ("Pune, Maharashtra", "Solapur, Maharashtra"),
    ("Mumbai, Maharashtra", "Nashik, Maharashtra"),
    ("Mumbai, Maharashtra", "Nagpur, Maharashtra"),
    ("Pune, Maharashtra", "Kolhapur, Maharashtra"),
    ("Mumbai, Maharashtra", "Goa, India"),
    ("Solapur, Maharashtra", "Chhatrapati Sambhajinagar, Maharashtra"),
    ("Nagpur, Maharashtra", "Pune, Maharashtra"),
    ("Nashik, Maharashtra", "Pune, Maharashtra"),
    ("Latur, Maharashtra", "Pune, Maharashtra"),
    ("Kolhapur, Maharashtra", "Pune, Maharashtra"),
    ("Nanded, Maharashtra", "Chhatrapati Sambhajinagar, Maharashtra"),
]

def main():
    results = []
    print("================================================================================")
    print("SAFE ROUTE AI — MAHARASHTRA CORRIDOR HAZARD COVERAGE AUDIT")
    print("================================================================================")
    for orig, dest in corridors:
        req = JourneyRequest(origin=orig, destination=dest, departure_datetime="2026-08-30T20:00:00")
        res = analyze_journey_safety(req)
        
        c_name = f"{orig.split(',')[0]} -> {dest.split(',')[0]}"
        print(f"\nRoute: {c_name}")
        print(f"  * Distance: {res.total_distance_km:.1f} km | Duration: {res.estimated_duration_formatted}")
        print(f"  * Hazard Breakdown: Total = {res.total_hazards_count} (ML Hotspots = {res.ml_hotspots_count}, Official Blackspots = {res.official_blackspots_count})")
        print(f"  * Peak Risk Window: {res.highest_risk_time_window}")
        
        milestones = [f"#{h.sequence} {h.location_name} [{h.hazard_type.split('_')[0]}] @ {h.distance_from_origin_km}km ({h.expected_arrival_time})" for h in res.hazards]
        print("  * Milestones along route:")
        for m in milestones:
            print(f"     - {m}")
            
        results.append({
            "corridor": c_name,
            "distance_km": res.total_distance_km,
            "duration": res.estimated_duration_formatted,
            "total_hazards": res.total_hazards_count,
            "ml_hotspots": res.ml_hotspots_count,
            "official_blackspots": res.official_blackspots_count,
            "coverage_density_per_100km": round(res.total_hazards_count / (res.total_distance_km / 100.0), 2) if res.total_distance_km > 0 else 0
        })

    df = pd.DataFrame(results)
    print("\n================================================================================")
    print("CORRIDOR COVERAGE SUMMARY TABLE")
    print("================================================================================")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
