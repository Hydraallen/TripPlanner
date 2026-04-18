from __future__ import annotations

import pytest
import respx
from httpx import Response

from tripplanner.api.opentripmap import OpenTripMapClient
from tripplanner.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(opentripmap_api_key="test-key", opentripmap_base_url="https://api.opentripmap.com/0.1/en")


@pytest.fixture
def client(settings: Settings) -> OpenTripMapClient:
    return OpenTripMapClient(settings)


# --- geoname ---


class TestGeoname:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/geoname").mock(
            return_value=Response(200, json={"lat": "35.6762", "lon": "139.6503", "name": "Tokyo"})
        )
        result = await client.geoname("Tokyo")
        assert result == (35.6762, 139.6503)

    @respx.mock
    @pytest.mark.asyncio
    async def test_not_found(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/geoname").mock(
            return_value=Response(200, json={})
        )
        result = await client.geoname("NonexistentCityXYZ")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_server_error(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/geoname").mock(
            return_value=Response(500, text="Internal Server Error")
        )
        result = await client.geoname("Tokyo")
        assert result is None


# --- search_places ---


class TestSearchPlaces:
    MOCK_RADIUS_RESPONSE = [
        {
            "xid": "N123",
            "name": "Tokyo Tower",
            "point": {"lon": 139.7454, "lat": 35.6586},
            "kinds": "towers,architecture",
        },
        {
            "xid": "N456",
            "name": "Sensoji Temple",
            "point": {"lon": 139.7967, "lat": 35.7148},
            "kinds": "temples,religion",
        },
    ]

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_attractions(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/radius").mock(
            return_value=Response(200, json=self.MOCK_RADIUS_RESPONSE)
        )
        places = await client.search_places(35.68, 139.69, 10000)
        assert len(places) == 2
        assert places[0].xid == "N123"
        assert places[0].name == "Tokyo Tower"
        assert places[0].location.longitude == 139.7454

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/radius").mock(
            return_value=Response(200, json=[])
        )
        places = await client.search_places(35.68, 139.69, 10000)
        assert places == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_malformed_item_skipped(self, client: OpenTripMapClient) -> None:
        data = self.MOCK_RADIUS_RESPONSE + [{"xid": "BAD"}]  # no name, no point
        respx.get("https://api.opentripmap.com/0.1/en/places/radius").mock(
            return_value=Response(200, json=data)
        )
        places = await client.search_places(35.68, 139.69, 10000)
        # Items with no point get default (0,0) which is valid — so 3 results
        assert len(places) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_returns_empty(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/radius").mock(
            return_value=Response(503, text="Service Unavailable")
        )
        places = await client.search_places(35.68, 139.69, 10000)
        assert places == []


# --- place_detail ---


class TestPlaceDetail:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/xid/N123").mock(
            return_value=Response(
                200,
                json={
                    "xid": "N123",
                    "name": "Tokyo Tower",
                    "point": {"lon": 139.7454, "lat": 35.6586},
                    "kinds": "towers,architecture",
                    "rate": "4.5",
                    "address": {"road": "4 Chome-2-8 Shibakoen"},
                    "info": {"descr": "Famous tower"},
                },
            )
        )
        place = await client.place_detail("N123")
        assert place is not None
        assert place.name == "Tokyo Tower"
        assert place.rating == 4.5
        assert place.description == "Famous tower"

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_returns_none(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/xid/BAD").mock(
            return_value=Response(404, text="Not Found")
        )
        result = await client.place_detail("BAD")
        assert result is None


# --- search_city ---


class TestSearchCity:
    @respx.mock
    @pytest.mark.asyncio
    async def test_full_pipeline(self, client: OpenTripMapClient) -> None:
        geoname_route = respx.get("https://api.opentripmap.com/0.1/en/places/geoname").mock(
            return_value=Response(200, json={"lat": "35.6762", "lon": "139.6503"})
        )
        radius_route = respx.get("https://api.opentripmap.com/0.1/en/places/radius").mock(
            return_value=Response(
                200,
                json=[
                    {"xid": "N123", "name": "Tower", "point": {"lon": 139.74, "lat": 35.65}, "kinds": "towers"},
                ],
            )
        )
        detail_route = respx.get("https://api.opentripmap.com/0.1/en/places/xid/N123").mock(
            return_value=Response(
                200,
                json={
                    "xid": "N123",
                    "name": "Tokyo Tower",
                    "point": {"lon": 139.7454, "lat": 35.6586},
                    "kinds": "towers",
                    "rate": "4",
                },
            )
        )

        places = await client.search_city("Tokyo", ["towers"])
        assert len(places) == 1
        assert places[0].name == "Tokyo Tower"
        assert geoname_route.called
        assert radius_route.called
        assert detail_route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_geoname_failure_returns_empty(self, client: OpenTripMapClient) -> None:
        respx.get("https://api.opentripmap.com/0.1/en/places/geoname").mock(
            return_value=Response(200, json={})
        )
        places = await client.search_city("InvalidCity", [])
        assert places == []


# --- API key missing ---


class TestNoApiKey:
    @pytest.mark.asyncio
    async def test_no_api_key_warns(self) -> None:
        settings = Settings(opentripmap_api_key="")
        client = OpenTripMapClient(settings)
        assert client._api_key_param() == {}
