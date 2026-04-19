# Sprint S22: Docker Setup

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S21
**Estimated complexity:** Medium

---

## Goal

Containerize the full-stack application with Docker Compose, including backend (Python/FastAPI), frontend (Node/Vite build), PostgreSQL database, and nginx reverse proxy for production deployment.

## Files to Create/Modify

| File | Action |
|------|--------|
| `docker-compose.yml` | Create — orchestrate backend, frontend, PostgreSQL, nginx |
| `docker/backend.Dockerfile` | Create — Python backend with pip install |
| `docker/frontend.Dockerfile` | Create — Node build stage + nginx serve |
| `docker/nginx.conf` | Create — reverse proxy routing to backend and frontend |

## Done Criteria

- [x] `docker compose up --build` starts all services without errors
- [x] Backend container runs FastAPI with uvicorn, connects to PostgreSQL
- [x] Frontend container builds React app and serves static files via nginx
- [x] nginx proxies `/api/*` to backend and serves frontend for all other routes
- [x] PostgreSQL container persists data via named volume
- [x] All inter-service communication uses Docker network (no host networking)
- [x] Environment variables configurable via `.env` file at compose level

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Build | `docker compose up --build` succeeds for all services | Any service fails to build |
| End-to-end | Full trip planning workflow works through Docker | API or frontend unreachable |
| Database | PostgreSQL persists data across container restarts | Data lost on restart |
| Proxy | nginx correctly routes API and frontend requests | Wrong routing or 502 errors |
