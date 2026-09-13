"""
retriever.py — Vector Store and Semantic Retrieval for SafeRoute AI RAG

Builds and persists a ChromaDB collection from embedded KnowledgeChunks.
Provides semantic retrieval with optional metadata filtering.

Architecture
------------
- Vector store: ChromaDB (local persistent, no server process required)
- Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- Retrieval: cosine similarity, top-k, with optional topic/risk_factor filters
- SHAP-to-query bridge: converts ML SHAP factor names to semantic retrieval queries
"""

import os
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings

from src.rag.schemas import KnowledgeChunk
from src.rag.embeddings import embed_query

COLLECTION_NAME = "saferoute_knowledge"


# ──────────────────────────────────────────────────────────────────────────────
# SHAP Factor → Knowledge Topic Mapping
# (retrieval formulation only — NOT causal inference)
# ──────────────────────────────────────────────────────────────────────────────

SHAP_FACTOR_TO_QUERY: Dict[str, str] = {
    # Historical accident volume
    "lag_expanding_accidents": (
        "road safety treatment for locations with high historical accident frequency and crash density "
        "India blackspot identification engineering countermeasure"
    ),
    "lag_accidents_30d": (
        "recent surge in road accident frequency short term trend road safety response India"
    ),
    "lag_accidents_90d": (
        "road accident cluster short term pattern treatment hotspot intervention India"
    ),
    "lag_accidents_180d": (
        "sustained high accident frequency 6 month road safety treatment India"
    ),
    "lag_trend_90d_vs_180d": (
        "increasing trend road accidents emerging risk escalation India response"
    ),

    # Severity and casualty history
    "lag_expanding_fatal_rate": (
        "high fatality rate road crash India countermeasure speed management infrastructure blackspot "
        "vulnerable road users pedestrian cyclist"
    ),
    "lag_expanding_major_rate": (
        "major injury crash hotspot road design infrastructure improvement India"
    ),
    "lag_expanding_casualty_density": (
        "high casualty density road safety emergency response trauma care India"
    ),

    # Zone-window specific severity
    "lag_zw_expanding_swri": (
        "high severity crash history specific location time window road safety engineering treatment "
        "India night time peak hour"
    ),
    "lag_zw_expanding_accidents": (
        "accident prone zone time window specific road safety intervention India"
    ),

    # Temporal / contextual
    "is_peak_window": (
        "peak hour traffic management road safety congestion urban India signal intersection"
    ),
    "time_window_4h": (
        "night time road safety late night driving visibility lighting India highway urban"
    ),

    # Spatial
    "center_lat": "urban road safety India city",
    "center_lon": "urban road safety India city",
    "max_r_km": "road safety large zone area treatment India",
}

# City-specific context modifiers
CITY_CONTEXT_SUFFIX = {
    "Pune": "Maharashtra urban arterial road safety",
    "Mumbai": "Mumbai Metropolitan Region urban highway road safety",
    "Delhi": "Delhi NCR National Capital road safety",
    "Bangalore": "Bangalore urban traffic management road safety",
    "Chennai": "Chennai urban road safety",
    "Hyderabad": "Hyderabad urban corridor road safety",
    "Kolkata": "Kolkata road safety pedestrian",
    "Chandigarh": "Chandigarh planned city road safety",
}


def build_shap_query(
    shap_factors: List[Tuple[str, float]],
    city: str = "",
    time_label: str = "",
    top_n_factors: int = 3,
) -> str:
    """
    Convert SHAP factor attributions into a semantic retrieval query.

    Parameters
    ----------
    shap_factors : List of (factor_name, shap_value) sorted by |shap_value| desc
    city         : City name for context suffix
    time_label   : Time window label (e.g. "20:00–23:59")
    top_n_factors: How many top SHAP factors to incorporate

    Returns
    -------
    Semantic query string for embedding-based retrieval.
    This is a RETRIEVAL FORMULATION TOOL, not a causal inference.
    """
    query_parts = []

    for factor, shap_val in shap_factors[:top_n_factors]:
        base_factor = factor
        # Strip city dummy prefix if present
        if factor.startswith("city_"):
            continue
        # Strip lag prefix for fallback
        query = SHAP_FACTOR_TO_QUERY.get(base_factor, f"road safety {base_factor.replace('_', ' ')}")
        query_parts.append(query)

    # Incorporate time context
    if time_label:
        hour_str = time_label.split(":")[0] if ":" in time_label else ""
        try:
            hour = int(hour_str)
            if 0 <= hour < 6 or hour >= 22:
                query_parts.append("night time road safety darkness driving India")
            elif 7 <= hour <= 10 or 16 <= hour <= 20:
                query_parts.append("peak hour traffic congestion road safety India")
        except ValueError:
            pass

    # City context
    city_suffix = CITY_CONTEXT_SUFFIX.get(city, "urban road safety India")
    query_parts.append(city_suffix)

    return ". ".join(query_parts)


# ──────────────────────────────────────────────────────────────────────────────
# ChromaDB Vector Store
# ──────────────────────────────────────────────────────────────────────────────

def _get_client(persist_dir: str) -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def build_vector_store(chunks: List[KnowledgeChunk], persist_dir: str) -> None:
    """
    Build and persist the ChromaDB vector store from embedded chunks.
    Recreates the collection if it already exists (idempotent rebuild).
    """
    client = _get_client(persist_dir)

    # Drop existing collection if present for clean rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Existing collection deleted.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [chunk.chunk_id for chunk in chunks]
    embeddings = [chunk.embedding for chunk in chunks]
    documents = [chunk.content for chunk in chunks]
    metadatas = [chunk.to_dict() for chunk in chunks]

    # ChromaDB requires no None in metadata values
    for m in metadatas:
        for k, v in m.items():
            if v is None:
                m[k] = ""

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print(f"  ChromaDB collection '{COLLECTION_NAME}' built with {len(ids)} chunks.")
    print(f"  Persisted to: {persist_dir}")


def retrieve(
    query: str,
    persist_dir: str,
    top_k: int = 5,
    risk_factor_filter: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieve top-k chunks semantically similar to the query.

    Parameters
    ----------
    query : Semantic query string
    persist_dir : Path to the persisted ChromaDB store
    top_k : Number of results to return
    risk_factor_filter : Optional risk factor tag to pre-filter (not strictly applied —
                         ChromaDB metadata filtering is used as soft post-filter here)

    Returns
    -------
    List of result dicts with keys:
        rank, chunk_id, document_id, title, source_organization, topic,
        source_url, relevance_score, content, risk_factors
    """
    client = _get_client(persist_dir)
    collection = client.get_collection(COLLECTION_NAME)

    query_emb = embed_query(query)

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for rank, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ), start=1):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Relevance score (higher = more relevant): 1 - (dist / 2)
        relevance_score = round(1.0 - (dist / 2.0), 4)
        output.append({
            "rank": rank,
            "chunk_id": meta.get("chunk_id", ""),
            "document_id": meta.get("document_id", ""),
            "title": meta.get("title", ""),
            "source_organization": meta.get("source_organization", ""),
            "topic": meta.get("topic", ""),
            "source_url": meta.get("source_url", ""),
            "document_type": meta.get("document_type", ""),
            "publication_date": meta.get("publication_date", ""),
            "risk_factors": meta.get("risk_factors", ""),
            "relevance_score": relevance_score,
            "content": doc,
        })
    return output
