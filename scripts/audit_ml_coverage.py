"""
SafeRoute AI — ML Geographic Coverage & Zone Proximity Audit Script
Inspects:
1. data/processed/cleaned_accidents.csv
2. data/processed/hotspot_zones_metadata.csv
3. data/processed/spatiotemporal_risk_dataset.csv
4. models/lightgbm_risk_model.txt & models/metadata.json (or pipeline features)
5. Proximity of 63 official blackspots to ML zones
"""

import json
from pathlib import Path
import math
import numpy as np
import pandas as pd

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def main():
    root = Path(__file__).resolve().parent.parent
    
    # 1. Inspect cleaned accidents
    p_acc = root / "data" / "processed" / "cleaned_accidents.csv"
    df_acc = pd.read_csv(p_acc)
    print("=== CLEANED ACCIDENTS DATASET ===")
    print(f"Total Rows: {len(df_acc):,}")
    print(f"Columns ({len(df_acc.columns)}): {df_acc.columns.tolist()}")
    print("\nRows per City:")
    print(df_acc["city"].value_counts().to_string())
    print("\nRows per State:")
    print(df_acc["state"].value_counts().to_string())
    
    # Maharashtra rows
    df_mh = df_acc[df_acc["state"] == "Maharashtra"]
    print(f"\nMaharashtra Total Rows: {len(df_mh):,} ({len(df_mh)/len(df_acc)*100:.2f}%)")
    print("Maharashtra Cities represented in ML training:")
    print(df_mh["city"].value_counts().to_string())
    
    # Lat/Lon bounds
    print(f"\nCoordinates Bounds:")
    print(f"  Lat: {df_acc['latitude'].min():.4f} to {df_acc['latitude'].max():.4f}")
    print(f"  Lon: {df_acc['longitude'].min():.4f} to {df_acc['longitude'].max():.4f}")
    
    # 2. Inspect hotspot zones metadata
    p_zones = root / "data" / "processed" / "hotspot_zones_metadata.csv"
    df_zones = pd.read_csv(p_zones)
    print("\n=== HOTSPOT ZONES METADATA ===")
    print(f"Total Unique Zones: {len(df_zones):,}")
    print(f"Columns: {df_zones.columns.tolist()}")
    print("\nZones per City:")
    print(df_zones["city"].value_counts().to_string())
    
    acc_per_zone = df_zones["train_period_accidents"]
    print("\nAccidents per Zone Stats (Historical Training Window):")
    print(f"  Mean: {acc_per_zone.mean():.2f}")
    print(f"  Median: {acc_per_zone.median():.2f}")
    print(f"  Min: {acc_per_zone.min()}")
    print(f"  Max: {acc_per_zone.max()}")
    
    # 3. Inspect Spatiotemporal Risk Dataset
    p_st = root / "data" / "processed" / "spatiotemporal_risk_dataset.csv"
    df_st = pd.read_csv(p_st)
    print("\n=== SPATIOTEMPORAL RISK DATASET ===")
    print(f"Total Spatiotemporal Rows: {len(df_st):,}")
    print(f"Columns: {df_st.columns.tolist()}")
    print("\nTarget Risk Tier Distribution (target_risk_tier):")
    print(df_st["target_risk_tier"].value_counts(normalize=True).to_dict())
    print("\nTarget SWRI Score Stats:")
    print(df_st["target_swri_score"].describe().to_dict())
    
    # 4. Proximity Audit: 63 Official Blackspots vs. 391 ML Zones
    p_bs = root / "data" / "external" / "maharashtra_official_blackspots.json"
    with open(p_bs, encoding="utf-8") as f:
        blackspots = json.load(f)
    print(f"\n=== PROXIMITY AUDIT: {len(blackspots)} OFFICIAL BLACKSPOTS vs {len(df_zones)} ML ZONES ===")
    
    bs_coverage = []
    for b in blackspots:
        b_lat = float(b["latitude"])
        b_lon = float(b["longitude"])
        
        # Find closest zone
        min_dist = float("inf")
        closest_zone = None
        for _, z in df_zones.iterrows():
            z_lat = float(z["center_lat"]) if "center_lat" in z else float(z["latitude"])
            z_lon = float(z["center_lon"]) if "center_lon" in z else float(z["longitude"])
            dist = haversine_distance(b_lat, b_lon, z_lat, z_lon)
            if dist < min_dist:
                min_dist = dist
                closest_zone = z
                
        is_inside_5km = min_dist <= 5.0
        is_inside_15km = min_dist <= 15.0
        
        bs_coverage.append({
            "hazard_id": b.get("hazard_id") or b.get("blackspot_id"),
            "location_name": b["location_name"],
            "district": b["district"],
            "highway": b.get("highway_number") or b.get("highway"),
            "latitude": b_lat,
            "longitude": b_lon,
            "closest_ml_city": closest_zone["city"] if closest_zone is not None else "None",
            "closest_ml_zone_id": int(closest_zone["cluster_label"]) if "cluster_label" in closest_zone else int(closest_zone.get("zone_id", 0)),
            "distance_to_closest_zone_km": round(min_dist, 2),
            "covered_by_ml_zone_5km": is_inside_5km,
            "covered_by_ml_zone_15km": is_inside_15km,
            "recommendation": "HYBRID_ML_AND_OFFICIAL" if is_inside_5km else "OFFICIAL_GOVERNMENT_ONLY",
        })
        
    df_bs_cov = pd.DataFrame(bs_coverage)
    print(f"Blackspots within 5 km of an ML Zone: {df_bs_cov['covered_by_ml_zone_5km'].sum()} / {len(df_bs_cov)} ({df_bs_cov['covered_by_ml_zone_5km'].mean()*100:.1f}%)")
    print(f"Blackspots within 15 km of an ML Zone: {df_bs_cov['covered_by_ml_zone_15km'].sum()} / {len(df_bs_cov)} ({df_bs_cov['covered_by_ml_zone_15km'].mean()*100:.1f}%)")
    print(f"Blackspots > 15 km from ANY ML Zone: {(~df_bs_cov['covered_by_ml_zone_15km']).sum()} / {len(df_bs_cov)} ({(~df_bs_cov['covered_by_ml_zone_15km']).mean()*100:.1f}%)")
    
    # Save CSV
    out_csv = root / "outputs" / "reports" / "ml_geographic_coverage.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_bs_cov.to_csv(out_csv, index=False)
    print(f"\nSaved ML Geographic Coverage CSV to: {out_csv}")
    
    print("\nSample Blackspots Proximity:")
    print(df_bs_cov[["hazard_id", "location_name", "district", "closest_ml_city", "distance_to_closest_zone_km", "recommendation"]].head(15).to_string())

if __name__ == "__main__":
    main()
