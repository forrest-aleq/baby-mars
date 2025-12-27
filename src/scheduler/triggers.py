"""
Trigger Types
=============

Type definitions for scheduler triggers.
Aleq uses triggers to wake up proactively.

Four trigger types:
1. Time triggers - "8am daily", "5pm weekdays"
2. Event triggers - "when lockbox_processed"
3. Deadline triggers - "7 days before month-end"
4. Note TTL triggers - "when follow-up 75% expired"
"""

from typing import Any, Literal, Optional, TypedDict


class TimeTriggerConfig(TypedDict):
    """Configuration for time-based triggers."""

    schedule_type: Literal["daily", "weekdays", "weekly", "monthly"]
    hour: int  # 0-23
    minute: int  # 0-59
    day_of_week: Optional[int]  # 0-6 for weekly (0 = Monday)
    day_of_month: Optional[int]  # 1-31 for monthly
    timezone: str  # IANA timezone


class EventTriggerConfig(TypedDict):
    """Configuration for event-based triggers."""

    event_type: str  # "lockbox_processed", "invoice_received", etc.
    conditions: dict[str, Any]  # Optional filters
    delay_seconds: int  # 0 = immediate, >0 = debounce


class DeadlineTriggerConfig(TypedDict):
    """Configuration for deadline-based triggers."""

    deadline_type: Literal["month_end", "quarter_end", "year_end", "custom"]
    custom_date: Optional[str]  # ISO date for custom deadlines
    alert_days: list[int]  # Days before deadline to alert (e.g., [7, 3, 1])


class NoteTTLTriggerConfig(TypedDict):
    """Configuration for note TTL-based triggers."""

    alert_threshold: float  # Fraction of TTL remaining (e.g., 0.25 = 25%)
    min_priority: float  # Only trigger for notes above this priority


class ScheduledTrigger(TypedDict):
    """
    Complete trigger definition stored in database.

    Triggers can be org-level (default) or user-level (override).
    """

    trigger_id: str
    org_id: str
    user_id: Optional[str]  # None = org-level, set = user-specific

    # Type and configuration
    trigger_type: Literal["time", "event", "deadline", "note_ttl"]
    config: dict[str, Any]  # One of the config types above

    # What to do when triggered
    action: str  # "morning_check", "end_of_day_summary", etc.
    action_context: dict[str, Any]  # Additional context for the action

    # Human-readable
    description: str

    # State
    enabled: bool
    last_fired: Optional[str]  # ISO datetime
    next_fire: Optional[str]  # ISO datetime (for time triggers)
    fire_count: int

    # Metadata
    created_at: str
    updated_at: str
    created_by: Literal["system", "user", "aleq"]


class TriggerResult(TypedDict):
    """Result of executing a trigger."""

    trigger_id: str
    success: bool
    fired_at: str  # ISO datetime
    duration_ms: float

    # Cognitive loop result
    supervision_mode: Optional[str]
    message_generated: Optional[str]
    action_taken: Optional[str]

    # Error info
    error: Optional[str]


# Standard actions that triggers can invoke
STANDARD_ACTIONS = {
    "morning_check": "Morning task review and prioritization",
    "end_of_day_summary": "Daily summary and pending items review",
    "deadline_reminder": "Reminder about approaching deadline",
    "follow_up_reminder": "Reminder about aging follow-up items",
    "weekly_reconciliation": "Weekly reconciliation check",
    "month_end_prep": "Month-end close preparation",
    "lockbox_summary": "Summary after lockbox processing",
}
