# Sprint S25: AI Plan Generator + Scorer

**Phase:** 6 (AI-Powered Multi-Plan Generation)
**Depends on:** S24
**Estimated complexity:** High

---

## Goal

Build the LLM-powered multi-plan generator and 6-dimensional scorer. Generate up to 6 focused plans per trip with LLM-first strategy and algorithmic fallback.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/web/services/plan_generator.py` | Create — multi-focus plan generation with LLM + fallback |
| `src/tripplanner/web/services/plan_scorer.py` | Create — 6-dimensional weighted scoring |
| `src/tripplanner/web/services/llm.py` | Modify — knowledge-first prompts, cross-plan dedup |

## Done Criteria

- [x] `PlanGenerator` generates up to 6 plans (one per focus)
- [x] LLM-first per focus, algorithmic pipeline as fallback
- [x] Knowledge-first prompt: iconic attractions from training data, POI data for coordinates only
- [x] Cross-plan deduplication: prompt-level + post-processing filter
- [x] `PlanScorer` scores on price (25%), rating (25%), convenience (20%), diversity (10%), safety (10%), popularity (10%)
- [x] Unit tests for scorer with mock data

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Plan generation | 3-6 distinct plans per trip, LLM + fallback working | Fewer than 3 plans or no fallback |
| Scoring | 6 dimensions with correct weights, total = 100% | Missing dimensions or wrong weights |
| Deduplication | No duplicate POIs across plans | Duplicate attractions in output |
