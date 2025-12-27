"""
Scheduler Persistence
=====================

Database operations for scheduled triggers.
Uses Postgres for durable storage.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional, cast
from zoneinfo import ZoneInfo

from ..observability import get_logger
from ..persistence.database import get_connection
from .triggers import ScheduledTrigger

logger = get_logger(__name__)


async def load_active_triggers() -> list[ScheduledTrigger]:
    """Load all active (enabled) triggers from database."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM scheduled_triggers
            WHERE enabled = TRUE
            ORDER BY created_at
            """
        )
        return [_row_to_trigger(row) for row in rows]


async def load_org_triggers(org_id: str) -> list[ScheduledTrigger]:
    """Load all triggers for an organization."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM scheduled_triggers
            WHERE org_id = $1
            ORDER BY created_at
            """,
            org_id,
        )
        return [_row_to_trigger(row) for row in rows]


async def get_trigger(trigger_id: str) -> Optional[ScheduledTrigger]:
    """Get a specific trigger by ID."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM scheduled_triggers WHERE trigger_id = $1",
            trigger_id,
        )
        if row:
            return _row_to_trigger(row)
        return None


async def save_trigger(trigger: ScheduledTrigger) -> None:
    """Save or update a trigger."""
    now = datetime.now(ZoneInfo("UTC"))

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO scheduled_triggers (
                trigger_id, org_id, user_id, trigger_type, config, action,
                action_context, description, enabled, last_fired, next_fire,
                fire_count, created_at, updated_at, created_by
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (trigger_id) DO UPDATE SET
                config = EXCLUDED.config,
                action = EXCLUDED.action,
                action_context = EXCLUDED.action_context,
                description = EXCLUDED.description,
                enabled = EXCLUDED.enabled,
                last_fired = EXCLUDED.last_fired,
                next_fire = EXCLUDED.next_fire,
                fire_count = EXCLUDED.fire_count,
                updated_at = $14
            """,
            trigger["trigger_id"],
            trigger["org_id"],
            trigger.get("user_id"),
            trigger["trigger_type"],
            json.dumps(trigger["config"]),
            trigger["action"],
            json.dumps(trigger.get("action_context", {})),
            trigger.get("description", ""),
            trigger.get("enabled", True),
            _parse_timestamp(trigger.get("last_fired")),
            _parse_timestamp(trigger.get("next_fire")),
            trigger.get("fire_count", 0),
            _parse_timestamp(trigger.get("created_at")) or now,
            now,
            trigger.get("created_by", "system"),
        )
    logger.debug(f"Saved trigger: {trigger['trigger_id']}")


async def delete_trigger(trigger_id: str) -> bool:
    """Delete a trigger."""
    async with get_connection() as conn:
        result = await conn.execute(
            "DELETE FROM scheduled_triggers WHERE trigger_id = $1",
            trigger_id,
        )
        deleted = str(result) == "DELETE 1"
        if deleted:
            logger.debug(f"Deleted trigger: {trigger_id}")
        return deleted


async def update_trigger_fired(trigger_id: str) -> None:
    """Update trigger after it fires."""
    now = datetime.now(ZoneInfo("UTC"))

    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE scheduled_triggers
            SET last_fired = $2,
                fire_count = fire_count + 1,
                updated_at = $2
            WHERE trigger_id = $1
            """,
            trigger_id,
            now,
        )


async def get_event_triggers(
    org_id: str,
    event_type: str,
) -> list[ScheduledTrigger]:
    """Get event triggers for a specific event type."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM scheduled_triggers
            WHERE org_id = $1
            AND trigger_type = 'event'
            AND config->>'event_type' = $2
            AND enabled = TRUE
            """,
            org_id,
            event_type,
        )
        return [_row_to_trigger(row) for row in rows]


async def get_user_triggers(
    org_id: str,
    user_id: str,
) -> list[ScheduledTrigger]:
    """Get user-specific triggers (overrides)."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM scheduled_triggers
            WHERE org_id = $1 AND user_id = $2
            """,
            org_id,
            user_id,
        )
        return [_row_to_trigger(row) for row in rows]


def create_trigger(
    org_id: str,
    trigger_type: str,
    action: str,
    config: dict[str, Any],
    description: str = "",
    user_id: Optional[str] = None,
    created_by: str = "system",
) -> ScheduledTrigger:
    """Create a new trigger (does not save, call save_trigger after)."""
    now = datetime.now(ZoneInfo("UTC")).isoformat()
    trigger_id = f"trigger_{uuid.uuid4().hex[:12]}"

    trigger: ScheduledTrigger = {
        "trigger_id": trigger_id,
        "org_id": org_id,
        "user_id": user_id,
        "trigger_type": trigger_type,  # type: ignore[typeddict-item]
        "config": config,
        "action": action,
        "action_context": {},
        "description": description,
        "enabled": True,
        "last_fired": None,
        "next_fire": None,
        "fire_count": 0,
        "created_at": now,
        "updated_at": now,
        "created_by": created_by,  # type: ignore[typeddict-item]
    }

    return trigger


def _row_to_trigger(row: Any) -> ScheduledTrigger:
    """Convert a database row to a ScheduledTrigger."""
    return cast(
        ScheduledTrigger,
        {
            "trigger_id": row["trigger_id"],
            "org_id": row["org_id"],
            "user_id": row["user_id"],
            "trigger_type": row["trigger_type"],
            "config": row["config"] if row["config"] else {},
            "action": row["action"],
            "action_context": row["action_context"] if row["action_context"] else {},
            "description": row["description"] or "",
            "enabled": row["enabled"],
            "last_fired": row["last_fired"].isoformat() if row["last_fired"] else None,
            "next_fire": row["next_fire"].isoformat() if row["next_fire"] else None,
            "fire_count": row["fire_count"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "created_by": row["created_by"],
        },
    )


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime."""
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt
    except (ValueError, TypeError):
        return None
