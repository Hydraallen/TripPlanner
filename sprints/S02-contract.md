# Sprint S02: Pydantic Data Models

**Phase:** 1 (Foundation)
**Depends on:** S01
**Estimated complexity:** Medium

---

## Goal

Implement all Pydantic data models in `core/models.py` with validators, following the bottom-up design pattern from chapter 13.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/core/models.py` | Create — all Pydantic models |
| `tests/test_models.py` | Create — validator and constraint tests |

## Models to Implement

1. **Location** — lat/lon with numeric coercion validator
2. **Attraction** — POI with rating clamping, kinds parsing
3. **Meal** — dining with type/cost
4. **Hotel** — accommodation with price range
5. **Budget** — cost breakdown (attractions, hotels, meals, transport, total)
6. **WeatherInfo** — forecast with `is_rainy` property, WMO code description
7. **DayPlan** — single day (attractions, meals, hotel, date, transport)
8. **TripPlan** — full plan (city, dates, days, weather, budget, suggestions)
9. **Trip** — persisted record (id, city, dates, interests, plan, created_at)

## Done Criteria

- [ ] All 9 models instantiate with valid data
- [ ] `Location.coerce_numeric` handles: `float`, `int`, `"45.5"`, `"45,5"`
- [ ] `Attraction.clamp_rating` handles: `None`, `4.5`, `6.0` → clamped to 5.0, `-1.0` → clamped to 0.0
- [ ] `WeatherInfo.is_rainy` returns `True` when `precipitation_prob > 50`
- [ ] `WeatherInfo.description` maps WMO code 0 → "Clear", 61 → "Rain"
- [ ] `Budget.total` is computed as sum of category totals
- [ ] `DayPlan.day_number` rejects `0` or negative (validation error)
- [ ] `Attraction.rating` accepts `None` (optional field)
- [ ] All models serialize via `.model_dump_json()` and round-trip through JSON
- [ ] `ruff check` and `mypy` pass
- [ ] Tests cover: happy path, edge cases for each validator, serialization round-trip

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Model count | All 9 models defined | Missing any model |
| Validators | `coerce_numeric`, `clamp_rating` work with edge cases | Validator crashes on valid input |
| Round-trip | `Model.model_validate(m.model_dump())` succeeds for all models | Serialization error |
| Constraints | `day_number=0` raises `ValidationError` | Invalid value accepted |
| Test coverage | Models tests exist with edge cases | No tests or only happy path |

## Reference

See `plan.md` §1.3 for full model definitions with field types and validators.
