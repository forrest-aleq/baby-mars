"""
Notes Persistence
=================

Database operations for notes (TTL-based queue from Paper #8).
Used by the scheduler's note_scanner for TTL-based triggers.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from .database import get_connection


async def get_org_notes(org_id: str) -> list[dict[str, Any]]:
    """
    Load all notes for an organization.

    Returns notes with computed expires_at based on created_at + ttl_hours.
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                note_id,
                org_id,
                content,
                created_at,
                ttl_hours,
                priority,
                source,
                context
            FROM notes
            WHERE org_id = $1
            ORDER BY priority DESC, created_at DESC
            """,
            org_id,
        )

        notes = []
        for row in rows:
            created_at = row["created_at"]
            ttl_hours = row["ttl_hours"]

            # Compute expires_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=ZoneInfo("UTC"))
            expires_at = created_at + timedelta(hours=ttl_hours)

            notes.append(
                {
                    "note_id": row["note_id"],
                    "org_id": row["org_id"],
                    "content": row["content"],
                    "created_at": created_at.isoformat(),
                    "ttl_hours": ttl_hours,
                    "priority": row["priority"],
                    "source": row["source"],
                    "context": row["context"] if row["context"] else {},
                    "expires_at": expires_at.isoformat(),
                }
            )

        return notes


async def get_expiring_notes(
    org_id: str,
    threshold_hours: Optional[float] = None,
    threshold_fraction: Optional[float] = None,
    min_priority: float = 0.0,
) -> list[dict[str, Any]]:
    """
    Get notes that are approaching expiration.

    Args:
        org_id: Organization ID
        threshold_hours: Hours until expiration (e.g., 6 = expiring in 6 hours)
        threshold_fraction: Fraction of TTL remaining (e.g., 0.25 = 25% time left)
        min_priority: Minimum priority to include

    Returns:
        List of expiring notes
    """
    notes = await get_org_notes(org_id)
    now = datetime.now(ZoneInfo("UTC"))
    expiring = []

    for note in notes:
        if note["priority"] < min_priority:
            continue

        expires_at = datetime.fromisoformat(note["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("UTC"))

        time_remaining = (expires_at - now).total_seconds()
        if time_remaining <= 0:
            # Already expired - include with 0% remaining
            note["ttl_remaining"] = 0.0
            expiring.append(note)
            continue

        total_ttl = note["ttl_hours"] * 3600  # Convert to seconds

        # Check threshold_hours
        if threshold_hours is not None:
            if time_remaining <= threshold_hours * 3600:
                note["ttl_remaining"] = time_remaining / total_ttl if total_ttl > 0 else 0
                expiring.append(note)
                continue

        # Check threshold_fraction
        if threshold_fraction is not None:
            fraction_remaining = time_remaining / total_ttl if total_ttl > 0 else 0
            if fraction_remaining <= threshold_fraction:
                note["ttl_remaining"] = fraction_remaining
                expiring.append(note)

    return expiring


async def save_note(note: dict[str, Any]) -> None:
    """
    Save or update a note.

    Note dict should have: note_id, org_id, content, ttl_hours, priority, source, context
    """
    async with get_connection() as conn:
        context_json = json.dumps(note.get("context", {}))

        await conn.execute(
            """
            INSERT INTO notes (note_id, org_id, content, ttl_hours, priority, source, context)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            ON CONFLICT (note_id) DO UPDATE SET
                content = EXCLUDED.content,
                ttl_hours = EXCLUDED.ttl_hours,
                priority = EXCLUDED.priority,
                source = EXCLUDED.source,
                context = EXCLUDED.context
            """,
            note["note_id"],
            note["org_id"],
            note["content"],
            note.get("ttl_hours", 24),
            note.get("priority", 0.5),
            note.get("source", "system"),
            context_json,
        )


async def delete_note(note_id: str) -> bool:
    """Delete a note by ID."""
    async with get_connection() as conn:
        result = await conn.execute(
            "DELETE FROM notes WHERE note_id = $1",
            note_id,
        )
        return str(result) == "DELETE 1"


async def delete_expired_notes(org_id: str) -> int:
    """
    Delete all expired notes for an organization.

    Returns number of notes deleted.
    """
    async with get_connection() as conn:
        result = await conn.execute(
            """
            DELETE FROM notes
            WHERE org_id = $1
            AND created_at + (ttl_hours || ' hours')::INTERVAL < NOW()
            """,
            org_id,
        )
        # Parse "DELETE N" to get count
        if result.startswith("DELETE "):
            return int(result.split()[1])
        return 0
