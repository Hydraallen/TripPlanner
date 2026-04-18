from __future__ import annotations

import pytest
import respx

from tripplanner.api.amap import AmapClient
from tripplanner.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(amap_api_key="test-key")


@pytest.fixture
def client(settings: Settings) -> AmapClient:
    return AmapClient(settings)


class TestGeocode:
    @respx.mock
    @pytest.mark.asyncio
    async def test_geocode_success(self, client: AmapClient) -> None:
        respx.get("https://restapi.amap.com/v3/geocode/geo").mock(
            return_value=__import__("httpx").Response(
                200,
                json={
                    "status": "1",
                    "geocodes": [{"location": "116.397428,39.90923"}],
                },
            )
        )
        result = await client.geocode("北京")
        assert result is not None
        lat, lon = result
        assert abs(lat - 39.90923) < 0.001
        assert abs(lon - 116.397428) < 0.001

    @respx.mock
    @pytest.mark.asyncio
    async def test_geocode_not_found(self, client: AmapClient) -> None:
        respx.get("https://restapi.amap.com/v3/geocode/geo").mock(
            return_value=__import__("httpx").Response(
                200, json={"status": "1", "geocodes": []}
            )
        )
        assert await client.geocode("nonexistent") is None


class TestSearchPois:
    @respx.mock
    @pytest.mark.asyncio
    async def test_search_pois_success(self, client: AmapClient) -> None:
        respx.get("https://restapi.amap.com/v3/place/around").mock(
            return_value=__import__("httpx").Response(
                200,
                json={
                    "status": "1",
                    "pois": [
                        {
                            "id": "B000A83M61",
                            "name": "故宫博物院",
                            "location": "116.397428,39.90923",
                            "type": "旅游景点",
                            "rating": "4.8",
                        }
                    ],
                },
            )
        )
        results = await client.search_pois(39.90923, 116.397428)
        assert len(results) == 1
        assert results[0].name == "故宫博物院"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_pois_failure(self, client: AmapClient) -> None:
        respx.get("https://restapi.amap.com/v3/place/around").mock(
            return_value=__import__("httpx").Response(
                200, json={"status": "0", "info": "INVALID_KEY"}
            )
        )
        results = await client.search_pois(39.90923, 116.397428)
        assert results == []


class TestSearchCity:
    @respx.mock
    @pytest.mark.asyncio
    async def test_search_city_success(self, client: AmapClient) -> None:
        route_geocode = respx.get("https://restapi.amap.com/v3/geocode/geo")
        route_geocode.mock(
            return_value=__import__("httpx").Response(
                200,
                json={"status": "1", "geocodes": [{"location": "116.397428,39.90923"}]},
            )
        )
        route_pois = respx.get("https://restapi.amap.com/v3/place/around")
        route_pois.mock(
            return_value=__import__("httpx").Response(
                200,
                json={
                    "status": "1",
                    "pois": [
                        {
                            "id": "B000A83M61",
                            "name": "故宫",
                            "location": "116.397,39.909",
                            "type": "景点",
                        }
                    ],
                },
            )
        )
        results = await client.search_city("北京", ["景点"])
        assert len(results) == 1
