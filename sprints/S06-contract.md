# Sprint S06: Route Optimizer

**Phase:** 2 (Core Logic)
**Depends on:** S05
**Estimated complexity:** High

---

## Goal

Implement greedy nearest-neighbor route optimization using Haversine distance. Group attractions into day-sized clusters that minimize travel distance.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/logic/optimizer.py` | Create — optimization functions |
| `tests/test_optimizer.py` | Create — pure unit tests |

## Algorithms

### Haversine Distance

```python
def haversine(lat1, lon1, lat2, lon2) -> float  # km
```

### Travel Time Estimation

```python
def estimate_travel_time(distance_km, mode="walking") -> int  # minutes
```

### Greedy Nearest-Neighbor

1. Start from city center
2. Pick highest-scored unvisited place as anchor
3. Greedily add nearest unvisited place within threshold
4. When day has ~4 places, start new cluster
5. Repeat until all top-scored places assigned

```python
def optimize_routes(
    places: list[Attraction],
    center: tuple[float, float],
    num_days: int,
    places_per_day: int = 4,
    transport_mode: str = "walking",
) -> list[list[Attraction]]
```

## Done Criteria

- [ ] `haversine(0, 0, 0, 1)` returns ~111.19 km (equatorial degree)
- [ ] `estimate_travel_time(5.0, "walking")` returns `60` minutes
- [ ] `optimize_routes` returns exactly `num_days` clusters
- [ ] Each cluster has ≤ `places_per_day` attractions
- [ ] Within each cluster, consecutive places are closer than random (no excessive backtracking)
- [ ] Single place input → returns 1 cluster with 1 place
- [ ] Empty places → returns `num_days` empty clusters
- [ ] All functions are pure (no I/O, no side effects)
- [ ] Tests include: 10 places / 3 days, 1 place, 0 places, all same location

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Haversine accuracy | Within 1% of known distances | Grossly incorrect distances |
| Cluster count | Exactly `num_days` clusters | Wrong number of clusters |
| No backtracking | Consecutive places closer than average | Random zigzag patterns |
| Edge cases | Empty/single input handled | Crash on edge input |
| Purity | No I/O or mocking needed | Tests require external resources |

## Notes

- This is the most algorithmically complex sprint. Consider a quick whiteboard of the greedy algorithm before coding.
- Haversine is an approximation — no need for routing APIs ( proposal constraint).
- The optimizer only clusters — it does NOT assign dates or time slots (that's S07).
