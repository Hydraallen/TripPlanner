from __future__ import annotations

import logging
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import Attraction, Location

logger = logging.getLogger(__name__)


class AmapClient:
    """Async client for the Amap (Gaode) REST API.

    Used for Chinese destinations. Requires amap_api_key in settings.
    API docs: https://lbs.amap.com/api/webservice/guide/api
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.amap_base_url,
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AmapClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    @property
    def _key(self) -> str:
        return self._settings.amap_api_key

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        merged = {"key": self._key, **(params or {})}
        try:
            resp = await self._client.get(path, params=merged)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1":
                return data
            logger.warning("Amap API error: %s", data.get("info", "unknown"))
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("Amap %s returned %s", path, e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("Amap request failed: %s", e)
            return None

    async def geocode(self, city: str) -> tuple[float, float] | None:
        """Get city coordinates. Returns (lat, lon) or None."""
        data = await self._get("/v3/geocode/geo", {"address": city})
        if not data:
            return None
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return None
        location = geocodes[0].get("location", "")
        if not location:
            return None
        parts = location.split(",")
        if len(parts) != 2:
            return None
        return (float(parts[1]), float(parts[0]))  # (lat, lon)

    async def search_pois(
        self,
        lat: float,
        lon: float,
        keywords: str | None = None,
        radius: int = 10000,
        limit: int = 20,
    ) -> list[Attraction]:
        """Search POIs around a location. Returns list of Attraction models."""
        params: dict[str, Any] = {
            "location": f"{lon},{lat}",
            "radius": radius,
            "offset": limit,
        }
        if keywords:
            params["keywords"] = keywords

        data = await self._get("/v3/place/around", params)
        if not data:
            return []

        pois = data.get("pois", [])
        results: list[Attraction] = []
        for poi in pois:
            parsed = self._parse_poi(poi)
            if parsed:
                results.append(parsed)
        return results

    async def get_weather(self, city: str) -> list[dict[str, Any]]:
        """Get weather for a city. Returns list of weather data dicts."""
        data = await self._get("/v3/weather/weatherInfo", {"city": city, "extensions": "all"})
        if not data:
            return []
        return data.get("forecasts", [])

    async def search_city(
        self,
        city: str,
        interests: list[str],
        radius: int | None = None,
    ) -> list[Attraction]:
        """High-level: geocode city → search POIs."""
        radius = radius or self._settings.default_search_radius
        coords = await self.geocode(city)
        if not coords:
            return []

        lat, lon = coords
        keywords = ",".join(interests) if interests else None
        return await self.search_pois(lat, lon, keywords, radius, self._settings.max_places_per_trip)

    def _parse_poi(self, poi: dict[str, Any]) -> Attraction | None:
        """Parse a POI from Amap response."""
        try:
            location = poi.get("location", "")
            if not location:
                return None
            parts = location.split(",")
            if len(parts) != 2:
                return None

            return Attraction(
                xid=poi.get("id", ""),
                name=poi.get("name", "Unknown"),
                address=poi.get("address", "") or poi.get("pname", ""),
                location=Location(longitude=float(parts[0]), latitude=float(parts[1])),
                categories=[poi.get("type", "")],
                kinds=poi.get("type", ""),
                rating=float(poi.get("rating", 0)) if poi.get("rating") else None,
            )
        except Exception:
            logger.debug("Skipping malformed POI: %s", poi.get("id"))
            return None
