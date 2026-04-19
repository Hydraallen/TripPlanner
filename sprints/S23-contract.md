# Sprint S23: End-to-End Testing + Documentation

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S22
**Estimated complexity:** Medium

---

## Goal

Comprehensive API integration tests, update documentation for the full-stack application, and verify no regressions in existing CLI functionality.

## Files to Create/Modify

| File | Action |
|------|--------|
| `tests/test_web_api.py` | Extend — plan generation, LLM, chat tests |
| `README.md` | Create — full-stack documentation (CLI + Web + Docker) |
| `.env.example` | Modify — add all new environment variables |
| `sprints/00-task-tracker.md` | Update — mark S23 done |

## Done Criteria

- [ ] `tests/test_web_api.py` covers all API endpoints (CRUD, export, plan generate, LLM generate, chat)
- [ ] Tests mock external APIs (OpenTripMap, Amap, GLM-5.1)
- [ ] LLM fallback path tested (LLM fails → algorithmic pipeline)
- [ ] All 226+ tests pass with no regressions
- [ ] `README.md` covers: CLI usage, Web usage, Docker quickstart, env config
- [ ] `.env.example` lists all environment variables
- [ ] Sprint tracker updated with final status

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Test coverage | All API endpoints tested, 226+ tests pass | Missing endpoint coverage |
| Documentation | README covers CLI + Web + Docker | Missing sections |
| Regressions | All existing tests still pass | Any test broken |
| Sprint tracker | S23 marked Done | Not updated |
