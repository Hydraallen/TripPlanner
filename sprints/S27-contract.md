# Sprint S27: Frontend Plan Comparison UI

**Phase:** 6 (AI-Powered Multi-Plan Generation)
**Depends on:** S26
**Estimated complexity:** Medium

---

## Goal

Build the frontend plan comparison view with real-time SSE progress tracking and side-by-side plan cards showing scores, costs, and descriptions.

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/components/PlanComparison.tsx` | Create — side-by-side plan cards with scores and costs |
| `frontend/src/pages/PlanPage.tsx` | Modify — trip form + progress bar + plan comparison |
| `frontend/src/api/client.ts` | Modify — typed interfaces for plan alternatives, progress, SSE |

## Done Criteria

- [x] `PlanComparison` displays plan cards side-by-side with scores and estimated costs
- [x] Real-time progress bar reflects SSE stages (fetching POIs, generating plans, scoring)
- [x] `PlanPage` integrates trip form, progress display, and plan comparison
- [x] API client has typed interfaces for `PlanAlternative`, `GenerationProgress`, SSE endpoint
- [x] Users can select a plan from the comparison view

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Plan comparison | Cards render with scores, costs, descriptions | Missing data or broken layout |
| Progress tracking | SSE events update progress bar in real time | Static or missing progress |
| Type safety | All API interfaces typed in client.ts | Untyped or `any` types |
