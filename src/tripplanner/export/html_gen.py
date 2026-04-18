from __future__ import annotations

from tripplanner.core.models import TripPlan

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{city} Trip Plan</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; }}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }}
h2 {{ color: #2c3e50; margin-top: 2rem; }}
h3 {{ color: #555; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem 1rem; text-align: left; }}
th {{ background: #f8f9fa; font-weight: 600; }}
.total {{ font-weight: bold; background: #f0f0f0; }}
ol {{ padding-left: 1.5rem; }}
li {{ margin: 0.3rem 0; }}
.meals {{ color: #666; }}
.day-section {{ border-left: 3px solid #3498db; padding-left: 1rem; margin: 1.5rem 0; }}
</style>
</head>
<body>
<h1>{city} Trip Plan</h1>
<p><strong>{start_date} — {end_date}</strong></p>
{budget_html}
{days_html}
</body>
</html>"""


def export_html(plan: TripPlan) -> str:
    """Export trip plan as HTML."""
    budget_html = _render_budget(plan)
    days_html = _render_days(plan)

    return HTML_TEMPLATE.format(
        city=plan.city,
        start_date=plan.start_date,
        end_date=plan.end_date,
        budget_html=budget_html,
        days_html=days_html,
    )


def _render_budget(plan: TripPlan) -> str:
    if not plan.budget:
        return ""
    b = plan.budget
    return f"""
<h2>Budget Overview</h2>
<table>
<tr><th>Category</th><th>Cost</th></tr>
<tr><td>Attractions</td><td>{b.total_attractions:.0f}</td></tr>
<tr><td>Hotels</td><td>{b.total_hotels:.0f}</td></tr>
<tr><td>Meals</td><td>{b.total_meals:.0f}</td></tr>
<tr><td>Transport</td><td>{b.total_transportation:.0f}</td></tr>
<tr class="total"><td>Total</td><td>{b.total:.0f}</td></tr>
</table>
"""


def _render_days(plan: TripPlan) -> str:
    parts: list[str] = []
    for day in plan.days:
        parts.append('<div class="day-section">')
        parts.append(f"<h2>Day {day.day_number} — {day.date}</h2>")

        if day.attractions:
            parts.append("<h3>Attractions</h3><ol>")
            for a in day.attractions:
                rating = f" ({a.rating:.1f}/5)" if a.rating else ""
                parts.append(f"<li><strong>{a.name}</strong> — {a.visit_duration} min{rating}</li>")
            parts.append("</ol>")

        if day.meals:
            parts.append('<div class="meals"><h3>Meals</h3><ul>')
            for m in day.meals:
                parts.append(f"<li>{m.type.title()}: {m.name} (~{m.estimated_cost:.0f})</li>")
            parts.append("</ul></div>")

        parts.append("</div>")

    return "\n".join(parts)
