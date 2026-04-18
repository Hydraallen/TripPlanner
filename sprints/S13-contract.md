# Sprint S13: Weather Integration (Stretch)

**Phase:** 4 (Polish & Testing)
**Depends on:** S12
**Estimated complexity:** Medium

---

## Goal

Integrate Open-Meteo weather forecast into the itinerary. Make scheduling weather-aware (prefer indoor places on rainy days).

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/tripplanner/api/weather.py` | Create — Open-Meteo client |
| `src/tripplanner/logic/scheduler.py` | Modify — weather-aware scheduling |
| `tests/test_weather.py` | Create — weather API tests |
| `tests/test_scheduler.py` | Modify — weather-aware scheduling tests |

## Open-Meteo API

- Free, no API key required
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Params: `latitude`, `longitude`, `daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode,windspeed_10m_max`

## Functions to Implement

```python
# api/weather.py
class WeatherClient:
    async def get_forecast(lat, lon, start_date, end_date) -> list[WeatherInfo]
```

## Weather-Aware Scheduling

- If `WeatherInfo.is_rainy` for a day:
  - Prefer indoor places (museums, churches, theaters)
  - Deprioritize outdoor places (parks, viewpoints, beaches)
- Indoor/outdoor classification via `kinds` field from OpenTripMap

## Done Criteria

- [ ] `WeatherClient.get_forecast` returns list of `WeatherInfo` models
- [ ] API failure → returns empty list, scheduling proceeds without weather
- [ ] `scheduler` accepts optional `weather: list[WeatherInfo]` parameter
- [ ] Rainy days prefer indoor attractions over outdoor
- [ ] Non-rainy days keep original scheduling
- [ ] Weather info displayed in day plan output
- [ ] Tests mock Open-Meteo responses — no real API calls
- [ ] Tests cover: rainy day reordering, clear day no change, API failure fallback

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| API integration | Forecast data fetched and parsed | Client not implemented |
| Graceful fallback | No weather → itinerary still generated | Crash without weather |
| Rain-aware | Indoor places prioritized on rainy days | No reordering on rain |
| Test coverage | Weather client + scheduler tests | Missing test layer |
