# Sprint S01: Project Scaffolding + Config

**Phase:** 1 (Foundation)
**Depends on:** None
**Estimated complexity:** Low

---

## Goal

Set up the Python project structure with all necessary configuration so that subsequent sprints can start coding immediately.

## Files to Create

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, ruff config, entry point `tripplanner` |
| `.env.example` | Template for required environment variables |
| `src/tripplanner/__init__.py` | Package init with version |
| `src/tripplanner/core/__init__.py` | Core subpackage |
| `src/tripplanner/api/__init__.py` | API subpackage |
| `src/tripplanner/logic/__init__.py` | Logic subpackage |
| `src/tripplanner/db/__init__.py` | DB subpackage |
| `src/tripplanner/export/__init__.py` | Export subpackage |
| `src/tripplanner/export/templates/` | Jinja2 template directory |
| `tests/__init__.py` | Test package |
| `tests/conftest.py` | Shared fixtures |
| `src/tripplanner/core/config.py` | `Settings(BaseSettings)` class |

## Dependencies (pyproject.toml)

```
click>=8.1
httpx>=0.27
sqlalchemy[asyncio]>=2.0
aiosqlite>=0.20
pydantic>=2.0
pydantic-settings>=2.0
jinja2>=3.1
rich>=13.0
```

Dev deps: `pytest`, `pytest-asyncio`, `respx`, `ruff`, `mypy`.

## Done Criteria

- [ ] `pip install -e .` succeeds without errors
- [ ] `tripplanner --help` prints a Click help message (group with no subcommands yet)
- [ ] `Settings()` loads defaults without `.env` file (no crash on missing env)
- [ ] `ruff check src/` passes with zero violations
- [ ] `pytest` runs (0 tests collected is fine)
- [ ] `.env.example` lists `OPENTRIPMAP_API_KEY` as the only required secret
- [ ] All `__init__.py` files are empty (or contain only version in root)

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Install works | `pip install -e .` succeeds | Any install error |
| CLI responds | `tripplanner --help` outputs help text | Command not found or crash |
| Config safe | `Settings()` works without .env | `ValidationError` on missing env |
| Lint clean | `ruff check` = 0 violations | Any lint error |
| Structure correct | All directories exist under `src/tripplanner/` | Missing subpackage |

## Notes

- Use `src` layout to avoid import ambiguity.
- `pydantic-settings` reads `.env` automatically via `SettingsConfigDict`.
- `OPENTRIPMAP_API_KEY` default to empty string — validation happens at API call time, not config time.
