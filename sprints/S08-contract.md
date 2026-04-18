# Sprint S08: Budget Calculator + Pipeline State

**Phase:** 2 (Core Logic)
**Depends on:** S07
**Estimated complexity:** Medium

---

## Goal

Implement the budget calculator that computes trip costs algorithmically, and wire the full pipeline via `TripState`.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/logic/budget.py` | Create — budget calculation |
| `src/tripplanner/core/state.py` | Create — `TripState` pipeline |
| `tests/test_budget.py` | Create — budget unit tests |
| `tests/test_state.py` | Create — pipeline integration test |

## Budget Calculation

```python
def calculate_budget(plan: TripPlan, transport_mode: str) -> Budget
```

- Attractions: sum of `ticket_price`
- Hotels: sum of `estimated_cost_per_night` per day with hotel
- Meals: sum of `estimated_cost` for all meals
- Transport: estimated based on city radius and mode

### Default Heuristics (when API data missing)

| Item | Cost |
|------|------|
| Hotel per night | Budget ¥300, Mid ¥600, Luxury ¥1200 |
| Breakfast | ¥30 |
| Lunch | ¥60 |
| Dinner | ¥80 |
| Walking | ¥0 |
| Transit per trip | ¥10 |
| Driving per day | ¥50 |

## Pipeline State

```python
class TripState:
    city: str
    start_date: date
    end_date: date
    interests: list[str]
    transport_mode: str
    city_coords: tuple[float, float] | None
    raw_places: list[Attraction]
    scored_places: list[Attraction]
    optimized_clusters: list[list[Attraction]]
    itinerary: TripPlan | None
```

The `cli.py` plan command orchestrates: fetch → score → optimize → schedule → budget → result.

## Done Criteria

- [ ] `calculate_budget` returns `Budget` with all fields populated
- [ ] `Budget.total` equals sum of category totals
- [ ] Missing ticket prices → uses `0` (free attractions)
- [ ] Missing meal costs → uses default heuristics
- [ ] Transport cost varies by mode: walking < transit < driving
- [ ] `TripState` correctly passes data through pipeline stages
- [ ] Pipeline integration test: mock API → full pipeline → valid TripPlan
- [ ] Phase 2 milestone passes: `tripplanner plan --city Paris --days 3 --interests museums,food` generates valid itinerary internally

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Budget correctness | Total = sum of categories | Total ≠ sum |
| Defaults | Missing prices handled with heuristics | `None` in cost fields |
| Pipeline | End-to-end: API → score → optimize → schedule → budget | Pipeline breaks mid-way |
| Integration test | One test covering full pipeline | Only isolated unit tests |

## Phase 2 Milestone Checkpoint

After S08, the following must work:

```bash
tripplanner plan --city Paris --days 3 --interests museums,food
# Generates a 3-day itinerary with 8-12 places, routes, budget
# (Saved to DB in S09, for now just printed)
```
