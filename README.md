# TripPlanner

A Python full-stack travel itinerary generator. Generates personalized day-by-day travel plans with route optimization, budget estimation, and weather forecasts.

Supports both CLI and web interface. Chinese destinations use Amap API; international destinations use Overpass API (OpenStreetMap). No API key required for international cities. Optional AI-powered multi-plan generation via GLM-5.1.

## Features

- **Multi-plan generation** — creates up to 6 themed itineraries per trip (budget, culture, nature, food, romantic, adventure), scored on 6 dimensions so you can compare and pick the best one
- **LLM-powered plans** — GLM-5.1 generates detailed schedules with time slots, descriptions, commute estimates, and restaurant recommendations; falls back to algorithmic pipeline when LLM is unavailable
- **Interactive map** — Leaflet-based map showing all attractions with markers and routes
- **AI chat** — travel advisor chatbot with context-aware suggestions based on your selected plan
- **Smart API routing** — auto-detects Chinese destinations and switches to Amap; international cities use free Overpass API
- **Real-time progress** — SSE-based progress tracking during plan generation
- **Export** — download plans as Markdown, JSON, or HTML

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configure (optional — international cities work without any API key)
cp .env.example .env
```

> **Note:** You must activate the virtual environment every time you open a new terminal before running `tripplanner` commands:
> ```bash
> source .venv/bin/activate
> ```
> You'll see `(.venv)` in your prompt when the environment is active.

### CLI Usage

```bash
# Minimal — just city and dates, AI decides everything else
tripplanner plan --city "San Francisco" --dates 2026-05-01 2026-05-03

# Generate more plan alternatives
tripplanner plan --city "Chicago" --dates 2026-05-01 2026-05-03 --num-plans 5

# Preview POIs without generating itinerary (no --dates needed)
tripplanner plan --city "Paris" --dry-run

# Export selected plan to file
tripplanner plan --city "London" --dates 2026-07-01 2026-07-03 --export markdown --output london.md
```

#### CLI Command Reference

| Command | Description |
|---------|-------------|
| `tripplanner plan` | Generate a new trip plan |
| `tripplanner list` | List all saved trips |
| `tripplanner show <trip-id>` | Display trip details |
| `tripplanner export <trip-id> --format <fmt>` | Export trip (markdown/json/html) |
| `tripplanner delete <trip-id>` | Delete a saved trip |

#### `plan` Options

| Option | Default | Description |
|--------|---------|-------------|
| `--city` | *required* | Target city name |
| `--dates` | required | Start and end dates as two arguments (YYYY-MM-DD) |
| `--num-plans` | 3 | Number of plan alternatives to generate (1-6) |
| `--radius` | 10000 | Search radius in meters |
| `--dry-run` | off | Fetch POIs only, skip itinerary generation |
| `--export` | | Export format: markdown / json / html |
| `--output` | stdout | Output file path |

### Web Mode

```bash
# Start backend
tripplanner web               # production mode
tripplanner web --dev         # development with auto-reload

# Start frontend (separate terminal)
cd frontend
npm install
npm run dev                   # opens at http://localhost:5173
```

The frontend proxies `/api` requests to the backend at `localhost:8000`.

#### Frontend Pages

| Route | Description |
|-------|-------------|
| `/` | Home — enter trip details and generate plans |
| `/plan` | Plan generation page with real-time progress |
| `/trips` | List all saved trips |
| `/trips/:id` | Trip detail — selected plan, map, day-by-day view, chat |

### Docker

```bash
cp .env.example .env
docker compose up --build

# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
```

Docker uses PostgreSQL by default. Without Docker, the app falls back to SQLite (zero config).

## API Reference

API docs available at `http://localhost:8000/docs` (Swagger UI).

### Trips

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trips` | List all trips |
| POST | `/api/trips` | Create a trip (query params: city, start_date, end_date, interests, transport_mode) |
| GET | `/api/trips/{id}` | Get trip details |
| DELETE | `/api/trips/{id}` | Delete a trip |
| GET | `/api/trips/{id}/export?format=` | Export (markdown / json / html) |

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/generate` | Start multi-plan generation. Returns `trip_id` immediately; generation runs in background |
| GET | `/api/plans/{trip_id}/progress` | SSE stream for real-time generation progress |
| GET | `/api/plans/{trip_id}/plans` | Get generated plan alternatives with scores |
| POST | `/api/plans/{trip_id}/select` | Select a plan (`{"plan_id": "plan_1"}`) |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Chat with travel advisor |
| GET | `/api/chat/stream` | SSE streaming chat |

### Generation Progress (SSE events)

| Status | Progress | Phase |
|--------|----------|-------|
| `collecting` | 0–30% | Geocoding city → fetching POIs → weather forecast |
| `generating` | 30–90% | LLM generates plan for each focus type |
| `scoring` | 90–100% | 6-dimensional scoring and ranking |
| `completed` | 100% | Plans ready to retrieve |
| `failed` | 0% | Error occurred |

### Example: Generate Plans via API

```bash
# Step 1: Start generation (returns immediately)
curl -X POST http://localhost:8000/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Chicago",
    "start_date": "2026-05-01",
    "end_date": "2026-05-03",
    "interests": ["museums", "food", "architecture"],
    "transport_mode": "walking",
    "budget": 500,
    "num_plans": 3
  }'
# Response: {"trip_id": "abc-123-..."}

# Step 2: Track progress
curl -N http://localhost:8000/api/plans/abc-123-.../progress
# SSE events: data: {"status":"collecting","progress":20,"step":"Found 15 places in Chicago"}
#             data: {"status":"generating","progress":50,"step":"Generating culture plan... (2/3)"}
#             data: {"status":"completed","progress":100,"step":"Done!"}

# Step 3: Get results
curl http://localhost:8000/api/plans/abc-123-.../plans

# Step 4: Select a plan
curl -X POST http://localhost:8000/api/plans/abc-123-.../select \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "plan_2"}'
```

## Plan Focus Types

When generating multiple plans, each targets a different travel style:

| Focus | Theme | Prioritizes |
|-------|-------|-------------|
| `budget` | Budget-Friendly Explorer | Free/low-cost attractions, affordable dining |
| `culture` | Culture & Discovery | Museums, historical sites, art galleries, authentic cuisine |
| `nature` | Nature & Relaxation | Parks, gardens, scenic viewpoints, waterfront walks |
| `food` | Foodie's Delight | Local restaurants, food markets, cooking classes, specialty cafes |
| `romantic` | Romantic Getaway | Sunset viewpoints, fine dining, waterfront walks, cozy cafes |
| `adventure` | Adventure & Thrills | Outdoor activities, hiking, water sports, off-the-beaten-path |

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

All settings are in `.env` (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `AMAP_API_KEY` | For China | POI, maps, weather for Chinese cities |
| `OPENAI_API_KEY` | Optional | AI plan generation + chat (GLM-5.1) |
| `OPENAI_ENDPOINT` | Optional | LLM API endpoint (default: GLM) |
| `OPENAI_MODEL_NAME` | Optional | Model name (default: glm-5.1) |
| `LLM_TEMPERATURE` | Optional | LLM temperature (default: 0.7) |
| `LLM_MAX_TOKENS` | Optional | Max tokens per request (default: 16384) |
| `GEOAPIFY_API_KEY` | Optional | Reverse geocoding fallback |
| `DATABASE_URL` | No | Default: `sqlite+aiosqlite:///./trips.db` |
| `HOST` / `PORT` | No | Server bind address (default: 0.0.0.0:8000) |

> International cities work out of the box — no API key needed. POI data comes from Overpass API (OpenStreetMap) + Nominatim geocoding + Open-Meteo weather.

## Architecture

```
CLI (Click)                     React SPA (Vite + Ant Design + Leaflet)
   │                                      │
   └──────────────┬───────────────────────┘
                  │
             FastAPI Backend
             /api/trips  /api/plans  /api/chat
                  │
        ┌─────────┼─────────────┐
        │         │             │
    PlanGen    Scorer      Scheduler → Budget
    (6-focus   (6-dim)      Optimizer
    LLM calls,
    background)
        │
    API Clients (smart routing)
    China → Amap │ International → Overpass API (OSM)
                  │
             Weather (Open-Meteo)
                  │
             LLM (GLM-5.1, optional)
                  │
        SQLite (default) │ PostgreSQL (Docker)
```

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Pydantic 2.x, Click
- **Frontend:** React 19, TypeScript, Vite 8, Ant Design 5, React-Leaflet 5
- **Database:** SQLite (default) / PostgreSQL (Docker)
- **APIs:** Overpass API (OSM), Nominatim, Amap, Open-Meteo, Wikipedia
- **LLM:** GLM-5.1 via OpenAI-compatible API

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
pytest tests/test_scorer.py::test_score_attraction -v  # single test
pytest --cov=src/tripplanner tests/                     # with coverage

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/
```

## License

Educational project for SI511 course.
