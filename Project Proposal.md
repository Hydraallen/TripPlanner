# SI 511 Project Proposal

## What to build - TripPlanner

Basically, I'm planning to build a tool to generate personalized travel guidance based on user preferences, budget, and travel dates. This product aims at independent travelers who want to design their daily plans without spending hours researching online. During vacations, a lot of people choose to travel. Manual trip planning is hard and time-wasting. Travelers must cross-reference multiple sources, like Google Maps, TripAdvisor, and blogs, to build a coherent schedule. In the past, I have experienced the frustration of planning trips across multiple tabs, guessing travel times between locations, and discovering too late that a museum is closed on Mondays. Nowadays, I think with the help of AI and online platforms (including APIs), we should be able to speed up this process and generate a better trip plan.

## Core Features

### viable features

1. **Destination Search & Discovery**

The user should be able to input the city name, and the tool should be able to use the OpenTripMap API to fetch popular attractions, restaurants, and activities. I would expect results to include name, category, rating, coordinates, and a brief description

2. **Preference-Based Filtering**

The user has two ways to specify their interest. The first one would be before the tool requests the OpenTripMap API, the user can offer some brief categories to help the tool narrow down the scope. The tool needs to apply data filtering, data cleaning, and data processing at this moment. The second one should be after the tool finds some results, and the user can choose from them.

3. **Multi-Format Export**

I think the tool should be able to generate different formats of the plan, including markdown, JSON, and HTML. Markdown is for user readability, while the other two are for front-end usage.

4. **Responsive website**

At the early stage of the development, I would have AI mainly work through the terminal, which would be easier for claude code to debug. While there still should be a front-end webpage, where users can click on multiple choices. This would be much more user-friendly than purally in a terminal.

5. **Data Persistence**

All generated data should be saved to the local SQLite database. Users can list, view, edit, and delete saved trips. It can also help to reduce repetitive searching for the same thing.

### Stretch Goals

1. **Weather Integration**
   - Fetch weather forecast via Open-Meteo API
   - Suggest indoor activities on rainy days, and outdoor on sunny days
   - Display weather icons in the generated report
2. **PDF Export**
   - Generate a printable PDF with map screenshots or links
3. **Wikipedia**
   - Pull detailed descriptions from the Wikipedia API for each attraction
   - Include historical context and practical tips
4. **Multi-City Trip Support**
   - Plan routes spanning multiple cities
   - Estimate transportation time between cities
5. **Offline Mode**
   - Full offline capability using cached data
   - Sync when the internet is available

## Timeline

### Week 1: Prototype

**Goals:**

- Set up project structure and development environment
- Implement API clients with error handling and caching
- Design and create a SQLite database schema

**Milestone:** Successfully query and store attractions for a test city

---

### Week 2: Core Features

**Goals:**

- Build a preference scoring system
- Implement the route optimization algorithm
- Create day-by-day scheduler

**Milestone:** Generate a valid 3-day itinerary for a test city with 8-12 places, optimized routes

---

### Week 3: Testing and Polish

**Goals:**

- Implement all export formatters
- Polish experience and error handling

**Milestone:** Complete end-to-end workflow: input → generate → export → view

---

### Week 4: Final Demo

**Goals:**

- Comprehensive test coverage
- Prepare demo materials

**Milestone:** Demo-ready project with clear documentation







## 3. Technical Requirements

### Skills Required

| Skill | Purpose | My Current Level | How to Improve |
|-------|---------|------------------|----------------|
| **Python 3.11+** | Core language | Intermediate | Review async/await, type hints |
| **CLI Design (Click)** | Command-line interface | Beginner | Click documentation, examples |
| **REST API Integration** | Fetch data from external APIs | Intermediate | Practice with httpx, handle pagination/errors |
| **SQL/SQLite** | Data persistence | Beginner | SQLAlchemy ORM tutorial |
| **Algorithm Design** | Route optimization, scoring | Intermediate | Research clustering algorithms, TSP heuristics |
| **Templating (Jinja2)** | Generate formatted output | Beginner | Jinja2 docs, template inheritance |
| **Testing (pytest)** | Unit and integration tests | Beginner | pytest tutorial, mocking API calls |

### Tools & Libraries

| Tool/Library | Purpose | Version |
|--------------|---------|---------|
| **Python** | Core language | 3.11+ |
| **Click** | CLI framework with subcommands | 8.x |
| **httpx** | Async HTTP client for API calls | 0.27+ |
| **SQLAlchemy** | ORM for SQLite database | 2.x |
| **Pydantic** | Data validation and settings | 2.x |
| **Jinja2** | Template engine for exports | 3.x |
| **Rich** | Pretty CLI output, progress bars | 13.x |
| **python-dotenv** | Environment variables management | 1.x |
| **pytest** | Testing framework | 8.x |
| **pytest-asyncio** | Async test support | 0.23+ |

### External APIs (All Free)

| API | What It Provides | Free Tier Limits | Documentation |
|-----|------------------|------------------|---------------|
| **OpenTripMap** | Attractions, POIs, categories, ratings | 10,000 requests/day | https://opentripmap.io/docs |
| **Open-Meteo** | Weather forecast (7-day) | Unlimited | https://open-meteo.com/en/docs |
| **Wikipedia API** | Article summaries, images | Unlimited | https://api.wikimedia.org |

### Project Structure

```
tripplanner/
├── __init__.py
├── cli.py              # Click CLI entry point
├── core/
│   ├── __init__.py
│   ├── models.py       # Pydantic models (Trip, Place, Itinerary)
│   ├── state.py        # Shared TripState across pipeline
│   └── config.py       # Configuration management
├── api/
│   ├── __init__.py
│   ├── opentripmap.py  # OpenTripMap client
│   ├── weather.py      # Open-Meteo client
│   └── wikipedia.py    # Wikipedia client
├── logic/
│   ├── __init__.py
│   ├── scorer.py       # Preference-based place scoring
│   ├── scheduler.py    # Day-by-day time slot allocation
│   └── optimizer.py    # Route optimization algorithms
├── db/
│   ├── __init__.py
│   ├── models.py       # SQLAlchemy models
│   ├── crud.py         # Database operations
│   └── cache.py        # API response caching
├── export/
│   ├── __init__.py
│   ├── markdown.py     # Markdown formatter
│   ├── json_export.py  # JSON formatter
│   ├── html_gen.py     # HTML generator
│   └── templates/      # Jinja2 templates
│       ├── itinerary.md.j2
│       ├── itinerary.html.j2
│       └── styles.css
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_logic.py
    └── test_export.py
```

---



---

## 5. Open Questions & Risks

### Open Questions

1. **Route Optimization Algorithm**
   - **Question:** Should I implement a proper TSP solver, or is greedy nearest-neighbor sufficient?
   - **Current Thinking:** Start with greedy clustering (group places by geographic proximity, then solve within cluster). If time permits, explore 2-opt improvement.

2. **Time Estimation Accuracy**
   - **Question:** How to estimate realistic travel times without a paid routing API?
   - **Options:**
     - Haversine distance + average walking/transit speeds (simpler, less accurate)
     - OSRM API (free self-hosted, more complex setup)
   - **Current Thinking:** Use haversine + heuristic speeds for MVP, note as limitation

3. **Opening Hours Data**
   - **Question:** OpenTripMap doesn't reliably include opening hours. Should I attempt to scrape or skip?
   - **Current Thinking:** Skip for MVP, add as stretch goal if data found

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OpenTripMap API rate limits hit | Medium | High | Aggressive caching, batch requests, local cache first |
| Route optimization too slow | Low | Medium | Pre-compute distance matrix, limit places per trip to 20 |
| Incomplete/low-quality POI data | Medium | Medium | Fall back to top-rated only, allow manual place addition |
| Scope creep on stretch features | High | Medium | Strict MVP focus, only add stretch after core is solid |

---

## 6. Success Criteria

### MVP Success (Must Have)
- [ ] User can input a city and get a valid 3-day itinerary
- [ ] Itinerary includes 8-12 relevant places based on preferences
- [ ] Routes are geographically optimized (no obvious backtracking)
- [ ] Itinerary can be exported as Markdown and viewed
- [ ] Trip is saved to database and can be retrieved later

### Stretch Success (Nice to Have)
- [ ] Weather integration with indoor/outdoor suggestions
- [ ] PDF export with embedded maps
- [ ] Multi-city trip support
- [ ] 80%+ test coverage
- [ ] Published to PyPI (installable via pip)

---

## 7. Demo Plan

**Demo Flow (5 minutes):**

1. **Introduction (30s)**
   - Problem statement: manual trip planning is tedious
   - Solution: TripPlanner automates the research and scheduling

2. **Live Demo (3 min)**
   - Run `tripplanner plan --city "Paris" --dates "2026-04-10 to 2026-04-13" --interests museums,food`
   - Show interactive prompts and progress bars
   - Display generated itinerary in terminal
   - Export to HTML and open in browser

3. **Technical Highlights (1 min)**
   - API integration: how data flows from OpenTripMap
   - Route optimization: before/after comparison
   - Code walkthrough: modular architecture

4. **Q&A (30s)**
   - Address questions about limitations, future work

---

## 8. AI Development Prompt

Use this prompt when working with AI assistants (GPT-4o, Claude Code, etc.) to build TripPlanner:

---

```
You are helping me build TripPlanner, a Python CLI tool that generates personalized travel itineraries.

## Project Overview

TripPlanner is a command-line application that:
1. Fetches attractions/restaurants from OpenTripMap API (free tier)
2. Filters and scores places based on user preferences (categories, budget)
3. Optimizes routes using geographic clustering to minimize travel time
4. Generates day-by-day itineraries with time slot allocation
5. Persists trips to SQLite database
6. Exports to Markdown, JSON, and HTML formats

## Technical Stack

- **Language:** Python 3.11+
- **CLI:** Click 8.x (subcommands: plan, list, export, delete)
- **HTTP Client:** httpx (async support)
- **Database:** SQLite + SQLAlchemy 2.x ORM
- **Validation:** Pydantic 2.x
- **Templates:** Jinja2 3.x
- **CLI UX:** Rich 13.x (progress bars, colors)
- **Testing:** pytest + pytest-asyncio

## External APIs (All Free)

1. **OpenTripMap** (https://opentripmap.io/docs)
   - Endpoint: `https://api.opentripmap.com/0.1/en/places/`
   - Key endpoints: geoname (city search), radius (places nearby), xid (details)
   - Rate limit: 10,000 requests/day
   - Cache all responses in SQLite

2. **Open-Meteo** (https://open-meteo.com/en/docs) [Stretch]
   - Endpoint: `https://api.open-meteo.com/v1/forecast`
   - No authentication required, unlimited

3. **Wikipedia API** [Stretch]
   - For enriching place descriptions

## Project Structure

```
tripplanner/
├── cli.py              # Click entry point
├── core/
│   ├── models.py       # Pydantic: Trip, Place, Itinerary, DayPlan
│   ├── state.py        # Shared TripState object
│   └── config.py       # Settings via pydantic-settings
├── api/
│   ├── opentripmap.py  # API client with caching
│   ├── weather.py      # Open-Meteo client
│   └── wikipedia.py    # Wikipedia client
├── logic/
│   ├── scorer.py       # Preference scoring
│   ├── scheduler.py    # Time slot allocation
│   └── optimizer.py    # Route optimization (greedy clustering)
├── db/
│   ├── models.py       # SQLAlchemy ORM models
│   ├── crud.py         # Database operations
│   └── cache.py        # API response cache
├── export/
│   ├── markdown.py     # Markdown formatter
│   ├── json_export.py  # JSON formatter
│   ├── html_gen.py     # HTML generator
│   └── templates/      # Jinja2 templates
└── tests/              # pytest tests
```

## Code Style Requirements

1. **Type hints everywhere** - All functions must have type annotations
2. **Pydantic for data** - Use Pydantic models for all data structures
3. **Async for I/O** - Use async/await for all API calls and database operations
4. **Error handling** - Graceful degradation, never crash on API failures
5. **Logging** - Use Python logging module, not print()
6. **Docstrings** - Google-style docstrings for public functions
7. **No magic numbers** - Constants in config.py or as Pydantic settings

## Example Code Style

```python
from typing import Optional
from pydantic import BaseModel

class Place(BaseModel):
    """A tourist attraction or point of interest."""
    xid: str
    name: str
    lat: float
    lon: float
    categories: list[str]
    rating: Optional[float] = None
    description: Optional[str] = None

async def fetch_places(city: str, radius: int = 1000) -> list[Place]:
    """
    Fetch places near a city center from OpenTripMap API.

    Args:
        city: City name to search
        radius: Search radius in meters (default: 1000)

    Returns:
        List of Place objects sorted by rating

    Raises:
        APIError: If the API request fails after retries
    """
    ...
```

## Development Priorities

### Phase 1: Foundation (Week 1)
1. Set up project structure with pyproject.toml
2. Implement OpenTripMap client with caching
3. Create SQLite schema
4. Build Click CLI skeleton

### Phase 2: Core Logic (Week 2)
1. Implement preference scorer (category matching + rating)
2. Build route optimizer (greedy nearest-neighbor)
3. Create day scheduler (morning/afternoon/evening slots)

### Phase 3: Export & Polish (Week 3)
1. Markdown/JSON/HTML export formatters
2. Rich CLI output (progress bars, colors)
3. Weather API integration (stretch)

### Phase 4: Testing & Docs (Week 4)
1. Unit tests with pytest (mock API responses)
2. Integration tests for CLI workflow
3. README with usage examples
4. Demo preparation

## Key Algorithms

### 1. Preference Scoring
```
score = (category_match * 0.4) + (rating_normalized * 0.3) + (popularity * 0.3)
```

### 2. Route Optimization (Greedy Clustering)
1. Start from user's hotel/center point
2. Find nearest unvisited place
3. Mark as visited, add to current day
4. Repeat until day has ~4 places
5. Start new day, repeat until all places assigned

### 3. Time Estimation (Haversine)
```python
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Calculate distance in km between two points."""
    R = 6371  # Earth radius in km
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def estimate_travel_time(distance_km: float, mode: str = "walking") -> int:
    """Estimate travel time in minutes."""
    speeds = {"walking": 5, "transit": 25, "driving": 30}  # km/h
    return int((distance_km / speeds[mode]) * 60)
```

## When You Get Stuck

1. **API issues?** Check rate limits, verify endpoint URLs, add caching
2. **Algorithm too complex?** Start with simpler version (e.g., random assignment), then optimize
3. **Type errors?** Run mypy, check Pydantic model compatibility
4. **Tests failing?** Mock external APIs, use pytest fixtures for database

## Constraints

- NO paid APIs (only free tiers)
- NO AI/LLM APIs in the final product
- Maximum 20 places per trip (for performance)
- Single-user CLI tool (no authentication needed)

## Success Criteria

- User can run: `tripplanner plan --city Tokyo --days 3 --interests museums,food`
- Output: Valid Markdown itinerary with 8-12 places, geographically optimized
- Trip saved to SQLite, can be retrieved with `tripplanner list`

---

When I ask you to implement a feature, start by:
1. Showing the file path you're creating/editing
2. Explaining your approach briefly
3. Writing clean, typed Python code
4. Including error handling and logging
5. Adding docstrings to public functions
```

---

*Proposal Version: 1.1*
*Last Updated: 2026-03-17*
