from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import defaultdict

from tripplanner.core.models import GenerationProgress

logger = logging.getLogger(__name__)


class ProgressTracker:
    """In-memory progress tracking with database persistence.

    Maintains an in-memory dict for fast SSE reads and syncs to
    the database via the provided session.
    """

    def __init__(self) -> None:
        self._store: dict[str, GenerationProgress] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict]]] = defaultdict(list)

    def update(self, progress: GenerationProgress) -> None:
        """Update progress in memory and notify subscribers."""
        self._store[progress.plan_id] = progress
        self._notify(progress)

    def get(self, plan_id: str) -> GenerationProgress | None:
        """Get current progress for a plan."""
        return self._store.get(plan_id)

    def subscribe(self, plan_id: str) -> asyncio.Queue[dict]:
        """Subscribe to progress updates for a plan. Returns a queue."""
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers[plan_id].append(queue)
        return queue

    def unsubscribe(self, plan_id: str, queue: asyncio.Queue[dict]) -> None:
        """Remove a subscriber queue."""
        if plan_id in self._subscribers:
            with contextlib.suppress(ValueError):
                self._subscribers[plan_id].remove(queue)
            if not self._subscribers[plan_id]:
                del self._subscribers[plan_id]

    def _notify(self, progress: GenerationProgress) -> None:
        """Push progress event to all subscribers."""
        event = progress.model_dump(mode="json")
        for queue in self._subscribers.get(progress.plan_id, []):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Progress queue full for %s, dropping event", progress.plan_id)

    def complete(self, plan_id: str) -> None:
        """Mark plan as completed and notify."""
        self.update(
            GenerationProgress(
                plan_id=plan_id,
                status="completed",
                progress=100,
                step="Done!",
            )
        )

    def fail(self, plan_id: str, reason: str = "") -> None:
        """Mark plan as failed and notify."""
        self.update(
            GenerationProgress(
                plan_id=plan_id,
                status="failed",
                progress=0,
                step=reason or "Generation failed",
            )
        )


# Global singleton
progress_tracker = ProgressTracker()
