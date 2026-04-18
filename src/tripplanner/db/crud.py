from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tripplanner.core.models import Trip, TripPlan
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
