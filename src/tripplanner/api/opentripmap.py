from __future__ import annotations

import logging
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import Attraction, Location

logger = logging.getLogger(__name__)


class OpenTripMapClient:
    """Async client for the OpenTripMap API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.opentripmap_base_url,
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OpenTripMapClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _api_key_param(self) -> dict[str, str]:
        if not self._settings.opentripmap_api_key:
            logger.warning("OPENTRIPMAP_API_KEY not configured — some endpoints may fail")
            return {}
        return {"apikey": self._settings.opentripmap_api_key}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        merged = {**self._api_key_param(), **(params or {})}
        try:
            resp = await self._client.get(path, params=merged)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("OpenTripMap %s returned %s", path, e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("OpenTripMap request failed: %s", e)
            return None

    async def geoname(self, city: str) -> tuple[float, float] | None:
        """Get city coordinates. Returns (lat, lon) or None."""
        data = await self._get("/places/geoname", {"name": city})
        if data and isinstance(data, dict) and "lat" in data and "lon" in data:
            return (float(data["lat"]), float(data["lon"]))
        logger.warning("Geoname failed for city: %s", city)
        return None

    async def search_places(
        self,
        lat: float,
        lon: float,
        radius: int,
        kinds: str | None = None,
        limit: int = 100,
    ) -> list[Attraction]:
        """Fetch POIs within radius. Returns list of basic Attraction models."""
        params: dict[str, Any] = {
            "radius": radius,
            "lat": lat,
            "lon": lon,
            "limit": limit,
            "format": "json",
        }
        if kinds:
            params["kinds"] = kinds

        data = await self._get("/places/radius", params)
        if not data or not isinstance(data, list):
            return []

        places: list[Attraction] = []
        for item in data:
            parsed = self._parse_place_summary(item)
            if parsed:
                places.append(parsed)
        return places

    async def place_detail(self, xid: str) -> Attraction | None:
        """Get full details for a specific place."""
        data = await self._get(f"/places/xid/{xid}")
        if not data or not isinstance(data, dict):
            return None
        return self._parse_place_detail(data)

    async def search_city(
        self,
        city: str,
        interests: list[str],
        radius: int | None = None,
    ) -> list[Attraction]:
        """High-level: geocode city → search POIs → enrich with details."""
        radius = radius or self._settings.default_search_radius
        coords = await self.geoname(city)
        if not coords:
            return []

        lat, lon = coords
        kinds = ",".join(interests) if interests else None
        places = await self.search_places(lat, lon, radius, kinds)

        enriched: list[Attraction] = []
        for place in places[: self._settings.max_places_per_trip]:
            detail = await self.place_detail(place.xid)
            enriched.append(detail if detail else place)

        return enriched

    def _parse_place_summary(self, item: dict[str, Any]) -> Attraction | None:
        """Parse a place from radius search results."""
        try:
            return Attraction(
                xid=item.get("xid", ""),
                name=item.get("name", "Unknown"),
                location=Location(
                    longitude=item.get("point", {}).get("lon", 0),
                    latitude=item.get("point", {}).get("lat", 0),
                ),
                kinds=item.get("kinds", ""),
            )
        except Exception:
            logger.debug("Skipping malformed place: %s", item.get("xid"))
            return None

    def _parse_place_detail(self, data: dict[str, Any]) -> Attraction | None:
        """Parse a place from xid detail response."""
        try:
            loc_data = data.get("point", {})
            return Attraction(
                xid=data.get("xid", ""),
                name=data.get("name", "Unknown"),
                address=data.get("address", {}).get("road", "") or data.get("address", {}).get(
                    "city", ""
                ),
                location=Location(
                    longitude=loc_data.get("lon", 0),
                    latitude=loc_data.get("lat", 0),
                ),
                kinds=data.get("kinds", ""),
                description=data.get("info", {}).get("descr", None),
                rating=data.get("rate"),
                ticket_price=float(
                    data.get("info", {}).get("price", 0)
                    if isinstance(data.get("info", {}).get("price"), int | float)
                    else 0
                ),
            )
        except Exception:
            logger.debug("Skipping malformed detail: %s", data.get("xid"))
            return None
