"""
Time Awareness
==============

Builds rich temporal context for Aleq's "sense of time".
Aleq always knows what day/time it is - this influences all behavior.

Usage:
    from src.scheduler import build_temporal_context

    temporal = build_temporal_context("America/Los_Angeles")
    # temporal["day_of_week"] -> "Monday"
    # temporal["time_of_day"] -> "morning"
    # temporal["is_month_end"] -> True
"""

from calendar import monthrange
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ..state.types import TemporalContext

# Default timezone if org doesn't specify
DEFAULT_TIMEZONE = "America/Los_Angeles"


def get_time_of_day(hour: int) -> str:
    """
    Map hour to human-friendly time of day.

    - morning: 5am - 11am
    - afternoon: 12pm - 5pm
    - evening: 6pm - 9pm
    - night: 10pm - 4am
    """
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def _days_until_month_end(now: datetime) -> int:
    """Calculate days remaining until end of current month."""
    _, last_day = monthrange(now.year, now.month)
    return last_day - now.day


def _days_until_quarter_end(now: datetime) -> int:
    """Calculate days remaining until end of current quarter."""
    # Quarter end months: 3, 6, 9, 12
    quarter_end_month = ((now.month - 1) // 3 + 1) * 3
    _, last_day = monthrange(now.year, quarter_end_month)

    if now.month == quarter_end_month:
        return last_day - now.day
    else:
        # Days left in current month + days in remaining months
        days = _days_until_month_end(now)
        for m in range(now.month + 1, quarter_end_month + 1):
            _, days_in_month = monthrange(now.year, m)
            days += days_in_month
        return days


def _calculate_urgency(
    is_month_end: bool,
    is_quarter_end: bool,
    is_year_end: bool,
    days_until_deadline: Optional[int],
) -> float:
    """
    Calculate urgency multiplier based on temporal context.

    Returns:
        1.0 = normal
        1.25 = slightly elevated (approaching month-end)
        1.5 = elevated (month-end)
        1.75 = high (quarter-end)
        2.0 = critical (year-end or imminent deadline)
    """
    urgency = 1.0

    # Deadline-based urgency (highest priority)
    if days_until_deadline is not None:
        if days_until_deadline <= 1:
            return 2.0
        elif days_until_deadline <= 3:
            urgency = max(urgency, 1.75)
        elif days_until_deadline <= 7:
            urgency = max(urgency, 1.5)

    # Period-based urgency
    if is_year_end:
        urgency = max(urgency, 2.0)
    elif is_quarter_end:
        urgency = max(urgency, 1.75)
    elif is_month_end:
        urgency = max(urgency, 1.5)

    return urgency


def _get_week_of_month(now: datetime) -> int:
    """Get week number within the month (1-5)."""
    first_day = now.replace(day=1)
    # Adjust for which day of week the month starts on
    adjusted_day = now.day + first_day.weekday()
    return (adjusted_day - 1) // 7 + 1


def build_temporal_context(
    timezone_str: str = DEFAULT_TIMEZONE,
    deadline_date: Optional[datetime] = None,
) -> TemporalContext:
    """
    Build rich temporal context for Aleq's time awareness.

    This is called on EVERY cognitive loop invocation to ensure
    Aleq always has current time awareness.

    Args:
        timezone_str: IANA timezone (e.g., "America/Los_Angeles")
        deadline_date: Optional specific deadline to track

    Returns:
        TemporalContext with full time awareness
    """
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo(DEFAULT_TIMEZONE)

    now = datetime.now(tz)

    # Basic time components
    hour = now.hour
    day_of_week = now.strftime("%A")  # "Monday", "Tuesday", etc.
    time_of_day = get_time_of_day(hour)
    is_weekend = now.weekday() >= 5
    is_business_hours = 8 <= hour < 18 and not is_weekend

    # Calendar components
    week_of_month = _get_week_of_month(now)
    day_of_month = now.day
    month = now.month
    year = now.year

    # Business period awareness
    is_month_end = day_of_month >= 25
    is_quarter_end = is_month_end and month in (3, 6, 9, 12)
    is_year_end = is_quarter_end and month == 12

    # Countdowns
    days_until_month_end = _days_until_month_end(now)
    days_until_quarter_end = _days_until_quarter_end(now)

    # Deadline tracking
    days_until_deadline: Optional[int] = None
    if deadline_date:
        if deadline_date.tzinfo is None:
            deadline_date = deadline_date.replace(tzinfo=tz)
        delta = deadline_date.date() - now.date()
        days_until_deadline = delta.days

    # Calculate urgency
    urgency = _calculate_urgency(is_month_end, is_quarter_end, is_year_end, days_until_deadline)

    return TemporalContext(
        current_time=now.isoformat(),
        day_of_week=day_of_week,
        time_of_day=time_of_day,
        hour=hour,
        is_business_hours=is_business_hours,
        is_weekend=is_weekend,
        week_of_month=week_of_month,
        day_of_month=day_of_month,
        month=month,
        year=year,
        is_month_end=is_month_end,
        is_quarter_end=is_quarter_end,
        is_year_end=is_year_end,
        days_until_month_end=days_until_month_end,
        days_until_quarter_end=days_until_quarter_end,
        days_until_deadline=days_until_deadline,
        urgency_multiplier=urgency,
    )
