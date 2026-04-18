# Sprint S15: Testing & Demo Prep

**Phase:** 4 (Polish & Testing)
**Depends on:** S14
**Estimated complexity:** Medium

---

## Goal

Achieve 80%+ test coverage, write missing tests, create demo script, final polish.

## Files to Create/Modify

| File | Action |
|------|--------|
| All test files | Review and fill gaps |
| `tests/conftest.py` | Modify — shared fixtures for all layers |
| `README.md` | Create — project documentation |

## Test Coverage Targets

| Module | Target Coverage |
|--------|----------------|
| `core/models.py` | 95% (validators are critical) |
| `core/config.py` | 90% |
| `api/opentripmap.py` | 85% (mocked HTTP) |
| `api/weather.py` | 85% (mocked HTTP) |
| `api/wikipedia.py` | 85% (mocked HTTP) |
| `logic/scorer.py` | 95% (pure functions, easy) |
| `logic/optimizer.py` | 90% (algorithm correctness) |
| `logic/scheduler.py` | 90% |
| `logic/budget.py` | 95% (pure functions) |
| `db/crud.py` | 90% |
| `db/cache.py` | 85% |
| `export/` | 85% |
| `cli.py` | 80% |
| **Overall** | **≥ 80%** |

## Demo Script Requirements

Create a demo that:
1. Plans a 3-day Tokyo trip with interests "museums,food,shrines"
2. Lists all trips
3. Shows the trip details
4. Exports to Markdown and HTML
5. Cleans up (deletes the trip)

This can be a shell script or a `Makefile` target.

## Done Criteria

- [ ] `pytest --cov=src --cov-report=term-missing` shows ≥ 80% overall
- [ ] No module below 70% coverage
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes (if configured)
- [ ] Demo script runs end-to-end without errors (with real API key)
- [ ] `README.md` includes: install instructions, usage examples, config guide
- [ ] `.env.example` is up-to-date with all required variables
- [ ] All sprint contracts reviewed and marked complete

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Coverage | ≥ 80% overall | Below 80% |
| Lint | `ruff` clean | Any violations |
| Demo | Full workflow works end-to-end | Any step breaks |
| Documentation | README covers install, config, usage | Missing sections |

## Final Acceptance Criteria (from Proposal)

- [ ] Can plan a 3-day trip for any major city
- [ ] Generates 8-12 places per trip
- [ ] Routes are geographically optimized (no excessive backtracking)
- [ ] Budget breakdown included
- [ ] Exports to Markdown (and JSON/HTML)
- [ ] Plans persisted in SQLite
- [ ] Full CRUD via CLI: plan, list, show, export, delete
- [ ] No AI/LLM used in final product
