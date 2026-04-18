# Sprint S14: Wikipedia Enrichment (Stretch)

**Phase:** 4 (Polish & Testing)
**Depends on:** S13
**Estimated complexity:** Low-Medium

---

## Goal

Enrich attraction descriptions using the Wikipedia REST API. Use as fallback when OpenTripMap description is missing.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/api/wikipedia.py` | Create — Wikipedia client |
| `tests/test_api.py` | Modify — add Wikipedia tests |

## Wikipedia REST API

- Endpoint: `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`
- Returns: `extract` field with plain-text summary
- Free, no API key required

## Functions to Implement

```python
# api/wikipedia.py
class WikipediaClient:
    async def get_summary(title: str) -> str | None
    async def enrich_attractions(places: list[Attraction]) -> list[Attraction]
```

## Logic

1. For each attraction with `description is None`:
   - Try `get_summary(attraction.name)`
   - If found, set `description = summary`
2. If Wikipedia also fails → leave description as `None`
3. Rate limit: 200ms delay between requests (respectful crawling)

## Done Criteria

- [ ] `get_summary("Tokyo Tower")` returns a non-empty string (mocked)
- [ ] `get_summary("NonExistentPlace12345")` returns `None`
- [ ] `enrich_attractions` only fills descriptions that are `None`
- [ ] Existing descriptions are NOT overwritten
- [ ] Rate limiting: measurable delay between requests
- [ ] API failure → returns attractions unchanged
- [ ] Tests mock Wikipedia API — no real HTTP calls

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Enrichment | Missing descriptions filled | No descriptions populated |
| No overwrite | Existing descriptions preserved | All descriptions replaced |
| Fallback | Wikipedia fails → graceful no-op | Crash on Wikipedia failure |
| Rate limiting | Requests spaced ≥200ms | Burst requests |
