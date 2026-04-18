# TripPlanner Implementation Plan

> Derived from `Project Proposal.md` and reference patterns in hello-agents chapter 13 (Intelligent Travel Assistant) and chapter 14 (Deep Research).

---

## Architecture Overview

Chapter 13 demonstrates a 4-layer architecture for a travel planning app. We adapt this for a CLI-first tool (no AI/LLM per proposal constraints):

```
┌─────────────────────────────────────────────────┐
│  CLI Layer (Click + Rich)                       │
│  plan / list / show / export / delete           │
├─────────────────────────────────────────────────┤
│  Logic Layer                                    │
│  scorer → optimizer → scheduler → budget_calc   │
├─────────────────────────────────────────────────┤
│  API Client Layer                               │
│  OpenTripMap · Open-Meteo · Wikipedia           │
├─────────────────────────────────────────────────┤
│  Persistence Layer                              │
│  SQLite (trips + cache) · Jinja2 export         │
└─────────────────────────────────────────────────┘
```

**Data flow:** User input → API clients fetch POIs → Score & filter → Optimize routes → Schedule into days → Calculate budget → Export & persist.

---

## Phase 1: Foundation

**Milestone:** `tripplanner plan --city Tokyo --dry-run` fetches POIs from OpenTripMap and prints structured results.

### 1.1 Project Scaffolding

```
tripplanner/
├── pyproject.toml              # deps, ruff config, entry point
├── .env.example
├── .gitignore
├── src/
│   └── tripplanner/
│       ├── __init__.py
│       ├── cli.py              # Click group + subcommands
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic data models
│       │   ├── state.py        # Shared TripState pipeline
│       │   └── config.py       # pydantic-settings
│       ├── api/
│       │   ├── __init__.py
│       │   ├── opentripmap.py  # POI search client
│       │   ├── weather.py      # Open-Meteo forecast
│       │   └── wikipedia.py    # Place descriptions
│       ├── logic/
│       │   ├── __init__.py
│       │   ├── scorer.py       # Preference scoring
│       │   ├── optimizer.py    # Route optimization
│       │   ├── scheduler.py    # Day-by-day scheduling
│       │   └── budget.py       # Budget calculator
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py       # SQLAlchemy ORM
│       │   ├── crud.py         # Database operations
│       │   └── cache.py        # API response cache
│       └── export/
│           ├── __init__.py
│           ├── markdown.py
│           ├── json_export.py
│           ├── html_gen.py
│           └── templates/
│               ├── itinerary.md.j2
│               ├── itinerary.html.j2
│               └── styles.css
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py
    ├── test_logic.py
    ├── test_export.py
    └── test_cli.py
```

Key decisions:

- **src layout** (`src/tripplanner/`) — avoids import ambiguity (ch14 pattern).
- **pydantic-settings** for config — proven in ch13/ch14.
- **Click** for CLI with subcommands: `plan`, `list`, `show`, `export`, `delete`.
- **Separate `logic/budget.py`** — budget calculation is a distinct concern (ch13 models it separately).

### 1.2 `core/config.py` — Settings

Pattern from ch13's `Settings(BaseSettings)` + ch14's `Configuration`:

```python
class Settings(BaseSettings):
    opentripmap_api_key: str = ""
    openmeteo_base_url: str = "https://api.open-meteo.com/v1"
    wikipedia_base_url: str = "https://en.wikipedia.org/api/rest_v1"
    database_url: str = "sqlite:///./trips.db"
    max_places_per_trip: int = 20
    default_search_radius: int = 10000  # meters
    cache_ttl: int = 86400              # 24 hours
    default_visit_duration: int = 90    # minutes
    walking_speed_kmh: float = 5.0
    transit_speed_kmh: float = 25.0
    driving_speed_kmh: float = 30.0

    model_config = SettingsConfigDict(env_file=".env")
```

Ch13 lesson: external APIs return inconsistent field names (e.g. `lng` vs `lon` vs `longitude`). Config centralizes endpoint URLs so API clients don't hardcode them.

### 1.3 `core/models.py` — Bottom-Up Pydantic Data Models

Chapter 13 Section 13.2 demonstrates **bottom-up model design**: build simple models first (Location), then compose into complex ones (DayPlan, TripPlan). We follow this exact approach.

**Lesson from ch13:** Use `Field(...)` with validation constraints (`ge`, `le`, `gt`) and `@field_validator` for cleaning messy API data. Ch13 shows temperature parsing (`"16°C" → 16`); we'll need similar for OpenTripMap data.

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional

# --- Base layer ---

class Location(BaseModel):
    """Geographic coordinates (ch13 pattern: validated lon/lat)."""
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

    @field_validator("longitude", "latitude", mode="before")
    @classmethod
    def coerce_numeric(cls, v: object) -> float:
        """Handle string coords from API responses."""
        if isinstance(v, str):
            return float(v.replace(",", "."))
        return float(v)

# --- Entity layer (ch13 has Attraction, Meal, Hotel separately) ---

class Attraction(BaseModel):
    """A tourist attraction or point of interest."""
    xid: str
    name: str
    address: str = ""
    location: Location
    categories: list[str] = Field(default_factory=list)
    kinds: str = ""                    # OpenTripMap "kinds" field
    visit_duration: int = Field(default=90, gt=0, description="minutes")
    description: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    ticket_price: float = Field(default=0, ge=0)
    score: float = Field(default=0.0, ge=0, le=1)  # computed by scorer

    @field_validator("rating", mode="before")
    @classmethod
    def clamp_rating(cls, v: object) -> float | None:
        if v is None:
            return None
        val = float(v)
        return min(max(val, 0.0), 5.0)

class Meal(BaseModel):
    """Dining recommendation (adapted from ch13 Meal model)."""
    type: str = Field(..., description="breakfast/lunch/dinner/snack")
    name: str
    address: str = ""
    location: Location | None = None
    description: str | None = None
    estimated_cost: float = Field(default=0, ge=0)

class Hotel(BaseModel):
    """Accommodation recommendation (adapted from ch13 Hotel model)."""
    name: str
    address: str = ""
    location: Location | None = None
    price_range: str = ""
    rating: float | None = Field(default=None, ge=0, le=5)
    estimated_cost_per_night: float = Field(default=0, ge=0)

# --- Aggregation layer ---

class Budget(BaseModel):
    """Budget breakdown (directly from ch13 Budget model)."""
    total_attractions: float = Field(default=0, ge=0)
    total_hotels: float = Field(default=0, ge=0)
    total_meals: float = Field(default=0, ge=0)
    total_transportation: float = Field(default=0, ge=0)
    total: float = Field(default=0, ge=0)

class WeatherInfo(BaseModel):
    """Weather forecast (adapted from ch13, using Open-Meteo fields)."""
    date: date
    temp_high: float = Field(..., description="Celsius")
    temp_low: float = Field(..., description="Celsius")
    precipitation_prob: float = Field(default=0, ge=0, le=100)
    weather_code: int = Field(default=0, description="WMO code")
    wind_speed: float = Field(default=0, ge=0, description="km/h")

    @property
    def is_rainy(self) -> bool:
        return self.precipitation_prob > 50

    @property
    def description(self) -> str:
        """Map WMO code to human-readable text."""
        codes = {0: "Clear", 1: "Mainly clear", 2: "Partly cloudy",
                 3: "Overcast", 51: "Drizzle", 61: "Rain", 71: "Snow",
                 80: "Showers", 95: "Thunderstorm"}
        return codes.get(self.weather_code, "Unknown")

# --- Plan layer ---

class DayPlan(BaseModel):
    """Single day itinerary (enriched from ch13 DayPlan)."""
    date: date
    day_number: int = Field(..., gt=0)
    description: str = ""
    transportation: str = "walking"
    attractions: list[Attraction] = Field(default_factory=list)
    meals: list[Meal] = Field(default_factory=list)
    hotel: Hotel | None = None

class TripPlan(BaseModel):
    """Complete travel plan (adapted from ch13 TripPlan, without AI-generated fields)."""
    city: str
    start_date: date
    end_date: date
    days: list[DayPlan] = Field(default_factory=list)
    weather: list[WeatherInfo] = Field(default_factory=list)
    budget: Budget | None = None
    suggestions: list[str] = Field(default_factory=list)

# --- Persistence layer ---

class Trip(BaseModel):
    """Persisted trip record."""
    id: str
    city: str
    start_date: date
    end_date: date
    interests: list[str]
    transport_mode: str = "walking"
    plan: TripPlan | None = None
    created_at: datetime
```

**Key differences from ch13:**
- No `overall_suggestions` (LLM-generated in ch13). Replaced with `suggestions: list[str]` computed from weather/budget.
- No `image_url` on Attraction (ch13 uses Unsplash; we skip images for MVP, can add via Wikipedia later).
- Weather uses Open-Meteo fields (WMO codes, precipitation probability) instead of Amap text-based weather.
- Budget is computed algorithmically instead of LLM-estimated.

### 1.4 `api/opentripmap.py` — API Client

Ch13 pattern: singleton service class (`AmapService`) wrapping external API. Ch14 pattern: consistent error handling with empty results + notice on failure.

```python
class OpenTripMapClient:
    """Singleton API client (ch13 AmapService pattern)."""

    async def geoname(self, city: str) -> tuple[float, float]:
        """Get city coordinates. Returns (lat, lon)."""

    async def search_places(
        self, lat: float, lon: float, radius: int, kinds: str | None = None
    ) -> list[Attraction]:
        """Fetch POIs within radius. All responses cached via db/cache.py."""

    async def place_detail(self, xid: str) -> Attraction | None:
        """Get full details for a specific place."""

    async def search_city(
        self, city: str, interests: list[str], radius: int
    ) -> list[Attraction]:
        """High-level: geocode city → search POIs → enrich with details."""
```

**Ch13 lesson on shared instances:** Ch13 Section 13.4.3 shows that multiple agents sharing one MCP instance is better than creating separate ones. Similarly, our `OpenTripMapClient` should be a single instance shared across the pipeline, with built-in caching to respect the 10k/day rate limit.

**Error handling (ch14 pattern):**
```python
async def search_places(self, lat, lon, radius, kinds=None):
    try:
        raw = await self._request("radius", params={...})
        return [self._parse_place(p) for p in raw]
    except httpx.HTTPError as e:
        logger.warning(f"OpenTripMap search failed: {e}")
        return []  # graceful degradation, not crash
```

**Milestone checkpoint:** `tripplanner plan --city Tokyo --dry-run` fetches and prints POIs.

---

## Phase 2: Core Logic

**Milestone:** Generate a valid 3-day itinerary with 8-12 places, optimized routes, budget breakdown.

### 2.1 `logic/scorer.py` — Preference Scorer

From proposal:

```
score = (category_match * 0.4) + (rating_normalized * 0.3) + (popularity * 0.3)
```

- `category_match`: Jaccard similarity between user interests and place `kinds` (comma-separated).
- `rating_normalized`: `rate / 5.0`. Handle missing ratings with dataset mean.
- `popularity`: `otm:popularity` or fallback to number of Wikipedia sources mentioning the place.

### 2.2 `logic/optimizer.py` — Route Optimization

Greedy nearest-neighbor clustering (from proposal):

1. Start from city center (from `geoname`).
2. Pick highest-scored unvisited place as anchor.
3. Greedily add nearest unvisited place within threshold.
4. When day has ~4 places, start new day.
5. Repeat until all top-scored places assigned.

Haversine distance (no paid routing API):

```python
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def estimate_travel_time(distance_km: float, mode: str = "walking") -> int:
    speeds = {"walking": 5, "transit": 25, "driving": 30}
    return int((distance_km / speeds[mode]) * 60)
```

### 2.3 `logic/scheduler.py` — Day Scheduler

Split optimized places into `DayPlan` objects. Ch13's DayPlan includes meals and hotels — we incorporate that richness:

- **Time slots:** morning (9-12), afternoon (13-17), evening (18-21).
- **Visit duration:** 90 min for attractions (configurable), 60 min for restaurants.
- **Travel time:** inserted between consecutive places using `estimate_travel_time()`.
- **Meal placeholders:** if `kinds` contains "restaurants" or "food", insert `Meal` objects for lunch (12:00) and dinner (18:00) at nearby restaurants.
- **Weather-aware (stretch):** if `WeatherInfo.is_rainy`, prefer indoor places (museums, churches) over outdoor ones (parks, viewpoints).

### 2.4 `logic/budget.py` — Budget Calculator

Ch13 computes budget via LLM estimation. We compute it algorithmically:

```python
def calculate_budget(plan: TripPlan, transport_mode: str) -> Budget:
    total_attractions = sum(a.ticket_price for day in plan.days for a in day.attractions)
    total_hotels = sum(h.estimated_cost_per_night for day in plan.days if day.hotel for _ in [1])
    total_meals = sum(m.estimated_cost for day in plan.days for m in day.meals)
    # Transportation: estimate based on city radius and mode
    total_transportation = estimate_transport_cost(plan, transport_mode)
    return Budget(
        total_attractions=total_attractions,
        total_hotels=total_hotels,
        total_meals=total_meals,
        total_transportation=total_transportation,
        total=total_attractions + total_hotels + total_meals + total_transportation,
    )
```

Default cost heuristics when API data is missing:
- Hotel: budget ¥300/night, mid-range ¥600/night, luxury ¥1200/night (or local equivalents).
- Meals: breakfast ¥30, lunch ¥60, dinner ¥80.
- Transport: walking ¥0, transit ¥10/trip, driving ¥50/day (gas/parking).

### 2.5 `core/state.py` — Pipeline State

Ch14's state management pattern adapted for our pipeline:

```python
class TripState:
    """Immutable pipeline state (ch14 pattern)."""
    city: str
    start_date: date
    end_date: date
    interests: list[str]
    transport_mode: str
    city_coords: tuple[float, float] | None = None
    raw_places: list[Attraction] = []       # from API
    scored_places: list[Attraction] = []    # after scorer
    optimized_places: list[Attraction] = [] # after optimizer
    itinerary: TripPlan | None = None       # after scheduler + budget
```

**Milestone checkpoint:** `tripplanner plan --city Paris --days 3 --interests museums,food` generates a valid itinerary internally.

---

## Phase 3: Persistence & Export

**Milestone:** Full CLI workflow: plan → save → list → show → export → delete.

### 3.1 `db/models.py` — SQLAlchemy ORM

```python
class TripRow(Base):
    __tablename__ = "trips"
    id: Mapped[str]                        # UUID primary key
    city: Mapped[str]
    start_date: Mapped[date]
    end_date: Mapped[date]
    interests: Mapped[str]                 # JSON-serialized list
    transport_mode: Mapped[str]            # walking/transit/driving
    plan_json: Mapped[str | None]          # full TripPlan as JSON
    created_at: Mapped[datetime]

class CacheRow(Base):
    __tablename__ = "api_cache"
    key: Mapped[str]                       # hash of URL + params
    response: Mapped[str]                  # JSON response body
    expires_at: Mapped[datetime]
```

Single-table trips design (JSON blob) + separate cache table. Simple, avoids complex joins for MVP.

### 3.2 `db/crud.py` — Database Operations

```python
async def save_trip(trip: Trip) -> str: ...
async def get_trip(trip_id: str) -> Trip | None: ...
async def list_trips(limit: int = 50) -> list[Trip]: ...
async def delete_trip(trip_id: str) -> bool: ...
```

### 3.3 `db/cache.py` — API Response Cache

Avoid redundant OpenTripMap calls (10k/day limit). Ch13 lesson: shared API instance + caching prevents rate limit issues.

```python
async def get_cached(key: str) -> dict | None:
    """Return cached response if not expired."""

async def set_cached(key: str, value: dict, ttl: int = 86400) -> None:
    """Store response with expiry."""
```

### 3.4 `export/` — Multi-Format Exporters

#### `export/markdown.py` — Jinja2 Template

```markdown
# {{ city }} Trip Plan
**{{ start_date }} — {{ end_date }}**

{% if budget %}
## Budget Overview
| Category | Cost |
|----------|------|
| Attractions | {{ budget.total_attractions }} |
| Hotels | {{ budget.total_hotels }} |
| Meals | {{ budget.total_meals }} |
| Transport | {{ budget.total_transportation }} |
| **Total** | **{{ budget.total }}** |
{% endif %}

{% for day in days %}
## Day {{ day.day_number }} — {{ day.date }}
{% if day.weather %}_{{ day.weather.description }}, {{ day.weather.temp_low }}–{{ day.weather.temp_high }}°C_{% endif %}

### Attractions
{% for a in day.attractions %}
{{ loop.index }}. **{{ a.name }}** — {{ a.visit_duration }} min
   {{ a.address }} | Rating: {{ a.rating or "N/A" }}/5
{% endfor %}

{% if day.meals %}
### Meals
{% for m in day.meals %}
- **{{ m.type | title }}**: {{ m.name }} (~{{ m.estimated_cost }})
{% endfor %}
{% endif %}
{% endfor %}
```

#### `export/json_export.py`

Pydantic `.model_dump_json()` with `exclude_none=True`.

#### `export/html_gen.py`

Jinja2 template `itinerary.html.j2` with embedded CSS. Minimal but printable. Includes map placeholder (static image via OpenStreetMap static tiles or simple coordinate list for MVP).

### 3.5 `cli.py` — Full CLI Commands

```
tripplanner plan    --city <city> --dates <start> <end> --interests <tags> [--transport <mode>] [--export <fmt>] [--output <path>]
tripplanner list    [--format table|json]
tripplanner show    <trip-id>
tripplanner export  <trip-id> --format markdown|json|html [--output <path>]
tripplanner delete  <trip-id>
```

**Milestone checkpoint:**

```bash
tripplanner plan --city Tokyo --dates 2026-04-10 2026-04-13 --interests museums,food --export markdown
tripplanner list
tripplanner show <id>
tripplanner export <id> --format html --output tokyo.html
tripplanner delete <id>
```

---

## Phase 4: Polish & Testing

**Milestone:** Demo-ready with 80%+ test coverage, weather integration, optional web frontend.

### 4.1 Rich CLI UX

- Progress spinner during API calls (`rich.progress`).
- Table display for `list` command (`rich.table`).
- Syntax-highlighted markdown preview for `show`.
- Budget summary with colored totals.

### 4.2 Weather Integration (`api/weather.py`) — Stretch

Open-Meteo is free, no auth required:

- Fetch daily forecast for trip date range.
- `WeatherInfo` model already defined in Phase 1.
- In `scheduler.py`: swap outdoor places with indoor ones on rainy days (use `kinds` to classify indoor/outdoor).

### 4.3 Wikipedia Enrichment (`api/wikipedia.py`) — Stretch

- Pull summary for each attraction name.
- Populate `Attraction.description`.
- Use as fallback when OpenTripMap description is missing.

### 4.4 Web Frontend — Stretch

Ch13 demonstrates a full Vue 3 + TypeScript SPA with map visualization, editing, and PDF export. For MVP, we keep it minimal:

**Option A: Jinja2-rendered HTML** (fastest to build)
- FastAPI serves both API endpoints and HTML pages.
- Templates reuse the same Jinja2 templates from `export/`.
- No JavaScript framework, minimal interactivity.

**Option B: Simple Vue SPA** (closer to ch13, better UX)
- Form page → POST to FastAPI → display results.
- Leaflet/OpenStreetMap for map visualization (free, no API key).
- Ant Design Vue for UI components (same as ch13).
- Session storage for trip state (ch13 pattern).

Ch13 Section 13.6 features to consider porting:
- Sidebar navigation with anchor scrolling (ch13 Section 13.6.5).
- Budget display with category breakdown (ch13 Section 13.6.1).
- Edit mode: reorder/delete attractions per day (ch13 Section 13.6.3).
- Export to PNG/PDF via html2canvas + jsPDF (ch13 Section 13.6.4).

### 4.5 Testing Strategy

| Layer | What to Test | How |
|-------|-------------|-----|
| `core/models` | Validators, defaults, constraints | Direct instantiation + edge cases |
| `api/` | HTTP parsing, error handling, caching | Mock httpx with `respx` |
| `logic/scorer` | Score calculation, category matching | Pure unit tests |
| `logic/optimizer` | Route ordering, no backtracking | Assert distance monotonicity |
| `logic/scheduler` | Day splitting, time slot fitting | Assert places fit within day hours |
| `logic/budget` | Cost calculation, heuristics | Known inputs → expected totals |
| `db/` | CRUD, cache TTL | In-memory SQLite via `aiosqlite` |
| `export/` | Template rendering, format correctness | Snapshot tests |
| `cli/` | Full workflow end-to-end | `click.testing.CliRunner` |

### 4.6 Fallback Mechanisms

Ch13 lesson: `_create_fallback_plan()` when agent fails. We adapt this for API failures:

- OpenTripMap returns no results → fall back to top-rated-only search with wider radius.
- Weather API fails → proceed without weather, skip rain-aware scheduling.
- Wikipedia fails → use OpenTripMap description only.
- Any API timeout → return cached data if available, otherwise empty with user-facing notice.

---

## Implementation Order

```
Week 1 — Phase 1 (Foundation)
  Day 1: pyproject.toml, config.py, models.py (all Pydantic models)
  Day 2: cli.py skeleton (plan command only, Rich output)
  Day 3: api/opentripmap.py (geoname + radius + xid + place_detail)
  Day 4: db/cache.py, integrate caching into OpenTripMapClient
  Day 5: End-to-end: tripplanner plan --city Tokyo --dry-run

Week 2 — Phase 2 (Core Logic)
  Day 6: logic/scorer.py + tests
  Day 7: logic/optimizer.py + tests
  Day 8: logic/scheduler.py (with meal/hotel logic) + tests
  Day 9: logic/budget.py + core/state.py, wire full pipeline
  Day 10: End-to-end: generate valid 3-day itinerary with budget

Week 3 — Phase 3 (Persistence & Export)
  Day 11: db/models.py, db/crud.py + tests
  Day 12: export/markdown.py + templates
  Day 13: export/json_export.py, export/html_gen.py + templates
  Day 14: Remaining CLI commands (list, show, export, delete)
  Day 15: End-to-end: full plan → save → list → export → delete workflow

Week 4 — Phase 4 (Polish & Testing)
  Day 16: Rich progress bars, budget tables, color formatting
  Day 17: Stretch: weather integration + rain-aware scheduling
  Day 18: Stretch: Wikipedia enrichment for descriptions
  Day 19: Full test suite, coverage > 80%
  Day 20: Demo prep, README, final polish
```

---

## Key Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project layout | `src/tripplanner/` | Avoids import ambiguity, standard Python packaging |
| Data models | Bottom-up Pydantic (ch13 §13.2) | `Location → Attraction/Meal/Hotel → DayPlan → TripPlan`. Composable, validated. |
| Field validators | `@field_validator` on models | Ch13 shows this for messy API data (coords as strings, ratings out of range) |
| Budget model | Separate `Budget` class + `logic/budget.py` | Ch13 separates budget from itinerary. Algorithmic calculation replaces LLM estimation. |
| Config | `pydantic-settings` + `.env` | Proven in ch13/ch14, type-safe |
| Async | `httpx` async + `aiosqlite` | Proposal requires async I/O, future-proof |
| ORM | SQLAlchemy 2.x async | Standard, well-documented, async support |
| CLI | Click 8.x with Rich | Proposal requirement, Rich for UX |
| Templates | Jinja2 | Proposal requirement, shared between export and web frontend |
| Caching | SQLite with TTL | Respects OpenTripMap 10k/day limit, ch13 lesson on shared instances |
| Route optimization | Greedy nearest-neighbor | Simple, sufficient for MVP (max 20 places) |
| DB schema | Single table + JSON blob | MVP simplicity, avoids premature normalization |
| Frontend | Jinja2-rendered HTML (MVP), Vue SPA (stretch) | Not the focus, can evolve to ch13-style SPA later |
| Fallback | Graceful degradation per-API | Ch13 pattern: always return structured data, never crash |
| Meal/Hotel | Models defined but populated heuristically | Ch13 has rich Meal/Hotel models. We define them now, populate with defaults + API data when available |

---

## What NOT to Copy from Chapter 13

| Ch13 Feature | Why We Skip It |
|-------------|---------------|
| LLM-powered agents (4 specialized agents) | Proposal explicitly forbids AI/LLM in final product |
| MCP tool integration (`MCPTool`, `auto_expand`) | No need for agent-tool protocol without LLM |
| Amap (高德地图) API | Using OpenTripMap (free, global coverage) |
| Unsplash image service | Not in proposal, can add later via Wikipedia |
| `sessionStorage` for persistence | Using SQLite instead |
| Vue 3 SPA for MVP | CLI-first; web frontend is stretch goal |
| Prompt engineering for tool calling | No LLM = no prompts needed |
