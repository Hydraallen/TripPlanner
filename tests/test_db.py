from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tripplanner.core.models import Trip, TripPlan
from tripplanner.db.cache import clear_expired, get_cached, set_cached
from tripplanner.db.crud import delete_trip, get_trip, init_db, list_trips, save_trip
from tripplanner.db.models import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(session_factory):
    async with session_factory() as s:
        yield s


def _trip(city: str = "Tokyo") -> Trip:
    return Trip(
        id="test-id-1",
        city=city,
        start_date=date(2026, 4, 10),
        end_date=date(2026, 4, 13),
        interests=["museums", "food"],
        transport_mode="walking",
        created_at=datetime(2026, 4, 9, 12, 0),
    )


# --- CRUD ---


class TestCRUD:
    @pytest.mark.asyncio
    async def test_save_and_get(self, session: AsyncSession) -> None:
        trip = _trip()
        await save_trip(session, trip)
        result = await get_trip(session, "test-id-1")
        assert result is not None
        assert result.city == "Tokyo"
        assert result.interests == ["museums", "food"]

    @pytest.mark.asyncio
    async def test_get_not_found(self, session: AsyncSession) -> None:
        result = await get_trip(session, "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_trips(self, session: AsyncSession) -> None:
        for i in range(3):
            trip = _trip(f"City{i}")
            trip.id = f"id-{i}"
            trip.created_at = datetime(2026, 4, 9, 12, i)
            await save_trip(session, trip)
        trips = await list_trips(session)
        assert len(trips) == 3
        # Sorted by created_at desc
        assert trips[0].city == "City2"

    @pytest.mark.asyncio
    async def test_list_limit(self, session: AsyncSession) -> None:
        for i in range(5):
            trip = _trip(f"City{i}")
            trip.id = f"id-{i}"
            await save_trip(session, trip)
        trips = await list_trips(session, limit=2)
        assert len(trips) == 2

    @pytest.mark.asyncio
    async def test_delete(self, session: AsyncSession) -> None:
        await save_trip(session, _trip())
        deleted = await delete_trip(session, "test-id-1")
        assert deleted is True
        result = await get_trip(session, "test-id-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, session: AsyncSession) -> None:
        deleted = await delete_trip(session, "nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_save_with_plan(self, session: AsyncSession) -> None:
        plan = TripPlan(city="Tokyo", start_date=date(2026, 4, 10), end_date=date(2026, 4, 13))
        trip = _trip()
        trip.plan = plan
        await save_trip(session, trip)
        result = await get_trip(session, "test-id-1")
        assert result is not None
        assert result.plan is not None
        assert result.plan.city == "Tokyo"


# --- Cache ---


class TestCache:
    @pytest.mark.asyncio
    async def test_set_and_get(self, session: AsyncSession) -> None:
        await set_cached(session, "key1", {"data": "value"}, ttl=3600)
        result = await get_cached(session, "key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_expired(self, session: AsyncSession) -> None:
        await set_cached(session, "key2", {"data": "old"}, ttl=-1)
        result = await get_cached(session, "key2")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_not_cached(self, session: AsyncSession) -> None:
        result = await get_cached(session, "nokey")
        assert result is None

    @pytest.mark.asyncio
    async def test_overwrite(self, session: AsyncSession) -> None:
        await set_cached(session, "key3", {"v": 1}, ttl=3600)
        await set_cached(session, "key3", {"v": 2}, ttl=3600)
        result = await get_cached(session, "key3")
        assert result == {"v": 2}

    @pytest.mark.asyncio
    async def test_clear_expired(self, session: AsyncSession) -> None:
        await set_cached(session, "expired", {"x": 1}, ttl=-1)
        await set_cached(session, "valid", {"x": 2}, ttl=3600)
        count = await clear_expired(session)
        assert count == 1
        assert await get_cached(session, "valid") == {"x": 2}
