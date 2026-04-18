from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from tripplanner.web.services.planning import generate_plan

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanRequest(BaseModel):
    city: str
    start_date: date
    end_date: date
    interests: list[str] = ["interesting_places"]
    transport_mode: str = "walking"
    radius: int | None = None


@router.post("/generate")
async def generate_plan_endpoint(req: PlanRequest) -> dict[str, Any]:
    """Generate a travel plan based on user preferences.

    Supports both Chinese (Amap) and international (OpenTripMap) destinations.
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
