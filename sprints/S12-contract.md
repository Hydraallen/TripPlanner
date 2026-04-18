# Sprint S12: Rich UX Polish

**Phase:** 4 (Polish & Testing)
**Depends on:** S11
**Estimated complexity:** Low-Medium

---

## Goal

Add Rich progress spinners, tables, color formatting, and markdown preview for a polished CLI experience.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/cli.py` | Modify — add Rich UX |
| `src/tripplanner/core/display.py` | Create — Rich helper functions |

## Features

1. **Progress spinner** during API calls: "Fetching Tokyo POIs..."
2. **Rich table** for `list` command with styled columns
3. **Markdown preview** for `show` command (Rich Markdown renderer)
4. **Budget summary** with colored totals (green for under budget, red for over)
5. **Day-by-day display** with attraction cards

## Done Criteria

- [ ] API calls show spinner with status messages
- [ ] `list` shows styled Rich table with alternating row colors
- [ ] `show` renders markdown-formatted itinerary in terminal
- [ ] Budget total is colored (green if < ¥5000, yellow if < ¥10000, red if >= ¥10000)
- [ ] Each day in `show` has a clear visual separator
- [ ] No raw dict/JSON printed to user (unless `--format json`)
- [ ] Tests verify Rich output contains expected strings (don't test formatting)

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Progress feedback | Spinner during API calls | Blank screen while waiting |
| Visual quality | Clear, readable tables and cards | Wall of text |
| Color usage | Meaningful colors (budget levels) | Random or no colors |
| No raw output | Users never see Python dicts | Raw data structure visible |
