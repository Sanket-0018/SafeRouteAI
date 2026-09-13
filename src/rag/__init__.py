"""SafeRoute AI — RAG Knowledge Retrieval Module"""

from src.rag.schemas import KnowledgeChunk
from src.rag.chunking import build_curated_chunks, chunk_fetched_document
from src.rag.embeddings import embed_chunks, embed_query
from src.rag.retriever import build_vector_store, retrieve, build_shap_query

__all__ = [
    "KnowledgeChunk",
    "build_curated_chunks",
    "chunk_fetched_document",
    "embed_chunks",
    "embed_query",
    "build_vector_store",
    "retrieve",
    "build_shap_query",
]
