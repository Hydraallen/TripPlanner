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

_PLAN_TITLES: dict[PlanFocus, str] = {
    PlanFocus.BUDGET: "Budget-Friendly Explorer",
    PlanFocus.CULTURE: "Culture & Discovery",
    PlanFocus.NATURE: "Nature & Relaxation",
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
                places=scored_places,
                weather=weather,
                center=(lat, lon),
                num_days=num_days,
            )

            if plan:
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
        places: list[Attraction],
        weather: list[WeatherInfo] | None,
        center: tuple[float, float],
        num_days: int,
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
                places=places[:20],
                weather=weather,
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
    ) -> TripPlan | None:
        """Generate a single plan using the algorithmic pipeline."""
        if not places or not center or center == (0.0, 0.0):
            return None

        clusters = optimize_routes(
            places,
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
