from __future__ import annotations

from datetime import date

from tripplanner.core.models import Attraction, DayPlan, Hotel, Location, Meal, TripPlan
from tripplanner.logic.budget import calculate_budget


def _attraction(price: float = 0.0) -> Attraction:
    return Attraction(
        xid="x1", name="Place",
        location=Location(longitude=0, latitude=0),
        ticket_price=price,
    )


def _plan(num_days: int = 1, transport: str = "walking") -> TripPlan:
    days = []
    for i in range(num_days):
        days.append(
            DayPlan(
                date=date(2026, 4, 10 + i),
                day_number=i + 1,
                attractions=[_attraction(50.0)],
                meals=[
                    Meal(type="breakfast", name="B", estimated_cost=30),
                    Meal(type="lunch", name="L", estimated_cost=60),
                    Meal(type="dinner", name="D", estimated_cost=80),
                ],
            )
        )
    return TripPlan(city="Test", start_date=date(2026, 4, 10), end_date=date(2026, 4, 10 + num_days - 1), days=days)


class TestCalculateBudget:
    def test_basic(self) -> None:
        plan = _plan(1)
        budget = calculate_budget(plan)
        assert budget.total_attractions == 50.0
        assert budget.total_meals == 170.0
        assert budget.total > 0

    def test_total_equals_sum(self) -> None:
        plan = _plan(2)
        budget = calculate_budget(plan)
        assert budget.total == (
            budget.total_attractions
            + budget.total_hotels
            + budget.total_meals
            + budget.total_transportation
        )

    def test_walking_no_transport_cost(self) -> None:
        plan = _plan(1)
        budget = calculate_budget(plan, "walking")
        assert budget.total_transportation == 0.0

    def test_transit_has_cost(self) -> None:
        plan = _plan(1)
        budget = calculate_budget(plan, "transit")
        assert budget.total_transportation > 0

    def test_driving_has_cost(self) -> None:
        plan = _plan(1)
        budget = calculate_budget(plan, "driving")
        assert budget.total_transportation > 0
        assert budget.total_transportation > calculate_budget(plan, "transit").total_transportation

    def test_empty_plan(self) -> None:
        plan = TripPlan(city="X", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        budget = calculate_budget(plan)
        assert budget.total_attractions == 0
