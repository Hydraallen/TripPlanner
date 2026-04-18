from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt

from tripplanner.core.models import Attraction

EARTH_RADIUS_KM = 6371.0

SPEED_KMH: dict[str, float] = {
    "walking": 5.0,
    "transit": 25.0,
    "driving": 30.0,
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Haversine distance in km between two points."""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * atan2(sqrt(a), sqrt(1 - a))


def estimate_travel_time(distance_km: float, mode: str = "walking") -> int:
    """Estimate travel time in minutes."""
    speed = SPEED_KMH.get(mode, SPEED_KMH["walking"])
    return int((distance_km / speed) * 60)


def optimize_routes(
    places: list[Attraction],
    center: tuple[float, float],
    num_days: int,
    places_per_day: int = 4,
    transport_mode: str = "walking",
    max_detour_km: float = 15.0,
) -> list[list[Attraction]]:
    """Greedy nearest-neighbor route optimization.

    1. Sort places by score descending.
    2. Pick highest-scored unassigned place as cluster anchor.
    3. Greedily add nearest unassigned place within threshold.
    4. When cluster reaches places_per_day, start a new cluster.
    5. Distribute remaining places across clusters.

    Returns exactly num_days clusters (some may be empty).
    """
    if num_days <= 0:
        return []

    if not places:
        return [[] for _ in range(num_days)]

    # Sort by score descending
    sorted_places = sorted(places, key=lambda p: p.score, reverse=True)
    unassigned = list(sorted_places)
    clusters: list[list[Attraction]] = []

    while unassigned and len(clusters) < num_days:
        cluster: list[Attraction] = [unassigned.pop(0)]  # anchor = highest scored

        while len(cluster) < places_per_day and unassigned:
            last = cluster[-1]
            best_idx = _find_nearest_index(
                last, unassigned, max_detour_km=max_detour_km
            )
            if best_idx is None:
                break
            cluster.append(unassigned.pop(best_idx))

        clusters.append(cluster)

    # If we ran out of days before assigning all places, spread extras
    if unassigned:
        for i, place in enumerate(unassigned):
            day_idx = i % num_days
            if day_idx < len(clusters):
                clusters[day_idx].append(place)
            else:
                clusters.append([place])

    # Pad to exactly num_days
    while len(clusters) < num_days:
        clusters.append([])

    # Sort within each cluster by nearest-neighbor from center
    for cluster in clusters:
        _sort_cluster_by_nn(cluster, center)

    return clusters[:num_days]


def _find_nearest_index(
    anchor: Attraction, candidates: list[Attraction], max_detour_km: float
) -> int | None:
    """Find index of the nearest candidate to anchor within max_detour_km."""
    best_dist = max_detour_km
    best_idx: int | None = None

    for i, c in enumerate(candidates):
        d = haversine(
            anchor.location.latitude, anchor.location.longitude,
            c.location.latitude, c.location.longitude,
        )
        if d < best_dist:
            best_dist = d
            best_idx = i

    return best_idx


def _sort_cluster_by_nn(
    cluster: list[Attraction], start: tuple[float, float]
) -> None:
    """Sort a cluster by nearest-neighbor starting from a point (in-place)."""
    if len(cluster) <= 1:
        return

    remaining = list(cluster)
    sorted_list: list[Attraction] = []
    current_lat, current_lon = start

    while remaining:
        best_idx = 0
        best_dist = float("inf")
        for i, p in enumerate(remaining):
            d = haversine(current_lat, current_lon, p.location.latitude, p.location.longitude)
            if d < best_dist:
                best_dist = d
                best_idx = i
        chosen = remaining.pop(best_idx)
        sorted_list.append(chosen)
        current_lat = chosen.location.latitude
        current_lon = chosen.location.longitude

    cluster[:] = sorted_list
