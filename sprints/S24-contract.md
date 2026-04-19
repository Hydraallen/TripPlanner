# Sprint S24: Multi-Plan Data Models + DB Schema

**Phase:** 6 (AI-Powered Multi-Plan Generation)
**Depends on:** S23
**Estimated complexity:** Medium

---

## Goal

Define the data structures and database schema to support generating, storing, and comparing multiple AI-generated travel plan alternatives.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/core/models.py` | Modify — add PlanFocus enum, PlanAlternative, PlanScores models |
| `src/tripplanner/db/models.py` | Modify — add generated_plans JSON column, selected_plan_id |

## Done Criteria

- [x] `PlanFocus` enum with 6 focuses (budget, culture, nature, food, romantic, adventure)
- [x] `PlanScores` model with 6 dimensions (price, rating, convenience, diversity, safety, popularity)
- [x] `PlanAlternative` model with id, focus, title, description, plan, scores, estimated_cost, source
- [x] DB schema supports storing multiple generated plans as JSON
- [x] `selected_plan_id` column tracks user's chosen plan
- [x] All models use Pydantic v2 with type annotations

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Data models | All 3 new types defined with correct fields | Missing models or fields |
| DB schema | generated_plans + selected_plan_id columns added | Schema migration incomplete |
| Type safety | Pydantic v2 validators, full type annotations | Untyped or loosely typed fields |
