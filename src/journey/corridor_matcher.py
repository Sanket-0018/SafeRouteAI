"""
SafeRoute AI — Corridor Spatial Matcher
Spatially projects hazard points onto a journey LineString, computes chainage from origin,
and deduplicates hazard milestones along the travel path.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Great Circle distance in km between two lat/lon points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def project_point_on_segment(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> Tuple[float, float, float]:
    """
    Projects point P onto segment AB in flat Cartesian approximation.
    Returns (nearest_x, nearest_y, fraction_t) where t is in [0, 1].
    """
    dx = bx - ax
    dy = by - ay
    seg_sq = dx * dx + dy * dy
    if seg_sq == 0.0:
        return ax, ay, 0.0

    t = ((px - ax) * dx + (py - ay) * dy) / seg_sq
    t = max(0.0, min(1.0, t))
    return ax + t * dx, ay + t * dy, t


def match_hazard_to_route(
    hazard_lat: float,
    hazard_lon: float,
    route_coordinates: List[List[float]],
    total_route_distance_km: float,
) -> Optional[Tuple[float, float]]:
    """
    Finds the shortest distance from a hazard to the route polyline and its cumulative distance from origin.
    route_coordinates is in [[lon, lat], ...] order.
    Returns (distance_to_corridor_km, cumulative_distance_from_origin_km) or None.
    """
    if not route_coordinates or len(route_coordinates) < 2:
        return None

    # Calculate cumulative distance at each vertex
    vertex_distances = [0.0]
    for i in range(len(route_coordinates) - 1):
        p1 = route_coordinates[i]
        p2 = route_coordinates[i + 1]
        seg_dist = haversine_km(p1[1], p1[0], p2[1], p2[0])
        vertex_distances.append(vertex_distances[-1] + seg_dist)

    total_polyline_km = vertex_distances[-1] if vertex_distances[-1] > 0 else total_route_distance_km
    scale_factor = total_route_distance_km / total_polyline_km if total_polyline_km > 0 else 1.0

    min_dist_to_route = float("inf")
    best_along_route_km = 0.0

    # Scale factor for degree-to-km conversion around the hazard latitude
    lat_mid = hazard_lat
    km_per_lat = 110.574
    km_per_lon = 111.320 * math.cos(math.radians(lat_mid))

    hx = hazard_lon * km_per_lon
    hy = hazard_lat * km_per_lat

    for i in range(len(route_coordinates) - 1):
        lon_a, lat_a = route_coordinates[i]
        lon_b, lat_b = route_coordinates[i + 1]

        ax = lon_a * km_per_lon
        ay = lat_a * km_per_lat
        bx = lon_b * km_per_lon
        by = lat_b * km_per_lat

        near_x, near_y, t = project_point_on_segment(hx, hy, ax, ay, bx, by)
        dist_km = math.hypot(hx - near_x, hy - near_y)

        if dist_km < min_dist_to_route:
            min_dist_to_route = dist_km
            seg_start_dist = vertex_distances[i] * scale_factor
            seg_len = (vertex_distances[i + 1] - vertex_distances[i]) * scale_factor
            best_along_route_km = seg_start_dist + t * seg_len

    return min_dist_to_route, round(best_along_route_km, 1)


def deduplicate_hazards(
    hazards: List[Dict[str, Any]], min_spacing_km: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Removes closely overlapping hazards within min_spacing_km of each other,
    prioritizing higher risk tier, higher probability, or higher crash severity.
    """
    if not hazards:
        return []

    # Sort by along-route distance
    sorted_hazards = sorted(hazards, key=lambda h: h["distance_from_origin_km"])
    unique: List[Dict[str, Any]] = []

    for h in sorted_hazards:
        if not unique:
            unique.append(h)
            continue

        prev = unique[-1]
        dist_diff = abs(h["distance_from_origin_km"] - prev["distance_from_origin_km"])

        if dist_diff >= min_spacing_km:
            unique.append(h)
        else:
            # Conflict within min_spacing_km:
            # Score comparison: ML with high confidence (>0.80) or official blackspot with high severity
            h_score = (h.get("risk_probability") or 0.70)
            prev_score = (prev.get("risk_probability") or 0.70)
            if h["hazard_type"] == "ML_PREDICTED_HOTSPOT" and h_score >= 0.80:
                h_score += 0.15
            if prev["hazard_type"] == "ML_PREDICTED_HOTSPOT" and prev_score >= 0.80:
                prev_score += 0.15

            if h_score > prev_score:
                unique[-1] = h

    return unique
