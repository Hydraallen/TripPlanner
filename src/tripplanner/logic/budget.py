from __future__ import annotations

from tripplanner.core.models import Budget, TripPlan

# Default cost heuristics (when API data missing)
DEFAULT_COSTS: dict[str, float] = {
    "breakfast": 30.0,
    "lunch": 60.0,
    "dinner": 80.0,
    "hotel_budget": 300.0,
    "hotel_mid": 600.0,
    "hotel_luxury": 1200.0,
    "transit_per_trip": 10.0,
    "driving_per_day": 50.0,
}

TRANSPORT_COST_PER_TRIP: dict[str, float] = {
    "walking": 0.0,
    "transit": 10.0,
    "driving": 50.0,
}


def calculate_budget(plan: TripPlan, transport_mode: str = "walking") -> Budget:
    """Calculate budget breakdown for a trip plan."""
    total_attractions = sum(
        a.ticket_price for day in plan.days for a in day.attractions
    )

    total_meals = sum(m.estimated_cost for day in plan.days for m in day.meals)
    if total_meals == 0:
        # Apply default heuristics per day
        for _ in plan.days:
            total_meals += (
                DEFAULT_COSTS["breakfast"]
                + DEFAULT_COSTS["lunch"]
                + DEFAULT_COSTS["dinner"]
            )

    total_hotels = sum(
        day.hotel.estimated_cost_per_night
        if day.hotel and day.hotel.estimated_cost_per_night > 0
        else DEFAULT_COSTS["hotel_mid"]
        for day in plan.days
        if day.hotel is not None or day.day_number < len(plan.days)
    )

    # Estimate transport cost based on mode
    cost_per_trip = TRANSPORT_COST_PER_TRIP.get(transport_mode, 0.0)
    num_days = len(plan.days)
    trips_per_day = 4  # rough estimate
    total_transportation = cost_per_trip * trips_per_day * num_days

    total = total_attractions + total_hotels + total_meals + total_transportation

    return Budget(
        total_attractions=round(total_attractions, 2),
        total_hotels=round(total_hotels, 2),
        total_meals=round(total_meals, 2),
        total_transportation=round(total_transportation, 2),
        total=round(total, 2),
    )
