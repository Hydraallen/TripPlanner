# Sprint S10: Multi-Format Export

**Phase:** 3 (Persistence & Export)
**Depends on:** S09
**Estimated complexity:** Medium

---

## Goal

Implement Markdown, JSON, and HTML export using Jinja2 templates and Pydantic serialization.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/export/markdown.py` | Create — Markdown export |
| `src/tripplanner/export/json_export.py` | Create — JSON export |
| `src/tripplanner/export/html_gen.py` | Create — HTML export |
| `src/tripplanner/export/templates/itinerary.md.j2` | Create — Markdown template |
| `src/tripplanner/export/templates/itinerary.html.j2` | Create — HTML template |
| `src/tripplanner/export/templates/styles.css` | Create — minimal CSS |
| `tests/test_export.py` | Create — export format tests |

## Export Functions

```python
# export/markdown.py
def export_markdown(plan: TripPlan) -> str

# export/json_export.py
def export_json(plan: TripPlan) -> str

# export/html_gen.py
def export_html(plan: TripPlan) -> str
```

## Markdown Template Requirements

- City name as H1
- Date range
- Budget table (if budget exists)
- Per-day: H2 with day number and date
- Attraction list with name, duration, address, rating
- Meal list with type, name, cost

## HTML Template Requirements

- Same content as Markdown but in styled HTML
- Embedded CSS (no external dependencies)
- Print-friendly (looks good when printed to PDF)
- Table-based budget display

## Done Criteria

- [ ] `export_markdown` produces valid Markdown (parses without error)
- [ ] `export_json` produces valid JSON (round-trips through `json.loads`)
- [ ] `export_html` produces valid HTML5 (opens in browser without errors)
- [ ] Markdown includes: city name, dates, budget table, day sections, attractions, meals
- [ ] JSON uses `model_dump_json(exclude_none=True)` format
- [ ] HTML has embedded CSS, looks clean in browser
- [ ] All three formats handle: empty budget, empty meals, missing ratings
- [ ] Tests verify output contains expected sections (substring assertions)
- [ ] Tests use snapshot-style comparison for Markdown and HTML

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Format validity | All 3 formats parse/validate correctly | Invalid Markdown/JSON/HTML |
| Content completeness | City, dates, budget, days, attractions all present | Missing sections |
| Graceful handling | Missing data → "N/A" or omitted, not crash | KeyError on None |
| Template rendering | Jinja2 renders without `UndefinedError` | Template errors |
