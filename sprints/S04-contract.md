# Sprint S04: CLI Skeleton (plan command)

**Phase:** 1 (Foundation)
**Depends on:** S03
**Estimated complexity:** Medium

---

## Goal

Wire the `plan` CLI command so that `tripplanner plan --city Tokyo --dry-run` fetches POIs and prints structured results via Rich.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/cli.py` | Create — Click group + `plan` command |
| `tests/test_cli.py` | Create — CLI runner tests |

## CLI Interface

```
tripplanner plan --city <city> [--dates <start> <end>] [--days <n>] [--interests <tags>] [--transport <mode>] [--dry-run] [--export <fmt>] [--output <path>]
```

- `--city` (required): Target city name
- `--dates`: Start and end dates (default: today → today+3)
- `--days`: Number of days (default: 3, ignored if --dates given)
- `--interests`: Comma-separated tags (default: "interesting_places")
- `--transport`: walking | transit | driving (default: walking)
- `--dry-run`: Fetch and display POIs without generating full itinerary
- `--export`: markdown | json | html (future, ignored for now)
- `--output`: Output file path (future, ignored for now)

## Done Criteria

- [ ] `tripplanner plan --city Tokyo --dry-run` fetches POIs and prints a Rich table
- [ ] `tripplanner plan` without `--city` shows error: "Missing option '--city'"
- [ ] `--dry-run` shows: city name, coordinates, POI count, top 10 POIs in table
- [ ] Rich table columns: Name, Category, Rating, Distance from center
- [ ] Invalid date format → clear error message, not traceback
- [ ] `--interests museums,food` correctly splits to `["museums", "food"]`
- [ ] Tests use `click.testing.CliRunner` with mocked API client
- [ ] Tests cover: dry-run success, missing city, invalid dates
- [ ] Phase 1 milestone passes: `tripplanner plan --city Tokyo --dry-run` works end-to-end

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Help text | `tripplanner plan --help` shows all options | Missing options or crash |
| Dry-run output | Rich table with POI data visible | Only raw dict or empty output |
| Error UX | Missing --city shows user-friendly error | Python traceback shown |
| Test coverage | CLI tests with mocked API | No CLI tests |

## Phase 1 Milestone Checkpoint

After S04, the following must work:

```bash
tripplanner plan --city Tokyo --dry-run
# Output: Rich table showing Tokyo POIs from OpenTripMap
```
