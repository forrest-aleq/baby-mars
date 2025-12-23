"""
State Reducers
===============

Custom reducers for LangGraph state management.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from .types import ActiveTask, Note

logger = logging.getLogger(__name__)


def task_reducer(existing: list[ActiveTask], new: list[ActiveTask]) -> list[ActiveTask]:
    """
    Keep max 4 active tasks, priority-based replacement.
    Paper #8: Working memory capacity of 3-4 items.
    """
    by_id = {t["task_id"]: t for t in existing}
    for t in new:
        by_id[t["task_id"]] = t

    combined = list(by_id.values())
    combined.sort(key=lambda t: t.get("priority", 0), reverse=True)
    return combined[:4]


def note_reducer(existing: list[Note], new: list[Note]) -> list[Note]:
    """
    Merge notes, expire TTL-exceeded ones.
    Paper #8: Notes with TTL.
    """
    now = datetime.now(timezone.utc)  # Use UTC for consistent comparison
    is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"

    by_id = {n["note_id"]: n for n in existing}
    for n in new:
        by_id[n["note_id"]] = n

    valid = []
    for note in by_id.values():
        try:
            created = datetime.fromisoformat(note["created_at"])
            # Normalize to UTC if naive datetime
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            ttl = timedelta(hours=note["ttl_hours"])
            if now - created < ttl:
                valid.append(note)
        except (ValueError, KeyError) as e:
            logger.warning(
                f"Invalid note data: note_id={note.get('note_id', 'unknown')}, "
                f"created_at={note.get('created_at', 'missing')}, "
                f"ttl_hours={note.get('ttl_hours', 'missing')}, error={e}"
            )
            if not is_production:
                valid.append(note)

    return valid
