"""
Script to systematically audit all CSV datasets in data/raw/.
Generates detailed diagnostics for:
- accident_prediction_india.csv
- ETP_4_New_Data_Accidents.csv
- indian_roads_dataset.csv
- india_traffic_accidents.csv
"""

import os
from pathlib import Path
import json
import pandas as pd
import numpy as np

RAW_DIR = Path("data/raw")

def analyze_dataset(file_path: Path):
    print(f"\n=======================================================")
    print(f"AUDITING: {file_path.name}")
    print(f"=======================================================")
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")
    
    # Read sample first to detect encoding and structure
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
    
    rows, cols = df.shape
    print(f"Rows: {rows:,} | Columns: {cols}")
    
    # Column summary
    print("\n--- Columns & Types ---")
    dtypes_dict = df.dtypes.to_dict()
    missing_dict = df.isnull().mean().to_dict()
    for col in df.columns:
        print(f"  • {col} ({dtypes_dict[col]}): {missing_dict[col]*100:.2f}% missing | {df[col].nunique()} unique")
    
    # Total missing & duplicates
    total_cells = rows * cols
    missing_cells = df.isnull().sum().sum()
    dup_rows = df.duplicated().sum()
    print(f"\nOverall Missing Cells: {missing_cells:,} ({missing_cells/total_cells*100:.2f}%)")
    print(f"Duplicate Rows: {dup_rows:,} ({dup_rows/rows*100:.2f}%)")
    
    # Geographic Analysis
    print("\n--- Geographic Analysis ---")
    lat_cols = [c for c in df.columns if any(k in c.lower() for k in ["lat", "latitude"])]
    lon_cols = [c for c in df.columns if any(k in c.lower() for k in ["lon", "lng", "longitude"])]
    city_cols = [c for c in df.columns if any(k in c.lower() for k in ["city", "district", "location", "area"])]
    state_cols = [c for c in df.columns if any(k in c.lower() for k in ["state", "province", "region"])]
    
    print(f"Latitude column(s): {lat_cols}")
    print(f"Longitude column(s): {lon_cols}")
    print(f"City/Location column(s): {city_cols}")
    print(f"State column(s): {state_cols}")
    
    if lat_cols and lon_cols:
        lat_c = lat_cols[0]
        lon_c = lon_cols[0]
        # Check numeric
        try:
            valid_lat = pd.to_numeric(df[lat_c], errors="coerce")
            valid_lon = pd.to_numeric(df[lon_c], errors="coerce")
            valid_coords = (~valid_lat.isnull()) & (~valid_lon.isnull())
            # India bounds: 6.0 to 37.5 N, 68.0 to 97.5 E
            india_coords = valid_coords & (valid_lat >= 6.0) & (valid_lat <= 37.5) & (valid_lon >= 68.0) & (valid_lon <= 97.5)
            # Maharashtra bounds: 15.0 to 22.5 N, 72.0 to 81.5 E
            mh_coords = valid_coords & (valid_lat >= 15.0) & (valid_lat <= 22.5) & (valid_lon >= 72.0) & (valid_lon <= 81.5)
            
            print(f"Valid numeric coordinates: {valid_coords.sum():,} ({valid_coords.mean()*100:.2f}%)")
            print(f"Coordinates within India bounding box: {india_coords.sum():,} ({india_coords.mean()*100:.2f}%)")
            print(f"Coordinates within Maharashtra bounding box: {mh_coords.sum():,} ({mh_coords.mean()*100:.2f}%)")
            print(f"Lat min/max: {valid_lat.min():.4f} to {valid_lat.max():.4f}")
            print(f"Lon min/max: {valid_lon.min():.4f} to {valid_lon.max():.4f}")
        except Exception as e:
            print(f"Coordinate analysis error: {e}")
    
    if city_cols:
        for cc in city_cols:
            print(f"Top values in {cc}:")
            print(df[cc].value_counts().head(10).to_dict())
            
    if state_cols:
        for sc in state_cols:
            print(f"Top values in {sc}:")
            print(df[sc].value_counts().head(10).to_dict())

    # Temporal Analysis
    print("\n--- Temporal Analysis ---")
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "timestamp", "datetime", "year", "month", "day"])]
    time_cols = [c for c in df.columns if any(k in c.lower() for k in ["time", "hour"])]
    print(f"Date column(s): {date_cols}")
    print(f"Time/Hour column(s): {time_cols}")
    
    for dc in date_cols:
        print(f"Sample values in {dc}: {df[dc].dropna().head(5).tolist()}")
    for tc in time_cols:
        print(f"Sample values in {tc}: {df[tc].dropna().head(5).tolist()}")

    # Risk & Accident Analysis
    print("\n--- Risk & Environmental Fields ---")
    sev_cols = [c for c in df.columns if any(k in c.lower() for k in ["sever", "fatal", "injur", "casual", "risk", "target", "score"])]
    env_cols = [c for c in df.columns if any(k in c.lower() for k in ["weather", "road", "light", "traffic", "speed", "surface", "lane", "vehicle"])]
    print(f"Severity/Risk columns: {sev_cols}")
    for sc in sev_cols:
        print(f"  Distribution of {sc}:")
        print(df[sc].value_counts(dropna=False).head(10).to_dict())
    
    print(f"Environmental/Road columns: {env_cols}")
    for ec in env_cols:
        if df[ec].nunique() < 20:
            print(f"  Distribution of {ec}:")
            print(df[ec].value_counts(dropna=False).head(8).to_dict())

    # Synthetic vs Real Inspection
    print("\n--- Synthetic / Generation Signatures ---")
    # Check for uniform float distributions, perfectly balanced categories, or formulaic patterns
    for col in df.select_dtypes(include=[np.number]).columns[:8]:
        stats = df[col].describe()
        print(f"  Numeric {col}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")

    return {
        "file_name": file_path.name,
        "rows": rows,
        "cols": cols,
        "size_mb": round(file_size_mb, 2),
        "columns": list(df.columns),
        "missing_pct": round(missing_cells / total_cells * 100, 2),
        "duplicate_pct": round(dup_rows / rows * 100, 2),
    }

def main():
    results = []
    for f in sorted(RAW_DIR.glob("*.csv")):
        res = analyze_dataset(f)
        if res:
            results.append(res)

if __name__ == "__main__":
    main()
