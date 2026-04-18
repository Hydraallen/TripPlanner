# Sprint S05: Preference Scorer

**Phase:** 2 (Core Logic)
**Depends on:** S04
**Estimated complexity:** Medium

---

## Goal

Implement the preference scoring algorithm that ranks attractions based on user interests, ratings, and popularity.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/logic/scorer.py` | Create — scoring functions |
| `tests/test_scorer.py` | Create — pure unit tests |

## Scoring Formula (from proposal)

```
score = (category_match * 0.4) + (rating_normalized * 0.3) + (popularity * 0.3)
```

- `category_match`: Jaccard similarity between user interests and place `kinds`
- `rating_normalized`: `rating / 5.0`. Missing → use dataset mean
- `popularity`: Normalize `otm:popularity` to [0, 1] across dataset

## Functions to Implement

```python
def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float
def normalize_ratings(places: list[Attraction]) -> list[Attraction]
def compute_scores(places: list[Attraction], interests: list[str]) -> list[Attraction]
```

## Done Criteria

- [ ] `jaccard_similarity({"a", "b"}, {"b", "c"})` returns `0.333...`
- [ ] `jaccard_similarity(set(), set())` returns `0.0` (not division by zero)
- [ ] `compute_scores` sets `Attraction.score` on each place (0.0 to 1.0)
- [ ] Places matching user interests rank higher than non-matching
- [ ] Missing ratings filled with dataset mean before normalization
- [ ] Empty interests list → all places get equal category_match (0.5 default)
- [ ] Results sorted by score descending
- [ ] All tests are pure unit tests (no mocks needed, pure functions)
- [ ] Tests cover: exact match, partial match, no match, empty inputs, single place

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Formula correctness | Manual calculation matches output | Score calculation off |
| Range | All scores in [0.0, 1.0] | Scores outside range |
| Sorting | Higher-interest places score higher | Random/unsorted output |
| Edge cases | Empty inputs handled without crash | `ZeroDivisionError` or similar |
| Purity | No I/O, no mocking needed in tests | Tests need mocks or network |
