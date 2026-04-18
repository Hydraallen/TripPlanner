from __future__ import annotations

from datetime import date, timedelta

from tripplanner.core.config import get_visit_duration
from tripplanner.core.models import Attraction, DayPlan, Meal, TripPlan
from tripplanner.logic.optimizer import estimate_travel_time, haversine

# Time slot boundaries (hours)
MORNING_START = 9
LUNCH_HOUR = 12
AFTERNOON_START = 13
DINNER_HOUR = 18
DAY_END = 19  # max 10 hours: 09:00 - 19:00

MAX_CONTENT_MINUTES = (DAY_END - MORNING_START) * 60  # 600


def _fmt(minutes: int) -> str:
    """Format minutes-since-midnight as HH:MM."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _time_slot(start: int, end: int) -> str:
    """Build a HH:MM-HH:MM time slot string."""
    return f"{_fmt(start)}-{_fmt(end)}"


def build_day_plan(
    day_number: int,
    day_date: date,
    attractions: list[Attraction],
    transport_mode: str = "walking",
) -> DayPlan:
    """Build a single day plan with time slots and meal placeholders."""
    meals: list[Meal] = []
    description_parts: list[str] = []
    scheduled: list[Attraction] = []
    current_time = MORNING_START * 60  # 540 min = 09:00

    for i, attraction in enumerate(attractions):
        # Dynamic visit duration by category
        visit = get_visit_duration(attraction.kinds)

        # Commute time from previous attraction
        commute = 0
        if scheduled:
            prev = scheduled[-1]
            dist = haversine(
                prev.location.latitude, prev.location.longitude,
                attraction.location.latitude, attraction.location.longitude,
            )
            commute = estimate_travel_time(dist, transport_mode)

        # Insert breakfast before first attraction
        if i == 0 and not any(m.type == "breakfast" for m in meals):
            meals.append(
                Meal(
                    type="breakfast",
                    name="Breakfast",
                    estimated_cost=30,
                    time_slot="08:00-09:00",
                )
            )
            current_time = MORNING_START * 60

        # Insert lunch when we cross 12:00
        if (
            not any(m.type == "lunch" for m in meals)
            and current_time + commute < LUNCH_HOUR * 60
            and current_time + commute + visit > LUNCH_HOUR * 60
        ):
            meals.append(
                Meal(
                    type="lunch",
                    name="Lunch",
                    estimated_cost=60,
                    time_slot="12:00-13:00",
                )
            )
            current_time = (LUNCH_HOUR + 1) * 60  # resume at 13:00

        # Check if fits in day
        if current_time + commute + visit > DAY_END * 60:
            overflow_count = len(attractions) - i
            description_parts.append(
                f"{overflow_count} more place(s) could not fit in this day."
            )
            break

        # Assign time slot, commute, and dynamic duration
        end_minutes = current_time + commute + visit
        attraction = attraction.model_copy(update={
            "time_slot": _time_slot(current_time + commute, end_minutes),
            "commute_minutes": commute,
            "visit_duration": visit,
        })

        scheduled.append(attraction)
        current_time = end_minutes

    # Ensure lunch exists if day had enough content for it
    if (
        scheduled
        and not any(m.type == "lunch" for m in meals)
        and (current_time >= (LUNCH_HOUR + 1) * 60 or len(scheduled) >= 2)
    ):
            lunch = Meal(
                type="lunch",
                name="Lunch",
                estimated_cost=60,
                time_slot="12:00-13:00",
            )
            meals.append(lunch)

    # Add dinner
    if scheduled:
        dinner_start = max(current_time, DINNER_HOUR * 60)
        dinner_end = dinner_start + 60
        if not any(m.type == "dinner" for m in meals):
            meals.append(
                Meal(
                    type="dinner",
                    name="Dinner",
                    estimated_cost=80,
                    time_slot=_time_slot(dinner_start, dinner_end),
                )
            )

    return DayPlan(
        date=day_date,
        day_number=day_number,
        description="; ".join(description_parts) if description_parts else "",
        transportation=transport_mode,
        attractions=scheduled,
        meals=meals,
    )


def build_itinerary(
    clustered_places: list[list[Attraction]],
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
