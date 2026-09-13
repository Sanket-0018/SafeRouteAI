"""
schemas.py — Knowledge Chunk Schema

Defines the canonical data model for a knowledge chunk in the SafeRoute AI
RAG knowledge base. Every chunk must carry full provenance metadata so that
every retrieved recommendation can be traced back to its original source.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KnowledgeChunk:
    """
    A single unit of knowledge in the SafeRoute AI RAG knowledge base.

    Every chunk is derived from a publicly accessible, authoritative
    road-safety source and carries full provenance metadata.
    """

    # --- Identity ---
    chunk_id: str                      # Unique identifier, e.g. "WHO-IND-001-01"
    document_id: str                   # Parent document identifier

    # --- Provenance (mandatory) ---
    title: str                         # Document / section title
    source_organization: str           # Issuing organization (e.g. "WHO India")
    source_url: str                    # Canonical public URL of the source
    document_type: str                 # e.g. "FACT_SHEET", "POLICY", "GUIDANCE"
    publication_date: str              # ISO date or "N/A" if unavailable
    retrieval_date: str                # Date this chunk was fetched (ISO)

    # --- Content ---
    topic: str                         # High-level topic category
    content: str                       # Chunk text

    # --- Retrieval tags ---
    risk_factors: List[str] = field(default_factory=list)   # SHAP factor tags
    keywords: List[str] = field(default_factory=list)        # Search keywords

    # --- Vector store fields (populated at indexing time) ---
    embedding: Optional[List[float]] = None

    def to_dict(self) -> dict:
        """Serialize to plain dict for JSON storage and ChromaDB metadata."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "source_organization": self.source_organization,
            "source_url": self.source_url,
            "document_type": self.document_type,
            "publication_date": self.publication_date,
            "retrieval_date": self.retrieval_date,
            "topic": self.topic,
            "content": self.content,
            "risk_factors": ", ".join(self.risk_factors),
            "keywords": ", ".join(self.keywords),
        }
