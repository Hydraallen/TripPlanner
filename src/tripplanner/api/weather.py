from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import WeatherInfo

logger = logging.getLogger(__name__)


class WeatherClient:
    """Async client for the Open-Meteo forecast API.

    Free, no API key required.
    API docs: https://open-meteo.com/en/docs
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.openmeteo_base_url,
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> WeatherClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherInfo]:
        """Get daily weather forecast for a date range.

        Returns a list of WeatherInfo objects. Empty list on failure.
        """
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,weather_code,wind_speed_10m_max"
            ),
            "timezone": "auto",
        }

        try:
            resp = await self._client.get("/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("Open-Meteo returned %s", e.response.status_code)
            return []
        except httpx.RequestError as e:
            logger.warning("Open-Meteo request failed: %s", e)
            return []

        return self._parse_forecast(data)

    def _parse_forecast(self, data: dict[str, Any]) -> list[WeatherInfo]:
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_probability_max", [])
        weather_codes = daily.get("weather_code", [])
        wind = daily.get("wind_speed_10m_max", [])

        results: list[WeatherInfo] = []
        for i, d in enumerate(dates):
            try:
                results.append(
                    WeatherInfo(
                        date=date.fromisoformat(d),
                        temp_high=float(temp_max[i]) if i < len(temp_max) else 0,
                        temp_low=float(temp_min[i]) if i < len(temp_min) else 0,
                        precipitation_prob=float(precip[i]) if i < len(precip) else 0,
                        weather_code=int(weather_codes[i]) if i < len(weather_codes) else 0,
                        wind_speed=float(wind[i]) if i < len(wind) else 0,
                    )
                )
            except (IndexError, ValueError, TypeError):
                logger.debug("Skipping malformed weather entry at index %d", i)

        return results
