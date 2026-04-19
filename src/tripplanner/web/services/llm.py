from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import date

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import Attraction, PlanFocus, TripPlan, WeatherInfo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are TripPlanner AI, an expert travel advisor. "
    "Help users plan personalized travel itineraries with practical advice "
    "on attractions, food, transportation, and budget."
)

_FOCUS_PROMPTS: dict[PlanFocus, str] = {
    PlanFocus.BUDGET: (
        "Focus on budget-friendly options. Prioritize free or low-cost attractions, "
        "affordable local eateries, and cost-effective transportation. "
        "Maximize experiences while minimizing spending."
    ),
    PlanFocus.CULTURE: (
        "Focus on cultural exploration. Prioritize museums, historical sites, "
        "local traditions, art galleries, and authentic cultural experiences. "
        "Include food experiences that reflect local cuisine."
    ),
    PlanFocus.NATURE: (
        "Focus on nature and relaxation. Prioritize parks, gardens, scenic viewpoints, "
        "waterfronts, hiking trails, and peaceful spots. "
        "Include leisurely pacing and outdoor dining."
    ),
    PlanFocus.FOOD: (
        "Focus on culinary experiences. Prioritize local restaurants, street food markets, "
        "food tours, cooking classes, and specialty cafes. Include both high-end dining and "
        "affordable local gems. Plan meal-centric days with food-related attractions nearby."
    ),
    PlanFocus.ROMANTIC: (
        "Focus on romantic and intimate experiences. Prioritize scenic viewpoints at sunset, "
        "fine dining restaurants, waterfront walks, botanical gardens, and cozy cafes. "
        "Keep a relaxed pace with fewer attractions per day and more quality time."
    ),
    PlanFocus.ADVENTURE: (
        "Focus on adventure and active experiences. Prioritize outdoor activities, "
        "hiking trails, water sports, unique local experiences, and exploration of "
        "off-the-beaten-path locations. Pack each day with exciting activities."
    ),
}

_TRIP_PLAN_SCHEMA = (
    '{"city": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", '
    '"days": [{"date": "YYYY-MM-DD", "day_number": int, "transportation": "string", '
    '"description": "string", "attractions": [{"xid": "string", "name": "string", '
    '"address": "string", "location": {"longitude": float, "latitude": float}, '
    '"kinds": "string", "visit_duration": int, "time_slot": "HH:MM-HH:MM", '
    '"commute_minutes": int, "rating": float, "ticket_price": float, '
    '"description": "string"}], "meals": [{"type": "string", "name": "string", '
    '"address": "string", "estimated_cost": float, "time_slot": "HH:MM-HH:MM"}]}], '
    '"budget": {"total_attractions": float, "total_meals": float, '
    '"total_hotels": float, "total_transportation": float, "total": float}, '
    '"suggestions": ["string"]}'
)

_TIME_RULES = (
    "\nTime scheduling rules:\n"
    "1. Group nearby attractions to minimize backtracking.\n"
    "2. On days with long commutes (>30 min), reduce attractions.\n"
    "3. Museums in morning, viewpoints/parks in afternoon.\n"
    "4. Each attraction must have time_slot as HH:MM-HH:MM.\n"
    "5. Each attraction must have commute_minutes "
    "(travel from previous, 0 for first).\n"
    "6. Meal slots: breakfast 08:00-09:00, lunch 12:00-13:00, "
    "dinner 18:00-19:00.\n"
    "7. Do not repeat an attraction on multiple days.\n"
    "8. Durations vary: museums ~120min, viewpoints ~45min, "
    "parks ~60min, restaurants ~60min, monuments ~45min.\n"
    "9. Day runs 09:00 to 19:00.\n"
)


class LLMClient:
    """Client for GLM-5.1 via OpenAI-compatible API.

    Used for LLM-powered plan generation and chat.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.openai_endpoint,
            headers={"Authorization": f"Bearer {self._settings.openai_api_key}"},
            timeout=300.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> LLMClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    @property
    def _model(self) -> str:
        return self._settings.openai_model_name

    async def generate_plan(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        transport_mode: str = "walking",
        preferences: str | None = None,
        transport_user_specified: bool = True,
    ) -> TripPlan | None:
        """Generate a travel plan using LLM.

        Returns a validated TripPlan or None on failure.
        """
        prompt = (
            f"Generate a detailed travel itinerary for {city} "
            f"from {start_date} to {end_date}.\n"
            f"Interests: {', '.join(interests)}\n"
        )
        if transport_user_specified:
            prompt += f"Transport mode: {transport_mode}\n"
        else:
            prompt += (
                "Transport mode: not specified — choose the best transport for each day "
                "based on the plan's focus (walking, transit, driving, cycling, etc.).\n"
                "Set 'transportation' in each day object to your recommendation.\n"
            )
        if preferences:
            prompt += f"Additional preferences: {preferences}\n"

        prompt += (
            f"{_TIME_RULES}\n"
            "Return a JSON object matching this schema:\n"
            '{"city": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", '
            '"days": [{"date": "YYYY-MM-DD", "day_number": int, "transportation": "string", '
            '"attractions": [{"xid": "string", "name": "string", "address": "string", '
            '"location": {"longitude": float, "latitude": float}, "kinds": "string", '
            '"visit_duration": int, "time_slot": "HH:MM-HH:MM", "commute_minutes": int, '
            '"rating": float}], "meals": [{"type": "string", '
            '"name": "string", "estimated_cost": float, "time_slot": "HH:MM-HH:MM"}]}], '
            '"budget": {"total_attractions": float, "total_meals": float, '
            '"total_hotels": float, "total_transportation": float, "total": float}}\n'
            "Return ONLY the JSON, no markdown fences."
        )

        try:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self._settings.llm_temperature,
                    "max_tokens": self._settings.llm_max_tokens,
                    "thinking": {"type": "disabled"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            plan_data = json.loads(content)
            return TripPlan.model_validate(plan_data)
        except Exception as e:
            logger.warning("LLM plan generation failed: %s", e)
            return None

    async def generate_plan_with_focus(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        focus: PlanFocus,
        transport_mode: str = "walking",
        places: list[Attraction] | None = None,
        weather: list[WeatherInfo] | None = None,
        transport_user_specified: bool = True,
    ) -> TripPlan | None:
        """Generate a focused travel plan using LLM with real data.

        Args:
            city: Target city
            start_date/end_date: Trip dates
            interests: User interests
            focus: Plan focus (budget/culture/nature)
            transport_mode: Transport mode
            places: Pre-collected POI data to include in prompt
            weather: Pre-fetched weather data

        Returns:
            Validated TripPlan or None on failure.
        """
        system_msg = (
            f"{SYSTEM_PROMPT}\n\n{_FOCUS_PROMPTS[focus]} "
            f"This plan should be focused on {focus.value} experiences."
        )

        prompt = (
            f"Generate a detailed travel itinerary for {city} "
            f"from {start_date} to {end_date}.\n"
            f"Interests: {', '.join(interests)}\n"
        )
        if transport_user_specified:
            prompt += f"Transport mode: {transport_mode}\n"
        else:
            prompt += (
                "Transport mode: not specified — choose the best transport for each day "
                "based on the plan's focus (walking, transit, driving, cycling, etc.).\n"
                "Set 'transportation' in each day object to your recommendation.\n"
            )

        if places:
            prompt += "\n\nAvailable places to consider (use these as reference):\n"
            for p in places[:20]:
                prompt += (
                    f"- {p.name} ({p.kinds or 'general'})"
                    f" rating:{p.rating or 'N/A'}"
                    f" cost:{p.ticket_price or 0}\n"
                )

        if weather:
            prompt += "\nWeather forecast:\n"
            for w in weather:
                prompt += f"- {w.date}: {w.description}, {w.temp_low}-{w.temp_high}C\n"

        prompt += (
            f"{_TIME_RULES}\n"
            f"\nReturn a JSON object matching this schema:\n{_TRIP_PLAN_SCHEMA}\n"
            "Return ONLY the JSON, no markdown fences."
        )

        try:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self._settings.llm_temperature,
                    "max_tokens": self._settings.llm_max_tokens,
                    "thinking": {"type": "disabled"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            content = (choice.get("message", {}).get("content") or "").strip()
            finish_reason = choice.get("finish_reason", "")
            if not content:
                logger.warning(
                    "LLM returned empty content (finish=%s, usage=%s)",
                    finish_reason,
                    data.get("usage"),
                )
                return None
            content = _strip_json_fences(content)
            plan_data = json.loads(content)
            return TripPlan.model_validate(plan_data)
        except json.JSONDecodeError as e:
            logger.warning(
                "LLM JSON parse failed (%s) at pos %d: %s\nContent snippet: %.500s",
                focus.value, e.pos, e, content if 'content' in dir() else "N/A",
            )
            return None
        except Exception as e:
            logger.warning("LLM focused plan generation failed (%s): %s", focus.value, e)
            return None

    async def chat(
        self,
        messages: list[dict[str, str]],
        plan_context: str | None = None,
    ) -> str:
        """Send a chat message and get a response."""
        system_msg = SYSTEM_PROMPT
        if plan_context:
            system_msg += f"\n\nCurrent trip context:\n{plan_context}"

        try:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "system", "content": system_msg}] + messages,
                    "temperature": self._settings.llm_temperature,
                    "max_tokens": self._settings.llm_max_tokens,
                    "thinking": {"type": "disabled"},
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("LLM chat failed: %s", e)
            return "Sorry, I couldn't process your request. Please try again."

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        plan_context: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response tokens."""
        system_msg = SYSTEM_PROMPT
        if plan_context:
            system_msg += f"\n\nCurrent trip context:\n{plan_context}"

        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "system", "content": system_msg}] + messages,
                    "temperature": self._settings.llm_temperature,
                    "max_tokens": self._settings.llm_max_tokens,
                    "thinking": {"type": "disabled"},
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            logger.warning("LLM stream failed: %s", e)
            yield "Sorry, streaming failed. Please try again."


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [line for line in lines[1:] if not line.strip().startswith("```")]
        text = "\n".join(lines)
    return text
