from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from tripplanner.core.config import get_settings
from tripplanner.web.services.llm import LLMClient
from tripplanner.web.services.planning import generate_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanRequest(BaseModel):
    city: str
    start_date: date
    end_date: date
    interests: list[str] = ["interesting_places"]
    transport_mode: str = "walking"
    radius: int | None = None


class LLMPlanRequest(PlanRequest):
    preferences: str | None = None


@router.post("/generate")
async def generate_plan_endpoint(req: PlanRequest) -> dict[str, Any]:
    """Generate a travel plan based on user preferences.

    Uses the algorithmic pipeline with smart API routing.
    """
    plan = await generate_plan(
        city=req.city,
        start_date=req.start_date,
        end_date=req.end_date,
        interests=req.interests,
        transport_mode=req.transport_mode,
        radius=req.radius,
    )
    if not plan:
        return {"error": f"Could not generate plan for {req.city}"}
    return plan.model_dump(mode="json")


@router.post("/generate-llm")
async def generate_llm_plan_endpoint(req: LLMPlanRequest) -> dict[str, Any]:
    """Generate a travel plan using LLM with algorithmic fallback.

    If LLM fails or returns invalid data, falls back to the
    algorithmic pipeline. Response includes source field.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        plan = await generate_plan(
            city=req.city,
            start_date=req.start_date,
            end_date=req.end_date,
            interests=req.interests,
            transport_mode=req.transport_mode,
            radius=req.radius,
        )
        if plan:
            return {**plan.model_dump(mode="json"), "source": "algorithmic"}
        return {"error": f"Could not generate plan for {req.city}"}

    async with LLMClient(settings) as client:
        llm_plan = await client.generate_plan(
            city=req.city,
            start_date=req.start_date,
            end_date=req.end_date,
            interests=req.interests,
            transport_mode=req.transport_mode,
            preferences=req.preferences,
        )

    if llm_plan:
        return {**llm_plan.model_dump(mode="json"), "source": "llm"}

    logger.info("LLM plan generation failed, falling back to algorithmic")
    plan = await generate_plan(
        city=req.city,
        start_date=req.start_date,
        end_date=req.end_date,
        interests=req.interests,
        transport_mode=req.transport_mode,
        radius=req.radius,
    )
    if plan:
        return {**plan.model_dump(mode="json"), "source": "algorithmic"}
    return {"error": f"Could not generate plan for {req.city}"}
