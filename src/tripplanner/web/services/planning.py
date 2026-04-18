from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from tripplanner.api.amap import AmapClient
from tripplanner.api.opentripmap import OpenTripMapClient
from tripplanner.api.weather import WeatherClient
from tripplanner.core.config import get_settings
from tripplanner.core.models import (
    Attraction,
    GenerationProgress,
    TripPlan,
    WeatherInfo,
)
from tripplanner.db.crud import (
    create_trip_draft,
    save_generated_plans,
    update_trip_progress,
)
from tripplanner.web.services.llm import LLMClient
from tripplanner.web.services.plan_generator import PlanGenerator
from tripplanner.web.services.plan_scorer import score_plans
from tripplanner.web.services.progress import progress_tracker
from tripplanner.web.services.region import is_chinese_destination

logger = logging.getLogger(__name__)


async def generate_plan(
    city: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    transport_mode: str = "walking",
    radius: int | None = None,
) -> TripPlan | None:
    """Generate a single travel plan with smart API routing.

    Detects region → dispatches to Amap or Overpass API → runs
    existing logic pipeline (scorer → optimizer → scheduler → budget)
    → attaches weather data → returns TripPlan.
    """
    settings = get_settings()
    search_radius = radius or settings.default_search_radius
    num_days = (end_date - start_date).days + 1

    if num_days <= 0:
        return None

    lat: float = 0.0
    lon: float = 0.0
    places: list[Attraction] = []

    if is_chinese_destination(city):
        places, coords = await _fetch_chinese(city, interests, search_radius, settings)
    else:
        places, coords = await _fetch_international(city, interests, search_radius, settings)

    if not places or not coords:
        logger.warning("No places found for city: %s", city)
        return None

    lat, lon = coords

    from tripplanner.logic.budget import calculate_budget
    from tripplanner.logic.optimizer import optimize_routes
    from tripplanner.logic.scheduler import build_itinerary
    from tripplanner.logic.scorer import compute_scores

    scored = compute_scores(places, interests)
    clusters = optimize_routes(
        scored, center=(lat, lon), num_days=num_days, transport_mode=transport_mode
    )
    itinerary = build_itinerary(clusters, start_date, end_date, transport_mode)
    itinerary.city = city
    budget = calculate_budget(itinerary, transport_mode)
    itinerary.budget = budget

    async with WeatherClient(settings) as weather_client:
        weather = await weather_client.get_forecast(lat, lon, start_date, end_date)
    itinerary.weather = weather

    return itinerary


async def generate_multi_plan(
    city: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    transport_mode: str = "walking",
    budget: float | None = None,
    radius: int | None = None,
    session: AsyncSession | None = None,
) -> str:
    """Orchestrate multi-plan generation with progress tracking.

    Returns the trip_id immediately. Generation runs synchronously —
    the caller should run this in a background task.

    Data flow:
    1. Create trip draft (returns trip_id)
    2. Collect data: geocode → POIs → weather (progress: 0-30%)
    3. Generate 3 plans via LLM (progress: 30-90%)
    4. Score and save (progress: 90-100%)
    """
    settings = get_settings()
    search_radius = radius or settings.default_search_radius
    num_days = (end_date - start_date).days + 1

    if num_days <= 0:
        raise ValueError("End date must be after start date")

    # Create draft trip
    if session is None:
        from tripplanner.db.crud import init_db

        factory = await init_db(settings.database_url)
        async with factory() as sess:
            return await generate_multi_plan(
                city=city,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                transport_mode=transport_mode,
                budget=budget,
                radius=search_radius,
                session=sess,
            )

    trip_id = await create_trip_draft(
        session, city, start_date, end_date, interests, transport_mode, budget
    )

    # Progress helper
    def _progress(status: str, pct: float, step: str) -> GenerationProgress:
        p = GenerationProgress(plan_id=trip_id, status=status, progress=pct, step=step)
        progress_tracker.update(p)
        if session:
            import asyncio

            asyncio.create_task(update_trip_progress(session, trip_id, p))
        return p

    try:
        # Phase 1: Collect data (0-30%)
        _progress("collecting", 5, "Geocoding city...")

        lat: float = 0.0
        lon: float = 0.0
        places: list[Attraction] = []

        if is_chinese_destination(city):
            places, coords = await _fetch_chinese(city, interests, search_radius, settings)
        else:
            places, coords = await _fetch_international(city, interests, search_radius, settings)

        if not coords:
            _progress("failed", 0, f"Could not find city: {city}")
            return trip_id

        lat, lon = coords
        _progress("collecting", 20, f"Found {len(places)} places in {city}")

        # Fetch weather
        _progress("collecting", 25, "Fetching weather forecast...")
        weather: list[WeatherInfo] = []
        async with WeatherClient(settings) as weather_client:
            weather = await weather_client.get_forecast(lat, lon, start_date, end_date)

        _progress(
            "collecting", 30,
            f"Data collected: {len(places)} places, {len(weather)} days weather",
        )

        # Phase 2: Generate 3 plans (30-90%)
        llm_client = LLMClient(settings) if settings.openai_api_key else None
        generator = PlanGenerator(llm=llm_client)

        alternatives = await generator.generate_alternatives(
            city=city,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            transport_mode=transport_mode,
            places=places,
            weather=weather,
            on_progress=lambda p: _progress(p.status, p.progress, p.step),
        )

        if not alternatives:
            _progress("failed", 0, "Could not generate any plans")
            return trip_id

        # Phase 3: Score and save (90-100%)
        _progress("scoring", 92, "Scoring and ranking plans...")
        alternatives = score_plans(alternatives)

        _progress("scoring", 98, "Saving plans...")
        await save_generated_plans(session, trip_id, alternatives)

        progress_tracker.complete(trip_id)

    except Exception as e:
        logger.error("Multi-plan generation failed: %s", e, exc_info=True)
        _progress("failed", 0, f"Generation failed: {e}")

    return trip_id


async def _fetch_chinese(
    city: str, interests: list[str], radius: int, settings: object
) -> tuple[list[Attraction], tuple[float, float] | None]:
    """Fetch places from Amap for Chinese destinations."""
    from tripplanner.core.config import Settings

    s = settings if isinstance(settings, Settings) else get_settings()

    async with AmapClient(s) as client:
        coords = await client.geocode(city)
        if not coords:
            return [], None
        places = await client.search_city(city, interests, radius)
    return places, coords


async def _fetch_international(
    city: str, interests: list[str], radius: int, settings: object
) -> tuple[list[Attraction], tuple[float, float] | None]:
    """Fetch places from Overpass API (OSM) for international destinations."""
    from tripplanner.core.config import Settings

    s = settings if isinstance(settings, Settings) else get_settings()

    async with OpenTripMapClient(s) as client:
        coords = await client.geoname(city)
        if not coords:
            return [], None
        places = await client.search_city(city, interests, radius)
    return places, coords
