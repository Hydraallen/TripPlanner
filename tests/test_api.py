from __future__ import annotations

import pytest
import respx
from httpx import Response

from tripplanner.api.opentripmap import (
    GEOAPIFY_BASE,
    NOMINATIM_BASE,
    OVERPASS_MIRRORS,
    OpenTripMapClient,
)
from tripplanner.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def client(settings: Settings) -> OpenTripMapClient:
    return OpenTripMapClient(settings)


# --- geoname (Nominatim) ---


class TestGeoname:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client: OpenTripMapClient) -> None:
        respx.get(f"{NOMINATIM_BASE}/search").mock(
            return_value=Response(
                200, json=[{"lat": "35.6762", "lon": "139.6503", "display_name": "Tokyo, Japan"}]
            )
        )
        result = await client.geoname("Tokyo")
        assert result == (35.6762, 139.6503)

    @respx.mock
    @pytest.mark.asyncio
    async def test_not_found(self, client: OpenTripMapClient) -> None:
        respx.get(f"{NOMINATIM_BASE}/search").mock(
            return_value=Response(200, json=[])
        )
        result = await client.geoname("NonexistentCityXYZ")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_server_error(self, client: OpenTripMapClient) -> None:
        respx.get(f"{NOMINATIM_BASE}/search").mock(
            return_value=Response(500, text="Internal Server Error")
        )
        result = await client.geoname("Tokyo")
        assert result is None


# --- search_places (Overpass) ---


class TestSearchPlaces:
    MOCK_OVERPASS_RESPONSE = {
        "elements": [
            {
                "type": "node",
                "id": 123,
                "lat": 35.6586,
                "lon": 139.7454,
                "tags": {
                    "name": "Tokyo Tower",
                    "tourism": "attraction",
                    "tower": "observation",
                },
            },
            {
                "type": "node",
                "id": 456,
                "lat": 35.7148,
                "lon": 139.7967,
                "tags": {
                    "name": "Sensoji Temple",
                    "amenity": "place_of_worship",
                    "religion": "buddhist",
                },
            },
        ]
    }

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_attractions(self, client: OpenTripMapClient) -> None:
        for m in OVERPASS_MIRRORS:
            respx.post(m).mock(
                return_value=Response(200, json=self.MOCK_OVERPASS_RESPONSE)
            )
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 2
        assert places[0].xid == "N123"
        assert places[0].name == "Tokyo Tower"
        assert places[0].location.longitude == 139.7454

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: OpenTripMapClient) -> None:
        respx.post(OVERPASS_MIRRORS[0]).mock(
            return_value=Response(200, json={"elements": []})
        )
        places = await client.search_places(35.68, 139.69, 10000)
        assert places == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_name_skipped(self, client: OpenTripMapClient) -> None:
        data = {
            "elements": [
                {"type": "node", "id": 999, "lat": 35.0, "lon": 139.0, "tags": {}},
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert places == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_way_with_center(self, client: OpenTripMapClient) -> None:
        data = {
            "elements": [
                {
                    "type": "way",
                    "id": 789,
                    "center": {"lat": 35.68, "lon": 139.70},
                    "tags": {"name": "Park", "leisure": "park"},
                }
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1
        assert places[0].xid == "W789"
        assert places[0].location.latitude == 35.68

    @respx.mock
    @pytest.mark.asyncio
    async def test_deduplication(self, client: OpenTripMapClient) -> None:
        data = {
            "elements": [
                {
                    "type": "node",
                    "id": 123,
                    "lat": 35.65,
                    "lon": 139.74,
                    "tags": {"name": "Tower", "tourism": "attraction"},
                },
                {
                    "type": "node",
                    "id": 123,
                    "lat": 35.65,
                    "lon": 139.74,
                    "tags": {"name": "Tower", "tourism": "attraction"},
                },
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_returns_empty(self, client: OpenTripMapClient) -> None:
        for m in OVERPASS_MIRRORS:
            respx.post(m).mock(
                return_value=Response(503, text="Service Unavailable")
            )
        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=Response(200, json={"query": {"pages": {}}})
        )
        places = await client.search_places(35.68, 139.69, 10000)
        assert places == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_name_en_fallback(self, client: OpenTripMapClient) -> None:
        """Elements without 'name' but with 'name:en' should be parsed."""
        data = {
            "elements": [
                {
                    "type": "node",
                    "id": 555,
                    "lat": 35.68,
                    "lon": 139.69,
                    "tags": {
                        "name:en": "English Name Place",
                        "tourism": "museum",
                    },
                }
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1
        assert places[0].name == "English Name Place"

    @respx.mock
    @pytest.mark.asyncio
    async def test_alt_name_fallback(self, client: OpenTripMapClient) -> None:
        """Elements with 'alt_name' but no 'name' should be parsed."""
        data = {
            "elements": [
                {
                    "type": "node",
                    "id": 666,
                    "lat": 35.68,
                    "lon": 139.69,
                    "tags": {
                        "alt_name": "Alt Name Place",
                        "tourism": "attraction",
                    },
                }
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1
        assert places[0].name == "Alt Name Place"

    @respx.mock
    @pytest.mark.asyncio
    async def test_description_uses_wikipedia_tag(self, client: OpenTripMapClient) -> None:
        """Description should prefer 'wikipedia' tag over 'wikidata'."""
        data = {
            "elements": [
                {
                    "type": "node",
                    "id": 777,
                    "lat": 35.68,
                    "lon": 139.69,
                    "tags": {
                        "name": "Famous Place",
                        "tourism": "attraction",
                        "wikipedia": "en:Famous Place",
                        "wikidata": "Q12345",
                    },
                }
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1
        assert places[0].description == "en:Famous Place"

    @respx.mock
    @pytest.mark.asyncio
    async def test_building_tag_in_categories(self, client: OpenTripMapClient) -> None:
        """Building tag should appear in categories."""
        data = {
            "elements": [
                {
                    "type": "node",
                    "id": 888,
                    "lat": 35.68,
                    "lon": 139.69,
                    "tags": {
                        "name": "Grand Cathedral",
                        "building": "cathedral",
                    },
                }
            ]
        }
        respx.post(OVERPASS_MIRRORS[0]).mock(return_value=Response(200, json=data))
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 1
        assert "cathedral" in places[0].categories


# --- place_detail ---


class TestPlaceDetail:
    @pytest.mark.asyncio
    async def test_returns_none(self, client: OpenTripMapClient) -> None:
        result = await client.place_detail("N123")
        assert result is None


# --- search_city ---


class TestSearchCity:
    @respx.mock
    @pytest.mark.asyncio
    async def test_full_pipeline(self, client: OpenTripMapClient) -> None:
        geoname_route = respx.get(f"{NOMINATIM_BASE}/search").mock(
            return_value=Response(
                200, json=[{"lat": "35.6762", "lon": "139.6503"}]
            )
        )
        overpass_route = respx.post(OVERPASS_MIRRORS[0]).mock(
            return_value=Response(
                200,
                json={
                    "elements": [
                        {
                            "type": "node",
                            "id": 123,
                            "lat": 35.65,
                            "lon": 139.74,
                            "tags": {
                                "name": "Tokyo Tower",
                                "tower": "observation",
                            },
                        }
                    ]
                },
            )
        )

        places = await client.search_city("Tokyo", ["towers"])
        assert len(places) == 1
        assert places[0].name == "Tokyo Tower"
        assert geoname_route.called
        assert overpass_route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_geoname_failure_returns_empty(self, client: OpenTripMapClient) -> None:
        respx.get(f"{NOMINATIM_BASE}/search").mock(
            return_value=Response(200, json=[])
        )
        places = await client.search_city("InvalidCity", [])
        assert places == []


# --- no api key needed ---


class TestNoApiKey:
    @pytest.mark.asyncio
    async def test_no_api_key_needed(self) -> None:
        settings = Settings()
        client = OpenTripMapClient(settings)
        assert client._api_key_param() == {}


# --- Fallback chain ---


class TestFallbackChain:
    """Test that the three-tier POI fallback works correctly."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_tier1_overpass_succeeds(
        self, client: OpenTripMapClient
    ) -> None:
        """Tier 1 Overpass succeeds → returns immediately."""
        overpass_route = respx.post(OVERPASS_MIRRORS[0]).mock(
            return_value=Response(
                200,
                json={
                    "elements": [
                        {
                            "type": "node",
                            "id": 100,
                            "lat": 41.88,
                            "lon": -87.63,
                            "tags": {
                                "name": "Test Attraction",
                                "tourism": "attraction",
                            },
                        }
                    ]
                },
            )
        )
        geoapify_route = respx.get(GEOAPIFY_BASE).mock(
            return_value=Response(200, json={"features": []})
        )

        places = await client.search_places_with_fallback(
            41.88, -87.63, 10000
        )
        assert len(places) == 1
        assert places[0].name == "Test Attraction"
        assert overpass_route.called
        assert not geoapify_route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_tier1_fails_tier2_geoapify_succeeds(self) -> None:
        """All Overpass mirrors fail → Geoapify succeeds."""
        settings = Settings(geoapify_api_key="test-key")
        client = OpenTripMapClient(settings)

        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(503, text="Unavailable")
            )

        respx.get(GEOAPIFY_BASE).mock(
            return_value=Response(
                200,
                json={
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "name": "Geoapify Museum",
                                "formatted": "123 Main St",
                                "category": "tourism.sights",
                                "place_id": "abc123",
                                "rank": {"importance": 0.8},
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-87.63, 41.88],
                            },
                        }
                    ]
                },
            )
        )

        places = await client.search_places_with_fallback(
            41.88, -87.63, 10000
        )
        assert len(places) == 1
        assert places[0].name == "Geoapify Museum"
        assert places[0].xid == "Gabc123"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_tier1_tier2_fail_tier3_wikipedia(self) -> None:
        """Overpass + Geoapify fail → Wikipedia Geosearch succeeds."""
        settings = Settings(geoapify_api_key="test-key")
        client = OpenTripMapClient(settings)

        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(504, text="Gateway Timeout")
            )

        respx.get(GEOAPIFY_BASE).mock(
            return_value=Response(200, json={"features": []})
        )

        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=Response(
                200,
                json={
                    "query": {
                        "pages": {
                            "12345": {
                                "pageid": 12345,
                                "title": "Millennium Park",
                                "length": 5000,
                                "description": "Public park in Chicago",
                                "fullurl": "https://en.wikipedia.org/wiki/Millennium_Park",
                                "coordinates": [
                                    {"lat": 41.882, "lon": -87.623}
                                ],
                            }
                        }
                    }
                },
            )
        )

        places = await client.search_places_with_fallback(
            41.88, -87.63, 10000
        )
        assert len(places) == 1
        assert places[0].name == "Millennium Park"
        assert places[0].xid == "W12345"
        assert "Public park in Chicago" in (places[0].description or "")
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_geoapify_key_skips_tier2(self) -> None:
        """Without Geoapify key, skips tier 2 and goes to Wikipedia."""
        settings = Settings(geoapify_api_key="")
        client = OpenTripMapClient(settings)

        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(504, text="Timeout")
            )

        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=Response(
                200,
                json={
                    "query": {
                        "pages": {
                            "99": {
                                "pageid": 99,
                                "title": "Test Place",
                                "length": 2000,
                                "coordinates": [
                                    {"lat": 41.0, "lon": -87.0}
                                ],
                            }
                        }
                    }
                },
            )
        )

        places = await client.search_places_with_fallback(
            41.0, -87.0, 10000
        )
        assert len(places) == 1
        assert places[0].name == "Test Place"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_all_fail_returns_empty(
        self, client: OpenTripMapClient
    ) -> None:
        """All tiers fail → returns empty list."""
        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(503, text="Unavailable")
            )

        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=Response(200, json={"query": {"pages": {}}})
        )

        places = await client.search_places_with_fallback(
            41.88, -87.63, 10000
        )
        assert places == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_wikipedia_skips_short_articles(self) -> None:
        """Wikipedia pages with < 500 bytes are skipped."""
        settings = Settings(geoapify_api_key="")
        client = OpenTripMapClient(settings)

        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(504, text="Timeout")
            )

        respx.get("https://en.wikipedia.org/w/api.php").mock(
            return_value=Response(
                200,
                json={
                    "query": {
                        "pages": {
                            "1": {
                                "pageid": 1,
                                "title": "Short Article",
                                "length": 100,
                                "coordinates": [
                                    {"lat": 41.0, "lon": -87.0}
                                ],
                            },
                            "2": {
                                "pageid": 2,
                                "title": "Real Article",
                                "length": 5000,
                                "coordinates": [
                                    {"lat": 41.1, "lon": -87.1}
                                ],
                            },
                        }
                    }
                },
            )
        )

        places = await client.search_places_with_fallback(
            41.0, -87.0, 10000
        )
        assert len(places) == 1
        assert places[0].name == "Real Article"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_geoapify_parse_feature(self) -> None:
        """Geoapify feature parsing extracts correct fields."""
        settings = Settings(geoapify_api_key="test-key")
        client = OpenTripMapClient(settings)

        for mirror in OVERPASS_MIRRORS:
            respx.post(mirror).mock(
                return_value=Response(504, text="Timeout")
            )

        respx.get(GEOAPIFY_BASE).mock(
            return_value=Response(
                200,
                json={
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "name": "Tower Bridge",
                                "formatted": "Tower Bridge, London, UK",
                                "category": "tourism.sights",
                                "place_id": "xyz789",
                                "rank": {"importance": 0.95},
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-0.0754, 51.5055],
                            },
                        }
                    ]
                },
            )
        )

        places = await client.search_places_with_fallback(
            51.5055, -0.0754, 5000
        )
        assert len(places) == 1
        assert places[0].name == "Tower Bridge"
        assert places[0].xid == "Gxyz789"
        assert places[0].score == 0.95
        assert places[0].address == "Tower Bridge, London, UK"
        await client.close()
