from __future__ import annotations

from datetime import date

from tripplanner.core.models import Attraction, Location
from tripplanner.logic.scheduler import build_day_plan, build_itinerary


def _place(name: str = "Place", duration: int = 90) -> Attraction:
    return Attraction(
        xid=f"x_{name}",
        name=name,
        location=Location(longitude=139.69, latitude=35.68),
        visit_duration=duration,
    )


class TestBuildDayPlan:
    def test_basic_day(self) -> None:
        dp = build_day_plan(1, date(2026, 4, 10), [_place("Tower"), _place("Shrine")])
        assert dp.day_number == 1
        assert dp.date == date(2026, 4, 10)
        assert len(dp.attractions) == 2

    def test_has_meals(self) -> None:
        dp = build_day_plan(1, date(2026, 4, 10), [_place("Tower")])
        meal_types = [m.type for m in dp.meals]
        assert "breakfast" in meal_types
        assert "dinner" in meal_types

    def test_respects_max_hours(self) -> None:
        # 8 attractions * 90 min each = 720 min > 600 max
        places = [_place(f"P{i}", duration=90) for i in range(8)]
        dp = build_day_plan(1, date(2026, 4, 10), places)
        # Should not schedule all 8
        assert len(dp.attractions) < 8
        assert "could not fit" in dp.description

    def test_empty_cluster(self) -> None:
        dp = build_day_plan(1, date(2026, 4, 10), [])
        assert dp.attractions == []
        assert dp.day_number == 1

    def test_single_place(self) -> None:
        dp = build_day_plan(1, date(2026, 4, 10), [_place("Solo")])
        assert len(dp.attractions) == 1
        assert dp.attractions[0].name == "Solo"


class TestBuildItinerary:
    def test_multi_day(self) -> None:
        clusters = [
            [_place("A"), _place("B")],
            [_place("C")],
            [_place("D"), _place("E"), _place("F")],
        ]
        plan = build_itinerary(
            clusters,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
        )
        assert len(plan.days) == 3
        assert plan.days[0].day_number == 1
        assert plan.days[2].day_number == 3
        assert len(plan.days[0].attractions) == 2

    def test_fewer_clusters_than_days(self) -> None:
        clusters = [[_place("A")]]
        plan = build_itinerary(
            clusters,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
        )
        assert len(plan.days) == 3
        assert plan.days[1].attractions == []
        assert plan.days[2].attractions == []

    def test_dates_correct(self) -> None:
        plan = build_itinerary(
            [],
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
        )
        assert plan.start_date == date(2026, 5, 1)
        assert plan.end_date == date(2026, 5, 3)
        assert plan.days[0].date == date(2026, 5, 1)
        assert plan.days[2].date == date(2026, 5, 3)
