# Sprint S26: SSE Progress + Multi-Plan API

**Phase:** 6 (AI-Powered Multi-Plan Generation)
**Depends on:** S25
**Estimated complexity:** High

---

## Goal

Implement Server-Sent Events (SSE) for real-time generation progress and expose multi-plan CRUD endpoints via the API layer.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/web/services/progress.py` | Create — SSE progress tracking |
| `src/tripplanner/web/routers/plans.py` | Create — POST /generate, GET /progress, GET /plans, POST /select |
| `src/tripplanner/web/services/planning.py` | Modify — background generation via asyncio.create_task |

## Done Criteria

- [x] SSE endpoint streams progress (0-30% POIs, 30-90% LLM, 90-100% scoring)
- [x] POST /generate creates trip draft synchronously, returns trip_id immediately
- [x] Background generation runs via `asyncio.create_task` with own DB session
- [x] GET /plans returns all generated alternatives for a trip
- [x] POST /select records user's chosen plan
- [x] API tests cover all endpoints

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| SSE progress | Real-time events with stage + percentage | Missing stages or broken stream |
| Async generation | trip_id returned immediately, generation non-blocking | Blocking request or missing trip_id |
| Endpoints | All 4 endpoints functional with correct status codes | Missing or broken endpoints |
