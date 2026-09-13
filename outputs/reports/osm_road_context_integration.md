# SafeRoute AI — OpenStreetMap Road Context Integration Report

**Document ID:** `REPORT-OSM-ROAD-CONTEXT-2026-08-28`  
**Author:** SafeRoute AI Engineering & Research Team  
**Scope:** OpenStreetMap Physical Road Context Layer, Schema Normalization, Hazard-Level Attribute Enrichment, Frontend 7-Part Chronological Sequencing, and Test Suite Verification.

---

## 1. Executive Summary & Objective

To enhance SafeRoute AI's **pre-travel journey road-safety assessment** without fabricating ungrounded accident predictions or confusing physical road attributes with crash causation, we integrated an **OpenStreetMap (OSM) Physical Road Context Layer**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          3-TIER ROAD SAFETY INTELLIGENCE MATRIX                        │
├─────────────────────────┬────────────────────────────┬─────────────────────────────────┤
│ Evidence Class          │ Role in Journey Assessment │ Scientific Grounding            │
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ 🔴 ML-Predicted Hotspots│ Predicts temporal risk tier│ LightGBM Classifier + SHAP      │
│                         │ & probability (Urban zones)│ feature attributions (20K set)  │
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ 🟠 Official Blackspots  │ Documents verified fatal   │ MoRTH TRW & Maharashtra Highway │
│                         │ crash locations (Highways) │ Police 3-year audit registries  │
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ 🌐 OSM Road Context     │ Describes physical highway │ OpenStreetMap (ODbL) physical   │
│                         │ infrastructure conditions  │ attributes (lanes, lit, ghats)  │
└─────────────────────────┴────────────────────────────┴─────────────────────────────────┘
```

---

## 2. Architecture & Data Flow

```
                                USER JOURNEY REQUEST
                     (Origin, Destination, Departure Date/Time)
                                         │
                                         ▼
                            OSRM ROUTE GEOMETRY ENGINE
                      (Polyline Coordinates, Total KM, ETA)
                                         │
                                         ▼
                             CORRIDOR SPATIAL MATCHER
                       (Orthogonal Distance <= 12.0 km)
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
                   ▼                                           ▼
         ML URBAN HOTSPOTS (391)                     OFFICIAL BLACKSPOTS (63)
       (LightGBM Probabilities)                   (MoRTH / Police Fatality Audits)
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                         CHRONOLOGICAL SEQUENCING & ETA
                       (Sorted by Distance Along Route)
                                         │
                                         ▼
                   OPENSTREETMAP PHYSICAL ROAD CONTEXT LAYER
                 (Highway Class, Lanes, Speed Limits, Surface,
                 Lighting, Bridges, Tunnels, Notable Sectors)
                                         │
                                         ▼
                       ENRICHED JOURNEY SAFETY ASSESSMENT
                      (7-Part Sequential Milestone Display)
```

---

## 3. Physical Road Attributes Collected & Normalized

Adhering to our strict zero-fabrication invariant, missing values are represented as `null`/`unknown`:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ROAD ATTRIBUTES DATA DICTIONARY                           │
├──────────────────┬─────────────────────────────┬───────────────────────────────────────┤
│ Attribute Key    │ Type / Typical Values       │ Contextual Engineering Significance   │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `highway_class`  │ motorway, trunk, primary,   │ Identifies divided expressways vs.    │
│                  │ secondary                   │ undivided secondary rural state roads │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `lanes`          │ 2, 4, 6, 8                  │ Identifies bottle-neck lane drops     │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `maxspeed_kmh`   │ 50, 60, 80, 100, 120 km/h   │ Flags high-speed differential sectors │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `surface`        │ asphalt, concrete           │ Indicates road traction & tyre wear   │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `is_lit`         │ true, false, null           │ Identifies unlit night-driving risks  │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `is_bridge`      │ boolean (true/false)        │ Flags narrow river bridge approaches  │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `is_tunnel`      │ boolean (true/false)        │ Flags sudden daylight/tunnel changes  │
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `is_junction`    │ boolean (true/false)        │ Flags cross-arterial turning conflicts│
├──────────────────┼─────────────────────────────┼───────────────────────────────────────┤
│ `is_divided`     │ boolean (true/false)        │ Flags head-on collision vulnerability │
└──────────────────┴─────────────────────────────┴───────────────────────────────────────┘
```

---

## 4. Frontend 7-Part Chronological Presentation Order

In `frontend/src/components/JourneyTimeline.jsx`, every milestone now follows the standardized 7-step sequence:

1. **WHERE:** Location name, district, highway, and exact geographic coordinates.
2. **WHEN / ETA:** Local expected arrival time and 4-hour temporal shift window.
3. **HAZARD TYPE:** Distinct, unmerged badges:
   * 🔴 **`ML-PREDICTED HIGH-RISK HOTSPOT`**
   * 🟠 **`OFFICIAL GOVERNMENT BLACKSPOT`**
4. **RISK / SEVERITY:** Risk tier (`HIGH`, `OFFICIAL_HIGH_SEVERITY`), ML probability percentage (where trained), or verified 3-year fatality/crash counts.
5. **WHY FLAGGED:** Intelligence assessment rationale + top predictive SHAP factor chips for ML hotspots, or official police audit findings for blackspots.
6. **ROAD CONTEXT:** Physical OpenStreetMap attributes badge (Highway class, Carriageway lanes, Speed limit, Surface, Street lighting status, Bridge/Tunnel/Junction markers).
7. **PREVENTION:** Evidence-grounded IRC:SP:88 and MoRTH prevention countermeasures.

---

## 5. Example Journey Assessment Output (Pune → Nagpur Corridor)

```json
{
  "sequence": 1,
  "hazard_type": "OFFICIAL_BLACKSPOT",
  "location_name": "Shikrapur Junction / Wagholi Merge",
  "district": "Pune",
  "highway": "NH-753F",
  "distance_from_origin_km": 38.0,
  "expected_arrival_time": "20:34",
  "expected_arrival_window": "20:00 - 23:59 (Night)",
  "risk_tier": "OFFICIAL_HIGH_SEVERITY",
  "risk_probability": null,
  "reason": "High-density industrial container traffic merging with local town traffic at unsignalized multi-directional intersection.",
  "road_context": {
    "highway_class": "trunk",
    "lanes": 4,
    "maxspeed_kmh": 70,
    "surface": "asphalt",
    "is_lit": false,
    "is_bridge": false,
    "is_tunnel": false,
    "is_junction": true,
    "is_divided": true,
    "road_name_or_ref": "NH-753F",
    "context_summary": "NH-753F (4 lanes, 70 km/h, asphalt, Unlit highway section)."
  },
  "official_provenance": {
    "source_organization": "Maharashtra Highway Traffic Police",
    "report_year": 2024,
    "blackspot_id": "MH-PN-08",
    "total_fatalities_3yr": 18,
    "fatal_crashes_3yr": 14
  }
}
```

---

## 6. Responsible AI Language & Disclaimers

The system strictly adheres to the following clear boundaries:
* **ML Predictions:** Statistical estimates based on historical cluster patterns; never phrased as guarantees.
* **SHAP Values:** Feature attribution indicating mathematical importance in the decision tree, not direct real-world causality.
* **Official Blackspots:** Verified historical government safety audit records.
* **OSM Attributes:** Physical road network descriptions; not accident causes.
* **Non-Navigation Scope:** SafeRoute AI is an advisory risk-assessment system and does NOT provide turn-by-turn routing or replace municipal/police traffic authorities.

---

## 7. Verification & Test Suite Results

* **Pytest Test Suite:** Full pass across all test modules:
  * `test_api.py` (37 tests)
  * `test_geocoding.py` (9 tests)
  * `test_hotspot_intelligence.py` (7 tests)
  * `test_journey.py` (8 tests)
  * `test_official_blackspots.py` (8 tests)
  * `test_road_context.py` (6 tests)
  * **Total:** **79 / 79 passed (100% pass rate)**.
* **Frontend Build:** `npm run build` completed cleanly in 1.94s with zero bundle errors.
