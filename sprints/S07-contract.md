# Sprint S07: Day Scheduler

**Phase:** 2 (Core Logic)
**Depends on:** S06
**Estimated complexity:** High

---

## Goal

Split optimized place clusters into `DayPlan` objects with time slots, meal placeholders, and hotel assignments.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/logic/scheduler.py` | Create — scheduling functions |
| `tests/test_scheduler.py` | Create — pure unit tests |

## Scheduling Logic

### Time Slots
- Morning: 09:00 – 12:00 (3 hours)
- Afternoon: 13:00 – 17:00 (4 hours)
- Evening: 18:00 – 21:00 (3 hours)

### Rules
1. Each attraction gets `visit_duration` minutes (default 90, from config)
2. Travel time inserted between consecutive places using `estimate_travel_time()`
3. Lunch placeholder at ~12:00, dinner at ~18:00
4. Day must not exceed 10 hours of content (09:00 – 19:00)
5. If attraction doesn't fit in remaining day time, move to next day

## Functions to Implement

```python
def build_day_plan(
    day_number: int,
    date: date,
    attractions: list[Attraction],
    transport_mode: str = "walking",
) -> DayPlan

def build_itinerary(
    clustered_places: list[list[Attraction]],
    start_date: date,
    end_date: date,
    transport_mode: str = "walking",
) -> TripPlan
```

## Done Criteria

- [ ] `build_day_plan` creates a `DayPlan` with correct date and day_number
- [ ] Attractions assigned to time slots without overlap
- [ ] Travel time correctly inserted between places (from optimizer's haversine)
- [ ] Meal placeholders (lunch, dinner) inserted at correct times
- [ ] Day respects 10-hour maximum content window
- [ ] Overflow: if too many attractions for one day, extras get a note in `description`
- [ ] `build_itinerary` creates `TripPlan` with correct number of days
- [ ] `TripPlan.city`, `TripPlan.start_date`, `TripPlan.end_date` set correctly
- [ ] Empty cluster → day still created with no attractions (rest day)
- [ ] Tests cover: 4 attractions / 1 day, overflow case, empty cluster, multi-day

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Time feasibility | No overlapping time slots | Attractions scheduled simultaneously |
| Meal placement | Lunch ~12:00, dinner ~18:00 | Meals at wrong times or missing |
| Day limit | No day exceeds 10 hours | Day spans 12+ hours |
| Day count | TripPlan has exactly `num_days` DayPlans | Wrong day count |
| Overflow | Extras handled gracefully | Attractions silently dropped |
