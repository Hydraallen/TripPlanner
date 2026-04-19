# TripPlanner Implementation Plan

---

## Architecture Overview

Full-stack travel itinerary generator with CLI and web interfaces sharing a common Python backend. React SPA frontend with interactive maps, AI chat, and multi-plan comparison.

```
┌─────────────────────────────────────────────────┐
│  CLI (Click + Rich)  │  React SPA (Vite + Ant Design + Leaflet)  │
├─────────────────────────────────────────────────┤
│  FastAPI Backend                                 │
│  /api/trips  /api/plans  /api/chat              │
├─────────────────────────────────────────────────┤
│  Services Layer                                  │
│  PlanGenerator → PlanScorer → LLM → Progress    │
├─────────────────────────────────────────────────┤
│  Logic Layer                                     │
│  scorer → optimizer → scheduler → budget_calc   │
├─────────────────────────────────────────────────┤
│  API Client Layer (smart routing)                │
│  Overpass (OSM) · Amap · Geoapify · Wikipedia   │
│  Weather (Open-Meteo) · Routing (OSRM)          │
├─────────────────────────────────────────────────┤
│  Persistence Layer                               │
│  SQLite (default) · PostgreSQL (Docker) · Export │
└─────────────────────────────────────────────────┘
```

**Data flow:** User input → API clients fetch POIs (3-tier fallback) → LLM generates multi-focus plans (background task) → 6-dimensional scoring → User selects plan → Persist & display with interactive map.

---

## Phase 1: Foundation — DONE

### 1.1 Project Scaffolding — DONE

```
src/tripplanner/
├── __init__.py
├── cli.py              # Click group + subcommands
├── core/
│   ├── models.py       # Pydantic v2 data models (Location, Attraction, DayPlan, TripPlan, PlanFocus, PlanAlternative, etc.)
│   ├── state.py        # Shared TripState pipeline
│   └── config.py       # pydantic-settings (.env)
├── api/
│   ├── opentripmap.py  # POI search: Overpass → Geoapify → Wikipedia (3-tier fallback)
│   ├── weather.py      # Open-Meteo forecast
│   └── wikipedia.py    # Place descriptions
├── logic/
│   ├── scorer.py       # Preference scoring (category 40% + rating 30% + popularity 30%)
│   ├── optimizer.py    # Route optimization (greedy nearest-neighbor clustering)
│   ├── scheduler.py    # Day-by-day scheduling with meal placement
│   └── budget.py       # Budget calculator
├── db/
│   ├── models.py       # SQLAlchemy 2.x async ORM
│   ├── crud.py         # Database CRUD operations
│   └── cache.py        # API response cache (24h TTL)
├── web/
│   ├── app.py          # FastAPI app factory
│   ├── routers/        # trips, plans, chat endpoints
│   └── services/       # planning, plan_generator, plan_scorer, llm, progress, region
├── export/
│   ├── markdown.py     # Jinja2 template
│   ├── json_export.py  # Pydantic JSON dump
│   └── html_gen.py     # Jinja2 HTML template
└── tests/              # pytest suite (226 tests)

frontend/src/
├── pages/              # HomePage, PlanPage, TripDetailPage
├── components/         # MapView, DayCard, ChatPanel, TripForm, BudgetChart, PlanComparison, Layout
├── api/                # TypeScript API client with typed interfaces
└── utils/              # Google Maps links, OSRM routing
```

### 1.2 Core Models — DONE

Pydantic v2 models built bottom-up:

- **Location** — validated lon/lat with numeric coercion
- **Attraction** — POI with xid, name, location, kinds, rating, ticket_price, score, time_slot, commute_minutes
- **Meal** — type (breakfast/lunch/dinner/snack), name, estimated_cost, time_slot
- **DayPlan** — date, day_number, transportation, attractions list, meals list
- **TripPlan** — city, date range, days, weather, budget, suggestions
- **PlanFocus** — enum: budget, culture, nature, food, romantic, adventure
- **PlanAlternative** — id, focus, title, description, plan, scores, estimated_cost, source
- **PlanScores** — 6-dimensional: price, rating, convenience, diversity, safety, popularity
- **GenerationProgress** — SSE progress tracking: status, progress%, step description
- **Budget** — total breakdown: attractions, meals, hotels, transportation

### 1.3 Configuration — DONE

`pydantic-settings` + `.env` file:

- `AMAP_API_KEY` — for Chinese cities (free, 5k calls/day)
- `OPENAI_API_KEY` / `OPENAI_ENDPOINT` / `OPENAI_MODEL_NAME` — GLM-5.1 LLM
- `GEOAPIFY_API_KEY` — optional reverse geocoding fallback
- `DATABASE_URL` — SQLite default or PostgreSQL
- Walking/transit/driving speed constants for commute estimation

---

## Phase 2: Core Logic — DONE

### 2.1 Scorer — DONE

`logic/scorer.py` computes composite score for each POI:

```
score = (category_match * 0.4) + (rating_normalized * 0.3) + (popularity * 0.3)
```

- Category match: Jaccard similarity between user interests and place kinds
- Rating: normalized to 0–1, missing ratings use dataset mean
- Popularity: based on data source indicators

### 2.2 Route Optimizer — DONE

`logic/optimizer.py` — greedy nearest-neighbor clustering:

1. Start from city center coordinates
2. Pick highest-scored unvisited place as anchor
3. Greedily add nearest unvisited place within threshold
4. When day has ~4 places, start new cluster
5. Repeat until all top-scored places assigned

Haversine distance calculation for proximity estimation.

### 2.3 Scheduler — DONE

`logic/scheduler.py` — splits optimized clusters into DayPlan objects:

- Time slots: morning (9–12), afternoon (13–17), evening (18–21)
- Visit durations: museums ~120min, viewpoints ~45min, parks ~60min
- Travel time between consecutive places
- Meal placement: breakfast 08:00, lunch 12:00, dinner 18:00
- Weather-aware: prefers indoor venues on rainy days

### 2.4 Budget Calculator — DONE

`logic/budget.py` — algorithmic cost estimation:

- Attraction costs from API ticket_price data
- Meal cost heuristics: breakfast ~$10, lunch ~$15, dinner ~$25
- Transport estimation based on mode and distance
- Hotel estimation per night

### 2.5 Pipeline State — DONE

`core/state.py` — TripState manages the generation pipeline flow through all stages.

---

## Phase 3: API Clients — DONE

### 3.1 POI Data: Three-Tier Fallback — DONE

`api/opentripmap.py` implements cascading fallback:

1. **Overpass API (OSM)** — primary, free, global coverage
2. **Geoapify** — fallback, respects 5000m radius limit
3. **Wikipedia Geosearch** — last resort, with proper User-Agent header

Each tier returns normalized `Attraction` objects. If one source fails, the next automatically takes over.

### 3.2 Smart Region Routing — DONE

`web/services/region.py` auto-detects destination type:

- Chinese characters or known Chinese cities → Amap API (requires API key)
- All other destinations → free Overpass API (no key needed)

### 3.3 Weather — DONE

`api/weather.py` — Open-Meteo daily forecast (free, no auth):

- Fetches temp_high, temp_low, precipitation, wind speed
- WMO weather code → human-readable description
- Integrated into plan scheduling for weather-aware attraction selection

---

## Phase 4: Persistence & Export — DONE

### 4.1 Database — DONE

SQLAlchemy 2.x async ORM:

- **Trips table** — UUID id, city, dates, status (draft/generating/completed), generated_plans JSON, selected_plan_id
- **Cache table** — API response cache with 24h TTL
- Auto-creates tables on startup
- SQLite default (zero config), PostgreSQL in Docker

### 4.2 CRUD Operations — DONE

`db/crud.py` — full async CRUD: save, get, list, delete trips.

### 4.3 Export — DONE

Three formats via Jinja2 templates and Pydantic serialization:

- **Markdown** — formatted itinerary with budget table, day-by-day breakdown
- **JSON** — `model_dump_json()` with `exclude_none=True`
- **HTML** — styled printable page with embedded CSS

---

## Phase 5: CLI — DONE

### 5.1 Commands — DONE

| Command | Description |
|---------|-------------|
| `tripplanner plan` | Generate trip plan interactively |
| `tripplanner list` | List all saved trips |
| `tripplanner show <id>` | Display trip details |
| `tripplanner export <id>` | Export (markdown/json/html) |
| `tripplanner delete <id>` | Delete a trip |
| `tripplanner web [--dev]` | Start web server |

### 5.2 Plan Command — DONE

Simplified to minimal input:

```bash
tripplanner plan --city "Chicago" --dates 2026-05-01 2026-05-03
```

Options: `--num-plans`, `--radius`, `--dry-run`, `--export`, `--output`

Generates multi-plan using same pipeline as web. Shows interactive comparison table, lets user select a plan.

---

## Phase 6: Web Backend — DONE

### 6.1 FastAPI Application — DONE

`web/app.py` — FastAPI factory with CORS, routers, lifespan events.

### 6.2 Routers — DONE

| Router | Endpoints |
|--------|-----------|
| `/api/trips` | CRUD: list, create, get, delete, export |
| `/api/plans` | `POST /generate` (async background), `GET /progress` (SSE), `GET /plans`, `POST /select` |
| `/api/chat` | `POST` (sync), `GET /stream` (SSE streaming) |

### 6.3 Background Multi-Plan Generation — DONE

`web/services/planning.py`:

1. `POST /api/plans/generate` → creates trip draft, returns `trip_id` immediately
2. `asyncio.create_task` kicks off background generation with own DB session
3. Pipeline: fetch POIs + weather (0–30%) → LLM generates plans per focus (30–90%) → score (90–100%)
4. Client tracks progress via SSE at `GET /api/plans/{id}/progress`

### 6.4 Plan Generator — DONE

`web/services/plan_generator.py`:

- Generates up to 6 plans, each targeting a different focus (budget, culture, nature, food, romantic, adventure)
- Tries LLM first per focus, falls back to algorithmic pipeline
- Cross-plan deduplication: tracks used attraction names across plans via prompt + post-processing filter

### 6.5 LLM Integration — DONE

`web/services/llm.py`:

- OpenAI-compatible API client (defaults to GLM-5.1)
- `generate_plan_with_focus()` — generates a single focused plan
- `chat()` / `chat_stream()` — travel advisor chat with plan context
- Knowledge-first system prompt: instructs LLM to prioritize iconic landmarks from its own training data
- POI data presented as "reference coordinates" only, not as recommendation list
- `used_attractions` parameter for cross-plan dedup
- Thinking mode disabled for GLM-5.1 compatibility

### 6.6 Plan Scoring — DONE

`web/services/plan_scorer.py` — 6-dimensional scoring:

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Price | 25% | Cost efficiency |
| Rating | 25% | Average attraction quality |
| Convenience | 20% | Route efficiency |
| Diversity | 10% | Category variety |
| Safety | 10% | Daytime-friendly venues |
| Popularity | 10% | Attraction density |

### 6.7 SSE Progress — DONE

`web/services/progress.py` — Server-Sent Events stream for real-time generation progress tracking.

---

## Phase 7: Web Frontend — DONE

### 7.1 React SPA — DONE

React 19 + TypeScript + Vite 8 + Ant Design 5:

| Route | Page | Features |
|-------|------|----------|
| `/` | HomePage | Hero section, trip planning form, features showcase |
| `/plan` | PlanPage | Trip form, real-time progress bar, plan comparison |
| `/trips/:id` | TripDetailPage | Day-by-day itinerary, interactive map, budget chart, AI chat |

### 7.2 Interactive Map — DONE

`components/MapView.tsx` — Leaflet-based map:

- Color-coded markers per day with custom SVG pin icons
- Route polylines connecting attractions within each day
- Auto-fit bounds to show all attractions
- Marker popups with Google Maps link + "Directions to next" link

### 7.3 Day Card — DONE

`components/DayCard.tsx` — day-by-day itinerary display:

- Clickable attraction names → opens Google Maps search in new tab
- Wikipedia icon link when attraction has wiki article
- Commute time Popover → shows walking/driving/cycling times from OSRM
- "Open in Google Maps" directions link in popover

### 7.4 Transport Comparison — DONE

`utils/routing.ts` — OSRM routing client:

- Fetches walking, driving, cycling duration/distance between two points
- Falls back to haversine estimate on failure
- Results cached to avoid duplicate API calls
- Lazy loading: only fetches when user hovers over commute badge

### 7.5 Google Maps Links — DONE

`utils/maps.ts`:

- `googleMapsSearchUrl()` — search for attraction on Google Maps
- `googleMapsDirectionsUrl()` — directions between two locations
- `extractWikipediaUrl()` — extract Wikipedia link from description text

### 7.6 Plan Comparison — DONE

`components/PlanComparison.tsx` — side-by-side plan cards with scores, costs, descriptions, and select button.

### 7.7 Budget Chart — DONE

`components/BudgetChart.tsx` — visual budget breakdown by category.

### 7.8 AI Chat Panel — DONE

`components/ChatPanel.tsx` — travel advisor chatbot:

- Context-aware: knows about the current plan
- Streaming responses via SSE
- "Compare with AI" button auto-generates comparison prompt
- Floating panel overlay

### 7.9 Trip Form — DONE

`components/TripForm.tsx` — simplified form:

- Required: city, start date, end date
- Collapsible advanced options: interests, transport mode
- AI decides everything by default

---

## Phase 8: LLM Prompt Optimization — DONE

### 8.1 Knowledge-First System Prompt — DONE

System prompt instructs LLM to:

- Prioritize iconic, well-known attractions for each city
- Use its own training knowledge as primary source
- Treat POI data as coordinate reference only
- Use realistic ticket prices (museums $15–35, observation decks $20–40)
- Estimate commute times realistically (walking ~5 km/h, driving ~30 km/h)
- Provide accurate lat/lon coordinates

### 8.2 Strengthened Focus Prompts — DONE

Each focus prompt now includes specific guidance:

- Budget: "Choose famous FREE attractions first (iconic parks, monuments, waterfronts)"
- Culture: "Choose the city's MOST FAMOUS museums — the ones every guidebook recommends"
- Nature: "If the city has a famous park, it MUST be included"
- Food: "Choose the city's most renowned restaurants and iconic food markets"

### 8.3 Cross-Plan Deduplication — DONE

Two-layer dedup strategy:

1. **Prompt-level** — passes `used_attractions` set to LLM with mandatory exclusion instruction
2. **Post-processing** — `_dedup_plan()` filter removes any attractions that appear in earlier plans

Result: 0 duplicate attractions across plans (verified with Chicago and Boston tests).

---

## Phase 9: Docker & Deployment — DONE

### 9.1 Docker Compose — DONE

- Backend: Python container with FastAPI
- Frontend: Node container with Vite build
- PostgreSQL: production database
- Nginx: reverse proxy for static files
- `docker compose up --build` to launch everything

---

## Test Results

- **226 tests passing** across all layers
- Coverage: models, API clients, logic, DB, CLI, plan generator, plan scorer
- `pytest` with `asyncio_mode = "auto"`, `respx` for HTTP mocking

---

## Key Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project layout | `src/tripplanner/` | Avoids import ambiguity, standard Python packaging |
| Data models | Bottom-up Pydantic v2 | Location → Attraction → DayPlan → TripPlan. Composable, validated. |
| Async | `httpx` + `aiosqlite` + SQLAlchemy 2.x async | Full async stack, future-proof |
| CLI | Click 8.x with Rich tables | Interactive comparison table, formatted output |
| Database | SQLite default, PostgreSQL in Docker | Zero-config for development, scalable for production |
| Route optimization | Greedy nearest-neighbor | Simple, sufficient for ≤20 places per trip |
| POI fallback | 3-tier: Overpass → Geoapify → Wikipedia | Graceful degradation, never crashes |
| Region routing | Auto-detect Chinese destinations → Amap | Free for international, Amap for China accuracy |
| Multi-plan | 6 focus types, LLM per focus | Diverse options, user compares and selects |
| LLM | GLM-5.1 via OpenAI-compatible API | Knowledge-first prompt, algorithmic fallback |
| Cross-plan dedup | Prompt + post-processing filter | 0 duplicate attractions across plans |
| Frontend | React 19 + Ant Design 5 + Leaflet | Modern SPA with interactive map |
| Transport comparison | OSRM (free, no key) | Walking/driving/cycling times on hover |
| Background generation | `asyncio.create_task` with SSE | Non-blocking, real-time progress updates |
