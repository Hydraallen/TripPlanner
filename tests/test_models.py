import json
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from tripplanner.core.models import (
    Attraction,
    Budget,
    DayPlan,
    GenerationProgress,
    Hotel,
    Location,
    Meal,
    PlanAlternative,
    PlanFocus,
    PlanScores,
    Trip,
    TripPlan,
    WeatherInfo,
)


# --- Location ---


class TestLocation:
    def test_valid_float(self) -> None:
        loc = Location(longitude=139.69, latitude=35.68)
        assert loc.longitude == 139.69

    def test_coerce_int(self) -> None:
        loc = Location(longitude=139, latitude=35)
        assert loc.longitude == 139.0

    def test_coerce_string(self) -> None:
        loc = Location(longitude="45.5", latitude="45.5")
        assert loc.longitude == 45.5

    def test_coerce_comma_decimal(self) -> None:
        loc = Location(longitude="45,5", latitude="45,5")
        assert loc.longitude == 45.5

    def test_rejects_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            Location(longitude=200, latitude=0)
        with pytest.raises(ValidationError):
            Location(longitude=0, latitude=-100)

    def test_round_trip(self) -> None:
        loc = Location(longitude=139.69, latitude=35.68)
        assert Location.model_validate(loc.model_dump()) == loc


# --- Attraction ---


class TestAttraction:
    def _make(self, **overrides: object) -> Attraction:
        defaults = {
            "xid": "N123",
            "name": "Tokyo Tower",
            "location": {"longitude": 139.75, "latitude": 35.66},
        }
        defaults.update(overrides)
        return Attraction.model_validate(defaults)

    def test_basic(self) -> None:
        a = self._make()
        assert a.xid == "N123"
        assert a.visit_duration == 90

    def test_rating_none(self) -> None:
        a = self._make(rating=None)
        assert a.rating is None

    def test_rating_clamp_high(self) -> None:
        a = self._make(rating=6.0)
        assert a.rating == 5.0

    def test_rating_clamp_negative(self) -> None:
        a = self._make(rating=-1.0)
        assert a.rating == 0.0

    def test_rating_normal(self) -> None:
        a = self._make(rating=4.5)
        assert a.rating == 4.5

    def test_score_default(self) -> None:
        a = self._make()
        assert a.score == 0.0

    def test_round_trip(self) -> None:
        a = self._make(rating=4.2, ticket_price=15.0, kinds="museums")
        data = json.loads(a.model_dump_json())
        assert Attraction.model_validate(data) == a


# --- Meal ---


class TestMeal:
    def test_basic(self) -> None:
        m = Meal(type="lunch", name="Ramen Shop", estimated_cost=60)
        assert m.type == "lunch"
        assert m.estimated_cost == 60

    def test_negative_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Meal(type="dinner", name="A", estimated_cost=-10)

    def test_round_trip(self) -> None:
        m = Meal(type="breakfast", name="Cafe", estimated_cost=30)
        assert Meal.model_validate(m.model_dump()) == m


# --- Hotel ---


class TestHotel:
    def test_basic(self) -> None:
        h = Hotel(name="Grand Hotel", estimated_cost_per_night=600)
        assert h.estimated_cost_per_night == 600

    def test_round_trip(self) -> None:
        h = Hotel(name="Inn", rating=4.0, price_range="mid-range")
        assert Hotel.model_validate(h.model_dump()) == h


# --- Budget ---


class TestBudget:
    def test_default_zeros(self) -> None:
        b = Budget()
        assert b.total == 0

    def test_auto_total(self) -> None:
        b = Budget(total_attractions=100, total_hotels=300, total_meals=150, total_transportation=50)
        assert b.total == 600

    def test_explicit_total(self) -> None:
        b = Budget(total_attractions=100, total=100)
        assert b.total == 100

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Budget(total_attractions=-10)

    def test_round_trip(self) -> None:
        b = Budget(total_attractions=100, total_hotels=200, total_meals=80, total_transportation=30)
        assert Budget.model_validate(b.model_dump()) == b


# --- WeatherInfo ---


class TestWeatherInfo:
    def test_basic(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=22, temp_low=12)
        assert w.temp_high == 22

    def test_is_rainy_true(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=15, temp_low=8, precipitation_prob=80)
        assert w.is_rainy is True

    def test_is_rainy_false(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=20, temp_low=10, precipitation_prob=30)
        assert w.is_rainy is False

    def test_description_clear(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=20, temp_low=10, weather_code=0)
        assert w.description == "Clear"

    def test_description_rain(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=15, temp_low=8, weather_code=61)
        assert w.description == "Rain"

    def test_description_unknown(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=15, temp_low=8, weather_code=999)
        assert w.description == "Unknown"

    def test_round_trip(self) -> None:
        w = WeatherInfo(date=date(2026, 4, 10), temp_high=22, temp_low=12, weather_code=2)
        assert WeatherInfo.model_validate(w.model_dump()) == w


# --- DayPlan ---


class TestDayPlan:
    def test_basic(self) -> None:
        dp = DayPlan(date=date(2026, 4, 10), day_number=1)
        assert dp.day_number == 1
        assert dp.attractions == []

    def test_rejects_zero_day(self) -> None:
        with pytest.raises(ValidationError):
            DayPlan(date=date(2026, 4, 10), day_number=0)

    def test_rejects_negative_day(self) -> None:
        with pytest.raises(ValidationError):
            DayPlan(date=date(2026, 4, 10), day_number=-1)

    def test_with_attractions(self) -> None:
        a = Attraction(
            xid="N1", name="Museum",
            location={"longitude": 0, "latitude": 0},
        )
        dp = DayPlan(date=date(2026, 4, 10), day_number=1, attractions=[a])
        assert len(dp.attractions) == 1

    def test_round_trip(self) -> None:
        dp = DayPlan(date=date(2026, 4, 10), day_number=2, transportation="transit")
        assert DayPlan.model_validate(dp.model_dump()) == dp


# --- TripPlan ---


class TestTripPlan:
    def test_basic(self) -> None:
        tp = TripPlan(city="Tokyo", start_date=date(2026, 4, 10), end_date=date(2026, 4, 13))
        assert tp.city == "Tokyo"
        assert tp.days == []

    def test_with_days(self) -> None:
        days = [
            DayPlan(date=date(2026, 4, 10), day_number=1),
            DayPlan(date=date(2026, 4, 11), day_number=2),
        ]
        tp = TripPlan(city="Tokyo", start_date=date(2026, 4, 10), end_date=date(2026, 4, 11), days=days)
        assert len(tp.days) == 2

    def test_round_trip(self) -> None:
        tp = TripPlan(
            city="Paris",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            suggestions=["Bring umbrella"],
        )
        data = json.loads(tp.model_dump_json())
        assert TripPlan.model_validate(data) == tp


# --- Trip ---


class TestTrip:
    def test_basic(self) -> None:
        t = Trip(
            id="abc-123",
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 13),
            interests=["museums", "food"],
            created_at=datetime(2026, 4, 9, 12, 0),
        )
        assert t.id == "abc-123"
        assert t.plan is None

    def test_with_plan(self) -> None:
        plan = TripPlan(city="Tokyo", start_date=date(2026, 4, 10), end_date=date(2026, 4, 13))
        t = Trip(
            id="abc-123",
            city="Tokyo",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 13),
            interests=["museums"],
            plan=plan,
            created_at=datetime(2026, 4, 9, 12, 0),
        )
        assert t.plan is not None
        assert t.plan.city == "Tokyo"

    def test_round_trip(self) -> None:
        t = Trip(
            id="abc-123",
            city="Paris",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 3),
            interests=["food", "art"],
            created_at=datetime(2026, 4, 30, 10, 0),
        )
        data = json.loads(t.model_dump_json())
        assert Trip.model_validate(data) == t


# --- PlanFocus ---


class TestPlanFocus:
    def test_values(self) -> None:
        assert PlanFocus.BUDGET == "budget"
        assert PlanFocus.CULTURE == "culture"
        assert PlanFocus.NATURE == "nature"

    def test_from_string(self) -> None:
        assert PlanFocus("budget") is PlanFocus.BUDGET


# --- PlanScores ---


class TestPlanScores:
    def test_defaults(self) -> None:
        s = PlanScores()
        assert s.total == 0.0

    def test_custom_values(self) -> None:
        s = PlanScores(price=0.8, rating=0.7, convenience=0.6, diversity=0.9)
        assert s.price == 0.8

    def test_rejects_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            PlanScores(price=1.5)

    def test_round_trip(self) -> None:
        s = PlanScores(price=0.5, rating=0.6, convenience=0.7, diversity=0.8, total=0.65)
        assert PlanScores.model_validate(s.model_dump()) == s


# --- PlanAlternative ---


class TestPlanAlternative:
    def _make_plan(self) -> TripPlan:
        return TripPlan(city="Tokyo", start_date=date(2026, 4, 10), end_date=date(2026, 4, 13))

    def test_basic(self) -> None:
        alt = PlanAlternative(
            id="plan_1",
            focus=PlanFocus.BUDGET,
            title="Budget-Friendly",
            plan=self._make_plan(),
        )
        assert alt.focus == PlanFocus.BUDGET
        assert alt.source == "llm"
        assert alt.estimated_cost == 0

    def test_with_scores(self) -> None:
        scores = PlanScores(price=0.9, rating=0.6, total=0.75)
        alt = PlanAlternative(
            id="plan_2",
            focus=PlanFocus.CULTURE,
            title="Culture Explorer",
            plan=self._make_plan(),
            scores=scores,
            estimated_cost=5000,
        )
        assert alt.scores is not None
        assert alt.scores.total == 0.75
        assert alt.estimated_cost == 5000

    def test_round_trip(self) -> None:
        alt = PlanAlternative(
            id="plan_3",
            focus=PlanFocus.NATURE,
            title="Nature Retreat",
            description="Relaxing nature trip",
            plan=self._make_plan(),
            scores=PlanScores(diversity=0.8),
        )
        data = json.loads(alt.model_dump_json())
        assert PlanAlternative.model_validate(data) == alt


# --- GenerationProgress ---


class TestGenerationProgress:
    def test_defaults(self) -> None:
        p = GenerationProgress(plan_id="abc")
        assert p.status == "collecting"
        assert p.progress == 0

    def test_custom(self) -> None:
        p = GenerationProgress(
            plan_id="abc",
            status="generating",
            progress=50.0,
            step="Generating culture plan... (2/3)",
        )
        assert p.progress == 50.0
        assert "2/3" in p.step

    def test_with_preview(self) -> None:
        p = GenerationProgress(
            plan_id="abc",
            status="collecting",
            progress=20,
            preview={"places_found": 15},
        )
        assert p.preview == {"places_found": 15}

    def test_rejects_over_100(self) -> None:
        with pytest.raises(ValidationError):
            GenerationProgress(plan_id="abc", progress=150)

    def test_round_trip(self) -> None:
        p = GenerationProgress(
            plan_id="abc",
            status="completed",
            progress=100,
            step="Done!",
        )
        assert GenerationProgress.model_validate(p.model_dump()) == p
