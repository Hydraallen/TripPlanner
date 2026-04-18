# Sprint S03: OpenTripMap API Client

**Phase:** 1 (Foundation)
**Depends on:** S02
**Estimated complexity:** High

---

## Goal

Build the async API client for OpenTripMap that fetches city coordinates, searches POIs, and enriches them with details. All responses cached to respect 10k/day rate limit.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/api/opentripmap.py` | Create — `OpenTripMapClient` class |
| `tests/test_api.py` | Create — mocked HTTP tests |

## API Endpoints to Implement

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `geoname(city)` | `/0.1/en/places/geoname` | City → (lat, lon) |
| `search_places(lat, lon, radius, kinds)` | `/0.1/en/places/radius` | Search POIs in radius |
| `place_detail(xid)` | `/0.1/en/places/xid/{xid}` | Full place details |

## Key Methods

```python
class OpenTripMapClient:
    async def geoname(self, city: str) -> tuple[float, float]
    async def search_places(self, lat, lon, radius, kinds=None) -> list[Attraction]
    async def place_detail(self, xid: str) -> Attraction | None
    async def search_city(self, city, interests, radius) -> list[Attraction]
```

## Done Criteria

- [ ] `geoname("Tokyo")` returns `(35.6762, 139.6503)` (mocked)
- [ ] `search_places` returns list of `Attraction` models (not raw dicts)
- [ ] `place_detail` returns `None` gracefully on 404
- [ ] `search_city` chains: geocode → search → detail enrichment
- [ ] API key missing → logs warning, returns empty list (no crash)
- [ ] All HTTP errors caught → graceful degradation (empty results + warning log)
- [ ] Rate limiting: built-in respect for 10k/day (log remaining count from headers)
- [ ] Tests use `respx` to mock httpx — no real HTTP calls in tests
- [ ] Tests cover: success, 404, timeout, empty results, malformed response
- [ ] `ruff check` passes

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Type safety | All public methods return Pydantic models, not dicts | Raw dict returned |
| Error handling | HTTP errors → empty list + log, no uncaught exceptions | Crash on 404/timeout |
| API key missing | Graceful warning + empty results | `ValidationError` or crash |
| Test isolation | All tests use mocked HTTP | Tests make real API calls |
| Search pipeline | `search_city` correctly chains 3 API calls | Missing geocode or detail step |

## Notes

- Use `httpx.AsyncClient` as a class attribute, initialized once.
- Ch13 pattern: singleton service wrapping external API with shared instance.
- Ch14 pattern: return empty results on failure, never raise to caller.
- Caching will be added in S09 (Database Layer) — for now, just log cache misses.
