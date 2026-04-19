# Sprint S16: FastAPI Scaffolding + Trip CRUD

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S15
**Estimated complexity:** Medium

---

## Goal

Set up the FastAPI application factory with CORS, lifespan management, and router registration. Implement full CRUD REST endpoints for trips so the web frontend can list, create, view, delete, and export trips.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/web/app.py` | Create — FastAPI factory with CORS, routers, lifespan |
| `src/tripplanner/web/deps.py` | Create — shared dependency injection (DB session, settings) |
| `src/tripplanner/web/routers/trips.py` | Create — CRUD endpoints: list, create, get, delete, export |

## Done Criteria

- [x] `web/app.py` creates a FastAPI app with CORS middleware and lifespan handler
- [x] Trip router exposes: `GET /api/trips`, `POST /api/trips`, `GET /api/trips/{id}`, `DELETE /api/trips/{id}`, `GET /api/trips/{id}/export`
- [x] All endpoints use async SQLAlchemy sessions via dependency injection
- [x] Pydantic response models serialize trip data correctly
- [x] Export endpoint supports markdown, JSON, and HTML formats
- [x] `tripplanner web --dev` starts the server with auto-reload on port 8000
- [x] Existing CLI functionality unaffected by new web module

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Server starts | `tripplanner web --dev` serves on :8000 | Server fails to start |
| CRUD endpoints | All 5 trip endpoints return correct status codes | Missing or broken endpoints |
| Async DB | All DB operations use async sessions | Synchronous DB calls |
| CLI regression | `tripplanner plan --city "Paris"` still works | CLI broken by web changes |
