# SafeRoute AI — ML Geographic Coverage & Model Generalizability Audit

**Document ID:** `REPORT-ML-COVERAGE-AUDIT-2026-08-28`  
**Author:** SafeRoute AI Research & Machine Learning Team  
**Scope:** Rigorous Audit of ML Dataset Statistics, Feature Engineering, Spatial Generalizability Limits, Official Blackspots Proximity, and Non-Geographic Benchmark Utility of Candidate Raw Datasets.

---

## 1. Executive Summary

SafeRoute AI's primary product is a **pre-travel journey road-safety assessment engine**:
$$\text{Origin} \longrightarrow \text{Destination} \longrightarrow \text{Departure Date/Time} \longrightarrow \text{Corridor Matching} \longrightarrow \begin{cases} \text{ML Risk Hotspots (Urban)} \\ \text{Official Blackspots (Highway)} \end{cases}$$

This audit evaluates the exact geographic, feature, and architectural boundaries of the current LightGBM ML model.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               ML AUDIT KEY FINDINGS                                    │
├──────────────────────────────────────┬─────────────────────────────────────────────────┤
│ Metric / Audit Dimension             │ Audit Finding & Architectural Reality           │
├──────────────────────────────────────┼─────────────────────────────────────────────────┤
│ Training Dataset Size                │ 20,000 historical accident records              │
│ Geographic Scope                     │ 8 metropolitan cities (51–55 zones per city)    │
│ Total Unique ML Spatial Zones        │ 391 DBSCAN clusters ($r \approx 0.5\text{--}2.5$ km)│
│ Maharashtra ML Training Representation│ 5,009 records (25.05%) strictly in Pune & Mumbai│
│ Intercity Highway ML Representation  │ 0 records (0.00% on rural/state/national NH/SH) │
│ Model Architectural Classification   │ Combination: Zone-Specific + City-Specific      │
│ 63 Official Blackspots Proximity     │ 92.1% (58/63) are >15 km away from ANY ML zone  │
│ 1M Dataset (`india_traffic_accidents`│ Synthetic coordinates; strictly stress-test only│
└──────────────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 2. ML Dataset Statistics & Geographic Distribution

The current production ML model was trained on `data/processed/cleaned_accidents.csv` (20,000 records) and aggregated into `data/processed/spatiotemporal_risk_dataset.csv` (93,840 zone-window observations across rolling monthly temporal windows).

### 2.1 City and State Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ML DATASET GEOGRAPHIC DISTRIBUTION                              │
├───────────────┬──────────────────┬──────────────┬───────────────┬──────────────────────┤
│ City          │ State            │ Raw Records  │ % Total Data  │ Spatial Zones (391)  │
├───────────────┼──────────────────┼──────────────┼───────────────┼──────────────────────┤
│ Chandigarh    │ Punjab           │ 2,577        │ 12.88%        │ 51 zones             │
│ Chennai       │ Tamil Nadu       │ 2,575        │ 12.88%        │ 55 zones             │
│ Kolkata       │ West Bengal      │ 2,559        │ 12.80%        │ 50 zones             │
│ Pune          │ Maharashtra      │ 2,517        │ 12.58%        │ 51 zones             │
│ Mumbai        │ Maharashtra      │ 2,492        │ 12.46%        │ 39 zones             │
│ Bangalore     │ Karnataka        │ 2,438        │ 12.19%        │ 52 zones             │
│ Delhi         │ Delhi (UT)       │ 2,433        │ 12.16%        │ 49 zones             │
│ Hyderabad     │ Telangana        │ 2,409        │ 12.05%        │ 44 zones             │
├───────────────┴──────────────────┼──────────────┼───────────────┼──────────────────────┤
│ TOTAL NATIONWIDE DATASET         │ 20,000       │ 100.00%       │ 391 zones            │
│ TOTAL MAHARASHTRA SUBSET         │ 5,009        │ 25.05%        │ 90 zones             │
└──────────────────────────────────┴──────────────┴───────────────┴──────────────────────┘
```

### 2.2 Geographic Bounds & Zone Properties
* **Latitude Bounds:** $12.8002^\circ\text{N}$ to $30.8000^\circ\text{N}$
* **Longitude Bounds:** $72.7000^\circ\text{E}$ to $88.4999^\circ\text{E}$
* **Temporal Window:** 2020-01-01 to 2023-12-31 (4 full calendar years)
* **Historical Accidents per Zone:**
  * Mean: $25.32$ accidents
  * Median: $20.00$ accidents
  * Min: $10$ accidents
  * Max: $147$ accidents
* **Target Risk Tier Distribution (`target_risk_tier`):**
  * `LOW`: $84.39\%$
  * `MEDIUM`: $8.09\%$
  * `HIGH`: $7.52\%$

---

## 3. Model Generalizability Classification

### Architectural Verdict: **Combination of (B) Zone-Specific and (A) City-Specific**

```
                  ┌──────────────────────────────────────────────┐
                  │          LIGHTGBM MODEL ARCHITECTURE         │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │ Historical Lag Features   │                   │ Spatial Coordinates &     │
   │ (Zone-Specific Memory)    │                   │ City One-Hot Encodings    │
   ├───────────────────────────┤                   ├───────────────────────────┤
   │ * lag_accidents_90d       │                   │ * center_lat, center_lon  │
   │ * lag_expanding_fatal_rate│                   │ * max_r_km (cluster area) │
   │ * lag_zw_expanding_acc    │                   │ * city_Pune, city_Mumbai  │
   │ * lag_zw_expanding_swri   │                   │ * city_Bangalore, etc.    │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       Inference on Unseen Rural Highway       │
                 │   -> All lag features = 0                     │
                 │   -> All city one-hot features = 0            │
                 │   -> Coordinates outside city bounding trees  │
                 │   => OUTPUT IS MEDICALLY UNRELIABLE / VOID    │
                 └───────────────────────────────────────────────┘
```

### Why the ML Model Cannot Blindly Predict on Rural Highways:
1. **Zero Historical Baseline:** The model relies on rolling accident history (`lag_accidents_90d`, `lag_expanding_fatal_rate`, `lag_zw_expanding_swri`). In an unmonitored rural highway point, all lag metrics evaluate to 0.
2. **City One-Hot Encodings:** The model splits on explicit city flags (`city_Pune`, `city_Mumbai`, etc.). Any point in Ahmednagar, Dhule, Jalna, or Satara sets all 8 city columns to 0.
3. **Coordinate Tree Partitions:** Decision tree thresholds on `center_lat` and `center_lon` form tight axis-aligned bounding boxes around the 8 trained cities. Evaluating coordinates between cities falls into leaf nodes with high epistemic uncertainty.

---

## 4. Feature Engineering & Data Integrity Audit

We reviewed the full feature dictionary against data-leakage and causality standards:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           FEATURE ENGINEERING CATEGORIZATION                           │
├──────────────────────┬────────────────────────────────┬────────────────────────────────┤
│ Feature Category     │ Feature Names                  │ Leakage & Integrity Status     │
├──────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ **Temporal**         │ `time_window_4h`,              │ **SAFE**: Derived strictly from│
│                      │ `is_peak_window`               │ scheduled travel departure time│
├──────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ **Historical Lag**   │ `lag_accidents_30d`, 90d, 180d,│ **SAFE**: Computed strictly    │
│                      │ `lag_trend_90d_vs_180d`,       │ backwards from monthly feature │
│                      │ `lag_expanding_accidents`,     │ cutoff date (zero lookahead).  │
│                      │ `lag_expanding_fatal_rate`,    │                                │
│                      │ `lag_expanding_major_rate`,    │                                │
│                      │ `lag_expanding_casualty_dens`, │                                │
│                      │ `lag_zw_expanding_accidents`,  │                                │
│                      │ `lag_zw_expanding_swri`        │                                │
├──────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ **Spatial**          │ `center_lat`, `center_lon`,    │ **SAFE**: Centroid coordinates │
│                      │ `max_r_km`, 8 city one-hots    │ of verified spatial clusters.  │
├──────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ **Weather / Traffic**│ `actual_rain_fog_ratio`,       │ **EXCLUDED FROM BASELINE**:    │
│                      │ `actual_low_visibility_ratio`, │ Preserved in CSV for evaluation│
│                      │ `actual_high_traffic_ratio`    │ but excluded from training to  │
│                      │                                │ prevent live inference leakage.│
├──────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ **Excluded Columns** │ `risk_score` (synthetic col),  │ **STRICTLY EXCLUDED**: Never   │
│                      │ `accident_severity` (raw col)  │ used as training target.       │
└──────────────────────┴────────────────────────────────┴────────────────────────────────┘
```

---

## 5. Official Maharashtra Blackspots vs. ML Dataset Audit

We performed an orthogonal spatial proximity audit comparing all **63 official blackspots** against the **391 ML cluster zones**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        BLACKSPOT VS ML PROXIMITY AUDIT                                 │
├────────────────────────────────────────┬─────────────┬─────────────┬───────────────────┤
│ Distance to Closest Trained ML Zone    │ Count       │ Percentage  │ Recommended Action│
├────────────────────────────────────────┼─────────────┼─────────────┼───────────────────┤
│ $\le 5.0\text{ km}$ (Inside/Near Zone) │ 1 blackspot │ 1.6%        │ Hybrid ML + Official│
│ $5.1\text{ to }15.0\text{ km}$ (Suburban)| 4 blackspots| 6.3%        │ Official Evidence │
│ $> 15.0\text{ km}$ (Intercity / Rural) │ 58 blackspot│ 92.1%       │ Official Evidence │
├────────────────────────────────────────┼─────────────┼─────────────┼───────────────────┤
│ TOTAL OFFICIAL BLACKSPOTS EVALUATED    │ 63          │ 100.00%     │                   │
└────────────────────────────────────────┴─────────────┴─────────────┴───────────────────┘
```

### Key Geographic Insights:
* **The Only Hybrid Point:** `MH-BS-001` (Navale Bridge, Katraj Bypass, Pune) is located $2.01\text{ km}$ from Pune ML Zone 363. It legitimately receives both ML spatiotemporal risk probabilities and official MoRTH fatality/countermeasure evidence.
* **Suburban Boundary Points:** `MH-BS-004` (Loni Kalbhor, $5.6\text{ km}$ from Pune Zone), `MH-BS-011` (Gaimukh Ghat, $6.1\text{ km}$ from Mumbai Zone), `MH-BS-005` (Urse Toll, $7.1\text{ km}$), `MH-BS-007` (Somatane, $7.9\text{ km}$).
* **Intercity Highway Points (92.1%):** Kasara Ghat ($70.5\text{ km}$), Khambatki Ghat ($34.2\text{ km}$), Kashedi Ghat ($86.4\text{ km}$), Waluj MIDC ($185.0\text{ km}$), Butibori Nagpur ($640\text{ km}$ from Pune). **These locations have 0 ML training observations and MUST remain purely official government evidence points.**

---

## 6. Audit of the 1M-Row Dataset (`india_traffic_accidents.csv`)

### Characteristics:
* **Row Count:** $1,000,000$ records.
* **Coordinates:** Uniformly distributed random floats ($8.0^\circ\text{N}\text{--}37.0^\circ\text{N}, 68.0^\circ\text{E}\text{--}97.0^\circ\text{E}$) with no geographic clustering or adherence to road networks.

### Legitimate Non-Geographic Uses:
1. **High-Throughput API Stress Testing:** Benchmarking backend serialization and JSON payload throughput under 100,000 concurrent records.
2. **Tabular Preprocessing Benchmarks:** Profiling vectorization speed for datetime encoders and categorical lookup pipelines.
3. **Distribution Comparison:** Evaluating synthetic vs. real variance in environmental distributions (e.g. rain vs. fog frequencies).

### Non-Negotiable Rule:
* **MUST NEVER be merged into spatial clustering or model training.**

---

## 7. Audit of Other Candidate Raw Datasets

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            OTHER RAW DATASETS AUDIT                                    │
├──────────────────────────────┬────────────┬─────────────┬──────────────────────────────┤
│ Dataset Name                 │ Rows       │ GPS Coordinates? │ Production Utility      │
├──────────────────────────────┼────────────┼─────────────┼──────────────────────────────┤
│ `ETP_4_New_Data_Accidents`   │ 400,000    │ ❌ NO GPS   │ Reference only: state-level  │
│                              │            │             │ aggregate trends (2017-2022) │
│ `accident_prediction_india`  │ 15,000     │ ❌ NO GPS   │ REJECTED: Synthetic toy set  │
│ `indian_roads_dataset.csv`   │ 20,000     │ ✅ YES GPS  │ BASELINE: Current ML dataset │
└──────────────────────────────┴────────────┴─────────────┴──────────────────────────────┘
```

---

## 8. Exact Recommendation for the Next ML Step

### **Verdict & Recommended Action Plan:**

1. **Maintain Strict Dual-Evidence Architecture (No Premature Retraining):**
   * Keep **ML Spatiotemporal Predictions + SHAP** active for urban zones with historical crash clusters (Pune, Mumbai, etc.).
   * Keep **Official Government Blackspots + Provenance** active for all intercity highway corridors (63 verified locations).
2. **Do Not Synthesize Fake Rural Accident Labels:**
   * Never fabricate training rows along highways just to make the ML model fire everywhere.
3. **Next Technical Step — Integrate Real OSM Physical Road Context:**
   * Enhance corridor explanations by extracting real OpenStreetMap road attributes (`lanes`, `lit`, `maxspeed`, `surface`, `bridge/tunnel`) along the OSRM corridor.
   * This provides physical engineering intelligence for why an unmonitored road section may be vulnerable without falsifying statistical crash probabilities.
