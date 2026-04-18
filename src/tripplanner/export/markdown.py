from __future__ import annotations

from tripplanner.core.models import TripPlan


def export_markdown(plan: TripPlan) -> str:
    """Export trip plan as Markdown."""
    lines: list[str] = []

    lines.append(f"# {plan.city} Trip Plan")
    lines.append(f"**{plan.start_date} — {plan.end_date}**")
    lines.append("")

    if plan.budget:
        lines.append("## Budget Overview")
        lines.append("")
        lines.append("| Category | Cost |")
        lines.append("|----------|------|")
        lines.append(f"| Attractions | {plan.budget.total_attractions:.0f} |")
        lines.append(f"| Hotels | {plan.budget.total_hotels:.0f} |")
        lines.append(f"| Meals | {plan.budget.total_meals:.0f} |")
        lines.append(f"| Transport | {plan.budget.total_transportation:.0f} |")
        lines.append(f"| **Total** | **{plan.budget.total:.0f}** |")
        lines.append("")

    for day in plan.days:
        lines.append(f"## Day {day.day_number} — {day.date}")
        lines.append("")

        if day.attractions:
            lines.append("### Attractions")
            for i, a in enumerate(day.attractions, 1):
                rating_str = f" | Rating: {a.rating:.1f}/5" if a.rating else ""
                lines.append(f"{i}. **{a.name}** — {a.visit_duration} min{rating_str}")
                if a.address:
                    lines.append(f"   {a.address}")
            lines.append("")

        if day.meals:
            lines.append("### Meals")
            for m in day.meals:
                lines.append(f"- **{m.type.title()}**: {m.name} (~{m.estimated_cost:.0f})")
            lines.append("")

    if plan.suggestions:
        lines.append("## Suggestions")
        for s in plan.suggestions:
            lines.append(f"- {s}")

    return "\n".join(lines)
