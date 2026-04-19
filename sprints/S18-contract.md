# Sprint S18: LLM Integration + Chat API

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S17
**Estimated complexity:** High

---

## Goal

Integrate GLM-5.1 via an OpenAI-compatible API for focused plan generation (budget, culture, nature, food, romantic, adventure) and implement a conversational AI travel advisor with streaming support.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/web/services/llm.py` | Create — GLM-5.1 client via OpenAI-compatible API |
| `src/tripplanner/web/services/plan_generator.py` | Create — 6-focus plan generation with algorithmic fallback |
| `src/tripplanner/web/services/plan_scorer.py` | Create — 6-dimensional scoring (price, rating, convenience, diversity, safety, popularity) |
| `src/tripplanner/web/routers/chat.py` | Create — POST /api/chat, GET /api/chat/stream (SSE) |

## Done Criteria

- [x] `llm.py` sends chat completion requests to GLM-5.1 with `"thinking": {"type": "disabled"}` to prevent token consumption in reasoning mode
- [x] `plan_generator.py` generates 3-6 plans per focus area, falls back to algorithmic pipeline if LLM fails
- [x] `plan_scorer.py` scores plans on 6 dimensions: price (25%), rating (25%), convenience (20%), diversity (10%), safety (10%), popularity (10%)
- [x] `POST /api/chat` accepts messages with optional plan context and returns AI travel advice
- [x] `GET /api/chat/stream` returns SSE-streamed chat responses
- [x] LLM integration gracefully degrades when `OPENAI_API_KEY` is not configured

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| LLM plans | Generates 3-6 focused plans per trip | Only 1 plan or all same focus |
| Fallback | Algorithmic pipeline runs when LLM fails | Crashes or returns empty |
| Scoring | All 6 dimensions computed with correct weights | Missing dimensions or wrong weights |
| Chat API | Streaming chat works with plan context | No streaming or missing context |
