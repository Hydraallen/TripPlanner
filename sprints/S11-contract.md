# Sprint S11: Full CLI Commands

**Phase:** 3 (Persistence & Export)
**Depends on:** S10
**Estimated complexity:** Medium

---

## Goal

Implement all CLI subcommands: `plan`, `list`, `show`, `export`, `delete`. Wire full workflow.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/cli.py` | Modify — add all subcommands |
| `tests/test_cli.py` | Modify — test all commands |

## Commands

```
tripplanner plan    --city <city> [--dates <start> <end>] [--days <n>] [--interests <tags>] [--transport <mode>] [--export <fmt>] [--output <path>]
tripplanner list    [--format table|json]
tripplanner show    <trip-id>
tripplanner export  <trip-id> --format markdown|json|html [--output <path>]
tripplanner delete  <trip-id>
```

## Done Criteria

- [ ] `plan` generates itinerary, saves to DB, prints summary
- [ ] `plan --export markdown` also exports to stdout
- [ ] `plan --export markdown --output trip.md` writes to file
- [ ] `list` shows Rich table: ID, City, Dates, Created
- [ ] `list --format json` outputs JSON array
- [ ] `show <id>` displays full itinerary with Rich formatting
- [ ] `show <bad-id>` shows "Trip not found" error
- [ ] `export <id> --format html --output trip.html` writes HTML file
- [ ] `delete <id>` asks confirmation, then deletes
- [ ] `delete <id> --force` deletes without confirmation
- [ ] Phase 3 milestone passes: full plan → save → list → export → delete workflow

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Full workflow | plan → list → show → export → delete all work | Any command broken |
| Error UX | "Trip not found" for bad IDs, not tracebacks | Python exception shown |
- [ ] Rich formatting: tables, colors, progress spinner during API calls
- [ ] Confirmation prompts on destructive operations

## Phase 3 Milestone Checkpoint

After S11, the following must work:

```bash
tripplanner plan --city Tokyo --dates 2026-04-10 2026-04-13 --interests museums,food --export markdown
tripplanner list
tripplanner show <id>
tripplanner export <id> --format html --output tokyo.html
tripplanner delete <id>
```
