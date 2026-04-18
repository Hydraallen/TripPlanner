from __future__ import annotations

from datetime import date

from tripplanner.core.models import Attraction, Location
from tripplanner.core.state import TripState


class TestTripState:
    def test_initial_state(self) -> None:
        state = TripState(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 13),
            interests=["museums"],
        )
        assert state.city == "Tokyo"
        assert state.city_coords is None
        assert state.raw_places == []
        assert state.itinerary is None

    def test_state_mutation(self) -> None:
        state = TripState(
            city="Paris",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            interests=["food"],
        )
        state.city_coords = (48.85, 2.35)
        state.raw_places = [
            Attraction(xid="x1", name="Tower", location=Location(longitude=2.35, latitude=48.85))
        ]
        assert state.city_coords == (48.85, 2.35)
        assert len(state.raw_places) == 1
