from __future__ import annotations

from tripplanner.core.models import TripPlan


def export_json(plan: TripPlan) -> str:
    """Export trip plan as JSON."""
    return plan.model_dump_json(exclude_none=True, indent=2)
