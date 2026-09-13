# SafeRoute AI — AI Road Safety Risk & Hotspot Analysis System

> **1M1B AI for Sustainability Virtual Internship**  
> **Primary SDG:** SDG 11 — Sustainable Cities and Communities  
> **Secondary SDG:** SDG 3 — Good Health and Well-being  

---

## 1. Project Overview

**SafeRoute AI** is an end-to-end analytical road-safety intelligence system designed for Indian metropolitan cities. Rather than attempting turn-by-turn navigation or routing, SafeRoute AI analyzes historical road-accident patterns to identify, rank, and explain geographic accident hotspots and high-risk location + time-window combinations, providing evidence-grounded engineering countermeasures retrieved from official road safety standards.

### Core Architectural Flow
```
Historical Accident Data (~20,000 records)
           ↓
Spatiotemporal Hotspot Clustering (City-specific HDBSCAN + 4-Hour Time Windows)
           ↓
Expanding/Rolling Lag Feature Formulation (0 Target Leakage)
           ↓
Machine Learning Risk Prediction (LightGBM Classifier on Out-of-Time Test Set)
           ↓
Local Explainability & Factor Attribution (SHAP TreeExplainer)
           ↓
Authoritative Knowledge Retrieval (RAG with ChromaDB & all-MiniLM-L6-v2 on MoRTH / IRC / WHO)
           ↓
Unified Hotspot Intelligence Layer (src/pipeline/)
           ↓
FastAPI Backend (api/)
           ↓
React + Vite Interactive Dashboard (frontend/)
           ↓
[Planned] Conversational Safety Assistant (IBM Bob)
```

---

## 2. Key Modules & Capabilities

1. **Spatial & Spatiotemporal Clustering (`notebooks/03`, `04`):**
   - Discovers dense spatial accident clusters across 7 major Indian cities (Pune, Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata, Chandigarh).
   - Segregates time shifts into 4-hour temporal windows with expanding historical lag features to prevent future data leakage.

2. **Predictive Risk Modeling (`notebooks/05`):**
   - Predicts HIGH-risk location + time windows using an out-of-time temporal validation strategy.
   - Evaluates tree-based architectures, selecting a tuned LightGBM classifier evaluated by Macro F1 and Precision-Recall AUC (PR-AUC).

3. **SHAP Factor Attribution (`notebooks/05`, `src/pipeline/`):**
   - Extracts local feature attributions for each predicted hotspot (e.g. 180-day crash volume, shift severity index, spatial footprint radius).
   - Accurately presented as statistical model sensitivity, not physical causation.

4. **Retrieval-Augmented Generation / RAG (`notebooks/06`, `src/rag/`):**
   - Persisted vector database using ChromaDB and `sentence-transformers/all-MiniLM-L6-v2`.
   - Indexes official guidelines from the Ministry of Road Transport and Highways (MoRTH), Indian Roads Congress (IRC), and World Health Organization (WHO).
   - Synthesizes queries from top SHAP factors to retrieve relevant engineering standards and countermeasures.

5. **FastAPI Backend (`api/`):**
   - High-performance RESTful API serving pre-computed hotspot intelligence, statistics, and filtering.
   - Fully typed Pydantic models with OpenAPI/Swagger docs at `/docs`.

6. **Interactive React Dashboard (`frontend/`):**
   - Modern React 19 + Vite dashboard featuring Leaflet OpenStreetMap spatial clustering, ranked table, SHAP horizontal contribution bars, and RAG knowledge cards with verified source links.

7. **IBM Bob Conversational Assistant *(Planned)*:**
   - Future conversational interface layer that synthesizes backend ML predictions, SHAP factors, and RAG guidance into traffic authority briefings and commuter risk-window alerts.

---

## 3. Project Structure

```
SafeRouteAI/
├── AGENTS.md                  # Project charter & non-negotiable scope rules
├── README.md                  # System overview and run instructions
├── requirements.txt           # Python virtual environment dependencies
├── api/                       # FastAPI backend service
│   ├── main.py                # App entry point, CORS, and routes
│   ├── schemas.py             # Pydantic data schemas
│   └── services.py            # Data loading & query service layer
├── data/
│   ├── raw/                   # Immutable raw accident dataset
│   ├── processed/             # Cleaned datasets & spatiotemporal feature matrices
│   └── knowledge_base/        # Curated text corpus, chunk metadata & ChromaDB index
├── frontend/                  # Interactive React + Vite dashboard
│   ├── src/                   # React components (Map, List, SHAP, RAG views)
│   └── package.json           # Frontend dependencies (Leaflet, Lucide)
├── models/                    # Serialized LightGBM model and JSON metadata
├── notebooks/                 # Documented Jupyter notebooks (01 to 06)
├── outputs/
│   ├── figures/               # Model comparison, confusion matrices, SHAP charts
│   ├── maps/                  # Interactive HTML spatial maps
│   └── reports/               # Ranked predictions, SHAP attributions, RAG results
├── src/
│   ├── pipeline/              # Unified hotspot intelligence builder
│   └── rag/                   # Ingest, chunking, embeddings, and Chroma retriever
└── tests/                     # Automated unit and API test suite (41 tests)
```

---

## 4. Scope & Responsible AI Governance

- **Non-Routing Scope:** SafeRoute AI is an analytical hotspot prediction and domain knowledge retrieval tool. It is **NOT** a navigation system, turn-by-turn routing engine, or Google Maps replacement.
- **Probabilistic Risk:** A HIGH risk prediction signifies historically elevated danger conditions; it does not claim an accident is guaranteed.
- **Correlation vs. Causation:** SHAP values represent statistical feature contributions to the model's output score, not proven physical causation.
- **Authoritative Advisory:** Safety guidance is retrieved from official literature (MoRTH/IRC/WHO) to support municipal planning and traffic engineering decisions.

---

## 5. How to Run Locally

### Prerequisites
- Python 3.10+ with active `.venv`
- Node.js v18+ and npm

### 1. Start the FastAPI Backend
```powershell
# From the project root:
.venv\Scripts\uvicorn api.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`

### 2. Start the Frontend Dashboard
```powershell
# In a separate terminal:
cd frontend
npm run dev
```
- Open `http://localhost:5173` in your browser.

### 3. Run Test Suite
```powershell
# Run backend and pipeline tests:
.venv\Scripts\pytest tests/ -v

# Run frontend production build test:
cd frontend
npm run build
```