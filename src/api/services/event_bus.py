"""
Event Bus Service
=================

Pub/sub for real-time SSE events.
Will be backed by Redis for multi-instance deployments.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

from ...observability import get_logger

logger = get_logger("baby_mars.api.services.event_bus")


class EventBus:
    """
    Simple pub/sub for SSE events.

    In-memory implementation for single instance.
    For multi-instance, replace with Redis pub/sub.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._event_counter = 0
        self._event_history: list[dict[str, Any]] = []  # For replay on reconnect
        self._max_history = 100
        self._counter_lock = asyncio.Lock()  # Protect counter from race conditions

    def subscribe(self, org_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Subscribe to events for an org."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        if org_id not in self._subscribers:
            self._subscribers[org_id] = []
        self._subscribers[org_id].append(queue)
        logger.debug(f"New subscriber for org {org_id} (total: {len(self._subscribers[org_id])})")
        return queue

    def unsubscribe(self, org_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Unsubscribe from events."""
        if org_id in self._subscribers:
            try:
                self._subscribers[org_id].remove(queue)
                logger.debug(f"Subscriber removed for org {org_id}")
            except ValueError:
                pass

    async def publish(self, org_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to all subscribers of an org."""
        # Use lock to prevent race conditions on counter increment
        async with self._counter_lock:
            self._event_counter += 1
            event_id = f"evt_{self._event_counter}"

        event = {
            "event_id": event_id,
            "org_id": org_id,
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        # Store in history for replay
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Publish to subscribers (iterate over copy to avoid race with unsubscribe)
        if org_id in self._subscribers:
            for queue in list(self._subscribers[org_id]):
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.warning(f"Failed to publish event: {e}")

        logger.debug(f"Published {event_type} to org {org_id}")

    def get_events_since(self, org_id: str, last_event_id: str) -> list[dict[str, Any]]:
        """Get events since a given event ID for replay."""
        events = []
        found = False
        for event in self._event_history:
            if found and event["org_id"] == org_id:
                events.append(event)
            if event["event_id"] == last_event_id:
                found = True
        return events

    @property
    def subscriber_count(self) -> int:
        """Total number of active subscribers."""
        return sum(len(subs) for subs in self._subscribers.values())


# Global instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset event bus (for testing)."""
    global _event_bus
    _event_bus = None
