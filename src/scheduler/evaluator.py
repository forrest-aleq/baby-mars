"""
Trigger Evaluator
=================

Evaluates which triggers should fire based on current time and conditions.
Called by PulseScheduler on each check interval.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from ..observability import get_logger
from .triggers import ScheduledTrigger

logger = get_logger(__name__)


async def evaluate_triggers() -> int:
    """
    Evaluate all active triggers and fire those that should run.

    Returns:
        Number of triggers that fired
    """
    from .persistence import load_active_triggers

    triggers = await load_active_triggers()
    fired_count = 0

    for trigger in triggers:
        if await should_fire(trigger):
            from .executor import execute_trigger

            try:
                await execute_trigger(trigger["trigger_id"])
                fired_count += 1
            except Exception as e:
                logger.error(f"Trigger {trigger['trigger_id']} failed: {e}")

    return fired_count


async def should_fire(trigger: ScheduledTrigger) -> bool:
    """
    Determine if a trigger should fire now.

    Args:
        trigger: The trigger to evaluate

    Returns:
        True if trigger should fire
    """
    if not trigger["enabled"]:
        return False

    trigger_type = trigger["trigger_type"]

    if trigger_type == "time":
        return _should_fire_time_trigger(trigger)
    elif trigger_type == "deadline":
        return _should_fire_deadline_trigger(trigger)
    elif trigger_type == "note_ttl":
        return await _should_fire_note_ttl_trigger(trigger)
    elif trigger_type == "event":
        # Event triggers are handled separately via event bus
        return False

    return False


def _should_fire_time_trigger(trigger: ScheduledTrigger) -> bool:
    """Check if a time-based trigger should fire."""
    config = trigger["config"]
    timezone_str = config.get("timezone", "America/Los_Angeles")

    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("America/Los_Angeles")

    now = datetime.now(tz)
    target_hour = config.get("hour", 8)
    target_minute = config.get("minute", 0)
    schedule_type = config.get("schedule_type", "daily")

    # Check if we're in the right time window (within 2 minutes of target)
    if now.hour != target_hour:
        return False
    if abs(now.minute - target_minute) > 1:
        return False

    # Check schedule type
    if schedule_type == "weekdays" and now.weekday() >= 5:
        return False
    if schedule_type == "weekly":
        target_dow = config.get("day_of_week", 0)
        if now.weekday() != target_dow:
            return False
    if schedule_type == "monthly":
        target_dom = config.get("day_of_month", 1)
        if now.day != target_dom:
            return False

    # Check if already fired today
    last_fired = trigger.get("last_fired")
    if last_fired:
        last_fired_dt = datetime.fromisoformat(last_fired)
        if last_fired_dt.tzinfo is None:
            last_fired_dt = last_fired_dt.replace(tzinfo=tz)
        if last_fired_dt.date() == now.date():
            return False

    return True


def _should_fire_deadline_trigger(trigger: ScheduledTrigger) -> bool:
    """Check if a deadline-based trigger should fire."""
    config = trigger["config"]
    deadline_type = config.get("deadline_type", "month_end")
    alert_days = config.get("alert_days", [7, 3, 1])

    now = datetime.now(ZoneInfo("UTC"))

    # Calculate days until deadline
    if deadline_type == "month_end":
        from calendar import monthrange

        _, last_day = monthrange(now.year, now.month)
        days_until = last_day - now.day
    elif deadline_type == "quarter_end":
        from .time_awareness import _days_until_quarter_end

        days_until = _days_until_quarter_end(now)
    elif deadline_type == "year_end":
        from calendar import monthrange

        _, dec_last = monthrange(now.year, 12)
        if now.month == 12:
            days_until = dec_last - now.day
        else:
            days_until = 365  # Too far away
    elif deadline_type == "custom" and config.get("custom_date"):
        custom = datetime.fromisoformat(config["custom_date"])
        days_until = (custom.date() - now.date()).days
    else:
        return False

    # Check if we should alert
    if days_until not in alert_days:
        return False

    # Check if already fired for this alert day
    alerts_fired = _get_alerts_fired_this_period(trigger, deadline_type)
    if days_until in alerts_fired:
        return False

    return True


def _get_alerts_fired_this_period(trigger: ScheduledTrigger, deadline_type: str) -> list[int]:
    """Get which alert days have already fired this period."""
    # This would check trigger history - simplified for now
    last_fired = trigger.get("last_fired")
    if not last_fired:
        return []

    now = datetime.now(ZoneInfo("UTC"))
    last_fired_dt = datetime.fromisoformat(last_fired)

    # If last fired was in a different period, reset
    if deadline_type == "month_end":
        if last_fired_dt.month != now.month:
            return []
    elif deadline_type == "quarter_end":
        if (last_fired_dt.month - 1) // 3 != (now.month - 1) // 3:
            return []

    # For simplicity, just return empty - real implementation would track
    return []


async def _should_fire_note_ttl_trigger(trigger: ScheduledTrigger) -> bool:
    """Check if a note TTL trigger should fire."""
    config = trigger["config"]
    threshold = config.get("alert_threshold", 0.25)
    min_priority = config.get("min_priority", 0.5)

    # Check for expiring notes in this org
    from .note_scanner import get_expiring_notes

    expiring = await get_expiring_notes(
        trigger["org_id"],
        threshold=threshold,
        min_priority=min_priority,
    )

    if not expiring:
        return False

    # Check if we've already alerted about these notes recently
    last_fired = trigger.get("last_fired")
    if last_fired:
        last_fired_dt = datetime.fromisoformat(last_fired)
        now = datetime.now(ZoneInfo("UTC"))
        # Don't fire more than once per hour
        if (now - last_fired_dt.replace(tzinfo=ZoneInfo("UTC"))).seconds < 3600:
            return False

    return True


async def handle_event_trigger(
    org_id: str,
    event_type: str,
    event_data: dict[str, Any],
) -> None:
    """
    Handle an incoming event that might trigger actions.

    Called by the event bus when events occur.
    """
    from .persistence import get_event_triggers

    triggers = await get_event_triggers(org_id, event_type)

    for trigger in triggers:
        config = trigger["config"]
        conditions = config.get("conditions", {})

        # Check conditions
        if not _matches_conditions(event_data, conditions):
            continue

        delay = config.get("delay_seconds", 0)

        if delay > 0:
            # Schedule delayed execution
            from .executor import schedule_delayed_trigger

            await schedule_delayed_trigger(trigger["trigger_id"], delay, event_data)
        else:
            # Execute immediately
            from .executor import execute_trigger

            await execute_trigger(trigger["trigger_id"], event_data)


def _matches_conditions(
    event_data: dict[str, Any],
    conditions: dict[str, Any],
) -> bool:
    """Check if event data matches trigger conditions."""
    for key, expected in conditions.items():
        actual = event_data.get(key)
        if actual != expected:
            return False
    return True
