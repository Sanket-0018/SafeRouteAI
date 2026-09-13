"""
ingest.py — Document Ingestion for SafeRoute AI RAG Knowledge Base

Fetches publicly accessible, authoritative Indian and international road-safety
documents from official government and multilateral organisation URLs.

PROVENANCE POLICY
-----------------
Every document ingested here must:
  1. Be publicly accessible without login or paywalls.
  2. Carry the exact source URL that was successfully fetched.
  3. Be tagged with the organisation that published it.
  4. Include the retrieval date so downstream consumers know when it was fetched.

HONEST LIMITATION DISCLOSURE
-----------------------------
Several primary Indian government sources (MoRTH, NHAI, PIB) are Angular SPA
or ASP.NET sites that render content via JavaScript. Their textual content is
NOT accessible via static HTTP fetching. This module:
  - Attempts fetches and reports failures transparently.
  - Falls back to structured knowledge authored from *publicly known and
    attributed* official content (e.g. WHO India page, which IS static-accessible).
  - Never fabricates text or pretends a document was retrieved if it was not.

Accessible sources confirmed (as of 2026-08-24):
  - WHO India — Road Safety page (static HTML, content extractable)
  - WHO Global — Road Traffic Injuries fact sheet (static HTML, content extractable)
  - WHO SAVE LIVES technical package summary (referenced, publicly accessible)

Not accessible via static fetch:
  - morth.nic.in  (Angular SPA — no text in static HTML)
  - nhai.gov.in   (404 on road-safety paths)
  - pib.gov.in    (ASP.NET, content in VIEWSTATE — not extractable)
"""

import datetime
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from src.rag.schemas import KnowledgeChunk

RETRIEVAL_DATE = datetime.date.today().isoformat()

# ──────────────────────────────────────────────────────────────────────────────
# Source catalogue
# ──────────────────────────────────────────────────────────────────────────────

SOURCE_CATALOGUE: List[Dict] = [
    {
        "document_id": "WHO-IND-RS",
        "title": "Road Safety — India",
        "source_organization": "World Health Organization (WHO India)",
        "source_url": "https://www.who.int/india/health-topics/road-safety",
        "document_type": "HEALTH_TOPIC_PAGE",
        "publication_date": "2019-11-05",
        "topic": "Overview of road safety in India — risk factors, burden, preventive approach",
    },
    {
        "document_id": "WHO-GLB-RTI",
        "title": "Road Traffic Injuries — WHO Fact Sheet",
        "source_organization": "World Health Organization (WHO Global)",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
        "document_type": "FACT_SHEET",
        "publication_date": "2023-12-13",
        "topic": "Global road traffic injury burden, risk factors, and prevention",
    },
    {
        "document_id": "WHO-SAVE-LIVES",
        "title": "Save LIVES: A Road Safety Technical Package",
        "source_organization": "World Health Organization",
        "source_url": "https://www.who.int/publications/i/item/save-lives-a-road-safety-technical-package",
        "document_type": "TECHNICAL_PACKAGE",
        "publication_date": "2017-01-01",
        "topic": "Speed, alcohol, vehicle safety, infrastructure, post-crash care — comprehensive framework",
    },
]

# These sources confirmed inaccessible via static fetch — documented for transparency
INACCESSIBLE_SOURCES = [
    {
        "document_id": "MORTH-ANNUAL-2023",
        "title": "Road Accidents in India 2022 — Annual Report",
        "source_organization": "Ministry of Road Transport and Highways, Government of India",
        "source_url": "https://morth.nic.in/road-accident-india",
        "reason": "Angular SPA — content rendered client-side, not accessible via static HTTP fetch",
    },
    {
        "document_id": "NHAI-RS",
        "title": "Road Safety Initiative — NHAI",
        "source_organization": "National Highways Authority of India",
        "source_url": "https://nhai.gov.in/en/road-safety-initiative",
        "reason": "HTTP 404 — road safety path not found on static fetch",
    },
]


def _clean_html(html: str) -> str:
    """Extract text content from HTML using BeautifulSoup. Remove scripts, styles, nav."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse excessive whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def _fetch_url(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch a URL and return cleaned text content, or None on failure."""
    headers = {"User-Agent": "SafeRouteAI-RAG-Ingestion/1.0 (academic research project)"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return _clean_html(resp.text)
        else:
            return None
    except Exception as e:
        return None


def fetch_all_sources(raw_dir: str) -> Dict[str, Optional[str]]:
    """
    Attempt to fetch all sources in the catalogue.
    Returns dict: document_id -> fetched text (or None if inaccessible).
    Saves raw text to raw_dir for reproducibility.
    """
    os.makedirs(raw_dir, exist_ok=True)
    results = {}

    for source in SOURCE_CATALOGUE:
        doc_id = source["document_id"]
        url = source["source_url"]
        print(f"  Fetching {doc_id}: {url}")
        text = _fetch_url(url)
        if text:
            # Save raw text
            raw_path = os.path.join(raw_dir, f"{doc_id}.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(f"SOURCE: {url}\n")
                f.write(f"TITLE: {source['title']}\n")
                f.write(f"ORG: {source['source_organization']}\n")
                f.write(f"RETRIEVED: {RETRIEVAL_DATE}\n\n")
                f.write(text)
            print(f"    ✓ Fetched {len(text)} characters → {raw_path}")
            results[doc_id] = text
        else:
            print(f"    ✗ FAILED — {url} not accessible via static fetch")
            results[doc_id] = None

    # Log inaccessible sources
    inaccess_path = os.path.join(raw_dir, "_inaccessible_sources.json")
    with open(inaccess_path, "w", encoding="utf-8") as f:
        json.dump(INACCESSIBLE_SOURCES, f, indent=2)
    print(f"  Inaccessible sources logged → {inaccess_path}")

    return results
