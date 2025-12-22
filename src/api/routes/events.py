"""
Events Routes
=============

Real-time SSE event stream.
Per API_CONTRACT_V0.md section 6
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Query
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("baby_mars.api.events")

router = APIRouter()


# Simple in-memory event bus (will be replaced with Redis pub/sub for multi-instance)
class EventBus:
    """Simple pub/sub for SSE events."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._event_counter = 0

    def subscribe(self, org_id: str) -> asyncio.Queue:
        """Subscribe to events for an org."""
        queue = asyncio.Queue()
        if org_id not in self._subscribers:
            self._subscribers[org_id] = []
        self._subscribers[org_id].append(queue)
        logger.debug(f"New subscriber for org {org_id}")
        return queue

    def unsubscribe(self, org_id: str, queue: asyncio.Queue):
        """Unsubscribe from events."""
        if org_id in self._subscribers:
            try:
                self._subscribers[org_id].remove(queue)
                logger.debug(f"Subscriber removed for org {org_id}")
            except ValueError:
                pass

    async def publish(self, org_id: str, event_type: str, data: dict):
        """Publish an event to all subscribers of an org."""
        self._event_counter += 1
        event = {
            "event_id": f"evt_{self._event_counter}",
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if org_id in self._subscribers:
            for queue in self._subscribers[org_id]:
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.warning(f"Failed to publish event: {e}")

        logger.debug(f"Published {event_type} to org {org_id}")


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus."""
    return _event_bus


@router.get("")
async def event_stream(
    request: Request,
    org_id: str = Query(..., description="Organization ID"),
    last_event_id: Optional[str] = Query(None, description="Resume from event ID"),
):
    """
    Real-time event stream via SSE.

    Per API_CONTRACT_V0.md section 6.1, event types:
    - task:created - New task appeared
    - task:updated - Task status changed
    - task:decision_needed - Decision surfaced
    - decision:made - Someone decided
    - data:changed - Widget data changed
    - presence:update - Who's viewing what
    - aleq:message - Aleq proactively communicating

    Supports Last-Event-ID header for resume after disconnect.
    """
    queue = _event_bus.subscribe(org_id)

    async def event_generator():
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "org_id": org_id,
                    "timestamp": datetime.now().isoformat(),
                })
            }

            # TODO: If last_event_id provided, replay missed events

            while True:
                try:
                    # Wait for events with timeout for keepalive
                    event = await asyncio.wait_for(queue.get(), timeout=30)

                    yield {
                        "event": event["type"],
                        "id": event["event_id"],
                        "data": json.dumps(event["data"]),
                    }

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }

        except asyncio.CancelledError:
            logger.debug(f"SSE connection cancelled for org {org_id}")
        finally:
            _event_bus.unsubscribe(org_id, queue)

    return EventSourceResponse(event_generator())


# Helper functions for publishing events from other routes

async def publish_task_created(org_id: str, task_id: str, task_type: str, summary: str):
    """Publish task:created event."""
    await _event_bus.publish(org_id, "task:created", {
        "task_id": task_id,
        "type": task_type,
        "summary": summary,
    })


async def publish_task_updated(org_id: str, task_id: str, status: str, summary: str):
    """Publish task:updated event."""
    await _event_bus.publish(org_id, "task:updated", {
        "task_id": task_id,
        "status": status,
        "summary": summary,
    })


async def publish_task_decision_needed(
    org_id: str,
    task_id: str,
    decision_id: str,
    summary: str,
):
    """Publish task:decision_needed event."""
    await _event_bus.publish(org_id, "task:decision_needed", {
        "task_id": task_id,
        "decision_id": decision_id,
        "summary": summary,
    })


async def publish_decision_made(
    org_id: str,
    decision_id: str,
    made_by: str,
    action: str,
):
    """Publish decision:made event."""
    await _event_bus.publish(org_id, "decision:made", {
        "decision_id": decision_id,
        "made_by": made_by,
        "action": action,
    })


async def publish_data_changed(org_id: str, widget_id: str, change_type: str):
    """Publish data:changed event."""
    await _event_bus.publish(org_id, "data:changed", {
        "widget_id": widget_id,
        "change_type": change_type,
    })


async def publish_presence_update(org_id: str, task_id: str, users: list[str]):
    """Publish presence:update event."""
    await _event_bus.publish(org_id, "presence:update", {
        "task_id": task_id,
        "users": users,
    })


async def publish_aleq_message(org_id: str, message: str, references: list[dict]):
    """Publish aleq:message event for proactive communication."""
    await _event_bus.publish(org_id, "aleq:message", {
        "message": message,
        "references": references,
    })
