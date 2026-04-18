from __future__ import annotations

import json
from datetime import date

from tripplanner.core.models import (
    Attraction,
    Budget,
    DayPlan,
    Meal,
    TripPlan,
)
from tripplanner.export.html_gen import export_html
from tripplanner.export.json_export import export_json
from tripplanner.export.markdown import export_markdown


def _plan() -> TripPlan:
    return TripPlan(
        city="Tokyo",
        start_date=date(2026, 4, 10),
        end_date=date(2026, 4, 12),
        budget=Budget(
            total_attractions=100, total_hotels=600, total_meals=170, total_transportation=0, total=870
        ),
        days=[
            DayPlan(
                date=date(2026, 4, 10),
                day_number=1,
                attractions=[
                    Attraction(
                        xid="N1", name="Tokyo Tower",
                        location={"longitude": 139.75, "latitude": 35.66},
                        rating=4.5, ticket_price=50,
                    )
                ],
                meals=[
                    Meal(type="breakfast", name="Cafe", estimated_cost=30),
                    Meal(type="lunch", name="Ramen", estimated_cost=60),
                    Meal(type="dinner", name="Sushi", estimated_cost=80),
                ],
            ),
            DayPlan(
                date=date(2026, 4, 11),
                day_number=2,
                attractions=[],
            ),
        ],
        suggestions=["Bring umbrella"],
    )


class TestMarkdownExport:
    def test_contains_city(self) -> None:
        md = export_markdown(_plan())
        assert "# Tokyo Trip Plan" in md

    def test_contains_dates(self) -> None:
        md = export_markdown(_plan())
        assert "2026-04-10" in md
        assert "2026-04-12" in md

    def test_contains_budget(self) -> None:
        md = export_markdown(_plan())
        assert "## Budget Overview" in md
        assert "870" in md

    def test_contains_attraction(self) -> None:
        md = export_markdown(_plan())
        assert "Tokyo Tower" in md

    def test_contains_meals(self) -> None:
        md = export_markdown(_plan())
        assert "Breakfast" in md
        assert "Ramen" in md

    def test_contains_suggestions(self) -> None:
        md = export_markdown(_plan())
        assert "Bring umbrella" in md

    def test_empty_plan(self) -> None:
        plan = TripPlan(city="X", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        md = export_markdown(plan)
        assert "# X Trip Plan" in md

    def test_no_budget_no_section(self) -> None:
        plan = TripPlan(city="X", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        md = export_markdown(plan)
        assert "Budget Overview" not in md


class TestJsonExport:
    def test_valid_json(self) -> None:
        result = export_json(_plan())
        data = json.loads(result)
        assert data["city"] == "Tokyo"

    def test_round_trip(self) -> None:
        plan = _plan()
        result = export_json(plan)
        data = json.loads(result)
        restored = TripPlan.model_validate(data)
        assert restored.city == plan.city
        assert len(restored.days) == len(plan.days)

    def test_excludes_none(self) -> None:
        plan = TripPlan(city="X", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        result = export_json(plan)
        assert "budget" not in result


class TestHtmlExport:
    def test_valid_html(self) -> None:
        html = export_html(_plan())
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_contains_city(self) -> None:
        html = export_html(_plan())
        assert "Tokyo" in html

    def test_contains_budget_table(self) -> None:
        html = export_html(_plan())
        assert "Budget Overview" in html
        assert "870" in html

    def test_contains_attraction(self) -> None:
        html = export_html(_plan())
        assert "Tokyo Tower" in html

    def test_empty_plan(self) -> None:
        plan = TripPlan(city="X", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        html = export_html(plan)
        assert "X Trip Plan" in html
