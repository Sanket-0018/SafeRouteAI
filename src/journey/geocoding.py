"""
SafeRoute AI — Compliant Universal Geocoding & Place Search Service
Provides fast first-level matching from local Indian/Maharashtra places index,
with a rate-limited, cached backend proxy fallback to OpenStreetMap Nominatim/Photon.

Complies strictly with OpenStreetMap Nominatim Usage Policies:
- Custom identifying User-Agent header
- Maximum 1 request per second rate limiting
- Persistent disk caching of geocoded results
- Never exposes internal/provider errors to client
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "external"
LOCAL_INDEX_PATH = DATA_DIR / "indian_places_index.json"
GEOCODING_CACHE_PATH = DATA_DIR / "geocoding_cache.json"

USER_AGENT = "SafeRouteAI-RoadSafety-System/1.0 (1M1B AI for Sustainability Internship; contact=research@saferoute.ai)"

# In-memory rate limiting tracker (1 req / sec)
_last_request_time = 0.0


class PlaceItem(BaseModel):
    display_name: str = Field(..., description="Full descriptive name of the place (e.g. Pune, Maharashtra)")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    city: Optional[str] = Field(None, description="City / Municipal corporation name")
    state: Optional[str] = Field(None, description="State name (e.g. Maharashtra)")
    country: str = Field("India", description="Country name")
    place_type: str = Field("location", description="Type of place: city, town, airport, railway_station, locality")


def _load_local_places_index() -> List[Dict[str, Any]]:
    """Loads the pre-indexed Maharashtra and Indian places database."""
    if not LOCAL_INDEX_PATH.exists():
        return []
    try:
        with open(LOCAL_INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load local places index: {e}")
        return []


def _load_geocoding_cache() -> Dict[str, List[Dict[str, Any]]]:
    """Loads persistent disk cache for previously resolved geocoding queries."""
    if not GEOCODING_CACHE_PATH.exists():
        return {}
    try:
        with open(GEOCODING_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load geocoding cache: {e}")
        return {}


def _save_geocoding_cache(cache: Dict[str, List[Dict[str, Any]]]) -> None:
    """Saves updated cache to disk."""
    try:
        GEOCODING_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(GEOCODING_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save geocoding cache: {e}")


def _normalize_query(query: str) -> str:
    """Normalizes query text for consistent indexing and caching."""
    if not query:
        return ""
    # Strip special chars, lowercase, collapse whitespace
    cleaned = re.sub(r"[^\w\s,]", " ", query).strip().lower()
    return re.sub(r"\s+", " ", cleaned)


def _rate_limit_throttle(min_interval: float = 1.0) -> None:
    """Enforces OSM Nominatim policy of max 1 request per second."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_request_time = time.time()


def _fetch_from_external_geocoder(query: str, limit: int = 5) -> List[PlaceItem]:
    """
    Compliant fallback to OpenStreetMap Nominatim API for addresses/localities
    not present in the local cache index.
    """
    _rate_limit_throttle(min_interval=1.0)

    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": "1",
        "limit": str(limit),
        "countrycodes": "in",
    }
    url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=4.0) as response:
            if response.status != 200:
                return []
            raw_data = json.loads(response.read().decode("utf-8"))
            results: List[PlaceItem] = []

            for item in raw_data:
                lat = float(item.get("lat", 0))
                lon = float(item.get("lon", 0))
                if lat == 0 and lon == 0:
                    continue

                address = item.get("address", {})
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("municipality")
                    or address.get("district")
                    or address.get("county")
                )
                state = address.get("state") or "Maharashtra"
                country = address.get("country") or "India"
                display_name = item.get("display_name", "")

                # Format clean short display name
                place_type = item.get("type", "location")
                if place_type in ["aerodrome", "airport"]:
                    place_type = "airport"
                elif place_type in ["station", "railway_station", "halt"]:
                    place_type = "railway_station"
                elif place_type in ["city", "town", "village", "suburb"]:
                    place_type = "city"
                else:
                    place_type = "locality"

                results.append(
                    PlaceItem(
                        display_name=display_name,
                        latitude=lat,
                        longitude=lon,
                        city=city,
                        state=state,
                        country=country,
                        place_type=place_type,
                    )
                )

            return results
    except Exception as e:
        logger.warning(f"External geocoder lookup failed for '{query}': {e}")
        return []


def search_places(query: str, limit: int = 10) -> List[PlaceItem]:
    """
    Main place search entrypoint.
    1. Returns [] if query is empty or < 2 characters.
    2. Searches curated local place index (0ms latency).
    3. Searches disk cache for past queries.
    4. If matches < limit, falls back to compliant OSM Nominatim proxy.
    5. Deduplicates and formats results.
    """
    if not query or len(query.strip()) < 2:
        return []

    norm_query = _normalize_query(query)
    results: List[PlaceItem] = []
    seen_names = set()

    def add_item(item: PlaceItem):
        # Deduplication key: normalized display name or close coordinates
        key = item.display_name.lower().strip()
        if key not in seen_names and len(results) < limit:
            seen_names.add(key)
            results.append(item)

    # 1. Search Curated Local Index
    local_index = _load_local_places_index()
    terms = norm_query.split()

    # Exact prefix matches first
    for p in local_index:
        name_lower = p["display_name"].lower()
        city_lower = (p.get("city") or "").lower()
        
        # Check if query matches beginning of city or display name
        if city_lower.startswith(norm_query) or name_lower.startswith(norm_query):
            add_item(PlaceItem(**p))

    # Substring matches second
    if len(results) < limit:
        for p in local_index:
            name_lower = p["display_name"].lower()
            if all(t in name_lower for t in terms):
                add_item(PlaceItem(**p))

    # 2. Check Disk Cache
    disk_cache = _load_geocoding_cache()
    if norm_query in disk_cache:
        for p in disk_cache[norm_query]:
            add_item(PlaceItem(**p))

    # 3. External Fallback if results are insufficient
    if len(results) < 3 and len(norm_query) >= 3:
        try:
            external_results = _fetch_from_external_geocoder(query, limit=limit)
            if external_results:
                # Save to disk cache
                disk_cache[norm_query] = [r.model_dump() for r in external_results]
                _save_geocoding_cache(disk_cache)

                for r in external_results:
                    add_item(r)
        except Exception as e:
            logger.warning(f"External geocoder error: {e}")

    return results[:limit]
