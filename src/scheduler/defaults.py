"""
Default Triggers
================

Default proactive triggers seeded for each organization.
These give Aleq sensible out-of-the-box proactive behaviors.
"""

from typing import Any

from ..observability import get_logger
from .persistence import create_trigger, save_trigger

logger = get_logger(__name__)

# Default triggers every org gets
DEFAULT_TRIGGERS: list[dict[str, Any]] = [
    # Morning check-in at 8 AM
    {
        "trigger_type": "time",
        "action": "morning_check",
        "description": "Morning check-in and priority review",
        "config": {
            "schedule_type": "weekdays",
            "hour": 8,
            "minute": 0,
        },
    },
    # End of day summary at 5 PM
    {
        "trigger_type": "time",
        "action": "end_of_day_summary",
        "description": "End of day summary and rollover",
        "config": {
            "schedule_type": "weekdays",
            "hour": 17,
            "minute": 0,
        },
    },
    # Month-end deadline reminders (7, 3, 1 days before)
    {
        "trigger_type": "deadline",
        "action": "deadline_reminder",
        "description": "Month-end close reminders",
        "config": {
            "deadline_type": "month_end",
            "alert_days": [7, 3, 1],
        },
    },
    # Quarter-end deadline reminders (14, 7, 3, 1 days before)
    {
        "trigger_type": "deadline",
        "action": "deadline_reminder",
        "description": "Quarter-end close reminders",
        "config": {
            "deadline_type": "quarter_end",
            "alert_days": [14, 7, 3, 1],
        },
    },
    # Follow-up on aging notes (when 25% TTL remaining)
    {
        "trigger_type": "note_ttl",
        "action": "follow_up_reminder",
        "description": "Follow-up on aging items before they expire",
        "config": {
            "alert_threshold": 0.25,  # 25% TTL remaining
            "min_priority": 0.5,  # Only high-priority notes
        },
    },
]


async def seed_org_triggers(org_id: str, timezone: str = "America/Los_Angeles") -> int:
    """
    Seed default triggers for a new organization.

    Called during org birth/onboarding.

    Args:
        org_id: Organization ID
        timezone: IANA timezone for time-based triggers

    Returns:
        Number of triggers created
    """
    count = 0

    for trigger_def in DEFAULT_TRIGGERS:
        config = trigger_def["config"].copy()

        # Add timezone to time-based triggers
        if trigger_def["trigger_type"] == "time":
            config["timezone"] = timezone

        trigger = create_trigger(
            org_id=org_id,
            trigger_type=trigger_def["trigger_type"],
            action=trigger_def["action"],
            config=config,
            description=trigger_def["description"],
            created_by="system",
        )

        await save_trigger(trigger)
        count += 1
        logger.debug(f"Seeded trigger: {trigger['trigger_id']} ({trigger['action']})")

    logger.info(f"Seeded {count} default triggers for org {org_id}")
    return count


async def seed_user_overrides(
    org_id: str,
    user_id: str,
    preferences: dict[str, Any],
) -> int:
    """
    Seed user-specific trigger overrides.

    Users can customize their trigger schedule (e.g., different morning time).

    Args:
        org_id: Organization ID
        user_id: User ID
        preferences: User preferences dict

    Returns:
        Number of triggers created/modified
    """
    count = 0

    # Example: User prefers morning check at 7 AM instead of 8 AM
    morning_hour = preferences.get("morning_check_hour")
    if morning_hour is not None:
        trigger = create_trigger(
            org_id=org_id,
            trigger_type="time",
            action="morning_check",
            config={
                "schedule_type": "weekdays",
                "hour": morning_hour,
                "minute": 0,
                "timezone": preferences.get("timezone", "America/Los_Angeles"),
            },
            description="Morning check-in (user override)",
            user_id=user_id,
            created_by="user",
        )
        await save_trigger(trigger)
        count += 1

    # Example: User prefers end of day at different time
    eod_hour = preferences.get("end_of_day_hour")
    if eod_hour is not None:
        trigger = create_trigger(
            org_id=org_id,
            trigger_type="time",
            action="end_of_day_summary",
            config={
                "schedule_type": "weekdays",
                "hour": eod_hour,
                "minute": 0,
                "timezone": preferences.get("timezone", "America/Los_Angeles"),
            },
            description="End of day summary (user override)",
            user_id=user_id,
            created_by="user",
        )
        await save_trigger(trigger)
        count += 1

    if count > 0:
        logger.info(f"Created {count} user trigger overrides for {user_id}")

    return count


# Action types that can be triggered
ACTION_DESCRIPTIONS = {
    "morning_check": {
        "name": "Morning Check-in",
        "description": "Review pending tasks and priorities for the day",
        "typical_time": "8:00 AM",
    },
    "end_of_day_summary": {
        "name": "End of Day Summary",
        "description": "Summarize completed work and note pending items",
        "typical_time": "5:00 PM",
    },
    "deadline_reminder": {
        "name": "Deadline Reminder",
        "description": "Alert about approaching deadlines (month-end, quarter-end)",
        "typical_time": "Varies by deadline",
    },
    "follow_up_reminder": {
        "name": "Follow-up Reminder",
        "description": "Remind about aging items before they expire",
        "typical_time": "When items reach 25% TTL",
    },
    "weekly_reconciliation": {
        "name": "Weekly Reconciliation",
        "description": "Weekly reconciliation status check",
        "typical_time": "Friday afternoon",
    },
    "month_end_prep": {
        "name": "Month-end Prep",
        "description": "Preparation checklist for month-end close",
        "typical_time": "5 days before month-end",
    },
}
