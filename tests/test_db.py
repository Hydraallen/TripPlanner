from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tripplanner.core.models import (
    DayPlan,
    GenerationProgress,
    PlanAlternative,
    PlanFocus,
    PlanScores,
    Trip,
    TripPlan,
)
from tripplanner.db.cache import clear_expired, get_cached, set_cached
from tripplanner.db.crud import (
    create_trip_draft,
    delete_trip,
    get_plan_alternatives,
    get_progress,
    get_trip,
    init_db,
    list_trips,
    save_generated_plans,
    save_trip,
    select_plan,
    update_trip_progress,
    update_trip_status,
)
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


# --- Multi-Plan CRUD ---


def _make_plan(city: str = "Tokyo") -> TripPlan:
    return TripPlan(
        city=city,
        start_date=date(2026, 4, 10),
        end_date=date(2026, 4, 13),
        days=[DayPlan(date=date(2026, 4, 10), day_number=1)],
    )


def _make_alternatives() -> list[PlanAlternative]:
    return [
        PlanAlternative(
            id="plan_1",
            focus=PlanFocus.BUDGET,
            title="Budget-Friendly",
            plan=_make_plan(),
            scores=PlanScores(price=0.9, rating=0.6, total=0.75),
            estimated_cost=3000,
        ),
        PlanAlternative(
            id="plan_2",
            focus=PlanFocus.CULTURE,
            title="Culture Explorer",
            plan=_make_plan(),
            scores=PlanScores(price=0.5, rating=0.8, total=0.7),
            estimated_cost=5000,
        ),
        PlanAlternative(
            id="plan_3",
            focus=PlanFocus.NATURE,
            title="Nature Retreat",
            plan=_make_plan(),
            scores=PlanScores(price=0.7, rating=0.7, total=0.72),
            estimated_cost=4000,
        ),
    ]


class TestMultiPlanCRUD:
    @pytest.mark.asyncio
    async def test_create_trip_draft(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session,
            city="Paris",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            interests=["museums"],
        )
        assert trip_id
        trip = await get_trip(session, trip_id)
        assert trip is not None
        assert trip.city == "Paris"
        assert trip.plan is None

    @pytest.mark.asyncio
    async def test_update_trip_status(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Berlin", date(2026, 6, 1), date(2026, 6, 3), ["food"]
        )
        await update_trip_status(session, trip_id, "generating")
        progress = await get_progress(session, trip_id)
        # status updated but progress_data is still the initial one
        trip = await get_trip(session, trip_id)
        assert trip is not None

    @pytest.mark.asyncio
    async def test_update_trip_progress(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "London", date(2026, 7, 1), date(2026, 7, 3), ["parks"]
        )
        prog = GenerationProgress(
            plan_id=trip_id,
            status="generating",
            progress=50.0,
            step="Generating culture plan... (2/3)",
        )
        await update_trip_progress(session, trip_id, prog)
        result = await get_progress(session, trip_id)
        assert result is not None
        assert result.status == "generating"
        assert result.progress == 50.0

    @pytest.mark.asyncio
    async def test_save_and_get_alternatives(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Rome", date(2026, 8, 1), date(2026, 8, 3), ["history"]
        )
        alts = _make_alternatives()
        await save_generated_plans(session, trip_id, alts)

        result = await get_plan_alternatives(session, trip_id)
        assert len(result) == 3
        assert result[0].focus == PlanFocus.BUDGET
        assert result[1].title == "Culture Explorer"

    @pytest.mark.asyncio
    async def test_get_alternatives_empty(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Madrid", date(2026, 9, 1), date(2026, 9, 3), ["art"]
        )
        result = await get_plan_alternatives(session, trip_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_select_plan(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Vienna", date(2026, 10, 1), date(2026, 10, 3), ["music"]
        )
        alts = _make_alternatives()
        await save_generated_plans(session, trip_id, alts)

        ok = await select_plan(session, trip_id, "plan_2")
        assert ok is True

        trip = await get_trip(session, trip_id)
        assert trip is not None
        assert trip.plan is not None
        assert trip.plan.city == "Tokyo"

    @pytest.mark.asyncio
    async def test_select_plan_not_found(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Prague", date(2026, 11, 1), date(2026, 11, 3), ["castles"]
        )
        alts = _make_alternatives()
        await save_generated_plans(session, trip_id, alts)

        ok = await select_plan(session, trip_id, "plan_99")
        assert ok is False

    @pytest.mark.asyncio
    async def test_get_progress_none(self, session: AsyncSession) -> None:
        result = await get_progress(session, "nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_progress_after_save_plans(self, session: AsyncSession) -> None:
        trip_id = await create_trip_draft(
            session, "Oslo", date(2026, 12, 1), date(2026, 12, 3), ["nature"]
        )
        alts = _make_alternatives()
        await save_generated_plans(session, trip_id, alts)

        progress = await get_progress(session, trip_id)
        assert progress is not None
        assert progress.status == "completed"
        assert progress.progress == 100
