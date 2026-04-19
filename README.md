# TripPlanner

AI-powered travel itinerary generator. Enter a city and dates, get multiple personalized day-by-day plans with route optimization, budget estimation, real-time progress, and interactive maps. No API keys required for international cities.

## Features

- **Multi-plan comparison** — generates up to 6 themed itineraries per trip (budget, culture, nature, food, romantic, adventure), each scored on 6 dimensions so you can compare and pick the best one
- **LLM-powered generation** — GLM-5.1 creates detailed schedules with time slots, commute estimates, and restaurant recommendations; falls back to an algorithmic pipeline when no LLM key is configured
- **Interactive map** — Leaflet-based map with color-coded day routes, clickable markers linking to Google Maps and Wikipedia
- **Transport comparison** — hover over commute times to see walking, driving, and cycling estimates via OSRM routing
- **AI travel advisor** — context-aware chatbot that answers questions about your selected plan
- **Real-time progress** — SSE-based progress bar during plan generation
- **Smart API routing** — auto-detects Chinese destinations → switches to Amap; international cities use free Overpass/OSM
- **Cross-plan deduplication** — attractions are unique across plans; no repeats
- **Export** — download plans as Markdown, JSON, or HTML
- **CLI + Web** — two interfaces sharing the same backend and database

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (frontend only)
- (Optional) An OpenAI-compatible LLM API key for AI-powered plans

### 1. Clone and install

```bash
git clone https://github.com/Hydraallen/TripPlanner.git
cd TripPlanner

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# Windows: .venv\Scripts\activate

# Install backend
pip install -e ".[dev]"
```

> You must activate the virtual environment in each new terminal session. You'll see `(.venv)` in your prompt when active.

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env — only needed for Chinese cities (AMAP_API_KEY) or AI features (OPENAI_API_KEY)
# International cities work with zero API keys
```

### 3a. CLI — generate a plan in one command

```bash
# 3-day Chicago itinerary
tripplanner plan --city "Chicago" --dates 2026-05-01 2026-05-03

# 5-day Paris itinerary with 5 plan alternatives
tripplanner plan --city "Paris" --dates 2026-06-10 2026-06-14 --num-plans 5

# Preview POI data without generating a plan
tripplanner plan --city "Tokyo" --dry-run

# Export to file
tripplanner plan --city "London" --dates 2026-07-01 2026-07-03 --export markdown --output london.md
```

### 3b. Web — launch the full UI

```bash
# Option A: one-click launcher (starts both backend and frontend)
./start.sh

# Option B: start manually in two terminals
# Terminal 1 — backend
tripplanner web --dev

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `tripplanner plan` | Generate a new trip plan interactively |
| `tripplanner list` | List all saved trips |
| `tripplanner show <trip-id>` | Display trip details |
| `tripplanner export <trip-id> --format <fmt>` | Export trip (markdown/json/html) |
| `tripplanner delete <trip-id>` | Delete a saved trip |
| `tripplanner web [--dev]` | Start the web server |

### `plan` Options

| Option | Default | Description |
|--------|---------|-------------|
| `--city` | *required* | Target city name |
| `--dates` | *required* | Start and end dates (YYYY-MM-DD YYYY-MM-DD) |
| `--num-plans` | 3 | Number of plan alternatives (1–6) |
| `--radius` | 10000 | POI search radius in meters |
| `--dry-run` | off | Fetch POIs only, skip itinerary generation |
| `--export` | — | Export format: markdown / json / html |
| `--output` | stdout | Output file path |

## Web Interface

### Pages

| Route | Description |
|-------|-------------|
| `/` | Home — hero section and trip planning form |
| `/plan` | Plan generation with real-time progress bar |
| `/trips` | List all saved trips |
| `/trips/:id` | Trip detail — day-by-day itinerary, interactive map, budget chart, AI chat |

### How it works

1. Enter city and dates on the home page (or `/plan`)
2. Real-time progress bar tracks: collecting POIs → generating plans → scoring
3. Compare plans side-by-side with scores, costs, and descriptions
4. Select a plan to see the full itinerary with:
   - **Clickable attraction names** → opens Google Maps
   - **Wikipedia links** for attractions with wiki articles
   - **Commute time popover** → shows walking/driving/cycling duration
   - **Interactive map** with color-coded day routes and marker popups
   - **Budget breakdown** chart
5. Chat with the AI advisor about your selected plan

## API Reference

Interactive docs at `http://localhost:8000/docs` (Swagger UI).

### Trips

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trips` | List all trips |
| POST | `/api/trips` | Create a trip |
| GET | `/api/trips/{id}` | Get trip details |
| DELETE | `/api/trips/{id}` | Delete a trip |
| GET | `/api/trips/{id}/export?format=` | Export (markdown/json/html) |

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/generate` | Start multi-plan generation (returns `trip_id` immediately) |
| GET | `/api/plans/{trip_id}/progress` | SSE stream — real-time generation progress |
| GET | `/api/plans/{trip_id}/plans` | Get generated plan alternatives with scores |
| POST | `/api/plans/{trip_id}/select` | Select a plan (`{"plan_id": "plan_1"}`) |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Chat with travel advisor |
| GET | `/api/chat/stream` | SSE streaming chat |

### Example: Full generation flow

```bash
# 1. Start generation
curl -X POST http://localhost:8000/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{"city":"Chicago","start_date":"2026-05-01","end_date":"2026-05-03"}'
# → {"trip_id":"abc-123-..."}

# 2. Track progress (SSE)
curl -N http://localhost:8000/api/plans/abc-123-.../progress
# data: {"status":"collecting","progress":20,"step":"Found 45 places in Chicago"}
# data: {"status":"generating","progress":50,"step":"Generating culture plan... (2/3)"}
# data: {"status":"completed","progress":100,"step":"Done!"}

# 3. Get results
curl http://localhost:8000/api/plans/abc-123-.../plans

# 4. Select a plan
curl -X POST http://localhost:8000/api/plans/abc-123-.../select \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"plan_2"}'
```

## Plan Focus Types

Each generated plan targets a different travel style:

| Focus | Theme | Prioritizes |
|-------|-------|-------------|
| `budget` | Budget-Friendly Explorer | Free attractions, affordable local dining |
| `culture` | Culture & Discovery | Famous museums, historical landmarks, authentic cuisine |
| `nature` | Nature & Relaxation | Parks, botanical gardens, waterfronts, scenic trails |
| `food` | Foodie's Delight | Renowned restaurants, food markets, local specialties |
| `romantic` | Romantic Getaway | Scenic viewpoints, fine dining, waterfront walks |
| `adventure` | Adventure & Thrills | Outdoor activities, distinctive neighborhoods, unique experiences |

## Scoring System

Each plan is scored on 6 dimensions (0–1 scale):

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Price | 25% | Cost efficiency — lower total cost scores higher |
| Rating | 25% | Average attraction rating quality |
| Convenience | 20% | Route efficiency — 3–5 attractions per day is ideal |
| Diversity | 10% | Variety of attraction categories and meal types |
| Safety | 10% | Daytime-friendly venues vs nightlife-heavy plans |
| Popularity | 10% | Attraction density — 3–5 per day is ideal |

## Configuration

All settings via `.env` (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `AMAP_API_KEY` | Chinese cities only | POI and maps for Chinese destinations. Free at [lbs.amap.com](https://lbs.amap.com/) |
| `OPENAI_API_KEY` | Optional | Enables AI plan generation and chat (GLM-5.1 by default) |
| `OPENAI_ENDPOINT` | Optional | LLM API endpoint (default: `https://open.bigmodel.cn/api/coding/paas/v4`) |
| `OPENAI_MODEL_NAME` | Optional | Model name (default: `glm-5.1`) |
| `GEOAPIFY_API_KEY` | Optional | Reverse geocoding fallback. Free at [geoapify.com](https://www.geoapify.com/) |
| `DATABASE_URL` | No | Default: `sqlite+aiosqlite:///./trips.db` (zero config) |

> **International cities work out of the box** — no API key needed. POI data from Overpass API (OpenStreetMap), geocoding from Nominatim, weather from Open-Meteo.

## Architecture

```
CLI (Click)                          React SPA (Vite + Ant Design + Leaflet)
   │                                            │
   └─────────────────┬──────────────────────────┘
                     │
                FastAPI Backend
                /api/trips  /api/plans  /api/chat
                     │
           ┌─────────┼─────────────┐
           │         │             │
       PlanGen    Scorer     Scheduler → Budget
       (LLM per   (6-dim)    Optimizer
        focus,
        background task)
           │
       API Clients (smart routing)
       China → Amap  │  International → Overpass (OSM)
                       │
                  Weather (Open-Meteo)
                       │
                  LLM (GLM-5.1, optional)
                       │
           SQLite (default)  │  PostgreSQL (Docker)
```

### Source layout

```
src/tripplanner/
├── core/          # Pydantic domain models, config, TripState
├── logic/         # Pure algorithms: scorer, optimizer, scheduler, budget
├── api/           # External API clients: Overpass, Amap, weather, Wikipedia
├── db/            # SQLAlchemy 2.x async models, CRUD, response cache
├── web/
│   ├── routers/   # FastAPI endpoints: trips, plans, chat
│   ├── services/  # Orchestration: planning, plan_generator, plan_scorer, llm, progress, region
│   └── app.py     # FastAPI app factory
├── export/        # Markdown/JSON/HTML formatters
└── cli.py         # Click CLI entry point

frontend/src/
├── pages/         # Route pages (HomePage, PlanPage, TripDetailPage)
├── components/    # MapView, DayCard, ChatPanel, TripForm, BudgetChart, PlanComparison, Layout
├── api/           # Typed API client
└── utils/         # Google Maps links, OSRM routing
```

### Key design decisions

- **Background generation** — `POST /api/plans/generate` returns `trip_id` immediately, then runs LLM generation via `asyncio.create_task` with its own DB session. Client tracks progress via SSE.
- **6-focus LLM plans** — each plan targets one focus. `PlanGenerator` tries LLM first, falls back to algorithmic pipeline (greedy nearest-neighbor clustering + scoring).
- **Cross-plan dedup** — attractions are tracked across plans via prompt instructions + post-processing filter. Each plan features unique attractions.
- **Knowledge-first LLM prompt** — the system prompt instructs the LLM to prioritize iconic landmarks from its own training data, using POI data only for coordinates and logistics.
- **Three-tier POI fallback** — Overpass (OSM) → Geoapify → Wikipedia Geosearch. If one source fails, the next takes over.
- **Database** — auto-creates tables on startup. SQLite by default (zero config), PostgreSQL in Docker. All access is async via SQLAlchemy 2.x.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Pydantic v2, Click |
| Frontend | React 19, TypeScript, Vite 8, Ant Design 5, React-Leaflet 5 |
| Database | SQLite (default) / PostgreSQL (Docker) |
| POI Data | Overpass API (OSM), Nominatim, Amap, Geoapify, Wikipedia |
| Routing | OSRM (demo server, no key) |
| Weather | Open-Meteo (free) |
| LLM | GLM-5.1 via OpenAI-compatible API |

## Docker (optional)

```bash
cp .env.example .env
docker compose up --build

# Frontend: http://localhost:3000
# Backend docs: http://localhost:8000/docs
```

Docker adds PostgreSQL and nginx. Not required for development or personal use.

## Development

```bash
# Run tests
pytest                                        # all tests
pytest tests/test_scorer.py -v                # single file
pytest tests/test_scorer.py::test_score_attraction -v  # single test
pytest --cov=src/tripplanner tests/           # with coverage

# Lint and format
ruff check src/
ruff format src/

# Type check
mypy src/

# Frontend type check
cd frontend && npx tsc --noEmit
```

## License

Educational project for SI511 course.
