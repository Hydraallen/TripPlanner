from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import Attraction, Location

logger = logging.getLogger(__name__)

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

OVERPASS_MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]

GEOAPIFY_BASE = "https://api.geoapify.com/v2/places"

# Geoapify categories for tourism POIs
GEOAPIFY_TOURISM_CATEGORIES = (
    "tourism.sights,tourism.information,"
    "entertainment,leisure.park,leisure.garden,"
    "building.tourism,building.historic"
)

# Map interest keywords to OSM Overpass QL tag selectors.
_INTEREST_TO_OVERPASS: dict[str, list[str]] = {
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
    """Async client with three-tier POI fallback:

    1. Overpass (OSM) — free, unlimited, multi-mirror
    2. Geoapify Places API — free 3000 credits/day
    3. Wikipedia Geosearch — free, unlimited, no key
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(
            timeout=45.0,
            headers={"User-Agent": "TripPlanner/0.1"},
        )
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

    # ------------------------------------------------------------------
    # Geocoding (Nominatim)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Public search API (with fallback)
    # ------------------------------------------------------------------

    async def search_places(
        self,
        lat: float,
        lon: float,
        radius: int,
        kinds: str | None = None,
        limit: int = 100,
    ) -> list[Attraction]:
        """Fetch POIs using three-tier fallback."""
        return await self.search_places_with_fallback(
            lat, lon, radius, kinds, limit
        )

    async def search_places_with_fallback(
        self,
        lat: float,
        lon: float,
        radius: int,
        kinds: str | None = None,
        limit: int = 100,
    ) -> list[Attraction]:
        """Try Overpass mirrors → Geoapify → Wikipedia Geosearch."""
        # Tier 1: Overpass (try each mirror)
        for mirror in OVERPASS_MIRRORS:
            places = await self._overpass_search(
                mirror, lat, lon, radius, kinds, limit
            )
            if places:
                logger.info(
                    "Overpass returned %d places from %s",
                    len(places), mirror,
                )
                return places

        logger.warning("All Overpass mirrors failed, trying Geoapify")

        # Tier 2: Geoapify (if API key configured)
        if self._settings.geoapify_api_key:
            places = await self._geoapify_search(lat, lon, radius, limit)
            if places:
                logger.info("Geoapify returned %d places", len(places))
                return places
            logger.warning("Geoapify returned no results, trying Wikipedia")

        # Tier 3: Wikipedia Geosearch (always available)
        places = await self._wikipedia_search(lat, lon, radius, limit)
        if places:
            logger.info("Wikipedia Geosearch returned %d places", len(places))
        else:
            logger.warning("All POI sources returned no results")
        return places

    async def place_detail(self, xid: str) -> Attraction | None:
        """No-op — data returned in bulk by search methods."""
        return None

    async def search_city(
        self,
        city: str,
        interests: list[str],
        radius: int | None = None,
    ) -> list[Attraction]:
        """High-level: geocode city → search POIs with fallback."""
        radius = radius or self._settings.default_search_radius
        coords = await self.geoname(city)
        if not coords:
            return []

        lat, lon = coords
        kinds = ",".join(interests) if interests else None
        places = await self.search_places_with_fallback(
            lat, lon, radius, kinds
        )
        return places[: self._settings.max_places_per_trip]

    # ------------------------------------------------------------------
    # Tier 1: Overpass (OSM)
    # ------------------------------------------------------------------

    async def _overpass_search(
        self,
        mirror: str,
        lat: float,
        lon: float,
        radius: int,
        kinds: str | None,
        limit: int,
    ) -> list[Attraction]:
        """Query a single Overpass mirror. Returns [] on failure.

        Queries each interest category separately with a fair per-category
        limit so that high-cardinality tags (e.g. restaurants) don't drown
        out low-cardinality ones (e.g. museums).
        """
        interest_list = kinds.split(",") if kinds else ["interesting_places"]
        per_category_limit = max(limit // len(interest_list), 20)

        seen_ids: set[str] = set()
        places: list[Attraction] = []

        for interest in interest_list:
            queries = self._build_overpass_queries(
                lat, lon, radius, [interest]
            )
            if not queries:
                continue

            batch_size = 8
            batches = [
                queries[i : i + batch_size]
                for i in range(0, len(queries), batch_size)
            ]

            for batch_idx, batch in enumerate(batches):
                if places:
                    await asyncio.sleep(1.5)
                query = self._combine_queries(batch, per_category_limit)
                if not query:
                    continue
                try:
                    resp = await self._client.post(
                        mirror,
                        data={"data": query},
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.warning("Overpass %s failed: %s", mirror, e)
                    return []

                for elem in data.get("elements", []):
                    parsed = self._parse_element(elem)
                    if parsed and parsed.xid not in seen_ids:
                        seen_ids.add(parsed.xid)
                        places.append(parsed)

        return places

    # ------------------------------------------------------------------
    # Tier 2: Geoapify Places API
    # ------------------------------------------------------------------

    async def _geoapify_search(
        self,
        lat: float,
        lon: float,
        radius: int,
        limit: int,
    ) -> list[Attraction]:
        """Search POIs via Geoapify Places API."""
        try:
            resp = await self._client.get(
                GEOAPIFY_BASE,
                params={
                    "categories": GEOAPIFY_TOURISM_CATEGORIES,
                    "filter": f"circle:{lon},{lat},{min(radius, 5000)}",
                    "bias": f"proximity:{lon},{lat}",
                    "limit": min(limit, 50),
                    "apiKey": self._settings.geoapify_api_key,
                    "lang": "en",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("Geoapify request failed: %s", e)
            return []

        places: list[Attraction] = []
        for feature in data.get("features", []):
            parsed = self._parse_geoapify_feature(feature)
            if parsed:
                places.append(parsed)
        return places

    def _parse_geoapify_feature(
        self, feature: dict[str, Any]
    ) -> Attraction | None:
        """Parse a Geoapify GeoJSON feature into an Attraction."""
        try:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])

            name = props.get("name", "")
            if not name:
                return None

            lon = coords[0] if len(coords) > 0 else 0
            lat = coords[1] if len(coords) > 1 else 0
            if lat == 0 and lon == 0:
                return None

            category = props.get("category", "")
            rank = props.get("rank", {})
            importance = rank.get("importance", 0.5) or 0.5

            return Attraction(
                xid=f"G{props.get('place_id', '')}",
                name=name,
                address=props.get("formatted", ""),
                location=Location(longitude=lon, latitude=lat),
                categories=[category] if category else [],
                kinds=category,
                description=None,
                rating=None,
                score=round(min(importance, 1.0), 4),
            )
        except Exception:
            logger.debug("Skipping malformed Geoapify feature")
            return None

    # ------------------------------------------------------------------
    # Tier 3: Wikipedia Geosearch
    # ------------------------------------------------------------------

    async def _wikipedia_search(
        self,
        lat: float,
        lon: float,
        radius: int,
        limit: int,
    ) -> list[Attraction]:
        """Search nearby Wikipedia articles with coordinates."""
        try:
            resp = await self._client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "geosearch",
                    "ggscoord": f"{lat}|{lon}",
                    "ggsradius": min(radius, 10000),
                    "ggslimit": min(limit, 50),
                    "prop": "coordinates|pageimages|description|info",
                    "inprop": "url",
                    "pithumbsize": 144,
                    "format": "json",
                    "origin": "*",
                },
                headers={
                    "User-Agent": "TripPlanner/0.1 (https://github.com/Hydraallen/TripPlanner; educational project)",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("Wikipedia Geosearch failed: %s", e)
            return []

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return []

        places: list[Attraction] = []
        for _page_id, page in pages.items():
            parsed = self._parse_wikipedia_page(page)
            if parsed:
                places.append(parsed)
        return places

    def _parse_wikipedia_page(
        self, page: dict[str, Any]
    ) -> Attraction | None:
        """Parse a Wikipedia geosearch page into an Attraction."""
        try:
            title = page.get("title", "")
            if not title:
                return None

            # Skip very short articles (minor entries)
            length = page.get("length", 0)
            if length < 500:
                return None

            coords = page.get("coordinates", [{}])
            if not coords:
                return None
            coord = coords[0]
            lat = coord.get("lat", 0)
            lon = coord.get("lon", 0)
            if lat == 0 and lon == 0:
                return None

            desc_parts: list[str] = []
            description = page.get("description", "")
            if description:
                desc_parts.append(description)
            url = page.get("fullurl", "")
            if url:
                desc_parts.append(url)

            return Attraction(
                xid=f"W{page.get('pageid', 0)}",
                name=title,
                address="",
                location=Location(longitude=lon, latitude=lat),
                categories=["wikipedia"],
                kinds="wikipedia",
                description=" | ".join(desc_parts) or None,
                rating=None,
                score=0.5,
            )
        except Exception:
            logger.debug("Skipping malformed Wikipedia page")
            return None

    # ------------------------------------------------------------------
    # Overpass helpers
    # ------------------------------------------------------------------

    def _build_overpass_queries(
        self, lat: float, lon: float, radius: int, interests: list[str]
    ) -> list[str]:
        """Build Overpass QL query fragments for given interests."""
        queries: list[str] = []
        seen: set[str] = set()
        for interest in interests:
            tag_queries = _INTEREST_TO_OVERPASS.get(interest)
            if not tag_queries:
                tag_queries = _INTEREST_TO_OVERPASS.get(
                    "interesting_places", []
                )
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

            name = (
                tags.get("name")
                or tags.get("name:en")
                or tags.get("alt_name")
                or ""
            )
            if not name:
                return None

            if osm_type in ("way", "relation"):
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
            logger.debug(
                "Skipping malformed Overpass element: %s", elem.get("id")
            )
            return None
