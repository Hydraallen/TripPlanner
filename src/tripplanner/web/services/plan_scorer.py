from __future__ import annotations

import logging

from tripplanner.core.models import PlanAlternative, PlanScores, TripPlan

logger = logging.getLogger(__name__)

# Scoring weights
_WEIGHTS = {
    "price": 0.3,
    "rating": 0.3,
    "convenience": 0.2,
    "diversity": 0.2,
}

# Reference values for normalization
_MAX_REASONABLE_DAILY_COST = 2000.0  # CNY per person per day
_MIN_REASONABLE_DAILY_COST = 100.0


def score_plan(alt: PlanAlternative, days: int = 1) -> PlanScores:
    """Score a plan alternative on 4 dimensions.

    All scores are normalized to [0, 1]. Total is a weighted sum.
    """
    plan = alt.plan

    price_score = _score_price(plan, days)
    rating_score = _score_rating(plan)
    convenience_score = _score_convenience(plan)
    diversity_score = _score_diversity(plan)

    total = (
        _WEIGHTS["price"] * price_score
        + _WEIGHTS["rating"] * rating_score
        + _WEIGHTS["convenience"] * convenience_score
        + _WEIGHTS["diversity"] * diversity_score
    )

    return PlanScores(
        price=round(price_score, 3),
        rating=round(rating_score, 3),
        convenience=round(convenience_score, 3),
        diversity=round(diversity_score, 3),
        total=round(min(total, 1.0), 3),
    )


def score_plans(alternatives: list[PlanAlternative]) -> list[PlanAlternative]:
    """Score and return plan alternatives with scores attached.

    Returns a new list with scores populated.
    """
    results: list[PlanAlternative] = []
    for alt in alternatives:
        days = len(alt.plan.days) or 1
        scores = score_plan(alt, days)
        results.append(alt.model_copy(update={"scores": scores}))
    return results


def _score_price(plan: TripPlan, days: int) -> float:
    """Score based on cost efficiency. Lower cost = higher score."""
    if not plan.budget or plan.budget.total <= 0:
        return 0.5  # neutral when no budget data

    daily_cost = plan.budget.total / max(days, 1)

    if daily_cost <= _MIN_REASONABLE_DAILY_COST:
        return 1.0
    if daily_cost >= _MAX_REASONABLE_DAILY_COST:
        return 0.0

    normalized = (daily_cost - _MIN_REASONABLE_DAILY_COST) / (
        _MAX_REASONABLE_DAILY_COST - _MIN_REASONABLE_DAILY_COST
    )
    return 1.0 - normalized


def _score_rating(plan: TripPlan) -> float:
    """Score based on average attraction ratings."""
    ratings: list[float] = []
    for day in plan.days:
        for a in day.attractions:
            if a.rating is not None:
                ratings.append(a.rating)

    if not ratings:
        return 0.5

    avg = sum(ratings) / len(ratings)
    return min(avg / 5.0, 1.0)


def _score_convenience(plan: TripPlan) -> float:
    """Score based on route efficiency (fewer long gaps = better).

    Measures: reasonable attractions per day and travel efficiency.
    """
    if not plan.days:
        return 0.0

    day_scores: list[float] = []
    for day in plan.days:
        n_attractions = len(day.attractions)
        # Ideal: 3-5 attractions per day
        if 3 <= n_attractions <= 5:
            day_score = 1.0
        elif n_attractions < 3:
            day_score = n_attractions / 3.0
        else:
            day_score = max(0.5, 1.0 - (n_attractions - 5) * 0.1)

        day_scores.append(day_score)

    return sum(day_scores) / len(day_scores)


def _score_diversity(plan: TripPlan) -> float:
    """Score based on variety of attraction categories and meal types."""
    categories: set[str] = set()
    meal_types: set[str] = set()

    for day in plan.days:
        for a in day.attractions:
            if a.kinds:
                for kind in a.kinds.split(","):
                    kind = kind.strip()
                    if kind:
                        categories.add(kind)
            for cat in a.categories:
                if cat:
                    categories.add(cat)

        for m in day.meals:
            if m.type:
                meal_types.add(m.type)

    # Diversity based on unique categories
    cat_score = min(len(categories) / 10.0, 1.0) if categories else 0.0
    meal_score = min(len(meal_types) / 4.0, 1.0) if meal_types else 0.5

    return (cat_score * 0.7 + meal_score * 0.3)
