"""
SafeRoute AI — OSRM Route Geometry Client
Retrieves OpenStreetMap driving routes as GeoJSON LineStrings with local disk caching.
Strict Scope: Geometry retrieval only — no turn-by-turn directions or routing guidance.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.parse

from src.journey.schemas import RouteGeometry

logger = logging.getLogger(__name__)

# Known coordinates for Indian hubs to enable instant offline geocoding
KNOWN_CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "pune": (18.5204, 73.8567),
    "pune, maharashtra": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "nagpur, maharashtra": (21.1458, 79.0882),
    "mumbai": (19.0760, 72.8777),
    "mumbai, maharashtra": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bangalore, karnataka": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "hyderabad, telangana": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "chennai, tamil nadu": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "kolkata, west bengal": (22.5726, 88.3639),
    "delhi": (28.6139, 77.2090),
    "chandigarh": (30.7333, 76.7794),
    "ahmednagar": (19.0952, 74.7480),
    "chhatrapati sambhaji nagar": (19.8762, 75.3433),
    "aurangabad": (19.8762, 75.3433),
    "jalna": (19.8410, 75.8864),
    "amravati": (20.9320, 77.7523),
    "nashik": (19.9975, 73.7898),
    "solapur": (17.6599, 75.9064),
    "kolhapur": (16.7050, 74.2433),
    "kolhapur, maharashtra": (16.7050, 74.2433),
    "satara": (17.6805, 74.0183),
    "sangli": (16.8524, 74.5815),
    "latur": (18.4088, 76.5604),
    "latur, maharashtra": (18.4088, 76.5604),
    "nanded": (19.1383, 77.3210),
    "nanded, maharashtra": (19.1383, 77.3210),
    "dhule": (20.9042, 74.7749),
    "jalgaon": (21.0077, 75.5626),
    "akola": (20.7002, 77.0082),
    "wardha": (20.7453, 78.6022),
    "chandrapur": (19.9615, 79.2961),
    "ratnagiri": (16.9902, 73.3120),
    "sindhudurg": (16.0350, 73.6850),
    "goa": (15.2993, 74.1240),
    "goa, india": (15.2993, 74.1240),
    "panaji": (15.4909, 73.8278),
    "panaji, goa": (15.4909, 73.8278),
}

_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "external"
_CACHE_FILE = _CACHE_DIR / "route_cache.json"
_INDEX_FILE = _CACHE_DIR / "indian_places_index.json"
_PLACES_INDEX_CACHE: Optional[List[Dict[str, Any]]] = None


def _get_places_index() -> List[Dict[str, Any]]:
    global _PLACES_INDEX_CACHE
    if _PLACES_INDEX_CACHE is None:
        if _INDEX_FILE.exists():
            try:
                with open(_INDEX_FILE, encoding="utf-8") as f:
                    _PLACES_INDEX_CACHE = json.load(f)
            except Exception:
                _PLACES_INDEX_CACHE = []
        else:
            _PLACES_INDEX_CACHE = []
    return _PLACES_INDEX_CACHE


def _resolve_coordinates(
    query_name: str,
    custom_lat: Optional[float] = None,
    custom_lon: Optional[float] = None,
) -> Tuple[float, float]:
    """Resolves latitude and longitude for a city name or returns custom coordinates."""
    if custom_lat is not None and custom_lon is not None:
        return custom_lat, custom_lon

    clean = query_name.lower().strip()
    if clean in KNOWN_CITY_COORDINATES:
        return KNOWN_CITY_COORDINATES[clean]

    for k, coords in KNOWN_CITY_COORDINATES.items():
        if k in clean or clean in k:
            return coords

    # Check local Indian places index (55+ Maharashtra cities, airports, stations)
    places = _get_places_index()
    # Exact match on city or display_name
    for p in places:
        c_name = p.get("city", "").lower().strip()
        d_name = p.get("display_name", "").lower().strip()
        if clean == c_name or clean == d_name:
            return float(p["latitude"]), float(p["longitude"])

    # Substring match on city or display_name
    for p in places:
        c_name = p.get("city", "").lower().strip()
        d_name = p.get("display_name", "").lower().strip()
        if c_name and (c_name in clean or clean in c_name):
            return float(p["latitude"]), float(p["longitude"])
        if d_name and (clean in d_name):
            return float(p["latitude"]), float(p["longitude"])

    # Attempt dynamic Nominatim/Photon lookup via search_places
    try:
        from src.journey.geocoding import search_places
        ext_places = search_places(query_name, limit=1)
        if ext_places and len(ext_places) > 0:
            logger.info(f"Dynamically geocoded '{query_name}' to ({ext_places[0].latitude}, {ext_places[0].longitude})")
            return float(ext_places[0].latitude), float(ext_places[0].longitude)
    except Exception as e:
        logger.warning(f"Dynamic geocoding lookup failed for '{query_name}': {e}")

    # Fallback to Pune coordinates if unresolvable
    logger.warning(f"Could not resolve coordinates for '{query_name}'. Falling back to center coordinates.")
    return 18.5204, 73.8567


def _load_cache() -> Dict[str, Any]:
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save route cache: {e}")


def _generate_synthetic_corridor_line(
    lat1: float, lon1: float, lat2: float, lon2: float, n_points: int = 50
) -> List[List[float]]:
    """Generates an interpolated straight-line GeoJSON [[lon, lat], ...] for offline fallback."""
    coords = []
    for i in range(n_points):
        t = i / (n_points - 1)
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        coords.append([round(lon, 5), round(lat, 5)])
    return coords


def get_route_geometry(
    origin_name: str,
    destination_name: str,
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
    timeout_sec: float = 5.0,
) -> RouteGeometry:
    """
    Fetches the road route geometry between origin and destination via OSRM public API.
    Uses local caching to ensure sub-millisecond responses and offline stability.
    """
    lat1, lon1 = _resolve_coordinates(origin_name, origin_lat, origin_lon)
    lat2, lon2 = _resolve_coordinates(destination_name, dest_lat, dest_lon)

    cache_key = f"{round(lat1, 4)},{round(lon1, 4)}_to_{round(lat2, 4)},{round(lon2, 4)}"
    cache = _load_cache()

    if cache_key in cache:
        cached = cache[cache_key]
        return RouteGeometry(**cached)

    # Attempt to query OSRM Public Driving API (lon,lat order for OSRM URL)
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?geometries=geojson&overview=full"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SafeRouteAI-Research-System/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            coordinates = route["geometry"]["coordinates"]
            dist_km = round(route["distance"] / 1000.0, 1)
            duration_hours = round(route["duration"] / 3600.0, 2)
            
            hours = int(duration_hours)
            mins = int((duration_hours - hours) * 60)
            formatted = f"{hours}h {mins}m"

            result = RouteGeometry(
                coordinates=coordinates,
                distance_km=dist_km,
                duration_hours=duration_hours,
                estimated_duration_formatted=formatted,
            )

            cache[cache_key] = result.model_dump()
            _save_cache(cache)
            return result

    except Exception as e:
        logger.warning(f"OSRM API call failed ({e}). Using geodesic road corridor fallback.")

    # Geodesic fallback calculation
    # Calculate Haversine distance with standard 1.25 road winding factor
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    direct_km = r * c
    est_road_km = round(direct_km * 1.25, 1)
    
    # Average highway transit speed ~65 km/h
    est_duration_hours = round(est_road_km / 65.0, 2)
    hours = int(est_duration_hours)
    mins = int((est_duration_hours - hours) * 60)
    formatted = f"{hours}h {mins}m"

    coords = _generate_synthetic_corridor_line(lat1, lon1, lat2, lon2, n_points=80)

    result = RouteGeometry(
        coordinates=coords,
        distance_km=est_road_km,
        duration_hours=est_duration_hours,
        estimated_duration_formatted=formatted,
    )

    cache[cache_key] = result.model_dump()
    _save_cache(cache)
    return result
