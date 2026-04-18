from __future__ import annotations

from tripplanner.core.models import Attraction


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _parse_kinds(kinds: str) -> set[str]:
    """Parse comma-separated kinds string into a set of lowercase tokens."""
    if not kinds:
        return set()
    return {k.strip().lower() for k in kinds.split(",") if k.strip()}


def _compute_category_match(place_kinds: str, interests: list[str]) -> float:
    """Compute category match score between place kinds and user interests."""
    if not interests:
        return 0.5  # neutral score when no interests specified
    kind_set = _parse_kinds(place_kinds)
    interest_set = {i.lower() for i in interests}
    return jaccard_similarity(kind_set, interest_set)


def _mean_rating(places: list[Attraction]) -> float:
    """Compute mean rating across places that have ratings."""
    rated = [p.rating for p in places if p.rating is not None]
    if not rated:
        return 3.0  # default mid-range
    return sum(rated) / len(rated)


def compute_scores(
    places: list[Attraction],
    interests: list[str],
    w_category: float = 0.4,
    w_rating: float = 0.3,
    w_popularity: float = 0.3,
) -> list[Attraction]:
    """Score and rank attractions by user interests, rating, and popularity.

    Formula: score = (category_match * 0.4) + (rating_norm * 0.3) + (popularity * 0.3)

    Returns a new list sorted by score descending.
    """
    if not places:
        return []

    mean = _mean_rating(places)
    max_score_raw = max((p.score for p in places), default=1.0) or 1.0

    scored: list[Attraction] = []
    for place in places:
        cat_match = _compute_category_match(place.kinds, interests)

        rating_val = place.rating if place.rating is not None else mean
        rating_norm = rating_val / 5.0

        popularity = min(place.score / max_score_raw, 1.0) if max_score_raw > 0 else 0.5

        final_score = cat_match * w_category + rating_norm * w_rating + popularity * w_popularity
        final_score = min(max(final_score, 0.0), 1.0)

        scored.append(place.model_copy(update={"score": round(final_score, 4)}))

    scored.sort(key=lambda p: p.score, reverse=True)
    return scored
