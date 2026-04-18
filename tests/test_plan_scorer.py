from __future__ import annotations

from datetime import date

import pytest

from tripplanner.core.models import (
    Attraction,
    DayPlan,
    Location,
    Meal,
    PlanAlternative,
    PlanFocus,
    PlanScores,
    TripPlan,
)
from tripplanner.web.services.plan_scorer import score_plan, score_plans


def _make_attraction(
    name: str = "Museum",
    rating: float | None = 4.0,
    kinds: str = "museums",
    cost: float = 0,
) -> Attraction:
    return Attraction(
        xid=f"N_{name}",
        name=name,
        location=Location(longitude=139.69, latitude=35.68),
        rating=rating,
        kinds=kinds,
        ticket_price=cost,
    )


def _make_plan(
    budget_total: float = 0,
    attractions: list[Attraction] | None = None,
    meals: list[Meal] | None = None,
    num_days: int = 1,
) -> TripPlan:
    days: list[DayPlan] = []
    for i in range(num_days):
        day = DayPlan(
            date=date(2026, 4, 10 + i),
            day_number=i + 1,
            attractions=attractions or [_make_attraction()],
            meals=meals or [Meal(type="lunch", name="Food", estimated_cost=50)],
        )
        days.append(day)

    from tripplanner.core.models import Budget

    return TripPlan(
        city="Tokyo",
        start_date=date(2026, 4, 10),
        end_date=date(2026, 4, 10 + num_days - 1),
        days=days,
        budget=Budget(total=budget_total) if budget_total > 0 else None,
    )


def _make_alt(plan: TripPlan | None = None, cost: float = 0) -> PlanAlternative:
    return PlanAlternative(
        id="plan_1",
        focus=PlanFocus.BUDGET,
        title="Test Plan",
        plan=plan or _make_plan(),
        estimated_cost=cost,
    )


# --- score_plan ---


class TestScorePlan:
    def test_basic_plan(self) -> None:
        alt = _make_alt(_make_plan(attractions=[_make_attraction(rating=4.0)]))
        scores = score_plan(alt, days=1)
        assert isinstance(scores, PlanScores)
        assert 0 <= scores.total <= 1
        assert scores.rating > 0

    def test_no_budget(self) -> None:
        alt = _make_alt(_make_plan(budget_total=0))
        scores = score_plan(alt, days=1)
        assert scores.price == 0.5

    def test_cheap_plan(self) -> None:
        alt = _make_alt(_make_plan(budget_total=100))
        scores = score_plan(alt, days=1)
        assert scores.price > 0.8

    def test_expensive_plan(self) -> None:
        alt = _make_alt(_make_plan(budget_total=50000))
        scores = score_plan(alt, days=1)
        assert scores.price < 0.1

    def test_high_rating(self) -> None:
        attractions = [_make_attraction(rating=5.0) for _ in range(3)]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.rating == 1.0

    def test_no_ratings(self) -> None:
        attractions = [_make_attraction(rating=None)]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.rating == 0.5

    def test_convenience_ideal(self) -> None:
        attractions = [_make_attraction() for _ in range(4)]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.convenience == 1.0

    def test_convenience_too_few(self) -> None:
        attractions = [_make_attraction()]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.convenience < 1.0

    def test_diversity_many_categories(self) -> None:
        kinds = ["museums", "parks", "churches", "restaurants", "gardens"]
        attractions = [_make_attraction(name=f"P{i}", kinds=k) for i, k in enumerate(kinds)]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.diversity > 0.3

    def test_diversity_single_category(self) -> None:
        attractions = [_make_attraction(kinds="museums") for _ in range(3)]
        alt = _make_alt(_make_plan(attractions=attractions))
        scores = score_plan(alt, days=1)
        assert scores.diversity < 0.3


# --- score_plans ---


class TestScorePlans:
    def test_scores_attached(self) -> None:
        alts = [
            _make_alt(_make_plan(budget_total=500), cost=500),
            _make_alt(_make_plan(budget_total=5000), cost=5000),
        ]
        alts[1].id = "plan_2"
        alts[1].focus = PlanFocus.CULTURE

        results = score_plans(alts)
        assert len(results) == 2
        assert results[0].scores is not None
        assert results[1].scores is not None
        assert results[0].scores is not None and results[0].scores.total > 0

    def test_preserves_other_fields(self) -> None:
        alt = _make_alt()
        results = score_plans([alt])
        assert results[0].id == "plan_1"
        assert results[0].focus == PlanFocus.BUDGET
