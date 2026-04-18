from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from tripplanner.core.models import Trip
from tripplanner.db.crud import delete_trip as db_delete
from tripplanner.db.crud import get_trip as db_get
from tripplanner.db.crud import list_trips as db_list
from tripplanner.db.crud import save_trip as db_save
from tripplanner.export.html_gen import export_html
from tripplanner.export.json_export import export_json
from tripplanner.export.markdown import export_markdown
from tripplanner.web.deps import get_session

router = APIRouter(tags=["trips"])


@router.get("/trips", response_model=list[dict[str, Any]])
async def list_trips_endpoint(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    trips = await db_list(session)
    return [
        {
            "id": t.id,
            "city": t.city,
            "start_date": str(t.start_date),
            "end_date": str(t.end_date),
            "transport_mode": t.transport_mode,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trips
    ]


@router.post("/trips", status_code=201)
async def create_trip_endpoint(
    city: str,
    start_date: str,
    end_date: str,
    interests: list[str] | None = None,
    transport_mode: str = "walking",
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    trip = Trip(
        id=str(uuid4()),
        city=city,
        start_date=start_date,
        end_date=end_date,
        interests=interests or [],
        transport_mode=transport_mode,
        created_at=datetime.now(),
    )
    trip_id = await db_save(session, trip)
    return {"id": trip_id}


@router.get("/trips/{trip_id}")
async def get_trip_endpoint(
    trip_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    trip = await db_get(session, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.model_dump(mode="json")


@router.delete("/trips/{trip_id}")
async def delete_trip_endpoint(
    trip_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    deleted = await db_delete(session, trip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"status": "deleted"}


_EXPORT_FORMATS = {
    "markdown": ("text/markdown", export_markdown),
    "json": ("application/json", export_json),
    "html": ("text/html", export_html),
}


@router.get("/trips/{trip_id}/export")
async def export_trip_endpoint(
    trip_id: str,
    format: str = "markdown",
    session: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    if format not in _EXPORT_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format: {format}. Use: {', '.join(_EXPORT_FORMATS)}",
        )

    trip = await db_get(session, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not trip.plan:
        raise HTTPException(status_code=404, detail="Trip has no itinerary to export")

    content_type, exporter = _EXPORT_FORMATS[format]
    content = exporter(trip.plan)
    return PlainTextResponse(content=content, media_type=content_type)
