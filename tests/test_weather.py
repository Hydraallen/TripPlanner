from __future__ import annotations

from datetime import date

import httpx
import pytest
import respx

from tripplanner.api.weather import WeatherClient
from tripplanner.core.config import Settings


@pytest.fixture
def client() -> WeatherClient:
    return WeatherClient(Settings())


class TestGetForecast:
    @respx.mock
    @pytest.mark.asyncio
    async def test_forecast_success(self, client: WeatherClient) -> None:
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(
                200,
                json={
                    "daily": {
                        "time": ["2026-05-01", "2026-05-02"],
                        "temperature_2m_max": [25.0, 22.0],
                        "temperature_2m_min": [15.0, 12.0],
                        "precipitation_probability_max": [10, 80],
                        "weather_code": [0, 61],
                        "wind_speed_10m_max": [10.0, 20.0],
                    }
                },
            )
        )
        results = await client.get_forecast(
            35.6762, 139.6503, date(2026, 5, 1), date(2026, 5, 2)
        )
        assert len(results) == 2
        assert results[0].temp_high == 25.0
        assert results[0].is_rainy is False
        assert results[1].is_rainy is True
        assert results[0].description == "Clear"

    @respx.mock
    @pytest.mark.asyncio
    async def test_forecast_api_failure(self, client: WeatherClient) -> None:
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        results = await client.get_forecast(
            35.6762, 139.6503, date(2026, 5, 1), date(2026, 5, 2)
        )
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_forecast_network_error(self, client: WeatherClient) -> None:
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            side_effect=httpx.RequestError("Connection failed")
        )
        results = await client.get_forecast(
            35.6762, 139.6503, date(2026, 5, 1), date(2026, 5, 2)
        )
        assert results == []
