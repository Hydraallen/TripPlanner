from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from tripplanner.core.models import (
    Attraction,
    DayPlan,
    GenerationProgress,
    Location,
    PlanAlternative,
    PlanFocus,
    TripPlan,
)
from tripplanner.web.services.plan_generator import PlanGenerator


def _make_attraction(name: str = "Museum", lat: float = 35.68, lon: float = 139.69) -> Attraction:
    return Attraction(
        xid=f"N_{name}",
        name=name,
        location=Location(longitude=lon, latitude=lat),
        kinds="museums",
        rating=4.0,
        visit_duration=90,
    )


def _make_plan(city: str = "Tokyo") -> TripPlan:
    return TripPlan(
        city=city,
        start_date=date(2026, 4, 10),
        end_date=date(2026, 4, 12),
        days=[
            DayPlan(
                date=date(2026, 4, 10),
                day_number=1,
                attractions=[_make_attraction()],
            ),
        ],
    )


class TestPlanGenerator:
    @pytest.mark.asyncio
    async def test_generate_with_llm(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=_make_plan())

        gen = PlanGenerator(llm=mock_llm)
        places = [_make_attraction(f"P{i}") for i in range(5)]

        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=places,
        )

        assert len(results) == 3
        assert all(isinstance(r, PlanAlternative) for r in results)
        assert results[0].source == "llm"
        assert results[0].scores is not None
        assert results[0].focus == PlanFocus.BUDGET

    @pytest.mark.asyncio
    async def test_generate_llm_fails_falls_back_per_plan(self) -> None:
        mock_llm = AsyncMock()
        # LLM returns None for all calls
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=None)

        gen = PlanGenerator(llm=mock_llm)
        places = [_make_attraction(f"P{i}") for i in range(5)]

        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=places,
        )

        # Should get algorithmic fallback plans
        assert len(results) == 3
        assert all(r.source == "algorithmic" for r in results)

    @pytest.mark.asyncio
    async def test_generate_no_llm(self) -> None:
        gen = PlanGenerator(llm=None)
        places = [_make_attraction(f"P{i}") for i in range(5)]

        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=places,
        )

        assert len(results) == 3
        assert all(r.source == "algorithmic" for r in results)

    @pytest.mark.asyncio
    async def test_generate_no_places(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=_make_plan())

        gen = PlanGenerator(llm=mock_llm)

        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
        )

        # LLM still called even without places
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_progress_callback(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=_make_plan())

        gen = PlanGenerator(llm=mock_llm)
        progress_events: list[GenerationProgress] = []

        def on_progress(p: GenerationProgress) -> None:
            progress_events.append(p)

        await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=[_make_attraction()],
            on_progress=on_progress,
        )

        assert len(progress_events) == 3
        assert progress_events[0].status == "generating"
        assert "budget" in progress_events[0].step
        assert progress_events[0].progress >= 30

    @pytest.mark.asyncio
    async def test_different_focuses(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=_make_plan())

        gen = PlanGenerator(llm=mock_llm)
        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=[_make_attraction()],
        )

        focuses = [r.focus for r in results]
        assert PlanFocus.BUDGET in focuses
        assert PlanFocus.CULTURE in focuses
        assert PlanFocus.NATURE in focuses

    @pytest.mark.asyncio
    async def test_scores_populated(self) -> None:
        mock_llm = AsyncMock()
        mock_llm.generate_plan_with_focus = AsyncMock(return_value=_make_plan())

        gen = PlanGenerator(llm=mock_llm)
        results = await gen.generate_alternatives(
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 12),
            interests=["museums"],
            places=[_make_attraction()],
        )

        for r in results:
            assert r.scores is not None
            assert 0 <= r.scores.total <= 1
