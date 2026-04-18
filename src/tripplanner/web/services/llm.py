from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import date
from typing import Any

import httpx

from tripplanner.core.config import Settings
from tripplanner.core.models import TripPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are TripPlanner AI, an expert travel advisor. "
    "Help users plan personalized travel itineraries with practical advice "
    "on attractions, food, transportation, and budget."
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
            timeout=60.0,
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
    ) -> TripPlan | None:
        """Generate a travel plan using LLM.

        Returns a validated TripPlan or None on failure.
        """
        prompt = (
            f"Generate a detailed travel itinerary for {city} "
            f"from {start_date} to {end_date}.\n"
            f"Interests: {', '.join(interests)}\n"
            f"Transport mode: {transport_mode}\n"
        )
        if preferences:
            prompt += f"Additional preferences: {preferences}\n"

        prompt += (
            "\nReturn a JSON object matching this schema:\n"
            '{"city": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", '
            '"days": [{"date": "YYYY-MM-DD", "day_number": int, "transportation": "string", '
            '"attractions": [{"xid": "string", "name": "string", "address": "string", '
            '"location": {"longitude": float, "latitude": float}, "kinds": "string", '
            '"visit_duration": int, "rating": float}], "meals": [{"type": "string", '
            '"name": "string", "estimated_cost": float}]}], '
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
