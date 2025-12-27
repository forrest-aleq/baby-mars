"""
Pulse Scheduler
===============

SYSTEM_PULSE - Aleq's internal clock and proactive trigger system.

This scheduler runs as a background asyncio task within FastAPI's lifespan.
It evaluates triggers and invokes the cognitive loop proactively.

Usage:
    # In server lifespan:
    scheduler = get_pulse_scheduler()
    await scheduler.start()
    # ... on shutdown:
    await scheduler.stop()
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from ..observability import get_logger

logger = get_logger(__name__)

# Singleton instance
_scheduler: Optional["PulseScheduler"] = None


class PulseScheduler:
    """
    Lightweight asyncio-based scheduler for proactive triggers.

    Runs as a background task checking triggers every interval.
    When triggers fire, invokes cognitive loop with synthetic state.
    """

    def __init__(self, check_interval_seconds: int = 60) -> None:
        """
        Initialize the scheduler.

        Args:
            check_interval_seconds: How often to check triggers (default 60s)
        """
        self._check_interval = check_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._last_check: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._running and self._task is not None

    async def start(self) -> None:
        """Start the scheduler background loop."""
        if self._running:
            logger.warning("PulseScheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"PulseScheduler started (check interval: {self._check_interval}s)")

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("PulseScheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop - evaluates triggers every interval."""
        while self._running:
            try:
                await self._evaluate_all_triggers()
                self._last_check = datetime.now(ZoneInfo("UTC"))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)

            await asyncio.sleep(self._check_interval)

    async def _evaluate_all_triggers(self) -> None:
        """
        Evaluate all active triggers across all orgs.

        This is the heart of SYSTEM_PULSE - it checks what should fire.
        """
        # Import here to avoid circular imports
        from .evaluator import evaluate_triggers

        try:
            fired_count = await evaluate_triggers()
            if fired_count > 0:
                logger.info(f"PulseScheduler: {fired_count} triggers fired")
        except Exception as e:
            logger.error(f"Trigger evaluation failed: {e}", exc_info=True)

    async def fire_trigger_now(self, trigger_id: str) -> dict[str, Any]:
        """
        Manually fire a specific trigger (for testing/debugging).

        Args:
            trigger_id: The trigger to fire

        Returns:
            Result of the trigger execution
        """
        from .executor import execute_trigger

        logger.info(f"Manual trigger fire: {trigger_id}")
        result = await execute_trigger(trigger_id)
        return dict(result)

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status for health checks."""
        return {
            "running": self._running,
            "check_interval_seconds": self._check_interval,
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }


def get_pulse_scheduler() -> PulseScheduler:
    """Get or create the singleton PulseScheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = PulseScheduler()
    return _scheduler
