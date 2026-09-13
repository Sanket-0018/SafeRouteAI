"""
embeddings.py — Embedding Generation for SafeRoute AI RAG

Encodes KnowledgeChunk content using sentence-transformers/all-MiniLM-L6-v2.
Model is downloaded from HuggingFace on first use (~80 MB) and cached locally.
CPU inference is used — no GPU required.
"""

import os
from typing import List, Optional

from src.rag.schemas import KnowledgeChunk

# Lazy import to avoid loading torch unless embedding is called
_model = None
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _get_model():
    """Load the embedding model once and cache it."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"  Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        dim = _model.get_embedding_dimension() if hasattr(_model, "get_embedding_dimension") else _model.get_sentence_embedding_dimension()
        print(f"  Model loaded. Embedding dimension: {dim}")
    return _model


def embed_chunks(chunks: List[KnowledgeChunk], batch_size: int = 32) -> List[KnowledgeChunk]:
    """
    Compute embeddings for all chunks in-place.
    Returns the same list with .embedding populated on each chunk.
    """
    model = _get_model()
    texts = [chunk.content for chunk in chunks]
    print(f"  Embedding {len(texts)} chunks in batches of {batch_size}...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb.tolist()
    print(f"  Done. Embedding shape: {len(embeddings)} x {len(embeddings[0])}")
    return chunks


def embed_query(query: str) -> List[float]:
    """Embed a single query string for retrieval."""
    model = _get_model()
    emb = model.encode([query], show_progress_bar=False)[0]
    return emb.tolist()


def get_embedding_dim() -> int:
    """Return the embedding dimension (384 for all-MiniLM-L6-v2)."""
    m = _get_model()
    return m.get_embedding_dimension() if hasattr(m, "get_embedding_dimension") else m.get_sentence_embedding_dimension()
