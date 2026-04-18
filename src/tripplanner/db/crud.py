from __future__ import annotations

import json
import uuid
from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tripplanner.core.models import GenerationProgress, PlanAlternative, Trip, TripPlan
from tripplanner.db.models import Base, TripRow


async def init_db(url: str = "sqlite+aiosqlite:///./trips.db") -> async_sessionmaker[AsyncSession]:
    """Initialize database and create tables. Returns a session factory."""
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def save_trip(session: AsyncSession, trip: Trip) -> str:
    """Save a trip to the database. Returns the trip ID."""
    trip_id = trip.id or str(uuid.uuid4())
    row = TripRow(
        id=trip_id,
        city=trip.city,
        start_date=trip.start_date,
        end_date=trip.end_date,
        interests=json.dumps(trip.interests),
        transport_mode=trip.transport_mode,
        plan_json=trip.plan.model_dump_json(exclude_none=True) if trip.plan else None,
        created_at=trip.created_at or datetime.now(),
    )
    session.add(row)
    await session.commit()
    return trip_id


async def get_trip(session: AsyncSession, trip_id: str) -> Trip | None:
    """Get a trip by ID. Returns None if not found."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    return _row_to_trip(row)


async def list_trips(session: AsyncSession, limit: int = 50) -> list[Trip]:
    """List trips sorted by created_at descending."""
    result = await session.execute(
        select(TripRow).order_by(TripRow.created_at.desc()).limit(limit)
    )
    return [_row_to_trip(row) for row in result.scalars().all()]


async def delete_trip(session: AsyncSession, trip_id: str) -> bool:
    """Delete a trip. Returns True if deleted, False if not found."""
    result = await session.execute(delete(TripRow).where(TripRow.id == trip_id))
    await session.commit()
    return result.rowcount > 0


def _row_to_trip(row: TripRow) -> Trip:
    plan: TripPlan | None = None
    if row.plan_json:
        plan = TripPlan.model_validate_json(row.plan_json)
    elif row.generated_plans and row.selected_plan_id:
        plans = [PlanAlternative.model_validate(p) for p in json.loads(row.generated_plans)]
        for alt in plans:
            if alt.id == row.selected_plan_id:
                plan = alt.plan
                break
        if not plan and plans:
            plan = plans[0].plan

    return Trip(
        id=row.id,
        city=row.city,
        start_date=row.start_date,
        end_date=row.end_date,
        interests=json.loads(row.interests),
        transport_mode=row.transport_mode,
        plan=plan,
        created_at=row.created_at,
    )


async def create_trip_draft(
    session: AsyncSession,
    city: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    transport_mode: str = "walking",
    budget: float | None = None,
) -> str:
    """Create a draft trip record for multi-plan generation. Returns trip ID."""
    trip_id = str(uuid.uuid4())
    row = TripRow(
        id=trip_id,
        city=city,
        start_date=start_date,
        end_date=end_date,
        interests=json.dumps(interests),
        transport_mode=transport_mode,
        status="collecting",
        progress_data=json.dumps(
            {"plan_id": trip_id, "status": "collecting", "progress": 0, "step": ""}
        ),
        created_at=datetime.now(),
    )
    session.add(row)
    await session.commit()
    return trip_id


async def update_trip_status(session: AsyncSession, trip_id: str, status: str) -> None:
    """Update trip generation status."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if row:
        row.status = status
        await session.commit()


async def update_trip_progress(
    session: AsyncSession, trip_id: str, progress: GenerationProgress
) -> None:
    """Update trip generation progress."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if row:
        row.status = progress.status
        row.progress_data = progress.model_dump_json()
        await session.commit()


async def save_generated_plans(
    session: AsyncSession, trip_id: str, plans: list[PlanAlternative]
) -> None:
    """Save generated plan alternatives."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if row:
        row.generated_plans = json.dumps([p.model_dump(mode="json") for p in plans])
        row.status = "completed"
        row.progress_data = json.dumps(
            {"plan_id": trip_id, "status": "completed", "progress": 100, "step": "Done!"}
        )
        await session.commit()


async def get_plan_alternatives(session: AsyncSession, trip_id: str) -> list[PlanAlternative]:
    """Get all plan alternatives for a trip."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if not row or not row.generated_plans:
        return []
    return [PlanAlternative.model_validate(p) for p in json.loads(row.generated_plans)]


async def select_plan(session: AsyncSession, trip_id: str, plan_id: str) -> bool:
    """Select a plan alternative as the active plan. Returns False if plan_id not found."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if not row or not row.generated_plans:
        return False

    plans = [PlanAlternative.model_validate(p) for p in json.loads(row.generated_plans)]
    found = any(p.id == plan_id for p in plans)
    if not found:
        return False

    row.selected_plan_id = plan_id
    for alt in plans:
        if alt.id == plan_id:
            row.plan_json = alt.plan.model_dump_json(exclude_none=True)
            break
    await session.commit()
    return True


async def get_progress(session: AsyncSession, trip_id: str) -> GenerationProgress | None:
    """Get generation progress for a trip."""
    result = await session.execute(select(TripRow).where(TripRow.id == trip_id))
    row = result.scalar_one_or_none()
    if not row or not row.progress_data:
        return None
    return GenerationProgress.model_validate_json(row.progress_data)
