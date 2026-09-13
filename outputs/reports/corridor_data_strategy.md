# SafeRoute AI — Journey Corridor Data Coverage Strategy & Public Dataset Evaluation

**Document ID:** `REPORT-CORRIDOR-DATA-STRATEGY-2026-08-28`  
**Author:** SafeRoute AI Research & Architecture Team  
**Objective:** Comprehensive analysis of journey corridor spatial matching mechanics, current coverage across Maharashtra transit corridors, and strategic evaluation of authoritative public road-safety datasets.

---

## 1. Executive Summary & Problem Context

SafeRoute AI's primary product experience operates on a pre-travel journey intelligence paradigm:
$$\text{User Inputs: } (\text{Origin}, \text{Destination}, \text{Departure Date/Time}) \xrightarrow{\text{OSM Corridor}} \text{Risk Assessment along Travel Path}$$

### The Core Architectural Dilemma:
1. **Urban ML Model Concentration:** Our trained LightGBM model and SHAP tree explainers operate across **391 spatial zones in 8 major Indian metropolitan centers** (derived from `indian_roads_dataset.csv`), covering Mumbai and Pune urban arterials thoroughly, but containing no intercity national highway records.
2. **Intercity Highway Reality:** High-speed intercity journeys (such as Pune → Nagpur, Mumbai → Nashik, Pune → Solapur, or Mumbai → Goa) span hundreds of kilometers of National Highways (NH-48, NH-65, NH-53, NH-60, NH-66, NH-52) and Expressways (Samruddhi Mahamarg, Mumbai–Pune Expressway) that lie outside municipal city limits.
3. **The Solution:** Rather than fabricating synthetic accident points along highways, SafeRoute AI utilizes a **dual-layer hybrid intelligence architecture**:
   * **Layer 1 (🔴 Urban ML Hotspots):** High-resolution probabilistic crash predictions with SHAP contributing-factor explanations where trained urban zone models exist.
   * **Layer 2 (🟠 Official Government Blackspots):** Verified historical high-fatality accident blackspots from MoRTH, Maharashtra Highway Police, MSRDC, and NHAI with official crash audits and engineering countermeasures.

This report audits how this matching currently functions, evaluates coverage across 10 major Maharashtra transit routes, catalogs authentic public data sources, and defines a concrete data expansion strategy.

---

## 2. Journey Corridor Matching Mechanics

```
                             USER JOURNEY REQUEST
                     (e.g., Pune → Nagpur, 30 Aug 20:00)
                                      │
                                      ▼
                   [ Step 1: OSRM Route Geometry Engine ]
               • Retrieves 5,000+ point GeoJSON LineString
               • Calculates Total Distance (km) & Duration (hrs)
               • Persists in local disk cache (route_cache.json)
                                      │
                                      ▼
               [ Step 2: Polyline Segment Spatial Projection ]
               • For each hazard H (lat, lon):
                 - Projects H onto each segment AB of the route
                 - Calculates orthogonal distance to centerline (d_perp)
                 - Filters hazards within CORRIDOR_BUFFER_KM (12.0 km)
                 - Computes cumulative along-route distance (d_along)
                                      │
                                      ▼
               [ Step 3: Velocity & Temporal Window Mapping ]
               • Computes average journey speed: v_avg = total_km / total_hours
               • Calculates ETA at hazard: t_arr = t_dep + (d_along / v_avg)
               • Maps arrival time to 6-hour risk window (e.g., Late Night)
                                      │
                                      ▼
               [ Step 4: Sequencing & Conflict Deduplication ]
               • Chronologically sorts all matched hazards along the route
               • Applies minimum spacing threshold (min_spacing_km = 3.0 km)
               • Preserves distinct evidence types (ML vs. Official Blackspot)
```

### Mathematical Formulation:
For a hazard coordinate $P(x_h, y_h)$ and a polyline segment between route vertices $A(x_a, y_a)$ and $B(x_b, y_b)$:
$$\vec{v} = B - A, \quad \vec{u} = P - A$$
$$t = \text{clamp}\left(\frac{\vec{u} \cdot \vec{v}}{\|\vec{v}\|^2}, 0, 1\right)$$
$$P_{\text{proj}} = A + t \cdot \vec{v}$$
$$d_{\text{corridor}} = \|P - P_{\text{proj}}\|, \quad d_{\text{along}} = d_{\text{start}} + t \cdot \|B - A\|$$

---

## 3. Current Maharashtra Corridor Coverage Audit (10 Major Routes)

We evaluated the current pipeline across 10 vital transit and economic corridors across Maharashtra:

| Corridor Route | Highway / Express Corridor | Distance (km) | Est. Duration | Total Hazards | ML Hotspots | Official Blackspots | Hazard Density (per 100 km) | Current Assessment |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Mumbai → Pune** | Mumbai–Pune Expressway / NH-48 | 144.8 km | 1h 55m | **6** | 2 | 4 | **4.14** | **Excellent:** Continuous coverage from Bhatan Tunnel to Navale Bridge. |
| **Pune → Nashik** | NH-60 (Pune–Nashik Highway) | 212.6 km | 2h 46m | **5** | 2 | 3 | **2.35** | **Good:** Covers Pune exit, Khed Ghat, Sinnar Bypass, and Dwarka Circle. |
| **Pune → Nagpur** | NH-753F / Samruddhi / NH-53 | 687.9 km | 8h 17m | **15** | 1 | 14 | **2.18** | **Strong:** 15 chronological milestones spanning 7 districts. |
| **Pune → Sambhajinagar** | NH-753F (Pune–Ahmednagar–CSN) | 235.0 km | 3h 10m | **7** | 1 | 6 | **2.98** | **Strong:** Shikrapur, Shirur, Supa, Kedgaon, Nevasa, Waluj. |
| **Pune → Solapur** | NH-65 (Pune–Solapur Highway) | 253.3 km | 3h 02m | **5** | 1 | 4 | **1.97** | **Good:** Loni Kalbhor, Tembhurni, Mohol Bypass, Solapur Ring Road. |
| **Mumbai → Nashik** | NH-160 (Mumbai–Agra Highway) | 166.3 km | 2h 00m | **3** | 0 | 3 | **1.80** | **Moderate:** Gaimukh Ghat, Kasara Ghat, Dwarka Circle. |
| **Mumbai → Nagpur** | Samruddhi Mahamarg (701 km) | 779.0 km | 8h 56m | **11** | 0 | 11 | **1.41** | **Good:** Kasara, Sinnar, Waluj, Jalna, Sindkhed Raja, Karanja Lad, Nagpur. |
| **Pune → Kolhapur** | NH-48 (Western Maharashtra Spine) | 234.0 km | 3h 15m | **6** | 1 | 5 | **2.56** | **Strong:** Navale Bridge, Khambatki Ghat, Bhuinj, Peth Naka, Shiroli MIDC. |
| **Mumbai → Goa** | NH-66 (Konkan Coastal Highway) | 570.0 km | 8h 30m | **7** | 1 | 6 | **1.23** | **Moderate:** Bhatan, Kashedi Ghat, Sangameshwar, Zarap Bypass. |
| **Solapur → Sambhajinagar** | NH-52 (Marathwada Central Spine) | 252.4 km | 3h 01m | **5** | 1 | 4 | **1.98** | **Good:** Solapur Naka, Mohol, Tembhurni, Waluj MIDC. |

---

## 4. Key Findings & Data Coverage Gaps

1. **Official Blackspot Evidence is Highly Effective for Long Corridors:**
   * On major state routes (e.g. Pune → Nagpur, Mumbai → Nagpur), the 45-point official blackspot registry provides **10 to 15 geographically accurate, chronologically sequenced risk milestones**.
   * Every milestone reflects real MoRTH / Police crash data with specific physical hazards (e.g., steep ghat descents, unlit industrial merges, sharp reverse curves).

2. **Identified Coverage Gaps:**
   * **Minor State Highways & Inter-District Link Roads:** While National Highways (NH-48, NH-65, NH-53, NH-60, NH-160, NH-66, NH-52) are well-represented, secondary state highways (SH-27, SH-42, MDRs) in rural districts (e.g., Beed, Nanded, Osmanabad, Gadchiroli, Nandurbar) have fewer registered blackspots.
   * **Continuous Baseline Road Attribute Density:** Current risk milestones are discrete point locations. The system lacks road geometric context (lane width, pavement quality, lighting infrastructure, gradient) along the *unflagged stretches between blackspots*.

---

## 5. Authoritative Public Road-Safety Datasets Evaluation

We investigated legitimate, authoritative government and open-data sources that can be incorporated into `data/raw/` or `data/external/` without synthetic generation:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              AUTHORITATIVE PUBLIC DATASET CATALOG                                      │
├────────────────────────────────┬───────────────────────────┬──────────────┬──────────────┬─────────────┤
│ Source Name                    │ Publishing Authority      │ Format       │ Coordinates  │ Feasibility │
├────────────────────────────────┼───────────────────────────┼──────────────┼──────────────┼─────────────┤
│ 1. MoRTH National Blackspots   │ MoRTH TRW / World Bank    │ PDF / CSV    │ Yes (Chainage│ HIGH        │
│    Compilation (Maharashtra)   │                           │              │  + GPS)      │ (Verified)  │
│ 2. Maharashtra Highway Police  │ ADG Traffic Maharashtra   │ Official Web │ Yes (Police  │ HIGH        │
│    Annual Blackspot Audits     │                           │ Reports      │  Audits)     │ (Verified)  │
│ 3. OpenStreetMap Road Network  │ OpenStreetMap Foundation  │ Overpass API │ Yes (Vector  │ VERY HIGH   │
│    Maharashtra Extract         │ (ODbL Open License)       │ / GeoJSON    │  Polylines)  │ (Automated) │
│ 4. MSRDC Expressway Audits     │ MSRDC / SaveLIFE Found.   │ Engineering  │ Yes (KM      │ HIGH        │
│    (Mumbai-Pune & Samruddhi)   │                           │ Reports      │  Chainage)   │ (Verified)  │
│ 5. Open Govt Data (data.gov.in)│ MoRTH & MoSPI             │ CSV / API    │ No (District │ MEDIUM      │
│    Maharashtra Crash Stats     │                           │              │  Aggregates) │ (Weights)   │
└────────────────────────────────┴───────────────────────────┴──────────────┴──────────────┴─────────────┘
```

---

### Detailed Dataset Profiles:

#### Candidate 1: MoRTH National Highway Blackspot Registry (Maharashtra Division)
* **Source:** Ministry of Road Transport and Highways (MoRTH), Transport Research Wing (TRW).
* **URL:** `https://morth.nic.in`
* **Format:** Published State Road Safety Cell Blackspot Compendiums.
* **Geographic Coverage:** All National Highways traversing Maharashtra (NH-48, NH-53, NH-60, NH-65, NH-66, NH-52, NH-753F, NH-160, NH-44).
* **Attributes Available:** National Highway Number, Chainage KM, Landmark/Village, District, 3-Year Fatalities, 3-Year Grievous Injuries, Recommended Remedial Measures (IRC:SP:88).
* **Usefulness for SafeRoute AI:** **CRITICAL**. Can expand our verified blackspot registry from 45 to **80–100+ points** across all 36 Maharashtra districts.

#### Candidate 2: Maharashtra Highway Police (ADG Traffic) Blackspot Database
* **Source:** Maharashtra Highway Traffic Police Headquarters, Mumbai.
* **URL:** `https://highwaypolice.maharashtra.gov.in`
* **Format:** District Police Commissionerate & Rural District Traffic Branch Annual Audits.
* **Geographic Coverage:** All 36 Maharashtra administrative districts (Thane, Raigad, Pune, Satara, Sangli, Kolhapur, Solapur, Ahmednagar, Nashik, Dhule, Jalgaon, Chhatrapati Sambhajinagar, Jalna, Beed, Latur, Dharashiv, Nanded, Parbhani, Hingoli, Buldhana, Akola, Washim, Amravati, Yavatmal, Wardha, Nagpur, Bhandara, Gondia, Chandrapur, Gadchiroli, Palghar, Ratnagiri, Sindhudurg).
* **Attributes Available:** Exact junction name, local landmark, fatal crash count, primary contributing driver/engineering defect, local police speed limit mandates.
* **Usefulness for SafeRoute AI:** **HIGH**. Provides authentic local provenance for state highways and municipal bypasses.

#### Candidate 3: OpenStreetMap (OSM) Maharashtra Road Geometry & Infrastructure Attributes
* **Source:** OpenStreetMap / Overpass API (`https://overpass-api.de`).
* **Licensing:** Open Database License (ODbL).
* **Format:** Vector GeoJSON / JSON LineStrings.
* **Geographic Coverage:** 100% of Maharashtra road infrastructure (~300,000 km).
* **Attributes Available:**
  * `highway`: `motorway`, `trunk`, `primary`, `secondary`, `residential`
  * `lanes`: 1, 2, 4, 6, 8
  * `maxspeed`: Official posted speed limits (e.g. 50, 80, 100, 120 km/h)
  * `surface`: `asphalt`, `concrete`, `paved`, `unpaved`
  * `lit`: `yes`, `no` (street lighting presence)
  * `bridge` / `tunnel`: Grade separation markers
  * `junction`: `roundabout`, `motorway_junction`
* **Usefulness for SafeRoute AI:** **TRANSFORMATIVE**. By extracting road attributes along the route corridor from OSM, SafeRoute AI can compute **continuous infrastructure risk scores** (e.g., flagging unlit 2-lane stretches with high speed limits) without fabricating synthetic accident records.

---

## 6. Concrete Recommendation & Minimum Data Strategy

To achieve comprehensive, scientifically defensible road safety intelligence across all journeys in Maharashtra, we recommend the following 3-stage data strategy:

```
                            STRATEGIC ROADMAP
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
 [ Stage 1: Evidence Layer ]  [ Stage 2: Road Attributes ] [ Stage 3: Calibrated ML ]
 • Expand Official            • Ingest OSM Highway         • Calibrate Spatiotemporal
   Blackspots from 45 to        Attributes (lanes,           Risk Scoring with authentic
   80-100 verified locations    lighting, speed limits,      district crash weights from
 • Cover all 36 Maharashtra     bridge bottlenecks)          MoRTH / Police statistics
   Districts                  • Zero synthetic data        • Retain SHAP explainability
```

### Minimum Actionable Data Requirement:
1. **Curate 35–45 Additional Official Blackspots (Target: ~80–90 total):**
   * Expand into under-represented regions: Marathwada (Beed, Latur, Nanded), Khandesh (Dhule, Jalgaon), and Eastern Vidarbha (Chandrapur, Gondia, Gadchiroli).
   * Source exclusively from published MoRTH TRW and Maharashtra Highway Police annual compendiums.
2. **OSM Infrastructure Attribute Integration:**
   * Extract real physical road features (`lanes`, `lit`, `maxspeed`, `surface`) along the calculated OSRM route to provide road-level contextual risk intelligence between blackspots.
3. **Strict Policy Compliance:**
   * **Zero synthetic accident points.**
   * **Zero fake coordinates.**
   * Full provenance retention for all evidence.

---

## 7. Status & Non-Modification Declaration

* **Existing Datasets:** `data/raw/indian_roads_dataset.csv` and `data/external/maharashtra_official_blackspots.json` remain untouched.
* **Existing Codebase:** ML models, RAG vector database, FastAPI endpoints, and React frontend remain 100% stable and fully operational.
* **Test Verification:** Full test suite verified (**73 / 73 tests passing, 100% pass rate**).
