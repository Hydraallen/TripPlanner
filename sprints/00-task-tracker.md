# TripPlanner Task Tracker

> Tracks all sprints with status, contracts, and evaluation criteria.
> Based on Anthropic harness design principles: sprint contracts, structured evaluation, file-based coordination.

---

## Sprint Status

| Sprint | Title | Status | Contract | Phase |
|--------|-------|--------|----------|-------|
| S01 | Project Scaffolding + Config | Done | [S01-contract.md](S01-contract.md) | 1 |
| S02 | Pydantic Data Models | Done | [S02-contract.md](S02-contract.md) | 1 |
| S03 | OpenTripMap API Client | Done | [S03-contract.md](S03-contract.md) | 1 |
| S04 | CLI Skeleton (plan command) | Done | [S04-contract.md](S04-contract.md) | 1 |
| S05 | Preference Scorer | Done | [S05-contract.md](S05-contract.md) | 2 |
| S06 | Route Optimizer | Done | [S06-contract.md](S06-contract.md) | 2 |
| S07 | Day Scheduler | Done | [S07-contract.md](S07-contract.md) | 2 |
| S08 | Budget Calculator + Pipeline | Done | [S08-contract.md](S08-contract.md) | 2 |
| S09 | Database Layer | Done | [S09-contract.md](S09-contract.md) | 3 |
| S10 | Multi-Format Export | Done | [S10-contract.md](S10-contract.md) | 3 |
| S11 | Full CLI Commands | Done | [S11-contract.md](S11-contract.md) | 3 |
| S12 | Rich UX Polish | Done | [S12-contract.md](S12-contract.md) | 4 |
| S13 | Weather Integration | Done | [S13-contract.md](S13-contract.md) | 4 |
| S14 | Wikipedia Enrichment | Done | [S14-contract.md](S14-contract.md) | 4 |
| S15 | Testing & Demo Prep | Done | [S15-contract.md](S15-contract.md) | 4 |
| S16 | FastAPI Scaffolding + Trip CRUD | Done | [S16-contract.md](S16-contract.md) | 5 |
| S17 | Smart Routing + Amap + Plan API | Done | [S17-contract.md](S17-contract.md) | 5 |
| S18 | LLM Integration + Chat API | Done | [S18-contract.md](S18-contract.md) | 5 |
| S19 | React Scaffolding + Core Pages | Done | [S19-contract.md](S19-contract.md) | 5 |
| S20 | Map Visualization + Display | Done | [S20-contract.md](S20-contract.md) | 5 |
| S21 | Chat Panel + Polish | Done | [S21-contract.md](S21-contract.md) | 5 |
| S22 | Docker Setup | Done | [S22-contract.md](S22-contract.md) | 5 |
| S23 | E2E Testing + Documentation | Done | [S23-contract.md](S23-contract.md) | 5 |
| S24 | Multi-Plan Data Models + DB Schema | Done | [S24-contract.md](S24-contract.md) | 6 |
| S25 | AI Plan Generator + Scorer | Done | [S25-contract.md](S25-contract.md) | 6 |
| S26 | SSE Progress + Multi-Plan API | Done | [S26-contract.md](S26-contract.md) | 6 |
| S27 | Frontend Plan Comparison UI | Done | [S27-contract.md](S27-contract.md) | 6 |
| S28 | Enhanced AI Chat + Polish | Done | [S28-contract.md](S28-contract.md) | 6 |

## Dependencies

```
S01 ──→ S02 ──→ S03 ──→ S04
                      │
                      ▼
         S05 ──→ S06 ──→ S07 ──→ S08
                                  │
                                  ▼
                    S09 ──→ S10 ──→ S11
                                        │
                                        ▼
                              S12 ──→ S13 ──→ S14
                                              │
                                              ▼
                                            S15
                                              │
                                              ▼
                              S16 ──→ S17 ──→ S18 ──→ S19 ──→ S20 ──→ S21 ──→ S22 ──→ S23
                                                                                    │
                                                                                    ▼
                                                              S24 ──→ S25 ──→ S26 ──→ S27 ──→ S28
```

## Phase Milestones

| Phase | Milestone Command | Sprints |
|-------|------------------|---------|
| 1 | `tripplanner plan --city Tokyo --dry-run` fetches POIs and prints structured results | S01-S04 |
| 2 | Generate valid 3-day itinerary with 8-12 places, optimized routes, budget | S05-S08 |
| 3 | Full CLI workflow: plan → save → list → show → export → delete | S09-S11 |
| 4 | Demo-ready, 80%+ coverage, weather, optional Wikipedia | S12-S15 |
| 5 | Full-stack: FastAPI backend + React frontend + Docker | S16-S23 |
| 6 | AI-first multi-plan: 3 alternatives, SSE progress, scoring, AI chat | S24-S28 |

## Evaluation Roles

Per the harness design article, we separate **generation** from **evaluation**:

| Role | Responsibility |
|------|---------------|
| **Generator** (Claude Code) | Implements the sprint. Writes code, tests, docs. |
| **Evaluator** (code-reviewer agent) | Reviews completed sprint against contract criteria. Flags gaps. |
| **Planner** (Claude Code) | Breaks down next sprint if blocked. Adjusts plan on deviation. |

Each sprint contract defines concrete "done" criteria that the evaluator grades against.

## How to Use This Tracker

1. **Before sprint**: Read contract file, understand "done" criteria
2. **During sprint**: Implement, test locally, check off contract items
3. **After sprint**: Run evaluator agent, mark status, update dependencies
4. **On deviation**: Re-plan affected downstream sprints, update contracts if needed
