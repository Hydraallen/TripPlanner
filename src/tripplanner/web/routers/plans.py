from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tripplanner.core.config import get_settings
from tripplanner.db.crud import get_plan_alternatives, get_progress
from tripplanner.db.crud import select_plan as db_select_plan
from tripplanner.web.deps import get_session
from tripplanner.web.services.planning import generate_multi_plan
from tripplanner.web.services.progress import progress_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


class MultiPlanRequest(BaseModel):
    city: str
    start_date: date
    end_date: date
    interests: list[str] = ["interesting_places"]
    transport_mode: str = "walking"
    budget: float | None = None
    radius: int | None = None
    num_plans: int = 5
    transport_user_specified: bool = False


class SelectPlanRequest(BaseModel):
    plan_id: str


@router.post("/generate")
async def generate_plans_endpoint(
    req: MultiPlanRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Start multi-plan generation. Returns trip_id immediately.

    Use GET /plans/{trip_id}/progress to track progress via SSE.
    Use GET /plans/{trip_id}/plans to get the alternatives when done.
    """
    from tripplanner.db.crud import create_trip_draft

    # Create draft trip quickly in this request's session
    trip_id = await create_trip_draft(
        session,
        city=req.city,
        start_date=req.start_date,
        end_date=req.end_date,
        interests=req.interests,
        transport_mode=req.transport_mode,
        budget=req.budget,
    )

    # Run the heavy generation in background (creates its own DB session)
    asyncio.create_task(
        _background_generate(
            trip_id=trip_id,
            city=req.city,
            start_date=req.start_date,
            end_date=req.end_date,
            interests=req.interests,
            transport_mode=req.transport_mode,
            budget=req.budget,
            radius=req.radius,
            num_plans=min(req.num_plans, 6),
            transport_user_specified=req.transport_user_specified,
        )
    )
    return {"trip_id": trip_id}


async def _background_generate(
    trip_id: str,
    city: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    transport_mode: str = "walking",
    budget: float | None = None,
    radius: int | None = None,
    num_plans: int = 5,
    transport_user_specified: bool = True,
) -> None:
    """Run plan generation in background with its own DB session."""
    from tripplanner.web.services.planning import _run_generation

    await _run_generation(
        trip_id=trip_id,
        city=city,
        start_date=start_date,
        end_date=end_date,
        interests=interests,
        transport_mode=transport_mode,
        budget=budget,
        radius=radius,
        num_plans=num_plans,
        transport_user_specified=transport_user_specified,
    )


@router.get("/{trip_id}/progress")
async def progress_sse_endpoint(trip_id: str) -> Any:
    """SSE endpoint for real-time plan generation progress."""
    from fastapi.responses import StreamingResponse

    async def event_stream() -> Any:
        queue = progress_tracker.subscribe(trip_id)

        # Send current state if available
        current = progress_tracker.get(trip_id)
        if current:
            yield f"data: {current.model_dump_json()}\n\n"
            if current.status in ("completed", "failed"):
                progress_tracker.unsubscribe(trip_id, queue)
                return
        else:
            # Check database for initial state
            factory = await _get_factory()
            async with factory() as sess:
                db_prog = await get_progress(sess, trip_id)
            if db_prog:
                yield f"data: {db_prog.model_dump_json()}\n\n"
                if db_prog.status in ("completed", "failed"):
                    progress_tracker.unsubscribe(trip_id, queue)
                    return

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    import json

                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("status") in ("completed", "failed"):
                        break
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            progress_tracker.unsubscribe(trip_id, queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{trip_id}/plans")
async def get_plans_endpoint(
    trip_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get all plan alternatives for a trip."""
    alternatives = await get_plan_alternatives(session, trip_id)
    if not alternatives:
        prog = await get_progress(session, trip_id)
        if prog and prog.status not in ("completed",):
            return {"status": prog.status, "plans": []}
        raise HTTPException(status_code=404, detail="No plans found for this trip")

    return {
        "status": "completed",
        "plans": [a.model_dump(mode="json") for a in alternatives],
    }


@router.post("/{trip_id}/select")
async def select_plan_endpoint(
    trip_id: str,
    req: SelectPlanRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Select a plan alternative as the active plan."""
    ok = await db_select_plan(session, trip_id, req.plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "selected", "plan_id": req.plan_id}


async def _get_factory() -> Any:
    from tripplanner.db.crud import init_db

    settings = get_settings()
    return await init_db(settings.database_url)
