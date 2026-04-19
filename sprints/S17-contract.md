# Sprint S17: Smart Routing + Amap + Plan API

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S16
**Estimated complexity:** High

---

## Goal

Implement smart region detection that routes Chinese-destination queries to the Amap API and international queries to the free Overpass/OSM API. Build the multi-plan generation pipeline with background task execution and SSE progress tracking.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/web/services/region.py` | Create — auto-detect Chinese destinations, route to correct API |
| `src/tripplanner/web/services/planning.py` | Create — orchestrate POI fetching, plan generation, scoring |
| `src/tripplanner/web/services/progress.py` | Create — SSE progress tracker for background tasks |
| `src/tripplanner/web/routers/plans.py` | Create — POST /generate, GET /progress (SSE), GET /plans, POST /select |

## Done Criteria

- [x] `region.py` detects Chinese characters or known Chinese city names and routes to Amap
- [x] International destinations use Overpass/OSM (no API key required)
- [x] `POST /api/plans/generate` creates a trip draft synchronously and returns `trip_id` immediately
- [x] Background task runs LLM plan generation with its own DB session via `asyncio.create_task`
- [x] `GET /api/plans/{id}/progress` streams SSE events (0-30% POI fetch, 30-90% LLM generate, 90-100% score)
- [x] `GET /api/plans?trip_id=X` returns all plans for a trip
- [x] `POST /api/plans/{id}/select` marks a plan as selected
- [x] AMAP_API_KEY is only required for Chinese destinations; international works with zero API keys

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Smart routing | Chinese city -> Amap, other -> Overpass | Wrong API chosen or hardcoded |
| Async background | generate returns trip_id immediately, plans populate later | Blocking generation |
| SSE progress | Client receives streaming progress updates | No progress or polling required |
| Plan selection | Can generate, list, and select plans end-to-end | Any step fails |
