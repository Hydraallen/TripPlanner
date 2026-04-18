from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import Attraction, Location

logger = logging.getLogger(__name__)

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
OVERPASS_BASE = "https://overpass.private.coffee/api/interpreter"

# Map interest keywords to OSM Overpass QL tag selectors.
# Uses "nw" (node+way) and "nwr" (node+way+relation) type filters
# to halve query fragment count vs separate node/way entries.
_INTEREST_TO_OVERPASS: dict[str, list[str]] = {
    # --- Default / general ---
    # Curated for high-quality, notable attractions.
    # artwork/memorial excluded from default — too many minor entries.
    # Use "art" or "architecture" interests for those.
    "interesting_places": [
        'nwr["tourism"="attraction"]',
        'node["tourism"="viewpoint"]',
        'nw["tourism"="museum"]',
        'nw["tourism"="gallery"]',
        'node["tourism"="zoo"]',
        'way["leisure"="park"]',
        'way["leisure"="garden"]',
        'nw["historic"="monument"]',
        'nw["historic"="castle"]',
        'nw["historic"="fort"]',
        'nw["historic"="ship"]',
        'nw["amenity"="theatre"]',
        'nw["amenity"="library"]',
        'nw["building"="palace"]',
    ],
    # --- Thematic interests ---
    "museums": [
        'nw["tourism"="museum"]',
        'nw["amenity"="arts_centre"]',
    ],
    "architecture": [
        'nw["building"="cathedral"]',
        'nw["building"="chapel"]',
        'nw["building"="palace"]',
        'nw["building"="castle"]',
        'nw["building"="church"]',
        'nw["historic"="monument"]',
        'nw["historic"="memorial"]',
        'nw["historic"="archaeological_site"]',
        'nw["historic"="castle"]',
        'nw["historic"="ruins"]',
    ],
    "temples": [
        'nw["amenity"="place_of_worship"]',
    ],
    "religion": [
        'nw["amenity"="place_of_worship"]',
    ],
    "towers": [
        'nw["tower"="observation"]',
        'node["tourism"="viewpoint"]',
    ],
    "nature": [
        'nw["leisure"="park"]',
        'node["natural"="peak"]',
        'nw["natural"="wood"]',
        'nw["natural"="water"]',
        'nw["leisure"="nature_reserve"]',
        'node["tourism"="zoo"]',
    ],
    "parks": [
        'nw["leisure"="park"]',
        'nw["leisure"="garden"]',
        'nw["natural"="wood"]',
        'nw["leisure"="nature_reserve"]',
    ],
    "food": [
        'nw["amenity"="restaurant"]',
        'nw["amenity"="cafe"]',
        'node["amenity"="bar"]',
        'node["amenity"="pub"]',
        'node["amenity"="fast_food"]',
    ],
    "beaches": [
        'nw["natural"="beach"]',
    ],
    "shopping": [
        'nw["shop"="mall"]',
    ],
    "theatres": [
        'nw["amenity"="theatre"]',
    ],
    "gardens": [
        'nw["leisure"="garden"]',
    ],
    "fortifications": [
        'nw["historic"="castle"]',
    ],
    "art": [
        'nw["tourism"="gallery"]',
        'nw["tourism"="artwork"]',
        'nw["amenity"="arts_centre"]',
    ],
    "nightlife": [
        'node["amenity"="bar"]',
        'node["amenity"="pub"]',
        'node["amenity"="nightclub"]',
    ],
    "entertainment": [
        'nw["amenity"="cinema"]',
        'nw["amenity"="theatre"]',
        'node["amenity"="nightclub"]',
        'nw["leisure"="sports_centre"]',
    ],
}


class OpenTripMapClient:
    """Async client using Overpass API (OSM) + Nominatim for geocoding.

    Drop-in replacement for the original OpenTripMap client.
    No API key required — both services are free.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(timeout=45.0)
        self._nominatim = httpx.AsyncClient(
            base_url=NOMINATIM_BASE,
            timeout=10.0,
            headers={"User-Agent": "TripPlanner/0.1"},
        )

    async def close(self) -> None:
        await self._client.aclose()
        await self._nominatim.aclose()

    async def __aenter__(self) -> OpenTripMapClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _api_key_param(self) -> dict[str, str]:
        return {}

    async def geoname(self, city: str) -> tuple[float, float] | None:
        """Get city coordinates via Nominatim. Returns (lat, lon) or None."""
        try:
            resp = await self._nominatim.get(
                "/search",
                params={"q": city, "format": "json", "limit": 1},
            )
            resp.raise_for_status()
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0:
                return (float(data[0]["lat"]), float(data[0]["lon"]))
        except Exception as e:
            logger.warning("Nominatim geocoding failed for '%s': %s", city, e)
        return None

    async def search_places(
        self,
        lat: float,
        lon: float,
        radius: int,
        kinds: str | None = None,
        limit: int = 100,
    ) -> list[Attraction]:
        """Fetch POIs within radius using Overpass API.

        Splits large query sets into batches to avoid Overpass timeouts.
        """
        interest_list = kinds.split(",") if kinds else ["interesting_places"]
        queries = self._build_overpass_queries(lat, lon, radius, interest_list)

        if not queries:
            return []

        # Split into batches of ~8 query fragments to avoid Overpass timeouts
        batch_size = 8
        batches = [
            queries[i : i + batch_size]
            for i in range(0, len(queries), batch_size)
        ]

        seen_ids: set[str] = set()
        places: list[Attraction] = []

        for i, batch in enumerate(batches):
            # Delay between batches to avoid Overpass rate limits
            if i > 0:
                await asyncio.sleep(1.5)
            query = self._combine_queries(batch, limit)
            if not query:
                continue
            try:
                resp = await self._client.post(
                    OVERPASS_BASE,
                    data={"data": query},
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("Overpass API request failed: %s", e)
                continue

            for elem in data.get("elements", []):
                parsed = self._parse_element(elem)
                if parsed and parsed.xid not in seen_ids:
                    seen_ids.add(parsed.xid)
                    places.append(parsed)

        return places

    async def place_detail(self, xid: str) -> Attraction | None:
        """Get details for a place by re-querying Overpass.

        Since Overpass returns full data in bulk, this is a no-op
        that returns None — callers should use the data from search_places.
        """
        return None

    async def search_city(
        self,
        city: str,
        interests: list[str],
        radius: int | None = None,
    ) -> list[Attraction]:
        """High-level: geocode city → search POIs via Overpass."""
        radius = radius or self._settings.default_search_radius
        coords = await self.geoname(city)
        if not coords:
            return []

        lat, lon = coords
        kinds = ",".join(interests) if interests else None
        places = await self.search_places(lat, lon, radius, kinds)
        return places[: self._settings.max_places_per_trip]

    def _build_overpass_queries(
        self, lat: float, lon: float, radius: int, interests: list[str]
    ) -> list[str]:
        """Build Overpass QL query fragments for given interests."""
        queries: list[str] = []
        seen: set[str] = set()
        for interest in interests:
            tag_queries = _INTEREST_TO_OVERPASS.get(interest)
            if not tag_queries:
                tag_queries = _INTEREST_TO_OVERPASS.get("interesting_places", [])
            for tag_query in tag_queries:
                fragment = f"{tag_query}(around:{radius},{lat},{lon})"
                if fragment not in seen:
                    seen.add(fragment)
                    queries.append(fragment)
        return queries

    def _combine_queries(self, queries: list[str], limit: int) -> str:
        """Combine query fragments into a single Overpass QL query."""
        if not queries:
            return ""
        union_body = ";\n".join(queries)
        return f"[out:json][timeout:60];\n({union_body};);\nout center {limit};"

    def _parse_element(self, elem: dict[str, Any]) -> Attraction | None:
        """Parse an Overpass element into an Attraction."""
        try:
            tags = elem.get("tags", {})
            osm_type = elem.get("type", "node")
            osm_id = elem.get("id", 0)
            xid = f"{osm_type[0].upper()}{osm_id}"

            name = tags.get("name") or tags.get("name:en") or tags.get("alt_name") or ""
            if not name:
                return None

            if osm_type == "way" or osm_type == "relation":
                lat = elem.get("center", {}).get("lat", 0)
                lon = elem.get("center", {}).get("lon", 0)
            else:
                lat = elem.get("lat", 0)
                lon = elem.get("lon", 0)

            if lat == 0 and lon == 0:
                return None

            kinds_parts: list[str] = []
            for tag_key in (
                "tourism", "historic", "amenity", "natural",
                "leisure", "building", "shop", "tower",
            ):
                val = tags.get(tag_key)
                if val:
                    kinds_parts.append(val)

            addr_parts = []
            if tags.get("addr:street"):
                addr_parts.append(tags["addr:street"])
            if tags.get("addr:housenumber"):
                addr_parts.append(tags["addr:housenumber"])
            if tags.get("addr:city"):
                addr_parts.append(tags["addr:city"])

            return Attraction(
                xid=xid,
                name=name,
                address=" ".join(addr_parts),
                location=Location(longitude=lon, latitude=lat),
                categories=kinds_parts,
                kinds=",".join(kinds_parts),
                description=(
                    tags.get("description")
                    or tags.get("wikipedia")
                    or tags.get("wikidata")
                ),
                rating=None,
            )
        except Exception:
            logger.debug("Skipping malformed Overpass element: %s", elem.get("id"))
            return None
