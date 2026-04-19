from __future__ import annotations

import logging
from datetime import date

from tripplanner.core.models import (
    Attraction,
    GenerationProgress,
    PlanAlternative,
    PlanFocus,
    TripPlan,
    WeatherInfo,
)
from tripplanner.logic.budget import calculate_budget
from tripplanner.logic.optimizer import optimize_routes
from tripplanner.logic.scheduler import build_itinerary
from tripplanner.logic.scorer import compute_scores
from tripplanner.web.services.llm import LLMClient
from tripplanner.web.services.plan_scorer import score_plans

logger = logging.getLogger(__name__)

_FOCUS_PREFERRED_KINDS: dict[PlanFocus, set[str]] = {
    PlanFocus.BUDGET: {
        "park", "garden", "viewpoint", "monument", "memorial",
        "attraction", "place_of_worship",
    },
    PlanFocus.CULTURE: {
        "museum", "gallery", "theatre", "arts_centre",
        "historic", "monument", "castle", "ruins",
        "place_of_worship", "cathedral", "church", "library",
    },
    PlanFocus.NATURE: {
        "park", "garden", "nature_reserve", "peak",
        "wood", "beach", "water", "zoo",
    },
    PlanFocus.FOOD: {
        "restaurant", "cafe", "bar", "pub", "fast_food",
        "mall", "marketplace",
    },
    PlanFocus.ROMANTIC: {
        "viewpoint", "garden", "park", "restaurant", "cafe",
        "beach", "water", "gallery", "castle",
    },
    PlanFocus.ADVENTURE: {
        "peak", "nature_reserve", "beach", "wood", "water",
        "zoo", "park", "viewpoint",
    },
}

_PLAN_TITLES: dict[PlanFocus, str] = {
    PlanFocus.BUDGET: "Budget-Friendly Explorer",
    PlanFocus.CULTURE: "Culture & Discovery",
    PlanFocus.NATURE: "Nature & Relaxation",
    PlanFocus.FOOD: "Foodie's Delight",
    PlanFocus.ROMANTIC: "Romantic Getaway",
    PlanFocus.ADVENTURE: "Adventure & Thrills",
}

_PLAN_DESCRIPTIONS: dict[PlanFocus, str] = {
    PlanFocus.BUDGET: (
        "Maximize experiences while minimizing costs with free "
        "attractions and affordable dining."
    ),
    PlanFocus.CULTURE: (
        "Dive deep into local culture with museums, "
        "historical sites, and authentic cuisine."
    ),
    PlanFocus.NATURE: "Enjoy peaceful natural scenery, parks, and outdoor relaxation.",
    PlanFocus.FOOD: (
        "Savor local flavors with authentic cuisine, food markets, "
        "and hidden culinary gems."
    ),
    PlanFocus.ROMANTIC: (
        "Intimate experiences with scenic views, fine dining, "
        "and leisurely moments together."
    ),
    PlanFocus.ADVENTURE: (
        "Active exploration with outdoor activities and unique, "
        "off-the-beaten-path experiences."
    ),
}


class PlanGenerator:
    """Generates multiple plan alternatives via LLM with algorithmic fallback."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def generate_alternatives(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        transport_mode: str = "walking",
        places: list[Attraction] | None = None,
        weather: list[WeatherInfo] | None = None,
        num_plans: int = 3,
        transport_user_specified: bool = True,
        on_progress: object = None,
    ) -> list[PlanAlternative]:
        """Generate multiple plan alternatives.

        Args:
            on_progress: Optional callback(GenerationProgress) for progress updates.

        Returns:
            List of PlanAlternative with scores attached.
        """
        lat: float = 0.0
        lon: float = 0.0
        scored_places: list[Attraction] = []

        if places:
            scored_places = compute_scores(places, interests)
            if scored_places:
                lat = scored_places[0].location.latitude
                lon = scored_places[0].location.longitude

        num_days = (end_date - start_date).days + 1
        focuses = list(PlanFocus)[:num_plans]
        alternatives: list[PlanAlternative] = []
        used_attraction_names: set[str] = set()

        for i, focus in enumerate(focuses):
            step_text = f"Generating {focus.value} plan... ({i + 1}/{len(focuses)})"
            progress_pct = 30 + (i / len(focuses)) * 60

            if callable(on_progress):
                on_progress(
                    GenerationProgress(
                        plan_id="",
                        status="generating",
                        progress=progress_pct,
                        step=step_text,
                    )
                )

            plan, source = await self._generate_single(
                city=city,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                focus=focus,
                transport_mode=transport_mode,
                transport_user_specified=transport_user_specified,
                places=scored_places,
                weather=weather,
                center=(lat, lon),
                num_days=num_days,
                used_attractions=used_attraction_names,
            )

            if plan:
                # Post-process: filter out attractions that appear in earlier plans
                plan = self._dedup_plan(plan, used_attraction_names)
                for day in plan.days:
                    for a in day.attractions:
                        used_attraction_names.add(a.name.lower().strip())
                alternatives.append(
                    PlanAlternative(
                        id=f"plan_{i + 1}",
                        focus=focus,
                        title=_PLAN_TITLES[focus],
                        description=_PLAN_DESCRIPTIONS[focus],
                        plan=plan,
                        source=source,
                    )
                )
            else:
                logger.warning(
                    "LLM generation failed for focus=%s, skipping", focus.value
                )

        if not alternatives and scored_places:
            logger.info("All LLM plans failed, falling back to algorithmic pipeline")
            fallback = self._algorithmic_fallback(
                city=city,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                transport_mode=transport_mode,
                places=scored_places,
                center=(lat, lon),
                num_days=num_days,
                weather=weather,
            )
            alternatives.extend(fallback)

        if alternatives:
            alternatives = score_plans(alternatives)

        return alternatives

    async def _generate_single(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        focus: PlanFocus,
        transport_mode: str,
        transport_user_specified: bool,
        places: list[Attraction],
        weather: list[WeatherInfo] | None,
        center: tuple[float, float],
        num_days: int,
        used_attractions: set[str] | None = None,
    ) -> tuple[TripPlan | None, str]:
        """Try LLM generation, fall back to algorithmic for this single plan.

        Returns (plan, source) where source is "llm" or "algorithmic".
        """
        if self._llm:
            plan = await self._llm.generate_plan_with_focus(
                city=city,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                focus=focus,
                transport_mode=transport_mode,
                transport_user_specified=transport_user_specified,
                places=places[:30],
                weather=weather,
                used_attractions=used_attractions,
            )
            if plan:
                plan.city = city
                return plan, "llm"

        plan = self._algorithmic_single(
            city=city,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            transport_mode=transport_mode,
            places=places,
            center=center,
            num_days=num_days,
            weather=weather,
            focus=focus,
        )
        return plan, "algorithmic"

    def _algorithmic_fallback(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        transport_mode: str,
        places: list[Attraction],
        center: tuple[float, float],
        num_days: int,
        weather: list[WeatherInfo] | None,
    ) -> list[PlanAlternative]:
        """Generate 3 algorithmic plans as last resort."""
        focuses = list(PlanFocus)[:3]
        results: list[PlanAlternative] = []

        for i, focus in enumerate(focuses):
            plan = self._algorithmic_single(
                city=city,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                transport_mode=transport_mode,
                places=places,
                center=center,
                num_days=num_days,
                weather=weather,
                focus=focus,
            )
            if plan:
                results.append(
                    PlanAlternative(
                        id=f"plan_{i + 1}",
                        focus=focus,
                        title=_PLAN_TITLES[focus],
                        description=_PLAN_DESCRIPTIONS[focus],
                        plan=plan,
                        source="algorithmic",
                    )
                )

        return results

    def _algorithmic_single(
        self,
        city: str,
        start_date: date,
        end_date: date,
        interests: list[str],
        transport_mode: str,
        places: list[Attraction],
        center: tuple[float, float],
        num_days: int,
        weather: list[WeatherInfo] | None,
        focus: PlanFocus = PlanFocus.CULTURE,
    ) -> TripPlan | None:
        """Generate a single plan using the algorithmic pipeline.

        Reorders POIs so that focus-preferred kinds appear first, giving
        each focus variant a different set of attractions.
        """
        if not places or not center or center == (0.0, 0.0):
            return None

        preferred = _FOCUS_PREFERRED_KINDS.get(focus, set())
        reordered = self._reorder_by_focus(places, preferred)

        clusters = optimize_routes(
            reordered,
            center=center,
            num_days=num_days,
            transport_mode=transport_mode,
        )
        itinerary = build_itinerary(clusters, start_date, end_date, transport_mode)
        itinerary.city = city
        budget = calculate_budget(itinerary, transport_mode)
        itinerary.budget = budget
        if weather:
            itinerary.weather = weather
        return itinerary

    @staticmethod
    def _dedup_plan(plan: TripPlan, used: set[str]) -> TripPlan:
        """Remove attractions whose names were already used in earlier plans."""
        if not used:
            return plan
        for day in plan.days:
            day.attractions = [
                a for a in day.attractions
                if a.name.lower().strip() not in used
            ]
        return plan

    @staticmethod
    def _reorder_by_focus(
        places: list[Attraction], preferred_kinds: set[str]
    ) -> list[Attraction]:
        """Sort places so focus-matching kinds come first.

        Within each group the original order (e.g. by score) is preserved.
        """
        matched: list[Attraction] = []
        other: list[Attraction] = []
        for p in places:
            kinds_set = {k.strip().lower() for k in (p.kinds or "").split(",")}
            if kinds_set & preferred_kinds:
                matched.append(p)
            else:
                other.append(p)
        return matched + other if matched else places
