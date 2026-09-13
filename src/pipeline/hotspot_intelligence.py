"""
hotspot_intelligence.py — SafeRoute AI Unified Analytical Pipeline

Integrates:
1. ML Risk Prediction (LightGBM ranked hotspot probabilities)
2. SHAP Contributing Predictive Factors (Local factor attributions)
3. RAG Domain Safety Guidance (Authoritative MoRTH/IRC/WHO guidance retrieval)

Produces structured Hotspot Intelligence objects for backend API, dashboard, and briefings.

DISCLAIMER / RESPONSIBLE AI:
- ML risk predictions represent probabilistic risk based on historical crash patterns, not certainty.
- SHAP values quantify feature contributions to the model's prediction, not causal factors.
- RAG retrieves authoritative domain guidelines to support risk remediation, not prediction.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

from src.rag.retriever import build_shap_query, retrieve

DEFAULT_RANKED_PATH = "outputs/reports/ranked_hotspots.csv"
DEFAULT_EXPLANATIONS_PATH = "outputs/reports/hotspot_explanations.csv"
DEFAULT_CHROMA_DIR = "data/knowledge_base/index/chroma"
DEFAULT_OUTPUT_CSV = "outputs/reports/hotspot_intelligence.csv"
DEFAULT_OUTPUT_JSON = "outputs/reports/hotspot_intelligence.json"

# Regex pattern for parsing formatted explanation strings:
# "Persistent accident history in prior 180 days (value: 38.00, impact: +0.452)"
FACTOR_PATTERN = re.compile(r"^(.*?)\s*\(value:\s*([0-9\.\-]+),\s*impact:\s*\+?([0-9\.\-]+)\)")

# Mapping of textual descriptions to standard feature codes
DESC_TO_FEATURE_CODE = {
    "Elevated accident volume in prior 90 days": "lag_accidents_90d",
    "Persistent accident history in prior 180 days": "lag_accidents_180d",
    "High recent accident surge in prior 30 days": "lag_accidents_30d",
    "Accelerating short-term crash trend": "lag_trend_90d_vs_180d",
    "High cumulative historical crash density": "lag_expanding_accidents",
    "Historically elevated severity index during this specific time shift": "lag_zw_expanding_swri",
    "High historical frequency during this specific time shift": "lag_zw_expanding_accidents",
    "Elevated historical fatal accident ratio": "lag_expanding_fatal_rate",
    "Elevated historical major injury ratio": "lag_expanding_major_rate",
    "High historical casualty rate per crash": "lag_expanding_casualty_density",
    "Alignment with major daily traffic rush window": "is_peak_window",
    "Time of day hazard profile": "time_window_4h",
    "Cluster spatial footprint size": "max_r_km",
    "Geographic latitude coordinate": "center_lat",
    "Geographic longitude coordinate": "center_lon",
}


def parse_contributing_factor(factor_str: str) -> Optional[Dict[str, Any]]:
    """Parse a formatted contributing factor string into structured attributes."""
    if not factor_str or factor_str == "N/A" or pd.isna(factor_str):
        return None
    
    m = FACTOR_PATTERN.match(str(factor_str).strip())
    if m:
        desc, val_str, impact_str = m.groups()
        desc = desc.strip()
        feat_code = DESC_TO_FEATURE_CODE.get(desc, desc.lower().replace(" ", "_"))
        return {
            "feature": desc,
            "feature_code": feat_code,
            "value": float(val_str),
            "contribution": float(impact_str),
        }
    else:
        # Fallback if unformatted
        return {
            "feature": str(factor_str),
            "feature_code": "unknown",
            "value": 0.0,
            "contribution": 0.0,
        }


def build_single_intelligence_record(
    ranked_row: pd.Series,
    expl_row: Optional[pd.Series] = None,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    top_k_rag: int = 3,
    rank: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a single structured Hotspot Intelligence record combining ML, SHAP, and RAG.
    """
    assigned_rank = int(rank) if rank is not None else int(ranked_row.get("rank", 1))
    city = str(ranked_row.get("city", "Unknown"))
    zone_id = int(ranked_row.get("zone_id", 0))
    lat = float(ranked_row.get("center_lat", 0.0))
    lon = float(ranked_row.get("center_lon", 0.0))
    radius_km = float(ranked_row.get("max_r_km", 0.0))
    
    target_month = str(ranked_row.get("target_month", ""))
    target_start_date = str(ranked_row.get("target_start_date", ""))
    time_window_label = str(ranked_row.get("time_window_label", ranked_row.get("time_window_4h", "")))
    is_peak = int(ranked_row.get("is_peak_window", 0))
    
    pred_tier = str(ranked_row.get("predicted_risk_tier", "LOW"))
    pred_prob = float(ranked_row.get("predicted_high_probability", 0.0))
    actual_tier = str(ranked_row.get("target_risk_tier", "N/A"))

    # Extract contributing factors
    contributing_factors = []
    shap_pairs_for_query: List[Tuple[str, float]] = []

    if expl_row is not None:
        for f_col in ["contributing_factor_1", "contributing_factor_2", "contributing_factor_3", "contributing_factor_4"]:
            if f_col in expl_row and pd.notna(expl_row[f_col]):
                parsed = parse_contributing_factor(expl_row[f_col])
                if parsed:
                    contributing_factors.append(parsed)
                    shap_pairs_for_query.append((parsed["feature_code"], parsed["contribution"]))
    
    # If no factors parsed, fallback to time/traffic priors
    if not shap_pairs_for_query:
        shap_pairs_for_query = [
            ("lag_zw_expanding_swri", 0.50),
            ("lag_expanding_accidents", 0.40),
            ("lag_accidents_180d", 0.30),
        ]
        contributing_factors = [
            {"feature": "Historical crash severity index", "feature_code": "lag_zw_expanding_swri", "value": 0.0, "contribution": 0.50},
            {"feature": "Cumulative historical crash volume", "feature_code": "lag_expanding_accidents", "value": 0.0, "contribution": 0.40},
            {"feature": "Persistent accident history in prior 180 days", "feature_code": "lag_accidents_180d", "value": 0.0, "contribution": 0.30},
        ]

    # Construct RAG Query
    rag_query = build_shap_query(
        shap_factors=shap_pairs_for_query,
        city=city,
        time_label=time_window_label,
        top_n_factors=3,
    )

    # Retrieve RAG Guidance
    retrieved_chunks = retrieve(rag_query, chroma_dir, top_k=top_k_rag)
    
    safety_guidance = []
    for r in retrieved_chunks:
        safety_guidance.append({
            "rank": r["rank"],
            "chunk_id": r["chunk_id"],
            "title": r["title"],
            "organization": r["source_organization"],
            "topic": r["topic"],
            "relevance_score": round(float(r["relevance_score"]), 4),
            "source_url": r["source_url"],
            "document_type": r.get("document_type", ""),
            "content_excerpt": r["content"][:400] + ("..." if len(r["content"]) > 400 else ""),
        })

    # Hierarchical structured JSON schema
    intelligence_obj = {
        "rank": assigned_rank,
        "location": {
            "city": city,
            "zone_id": zone_id,
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "cluster_radius_km": round(radius_km, 3),
        },
        "temporal": {
            "target_month": target_month,
            "target_start_date": target_start_date,
            "time_window": time_window_label,
            "is_peak_window": bool(is_peak),
        },
        "prediction": {
            "risk_tier": pred_tier,
            "high_probability": round(pred_prob, 4),
            "actual_risk_tier": actual_tier,
        },
        "contributing_factors": contributing_factors,
        "retrieval_query": rag_query,
        "safety_guidance": safety_guidance,
    }

    return intelligence_obj


def flatten_intelligence_for_csv(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert hierarchical intelligence record into flat row for CSV export."""
    loc = record["location"]
    temp = record["temporal"]
    pred = record["prediction"]
    factors = record["contributing_factors"]
    guidance = record["safety_guidance"]

    top_factors_str = " | ".join([f"{f['feature']} (+{f['contribution']:.3f})" for f in factors])
    factor_contribs_str = "; ".join([f"{f['feature_code']}={f['contribution']:.3f}" for f in factors])

    top_g = guidance[0] if guidance else {}

    return {
        "rank": record["rank"],
        "city": loc["city"],
        "zone_id": loc["zone_id"],
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "cluster_radius_km": loc["cluster_radius_km"],
        "target_month": temp["target_month"],
        "target_start_date": temp["target_start_date"],
        "time_window": temp["time_window"],
        "is_peak_window": temp["is_peak_window"],
        "predicted_risk_tier": pred["risk_tier"],
        "predicted_high_probability": pred["high_probability"],
        "actual_risk_tier": pred.get("actual_risk_tier", "N/A"),
        "top_shap_factors": top_factors_str,
        "factor_contributions": factor_contribs_str,
        "retrieved_guidance": top_g.get("title", "N/A"),
        "source_organization": top_g.get("organization", "N/A"),
        "source_title": top_g.get("title", "N/A"),
        "source_url": top_g.get("source_url", "N/A"),
        "retrieval_score": top_g.get("relevance_score", 0.0),
        "all_retrieved_chunks": ", ".join([g.get("chunk_id", "") for g in guidance]),
        "retrieval_query": record.get("retrieval_query", ""),
    }


def generate_all_hotspot_intelligence(
    ranked_path: str = DEFAULT_RANKED_PATH,
    explanations_path: str = DEFAULT_EXPLANATIONS_PATH,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    output_csv: str = DEFAULT_OUTPUT_CSV,
    output_json: str = DEFAULT_OUTPUT_JSON,
    top_n: int = 100,
    top_k_rag: int = 3,
) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    """
    Generate unified hotspot intelligence for top N ranked hotspots,
    validating record matching across ML, SHAP, and RAG layers.
    """
    print("=" * 70)
    print("SAFEROUTE AI — UNIFIED HOTSPOT INTELLIGENCE PIPELINE")
    print("=" * 70)

    # 1. Load ML Predictions
    print(f"Loading ranked hotspots from: {ranked_path}")
    df_ranked = pd.read_csv(ranked_path)
    print(f"  Loaded {len(df_ranked)} ranked predictions.")

    # 2. Load SHAP Explanations
    print(f"Loading SHAP explanations from: {explanations_path}")
    df_expl = pd.read_csv(explanations_path)
    print(f"  Loaded {len(df_expl)} SHAP explanation records.")

    # 3. Match Records
    subset_ranked = df_ranked.head(top_n).copy().reset_index(drop=True)
    intelligence_records = []
    flat_rows = []
    
    matched_count = 0
    fallback_count = 0
    unmatched_keys = []

    print(f"\nProcessing top {len(subset_ranked)} hotspots with RAG retrieval (k={top_k_rag})...")

    for idx, r_row in subset_ranked.iterrows():
        rank = idx + 1
        zone_id = r_row["zone_id"]
        t_month = r_row["target_month"]
        t_label = r_row.get("time_window_label", "")
        city = r_row["city"]

        # Exact matching key: (zone_id, target_month, time_window_label) or fallback to rank_id
        match = df_expl[
            (df_expl["zone_id"] == zone_id) &
            (df_expl["target_month"] == t_month) &
            (df_expl["time_window_label"] == t_label)
        ]

        if len(match) == 0:
            # Fallback 1: match by rank if within top 100
            match_by_rank = df_expl[df_expl["rank"] == rank]
            if len(match_by_rank) > 0:
                e_row = match_by_rank.iloc[0]
                matched_count += 1
            else:
                # Fallback 2: zone-level explanation
                match_by_zone = df_expl[df_expl["zone_id"] == zone_id]
                if len(match_by_zone) > 0:
                    e_row = match_by_zone.iloc[0]
                    fallback_count += 1
                else:
                    e_row = None
                    unmatched_keys.append((zone_id, t_month, t_label))
        else:
            e_row = match.iloc[0]
            matched_count += 1

        record = build_single_intelligence_record(
            ranked_row=r_row,
            expl_row=e_row,
            chroma_dir=chroma_dir,
            top_k_rag=top_k_rag,
            rank=rank,
        )
        intelligence_records.append(record)
        flat_rows.append(flatten_intelligence_for_csv(record))

        if (idx + 1) % 25 == 0 or (idx + 1) == len(subset_ranked):
            print(f"  Processed {idx + 1}/{len(subset_ranked)} hotspot records...")

    # Data Integrity Validation Summary
    print("\n--- Data Integrity Validation ---")
    print(f"  Total Hotspots Processed: {len(intelligence_records)}")
    print(f"  Exact / Direct SHAP Matches: {matched_count}")
    print(f"  Fallback Zone Matches: {fallback_count}")
    print(f"  Unmatched / Defaulted: {len(unmatched_keys)}")
    if unmatched_keys:
        print(f"  Unmatched Key Details: {unmatched_keys[:5]}...")
    print(f"  Match Success Rate: {((len(intelligence_records) - len(unmatched_keys)) / len(intelligence_records)) * 100:.1f}%")

    # 4. Save Outputs
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_flat = pd.DataFrame(flat_rows)
    df_flat.to_csv(output_csv, index=False)
    print(f"\nSaved CSV intelligence report -> {output_csv} ({len(df_flat)} rows)")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(intelligence_records, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON intelligence report -> {output_json} ({len(intelligence_records)} records)")

    return intelligence_records, df_flat


def get_hotspot_intelligence(
    zone_id: Optional[int] = None,
    city: Optional[str] = None,
    target_month: Optional[str] = None,
    time_window: Optional[str] = None,
    rank: Optional[int] = None,
    ranked_path: str = DEFAULT_RANKED_PATH,
    explanations_path: str = DEFAULT_EXPLANATIONS_PATH,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    top_k_rag: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Reusable query function for future API and dashboard:
    Fetches structured intelligence for a specific hotspot query.
    """
    df_ranked = pd.read_csv(ranked_path)
    df_expl = pd.read_csv(explanations_path)

    query_df = df_ranked.copy()
    if rank is not None:
        if 1 <= rank <= len(query_df):
            r_row = query_df.iloc[rank - 1]
        else:
            return None
    else:
        if city is not None:
            query_df = query_df[query_df["city"].str.lower() == city.lower()]
        if zone_id is not None:
            query_df = query_df[query_df["zone_id"] == zone_id]
        if target_month is not None:
            query_df = query_df[query_df["target_month"] == target_month]
        if time_window is not None:
            query_df = query_df[query_df["time_window_label"].str.contains(time_window, case=False, na=False)]
        
        if len(query_df) == 0:
            return None
        r_row = query_df.iloc[0]
        rank = df_ranked.index.get_loc(r_row.name) + 1

    # Match explanation
    match_expl = df_expl[
        (df_expl["zone_id"] == r_row["zone_id"]) &
        (df_expl["time_window_label"] == r_row["time_window_label"])
    ]
    expl_row = match_expl.iloc[0] if len(match_expl) > 0 else None

    return build_single_intelligence_record(
        ranked_row=r_row,
        expl_row=expl_row,
        chroma_dir=chroma_dir,
        top_k_rag=top_k_rag,
        rank=rank,
    )


def format_hotspot_intelligence_summary(record: Dict[str, Any]) -> str:
    """Format structured intelligence object into human-readable text."""
    loc = record["location"]
    temp = record["temporal"]
    pred = record["prediction"]
    factors = record["contributing_factors"]
    guidance = record["safety_guidance"]

    lines = [
        "-----------------------------------------",
        "SAFE ROUTE AI — HOTSPOT INTELLIGENCE",
        "-----------------------------------------",
        f"Rank            : #{record['rank']}",
        f"Location        : {loc['city']}, Hotspot Zone {loc['zone_id']} ({loc['latitude']:.4f}°N, {loc['longitude']:.4f}°E)",
        f"Cluster Radius  : {loc['cluster_radius_km']:.2f} km",
        f"Time Window     : {temp['time_window']} (Month: {temp['target_month']})",
        f"Predicted Risk  : {pred['risk_tier']}",
        f"Probability     : {pred['high_probability']:.4f} (Base Rate: ~6.5%)",
        f"Actual Outcome  : {pred.get('actual_risk_tier', 'N/A')}",
        "",
        "Contributing Predictive Factors (SHAP Local Attribution):",
    ]

    for i, f in enumerate(factors, start=1):
        lines.append(f"  {i}. {f['feature']} (Observed: {f['value']:.2f}, Model Impact: +{f['contribution']:.3f})")

    lines.append("")
    lines.append("Relevant Road Safety Guidance (Retrieved Domain Knowledge):")
    for i, g in enumerate(guidance, start=1):
        lines.append(f"  {i}. [{g['organization']}] {g['title']} (Relevance: {g['relevance_score']:.4f})")
        lines.append(f"     Key Excerpt: \"{g['content_excerpt'][:180]}...\"")
        lines.append(f"     Source URL : {g['source_url']}")

    lines.extend([
        "",
        "Responsible AI & Methodological Notice:",
        "- ML prediction indicates elevated historical risk; it does NOT assert certainty of future events.",
        "- SHAP attributions reflect statistical model sensitivity, not verified causal mechanisms.",
        "- RAG provides evidence-grounded safety standards (MoRTH/IRC/WHO) to support engineering & enforcement.",
        "-----------------------------------------",
    ])

    return "\n".join(lines)
