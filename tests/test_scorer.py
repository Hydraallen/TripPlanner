from __future__ import annotations

from tripplanner.core.models import Attraction, Location
from tripplanner.logic.scorer import compute_scores, jaccard_similarity


def _attraction(
    name: str = "Place",
    kinds: str = "",
    rating: float | None = None,
    score: float = 0.0,
) -> Attraction:
    return Attraction(
        xid=f"x_{name}",
        name=name,
        location=Location(longitude=0, latitude=0),
        kinds=kinds,
        rating=rating,
        score=score,
    )


LOC = Location(longitude=0, latitude=0)


class TestJaccardSimilarity:
    def test_exact_match(self) -> None:
        assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_partial(self) -> None:
        result = jaccard_similarity({"a", "b"}, {"b", "c"})
        assert abs(result - 1 / 3) < 1e-6

    def test_no_overlap(self) -> None:
        assert jaccard_similarity({"a"}, {"b"}) == 0.0

    def test_both_empty(self) -> None:
        assert jaccard_similarity(set(), set()) == 0.0

    def test_one_empty(self) -> None:
        assert jaccard_similarity({"a"}, set()) == 0.0


class TestComputeScores:
    def test_empty_list(self) -> None:
        assert compute_scores([], ["museums"]) == []

    def test_matching_interests_score_higher(self) -> None:
        museum = _attraction("Museum", kinds="museums,culture", rating=4.0)
        park = _attraction("Park", kinds="parks,nature", rating=4.0)
        scored = compute_scores([museum, park], ["museums"])
        assert scored[0].name == "Museum"
        assert scored[0].score > scored[1].score

    def test_higher_rating_scores_higher(self) -> None:
        good = _attraction("Good", kinds="towers", rating=5.0)
        bad = _attraction("Bad", kinds="towers", rating=1.0)
        scored = compute_scores([good, bad], ["towers"])
        assert scored[0].name == "Good"

    def test_missing_rating_uses_mean(self) -> None:
        a = _attraction("A", kinds="museums", rating=4.0)
        b = _attraction("B", kinds="museums", rating=None)
        scored = compute_scores([a, b], ["museums"])
        # Both should have scores (b uses mean = 4.0)
        assert all(p.score > 0 for p in scored)

    def test_no_interests_neutral_category(self) -> None:
        place = _attraction("Place", kinds="towers", rating=4.0)
        scored = compute_scores([place], [])
        assert scored[0].score > 0

    def test_scores_in_range(self) -> None:
        places = [
            _attraction(f"P{i}", kinds="museums,parks", rating=float(i))
            for i in range(1, 6)
        ]
        scored = compute_scores(places, ["museums"])
        for p in scored:
            assert 0.0 <= p.score <= 1.0

    def test_sorted_descending(self) -> None:
        places = [
            _attraction("Low", kinds="other", rating=1.0),
            _attraction("High", kinds="museums", rating=5.0),
            _attraction("Mid", kinds="museums,other", rating=3.0),
        ]
        scored = compute_scores(places, ["museums"])
        scores = [p.score for p in scored]
        assert scores == sorted(scores, reverse=True)

    def test_single_place(self) -> None:
        place = _attraction("Solo", kinds="museums", rating=4.5)
        scored = compute_scores([place], ["museums"])
        assert len(scored) == 1
        assert scored[0].score > 0.5

    def test_returns_new_objects(self) -> None:
        place = _attraction("A", kinds="museums", rating=4.0, score=0.0)
        scored = compute_scores([place], ["museums"])
        assert scored[0] is not place
        assert place.score == 0.0  # original unchanged
