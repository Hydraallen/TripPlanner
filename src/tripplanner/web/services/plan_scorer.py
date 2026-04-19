from __future__ import annotations

import logging

from tripplanner.core.models import PlanAlternative, PlanScores, TripPlan

logger = logging.getLogger(__name__)

# Scoring weights (6 dimensions)
_WEIGHTS = {
    "price": 0.25,
    "rating": 0.25,
    "convenience": 0.20,
    "diversity": 0.10,
    "safety": 0.10,
    "popularity": 0.10,
}

# Reference values for normalization
_MAX_REASONABLE_DAILY_COST = 2000.0  # CNY per person per day
_MIN_REASONABLE_DAILY_COST = 100.0

# Safety scores by category — daytime-friendly venues score higher
_SAFETY_SCORES: dict[str, float] = {
    "museum": 0.95,
    "gallery": 0.95,
    "arts_centre": 0.90,
    "library": 0.95,
    "theatre": 0.85,
    "cinema": 0.80,
    "park": 0.85,
    "garden": 0.90,
    "nature_reserve": 0.85,
    "viewpoint": 0.85,
    "attraction": 0.85,
    "monument": 0.80,
    "castle": 0.85,
    "church": 0.90,
    "cathedral": 0.90,
    "place_of_worship": 0.90,
    "zoo": 0.85,
    "restaurant": 0.75,
    "cafe": 0.80,
    "beach": 0.75,
    "mall": 0.85,
    "bar": 0.55,
    "pub": 0.55,
    "nightclub": 0.45,
    "fast_food": 0.70,
}


def score_plan(alt: PlanAlternative, days: int = 1) -> PlanScores:
    """Score a plan alternative on 6 dimensions.

    All scores are normalized to [0, 1]. Total is a weighted sum.
    """
    plan = alt.plan

    price_score = _score_price(plan, days)
    rating_score = _score_rating(plan)
    convenience_score = _score_convenience(plan)
    diversity_score = _score_diversity(plan)
    safety_score = _score_safety(plan)
    popularity_score = _score_popularity(plan, days)

    total = (
        _WEIGHTS["price"] * price_score
        + _WEIGHTS["rating"] * rating_score
        + _WEIGHTS["convenience"] * convenience_score
        + _WEIGHTS["diversity"] * diversity_score
        + _WEIGHTS["safety"] * safety_score
        + _WEIGHTS["popularity"] * popularity_score
    )

    return PlanScores(
        price=round(price_score, 3),
        rating=round(rating_score, 3),
        convenience=round(convenience_score, 3),
        diversity=round(diversity_score, 3),
        safety=round(safety_score, 3),
        popularity=round(popularity_score, 3),
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


def _score_safety(plan: TripPlan) -> float:
    """Score based on daytime-friendly venues vs nightlife.

    Museums, parks, galleries score high; bars, nightclubs score low.
    """
    scores: list[float] = []
    for day in plan.days:
        for a in day.attractions:
            best = 0.5  # default neutral
            if a.kinds:
                for kind in a.kinds.split(","):
                    kind = kind.strip().lower()
                    if kind in _SAFETY_SCORES:
                        best = max(best, _SAFETY_SCORES[kind])
            for cat in a.categories:
                cat = cat.lower()
                if cat in _SAFETY_SCORES:
                    best = max(best, _SAFETY_SCORES[cat])
            scores.append(best)

    if not scores:
        return 0.5

    return sum(scores) / len(scores)


def _score_popularity(plan: TripPlan, days: int) -> float:
    """Score based on attraction count and plan fullness.

    Plans with more attractions (up to a sweet spot) score higher,
    reflecting a richer, more engaging itinerary.
    """
    total_attractions = sum(len(day.attractions) for day in plan.days)
    if total_attractions == 0:
        return 0.0

    # Ideal: 3-5 attractions per day
    avg_per_day = total_attractions / max(days, 1)
    if avg_per_day >= 3:
        score = min(avg_per_day / 5.0, 1.0)
    else:
        score = avg_per_day / 3.0 * 0.6

    return round(score, 3)
