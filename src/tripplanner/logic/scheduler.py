from __future__ import annotations

from datetime import date, timedelta

from tripplanner.core.config import get_settings
from tripplanner.core.models import DayPlan, Meal, TripPlan
from tripplanner.logic.optimizer import estimate_travel_time, haversine

# Time slot boundaries (hours)
MORNING_START = 9
LUNCH_HOUR = 12
AFTERNOON_START = 13
EVENING_START = 17
DINNER_HOUR = 18
DAY_END = 19  # max 10 hours: 09:00 - 19:00

MAX_CONTENT_MINUTES = (DAY_END - MORNING_START) * 60  # 600


def build_day_plan(
    day_number: int,
    day_date: date,
    attractions: list,
    transport_mode: str = "walking",
) -> DayPlan:
    """Build a single day plan with time slots and meal placeholders."""
    settings = get_settings()
    meals: list[Meal] = []
    description_parts: list[str] = []
    scheduled: list = []
    used_minutes = 0

    for i, attraction in enumerate(attractions):
        visit = attraction.visit_duration or settings.default_visit_duration
        travel = 0

        if scheduled:
            prev = scheduled[-1]
            dist = haversine(
                prev.location.latitude, prev.location.longitude,
                attraction.location.latitude, attraction.location.longitude,
            )
            travel = estimate_travel_time(dist, transport_mode)

        needed = visit + travel

        # Check if adding lunch before this attraction makes sense
        if (
            used_minutes < (LUNCH_HOUR - MORNING_START) * 60 <= used_minutes + needed
            and not any(m.type == "lunch" for m in meals)
        ):
            meals.append(Meal(type="lunch", name="Lunch", estimated_cost=60))
            used_minutes += 60  # 1 hour for lunch

        if used_minutes + needed > MAX_CONTENT_MINUTES:
            overflow_count = len(attractions) - i
            description_parts.append(
                f"{overflow_count} more place(s) could not fit in this day."
            )
            break

        scheduled.append(attraction)
        used_minutes += needed

    # Add dinner if time allows
    if used_minutes < DAY_END * 60 - MORNING_START * 60 and not any(
        m.type == "dinner" for m in meals
    ):
        meals.append(Meal(type="dinner", name="Dinner", estimated_cost=80))

    # Always add breakfast if it's a full day
    if scheduled and not any(m.type == "breakfast" for m in meals):
        meals.insert(0, Meal(type="breakfast", name="Breakfast", estimated_cost=30))

    return DayPlan(
        date=day_date,
        day_number=day_number,
        description="; ".join(description_parts) if description_parts else "",
        transportation=transport_mode,
        attractions=scheduled,
        meals=meals,
    )


def build_itinerary(
    clustered_places: list[list],
    start_date: date,
    end_date: date,
    transport_mode: str = "walking",
) -> TripPlan:
    """Build a complete TripPlan from clustered places."""
    num_days = (end_date - start_date).days + 1
    days: list[DayPlan] = []

    for i in range(num_days):
        day_date = start_date + timedelta(days=i)
        places = clustered_places[i] if i < len(clustered_places) else []
        day = build_day_plan(i + 1, day_date, places, transport_mode)
        days.append(day)

    return TripPlan(
        city="",  # filled by caller
        start_date=start_date,
        end_date=end_date,
        days=days,
    )
