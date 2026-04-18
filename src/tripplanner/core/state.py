from __future__ import annotations

from datetime import date

from tripplanner.core.models import Attraction, TripPlan


class TripState:
    """Immutable pipeline state for tracking data through the planning pipeline."""

    def __init__(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        transport_mode: str = "walking",
    ) -> None:
        self.city = city
        self.start_date = start_date
        self.end_date = end_date
        self.interests = interests
        self.transport_mode = transport_mode

        self.city_coords: tuple[float, float] | None = None
        self.raw_places: list[Attraction] = []
        self.scored_places: list[Attraction] = []
        self.optimized_clusters: list[list[Attraction]] = []
        self.itinerary: TripPlan | None = None
