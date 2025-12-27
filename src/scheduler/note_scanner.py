"""
Note Scanner
============

Scans for expiring notes based on TTL thresholds.
Used by note_ttl triggers to alert about aging follow-up items.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from ..observability import get_logger

logger = get_logger(__name__)


async def get_expiring_notes(
    org_id: str,
    threshold: float = 0.25,
    min_priority: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Get notes that are approaching expiration.

    Args:
        org_id: Organization ID to scan
        threshold: TTL fraction remaining (0.25 = 25% remaining)
        min_priority: Only return notes above this priority

    Returns:
        List of expiring notes with metadata
    """
    # Import here to avoid circular imports
    from ..persistence.notes import get_org_notes

    try:
        notes = await get_org_notes(org_id)
    except Exception as e:
        logger.warning(f"Could not load notes for org {org_id}: {e}")
        return []

    now = datetime.now(ZoneInfo("UTC"))
    expiring = []

    for note in notes:
        # Skip low priority notes
        priority = note.get("priority", 0.5)
        if priority < min_priority:
            continue

        # Calculate TTL remaining
        ttl_remaining = _calculate_ttl_remaining(note, now)
        if ttl_remaining is None:
            continue

        # Check if below threshold
        if ttl_remaining <= threshold:
            expiring.append(
                {
                    "note_id": note.get("note_id"),
                    "content": note.get("content", ""),
                    "priority": priority,
                    "ttl_remaining": ttl_remaining,
                    "created_at": note.get("created_at"),
                    "expires_at": note.get("expires_at"),
                }
            )

    # Sort by TTL remaining (most urgent first)
    expiring.sort(key=lambda n: n["ttl_remaining"])

    logger.debug(f"Found {len(expiring)} expiring notes for org {org_id}")
    return expiring


def _calculate_ttl_remaining(
    note: dict[str, Any],
    now: datetime,
) -> float | None:
    """
    Calculate fraction of TTL remaining for a note.

    Returns:
        Float 0.0-1.0 representing fraction remaining, or None if not applicable
    """
    created_at_str = note.get("created_at")
    expires_at_str = note.get("expires_at")

    if not created_at_str or not expires_at_str:
        return None

    try:
        created_at = datetime.fromisoformat(created_at_str)
        expires_at = datetime.fromisoformat(expires_at_str)

        # Ensure timezone awareness
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=ZoneInfo("UTC"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("UTC"))

        total_ttl = (expires_at - created_at).total_seconds()
        if total_ttl <= 0:
            return 0.0

        remaining = (expires_at - now).total_seconds()
        if remaining <= 0:
            return 0.0

        return remaining / total_ttl

    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse note dates: {e}")
        return None


async def get_note_summary_for_trigger(
    org_id: str,
    expiring_notes: list[dict[str, Any]],
) -> str:
    """
    Create a human-readable summary of expiring notes.

    Args:
        org_id: Organization ID
        expiring_notes: List of expiring note dicts

    Returns:
        Natural language summary for trigger message
    """
    if not expiring_notes:
        return "No pending follow-ups need attention."

    count = len(expiring_notes)

    if count == 1:
        note = expiring_notes[0]
        content = note.get("content", "item")[:50]
        pct = int(note["ttl_remaining"] * 100)
        return f"Quick reminder about '{content}' - only {pct}% of time left."

    # Multiple notes
    urgent = [n for n in expiring_notes if n["ttl_remaining"] < 0.1]
    soon = [n for n in expiring_notes if 0.1 <= n["ttl_remaining"] < 0.25]

    parts = []
    if urgent:
        parts.append(f"{len(urgent)} items expiring very soon")
    if soon:
        parts.append(f"{len(soon)} items need attention soon")

    if parts:
        return f"Hey, heads up - {', '.join(parts)}."
    else:
        return f"{count} follow-up items are getting close to their deadlines."
