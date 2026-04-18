from __future__ import annotations

import logging
from datetime import date

from tripplanner.api.amap import AmapClient
from tripplanner.api.opentripmap import OpenTripMapClient
from tripplanner.api.weather import WeatherClient
from tripplanner.core.config import get_settings
from tripplanner.core.models import Attraction, TripPlan
from tripplanner.logic.budget import calculate_budget
from tripplanner.logic.optimizer import optimize_routes
from tripplanner.logic.scheduler import build_itinerary
from tripplanner.logic.scorer import compute_scores
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
    """Generate a travel plan with smart API routing.

    Detects region → dispatches to Amap or Overpass API → runs
    existing logic pipeline (scorer → optimizer → scheduler → budget)
    → attaches weather data → returns TripPlan.
    """
    settings = get_settings()
    search_radius = radius or settings.default_search_radius
    num_days = (end_date - start_date).days + 1

    if num_days <= 0:
        return None

    # Step 1: Fetch places based on region
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

    # Step 2: Score and filter places
    scored = compute_scores(places, interests)

    # Step 3: Optimize routes by day
    clusters = optimize_routes(
        scored,
        center=(lat, lon),
        num_days=num_days,
        transport_mode=transport_mode,
    )

    # Step 4: Build day-by-day itinerary
    itinerary = build_itinerary(clusters, start_date, end_date, transport_mode)
    itinerary.city = city

    # Step 5: Calculate budget
    budget = calculate_budget(itinerary, transport_mode)
    itinerary.budget = budget

    # Step 6: Fetch weather data
    async with WeatherClient(settings) as weather_client:
        weather = await weather_client.get_forecast(lat, lon, start_date, end_date)
    itinerary.weather = weather

    return itinerary


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
