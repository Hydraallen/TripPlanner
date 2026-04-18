# Sprint S09: Database Layer

**Phase:** 3 (Persistence & Export)
**Depends on:** S08
**Estimated complexity:** Medium

---

## Goal

Implement SQLite persistence with SQLAlchemy ORM for trip CRUD and API response caching.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/db/models.py` | Create — SQLAlchemy ORM models |
| `src/tripplanner/db/crud.py` | Create — async CRUD operations |
| `src/tripplanner/db/cache.py` | Create — API response cache with TTL |
| `tests/test_db.py` | Create — in-memory SQLite tests |

## Schema

### `trips` table

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| city | TEXT | |
| start_date | DATE | |
| end_date | DATE | |
| interests | TEXT (JSON) | JSON-serialized list |
| transport_mode | TEXT | walking/transit/driving |
| plan_json | TEXT (nullable) | Full TripPlan as JSON |
| created_at | DATETIME | |

### `api_cache` table

| Column | Type | Notes |
|--------|------|-------|
| key | TEXT | Hash of URL + params |
| response | TEXT | JSON response body |
| expires_at | DATETIME | TTL-based expiry |

## Functions to Implement

```python
# db/crud.py
async def init_db(engine) -> None
async def save_trip(trip: Trip) -> str
async def get_trip(trip_id: str) -> Trip | None
async def list_trips(limit: int = 50) -> list[Trip]
async def delete_trip(trip_id: str) -> bool

# db/cache.py
async def get_cached(key: str) -> dict | None
async def set_cached(key: str, value: dict, ttl: int = 86400) -> None
async def clear_expired() -> int
```

## Done Criteria

- [ ] `init_db` creates both tables (idempotent)
- [ ] `save_trip` stores trip, returns UUID
- [ ] `get_trip` returns `Trip` model (not ORM object)
- [ ] `list_trips` returns list sorted by `created_at` descending
- [ ] `delete_trip` returns `True` if deleted, `False` if not found
- [ ] `get_cached` returns `None` for expired entries
- [ ] `set_cached` overwrites existing key
- [ ] `clear_expired` removes stale entries, returns count
- [ ] All tests use in-memory SQLite (`"sqlite+aiosqlite:///:memory:"`)
- [ ] Tests cover: CRUD cycle, cache hit/miss/expiry, duplicate key handling

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| CRUD cycle | Create → read → update → delete all work | Any CRUD operation fails |
| Type safety | CRUD functions return Pydantic models, not ORM objects | Raw SQLAlchemy objects leak |
| Cache TTL | Expired entries not returned | Stale data served |
| Test isolation | Tests use in-memory DB, no file I/O | Tests create actual files |
