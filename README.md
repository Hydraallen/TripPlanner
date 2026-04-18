# TripPlanner

A Python full-stack travel itinerary generator. Generates personalized day-by-day travel plans with route optimization, budget estimation, and weather forecasts.

Supports both CLI and web interface. Chinese destinations use Amap API; international destinations use OpenTripMap. Optional AI-powered plan generation via GLM-5.1.

## Quick Start

### CLI Mode

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env — add OPENTRIPMAP_API_KEY (required)

# Generate a trip
tripplanner plan --city "Paris" --dates "2026-04-10 to 2026-04-13" --interests museums,food

# List / Show / Export / Delete
tripplanner list
tripplanner show <trip-id>
tripplanner export <trip-id> --format markdown
tripplanner delete <trip-id>
```

### Web Mode

```bash
# Start the web server
tripplanner web --port 8000

# With auto-reload for development
tripplanner web --dev
```

Open `http://localhost:8000/docs` for the Swagger API UI.

### Frontend (Development)

```bash
cd frontend
npm install
npm run dev
```

Opens React app at `http://localhost:5173` with API proxy to backend.

### Docker

```bash
# Copy and configure environment
cp .env.example .env

# Start all services (PostgreSQL + Backend + Frontend)
docker compose up --build

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

Docker uses PostgreSQL by default. Without Docker, the app falls back to SQLite.

## Architecture

```
CLI (Click)              React SPA (Vite + Ant Design + Leaflet)
   │                              │
   └──────────┬───────────────────┘
              │
         FastAPI Backend
         /api/trips  /api/plans  /api/chat  /api/map
              │
    ┌─────────┼─────────────┐
    │         │             │
  Scorer  Optimizer  Scheduler → Budget
    │
  API Clients (smart routing)
  China: Amap │ International: OpenTripMap
              │
         Weather (Open-Meteo)
              │
         LLM (GLM-5.1, optional)
              │
    SQLite (default) │ PostgreSQL (Docker)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trips` | List all trips |
| POST | `/api/trips` | Create a trip |
| GET | `/api/trips/{id}` | Get trip details |
| DELETE | `/api/trips/{id}` | Delete a trip |
| GET | `/api/trips/{id}/export?format=` | Export (markdown/json/html) |
| POST | `/api/plans/generate` | Generate plan (algorithmic) |
| POST | `/api/plans/generate-llm` | Generate plan (AI with fallback) |
| POST | `/api/chat` | Chat with travel advisor |
| GET | `/api/chat/stream` | SSE streaming chat |

## Configuration

All settings are in `.env` (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENTRIPMAP_API_KEY` | Yes | POI data for international cities |
| `AMAP_API_KEY` | For China | POI, maps, weather for Chinese cities |
| `OPENAI_API_KEY` | Optional | AI plan generation + chat (GLM-5.1) |
| `OPENAI_ENDPOINT` | Optional | LLM API endpoint |
| `DATABASE_URL` | No | Default: SQLite |
| `HOST` / `PORT` | No | Server bind address |

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Pydantic 2.x
- **Frontend:** React 18, TypeScript, Vite, Ant Design 5, React-Leaflet
- **Database:** SQLite (default) / PostgreSQL (Docker)
- **APIs:** OpenTripMap, Amap, Open-Meteo, Wikipedia
- **LLM:** GLM-5.1 via OpenAI-compatible API

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
pytest tests/test_web_api.py -v  # specific file

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/
```

## License

Educational project for SI511 course.
