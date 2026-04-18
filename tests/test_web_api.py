from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tripplanner.core.models import (
    Budget,
    DayPlan,
    PlanAlternative,
    PlanFocus,
    PlanScores,
    Trip,
    TripPlan,
)
from tripplanner.web.app import create_app
from tripplanner.web.deps import get_session


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def app(mock_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: mock_session
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_trip() -> Trip:
    return Trip(
        id="test-123",
        city="Tokyo",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 3),
        interests=["museums", "food"],
        transport_mode="walking",
        plan=TripPlan(
            city="Tokyo",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            days=[
                DayPlan(
                    date=date(2026, 5, 1),
                    day_number=1,
                    attractions=[],
                    meals=[],
                )
            ],
            budget=Budget(total_attractions=500, total_meals=300, total=800),
        ),
        created_at=datetime(2026, 5, 1),
    )


def _mock_crud(trips: list[Trip] | None = None, saved_id: str = "test-123"):
    trip_list = trips or []

    async def mock_list(session, limit=50):
        return trip_list

    async def mock_get(session, trip_id):
        for t in trip_list:
            if t.id == trip_id:
                return t
        return None

    async def mock_save(session, trip):
        return saved_id

    async def mock_delete(session, trip_id):
        return any(t.id == trip_id for t in trip_list)

    return mock_list, mock_get, mock_save, mock_delete


class TestListTrips:
    def test_list_empty(self, client):
        mocks = _mock_crud()
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_trips(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["city"] == "Tokyo"


class TestCreateTrip:
    def test_create(self, client):
        mocks = _mock_crud(saved_id="new-456")
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.post(
                "/api/trips",
                params={
                    "city": "Paris",
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-03",
                },
            )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-456"


class TestGetTrip:
    def test_get_existing(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/test-123")
        assert resp.status_code == 200
        assert resp.json()["city"] == "Tokyo"

    def test_get_not_found(self, client):
        mocks = _mock_crud()
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/nonexistent")
        assert resp.status_code == 404


class TestDeleteTrip:
    def test_delete_existing(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.delete("/api/trips/test-123")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_not_found(self, client):
        mocks = _mock_crud()
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.delete("/api/trips/nonexistent")
        assert resp.status_code == 404


class TestExportTrip:
    def test_export_markdown(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/test-123/export?format=markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]

    def test_export_json(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/test-123/export?format=json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

    def test_export_html(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/test-123/export?format=html")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_export_not_found(self, client):
        mocks = _mock_crud()
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/nonexistent/export?format=markdown")
        assert resp.status_code == 404

    def test_export_unsupported_format(self, client, sample_trip):
        mocks = _mock_crud([sample_trip])
        with (
            patch("tripplanner.web.routers.trips.db_list", mocks[0]),
            patch("tripplanner.web.routers.trips.db_get", mocks[1]),
            patch("tripplanner.web.routers.trips.db_save", mocks[2]),
            patch("tripplanner.web.routers.trips.db_delete", mocks[3]),
        ):
            resp = client.get("/api/trips/test-123/export?format=pdf")
        assert resp.status_code == 422


class TestGenerateMultiPlan:
    def test_generate_returns_trip_id(self, client):
        with patch(
            "tripplanner.web.routers.plans.generate_multi_plan",
            new_callable=AsyncMock,
            return_value="trip-abc-123",
        ):
            resp = client.post(
                "/api/plans/generate",
                json={
                    "city": "Tokyo",
                    "start_date": "2026-05-01",
                    "end_date": "2026-05-03",
                    "interests": ["museums"],
                    "transport_mode": "walking",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "trip_id" in data
        assert data["trip_id"] == "trip-abc-123"


def _make_alt(plan_id: str = "plan_1", focus: PlanFocus = PlanFocus.BUDGET) -> PlanAlternative:
    return PlanAlternative(
        id=plan_id,
        focus=focus,
        title="Budget Plan",
        plan=TripPlan(
            city="Tokyo",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            days=[
                DayPlan(date=date(2026, 5, 1), day_number=1),
            ],
        ),
        scores=PlanScores(price=0.8, rating=0.7, total=0.75),
    )


class TestGetPlans:
    def test_get_plans_success(self, client):
        alts = [_make_alt("plan_1"), _make_alt("plan_2", PlanFocus.CULTURE)]
        with patch(
            "tripplanner.web.routers.plans.get_plan_alternatives",
            new_callable=AsyncMock,
            return_value=alts,
        ):
            resp = client.get("/api/plans/trip-123/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["plans"]) == 2

    def test_get_plans_not_found(self, client):
        with patch(
            "tripplanner.web.routers.plans.get_plan_alternatives",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "tripplanner.web.routers.plans.get_progress",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = client.get("/api/plans/nonexistent/plans")
        assert resp.status_code == 404

    def test_get_plans_still_generating(self, client):
        from tripplanner.core.models import GenerationProgress

        with patch(
            "tripplanner.web.routers.plans.get_plan_alternatives",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "tripplanner.web.routers.plans.get_progress",
            new_callable=AsyncMock,
            return_value=GenerationProgress(
                plan_id="trip-123", status="generating", progress=50, step="..."
            ),
        ):
            resp = client.get("/api/plans/trip-123/plans")
        assert resp.status_code == 200
        assert resp.json()["status"] == "generating"


class TestSelectPlan:
    def test_select_success(self, client):
        with patch(
            "tripplanner.web.routers.plans.db_select_plan",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = client.post(
                "/api/plans/trip-123/select",
                json={"plan_id": "plan_2"},
            )
        assert resp.status_code == 200
        assert resp.json()["plan_id"] == "plan_2"

    def test_select_not_found(self, client):
        with patch(
            "tripplanner.web.routers.plans.db_select_plan",
            new_callable=AsyncMock,
            return_value=False,
        ):
            resp = client.post(
                "/api/plans/trip-123/select",
                json={"plan_id": "plan_99"},
            )
        assert resp.status_code == 404


class TestChatEndpoint:
    def test_chat_no_key(self, client):
        with patch("tripplanner.web.routers.chat.get_settings") as mock_settings:
            s = mock_settings.return_value
            s.openai_api_key = None
            resp = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )
        assert resp.status_code == 200
        assert "not configured" in resp.json()["response"]

    def test_chat_success(self, client):
        mock_llm = AsyncMock()
        mock_llm.__aenter__ = AsyncMock(return_value=mock_llm)
        mock_llm.__aexit__ = AsyncMock(return_value=None)
        mock_llm.chat = AsyncMock(return_value="Tokyo is great in May!")

        with (
            patch("tripplanner.web.routers.chat.get_settings") as mock_settings,
            patch("tripplanner.web.routers.chat.LLMClient", return_value=mock_llm),
        ):
            s = mock_settings.return_value
            s.openai_api_key = "test-key"
            resp = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Tell me about Tokyo"}],
                    "plan_context": "User is planning a trip to Tokyo",
                },
            )
        assert resp.status_code == 200
        assert "Tokyo" in resp.json()["response"]
