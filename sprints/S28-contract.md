# Sprint S28: Enhanced AI Chat + Polish

**Phase:** 6 (AI-Powered Multi-Plan Generation)
**Depends on:** S27
**Estimated complexity:** Medium

---

## Goal

Enhance the AI chat panel with multi-plan context awareness, SSE streaming responses, and a "Compare with AI" quick-action button.

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/components/ChatPanel.tsx` | Modify — context-aware chat with SSE streaming |
| `frontend/src/pages/PlanPage.tsx` | Modify — "Compare with AI" button, floating chat overlay |

## Done Criteria

- [x] `ChatPanel` is a floating panel overlay for travel advisor chat
- [x] SSE streaming for real-time LLM responses
- [x] Multi-plan context (all alternatives) passed to LLM chat
- [x] "Compare with AI" button auto-generates comparison prompt from plan data
- [x] Chat panel integrates into PlanPage without breaking existing layout

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Chat streaming | SSE tokens render incrementally | Full response blocks until done |
| Multi-plan context | LLM receives all plan alternatives for informed responses | Chat unaware of generated plans |
| UX polish | Floating overlay, "Compare with AI" button functional | Intrusive layout or broken button |
