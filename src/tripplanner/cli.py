from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta
from typing import Any

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from tripplanner.api.opentripmap import OpenTripMapClient
from tripplanner.core.config import get_settings
from tripplanner.core.state import TripState
from tripplanner.db.crud import (
    delete_trip as db_delete,
)
from tripplanner.db.crud import (
    get_trip as db_get,
)
from tripplanner.db.crud import (
    init_db,
)
from tripplanner.db.crud import (
    list_trips as db_list,
)
from tripplanner.db.crud import (
    save_trip as db_save,
)
from tripplanner.export.html_gen import export_html
from tripplanner.export.json_export import export_json
from tripplanner.export.markdown import export_markdown
from tripplanner.logic.budget import calculate_budget
from tripplanner.logic.optimizer import haversine, optimize_routes
from tripplanner.logic.scheduler import build_itinerary
from tripplanner.logic.scorer import compute_scores

console = Console()


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise click.BadParameter(
            f"Invalid date format: '{value}'. Use YYYY-MM-DD."
        ) from None


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


async def _get_session():
    from tripplanner.core.config import get_settings
    settings = get_settings()
    factory = await init_db(settings.database_url)
    return factory


async def _dry_run(city: str, interests: list[str], radius: int) -> None:
    settings = get_settings()
    with console.status(f"[bold green]Fetching {city} POIs..."):
        async with OpenTripMapClient(settings) as client:
            coords = await client.geoname(city)
            if not coords:
                console.print(f"[red]Could not find city: {city}[/red]")
                return

            lat, lon = coords
            kinds = ",".join(interests) if interests else None
            places = await client.search_places(lat, lon, radius, kinds)

    console.print(f"\n[bold]{city}[/bold] ({lat:.4f}, {lon:.4f})")
    console.print(f"Found {len(places)} places\n")

    if not places:
        console.print(
            "[yellow]No places found. "
            "Try different interests or larger radius.[/yellow]"
        )
        return

    table = Table(title=f"Top POIs in {city}")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Rating", justify="right")
    table.add_column("Distance", justify="right", style="yellow")

    for p in places[:10]:
        dist = haversine(lat, lon, p.location.latitude, p.location.longitude)
        table.add_row(
            p.name,
            p.kinds[:30] if p.kinds else "-",
            f"{p.rating:.1f}" if p.rating else "N/A",
            f"{dist:.1f} km",
        )

    console.print(table)


async def _generate_plan(state: TripState, radius: int) -> TripState:
    """Run the full planning pipeline."""
    settings = get_settings()
    with console.status("[bold green]Fetching places from OpenStreetMap..."):
        async with OpenTripMapClient(settings) as client:
            state.city_coords = await client.geoname(state.city)
            if not state.city_coords:
                return state

            lat, lon = state.city_coords
            state.raw_places = await client.search_city(
                state.city, state.interests, radius
            )

    if not state.raw_places:
        return state

    state.scored_places = compute_scores(state.raw_places, state.interests)

    num_days = (state.end_date - state.start_date).days + 1
    state.optimized_clusters = optimize_routes(
        state.scored_places,
        center=(lat, lon),
        num_days=num_days,
        transport_mode=state.transport_mode,
    )

    state.itinerary = build_itinerary(
        state.optimized_clusters,
        state.start_date,
        state.end_date,
        state.transport_mode,
    )
    state.itinerary.city = state.city

    budget = calculate_budget(state.itinerary, state.transport_mode)
    state.itinerary.budget = budget

    return state


def _display_itinerary(state: TripState) -> None:
    """Display the generated itinerary with Rich formatting."""
    plan = state.itinerary
    if not plan:
        console.print(f"[red]Could not generate itinerary for {state.city}.[/red]")
        return

    console.print(f"\n[bold cyan]{plan.city} Trip Plan[/bold cyan]")
    console.print(f"[dim]{plan.start_date} — {plan.end_date}[/dim]\n")

    if plan.budget:
        total = plan.budget.total
        if total < 5000:
            color = "green"
        elif total < 10000:
            color = "yellow"
        else:
            color = "red"
        table = Table(title="Budget Overview", show_lines=False)
        table.add_column("Category", style="dim")
        table.add_column("Cost", justify="right")
        table.add_row("Attractions", f"{plan.budget.total_attractions:.0f}")
        table.add_row("Meals", f"{plan.budget.total_meals:.0f}")
        table.add_row("Hotels", f"{plan.budget.total_hotels:.0f}")
        table.add_row("Transport", f"{plan.budget.total_transportation:.0f}")
        table.add_row("[bold]Total[/bold]", f"[bold {color}]{total:.0f}[/bold {color}]")
        console.print(table)
        console.print()

    for day in plan.days:
        console.print(f"[bold]Day {day.day_number} — {day.date}[/bold]")
        for a in day.attractions:
            rating_str = f" ({a.rating:.1f}/5)" if a.rating else ""
            console.print(f"  - {a.name}{rating_str}")
        for m in day.meals:
            console.print(f"  [dim]{m.type}: {m.name} (~{m.estimated_cost:.0f})[/dim]")
        console.print()


@click.group()
@click.version_option()
def cli() -> None:
    """TripPlanner — generate personalized travel itineraries."""


TRANSPORT_CHOICES = click.Choice(["walking", "transit", "driving"])
EXPORT_CHOICES = click.Choice(["markdown", "json", "html"])


@cli.command()
@click.option("--city", required=True, help="Target city name")
@click.option(
    "--dates", nargs=2, type=str, default=None, help="Start and end dates (YYYY-MM-DD)"
)
@click.option("--days", type=int, default=3, help="Number of days (default: 3)")
@click.option(
    "--interests", default="interesting_places", help="Comma-separated interest tags"
)
@click.option("--transport", type=TRANSPORT_CHOICES, default="walking")
@click.option("--radius", type=int, default=None, help="Search radius in meters")
@click.option(
    "--dry-run", is_flag=True, help="Fetch and display POIs without generating itinerary"
)
@click.option("--export", "export_fmt", type=EXPORT_CHOICES, default=None)
@click.option("--output", type=click.Path(), default=None, help="Output file path")
def plan(
    city: str,
    dates: tuple[str, str] | None,
    days: int,
    interests: str,
    transport: str,
    radius: int | None,
    dry_run: bool,
    export_fmt: str | None,
    output: str | None,
) -> None:
    """Plan a new trip."""
    settings = get_settings()

    if dates:
        start = _parse_date(dates[0])
        end = _parse_date(dates[1])
        if end < start:
            raise click.BadParameter("End date must be after start date.")
    else:
        start = date.today() + timedelta(days=1)
        end = start + timedelta(days=days - 1)

    interest_list = [i.strip() for i in interests.split(",")]
    search_radius = radius or settings.default_search_radius

    if dry_run:
        _run_async(_dry_run(city, interest_list, search_radius))
        return

    state = TripState(city, start, end, interest_list, transport)
    _run_async(_generate_plan(state, search_radius))
    _display_itinerary(state)

    if state.itinerary:
        # Save to database
        async def _save():
            factory = await _get_session()
            async with factory() as session:
                from tripplanner.core.models import Trip
                trip = Trip(
                    id=str(uuid.uuid4()),
                    city=city,
                    start_date=start,
                    end_date=end,
                    interests=interest_list,
                    transport_mode=transport,
                    plan=state.itinerary,
                    created_at=datetime.now(),
                )
                trip_id = await db_save(session, trip)
                return trip_id

        trip_id = _run_async(_save())
        console.print(f"[dim]Saved as trip ID: {trip_id}[/dim]")

        # Export if requested
        if export_fmt:
            content = _export_content(state.itinerary, export_fmt)
            if output:
                with open(output, "w") as f:
                    f.write(content)
                console.print(f"[green]Exported to {output}[/green]")
            else:
                console.print(content)


def _export_content(plan: Any, fmt: str) -> str:
    if fmt == "markdown":
        return export_markdown(plan)
    elif fmt == "json":
        return export_json(plan)
    elif fmt == "html":
        return export_html(plan)
    raise click.BadParameter(f"Unknown format: {fmt}")


@cli.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_cmd(fmt: str) -> None:
    """List saved trips."""

    async def _list():
        factory = await _get_session()
        async with factory() as session:
            return await db_list(session)

    trips = _run_async(_list())

    if not trips:
        console.print("[yellow]No trips found.[/yellow]")
        return

    if fmt == "json":
        import json as json_mod
        data = [
            {"id": t.id, "city": t.city, "start": str(t.start_date), "end": str(t.end_date)}
            for t in trips
        ]
        console.print(json_mod.dumps(data, indent=2))
        return

    table = Table(title="Saved Trips")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("City", style="cyan")
    table.add_column("Dates")
    table.add_column("Created")

    for t in trips:
        table.add_row(
            t.id[:8] + "...",
            t.city,
            f"{t.start_date} — {t.end_date}",
            str(t.created_at.date()) if t.created_at else "-",
        )
    console.print(table)


@cli.command()
@click.argument("trip_id")
def show(trip_id: str) -> None:
    """Show trip details."""

    async def _show():
        factory = await _get_session()
        async with factory() as session:
            return await db_get(session, trip_id)

    trip = _run_async(_show())
    if not trip:
        console.print(f"[red]Trip not found: {trip_id}[/red]")
        return

    if trip.plan:
        md = export_markdown(trip.plan)
        console.print(Markdown(md))
    else:
        console.print(f"[yellow]Trip {trip_id} has no itinerary.[/yellow]")


@cli.command()
@click.argument("trip_id")
@click.option("--format", "fmt", type=EXPORT_CHOICES, required=True)
@click.option("--output", type=click.Path(), default=None, help="Output file path")
def export(trip_id: str, fmt: str, output: str | None) -> None:
    """Export a trip to file."""

    async def _export():
        factory = await _get_session()
        async with factory() as session:
            return await db_get(session, trip_id)

    trip = _run_async(_export())
    if not trip:
        console.print(f"[red]Trip not found: {trip_id}[/red]")
        return

    if not trip.plan:
        console.print(f"[red]Trip {trip_id} has no itinerary to export.[/red]")
        return

    content = _export_content(trip.plan, fmt)

    if output:
        with open(output, "w") as f:
            f.write(content)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(content)


@cli.command()
@click.argument("trip_id")
@click.option("--force", is_flag=True, help="Skip confirmation")
def delete(trip_id: str, force: bool) -> None:
    """Delete a saved trip."""
    if not force and not click.confirm(f"Delete trip {trip_id}?"):
        console.print("[dim]Cancelled.[/dim]")
        return

    async def _delete():
        factory = await _get_session()
        async with factory() as session:
            return await db_delete(session, trip_id)

    deleted = _run_async(_delete())
    if deleted:
        console.print(f"[green]Trip {trip_id} deleted.[/green]")
    else:
        console.print(f"[red]Trip not found: {trip_id}[/red]")


if __name__ == "__main__":
    cli()


@cli.command()
@click.option("--host", default=None, help="Bind host (default: 0.0.0.0)")
@click.option("--port", type=int, default=None, help="Bind port (default: 8000)")
@click.option("--dev", is_flag=True, help="Enable auto-reload for development")
def web(host: str | None, port: int | None, dev: bool) -> None:
    """Start the FastAPI web server."""
    settings = get_settings()
    bind_host = host or settings.host
    bind_port = port or settings.port

    console.print("[bold green]Starting TripPlanner web server[/bold green]")
    console.print(f"  Host: {bind_host}")
    console.print(f"  Port: {bind_port}")
    console.print(f"  Docs: http://{bind_host}:{bind_port}/docs")
    console.print()

    import uvicorn

    uvicorn.run(
        "tripplanner.web:create_app",
        host=bind_host,
        port=bind_port,
        reload=dev,
        factory=True,
    )
