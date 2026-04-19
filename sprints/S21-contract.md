# Sprint S21: Chat Panel + Polish

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S20
**Estimated complexity:** Medium

---

## Goal

Implement an AI travel advisor chat panel with streaming responses, context-aware conversations that reference plan data, and a side-by-side plan comparison component with a "Compare with AI" feature.

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/components/ChatPanel.tsx` | Create — AI travel advisor with SSE streaming |
| `frontend/src/components/PlanComparison.tsx` | Create — side-by-side plan comparison with scores |

## Done Criteria

- [x] ChatPanel connects to `GET /api/chat/stream` for real-time streaming responses
- [x] Chat is context-aware: sends current plan data with each message
- [x] Chat messages render markdown formatting correctly
- [x] PlanComparison displays multiple plans side-by-side with scores and key metrics
- [x] "Compare with AI" feature sends plan data to the LLM for a natural-language comparison
- [x] Chat panel has a clean, non-intrusive UI (sidebar or collapsible panel)
- [x] Error states handled gracefully (LLM unavailable, network errors)

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Streaming chat | Messages appear token-by-token in real time | No streaming or delayed |
| Context awareness | Chat responses reference current plan details | Generic responses ignoring context |
| Plan comparison | All plans displayed with scores and key differences | Missing plans or scores |
| AI comparison | LLM generates meaningful plan comparison | Feature missing or broken |
