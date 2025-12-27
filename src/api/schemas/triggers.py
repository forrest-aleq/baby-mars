"""
Trigger API Schemas
===================

Request/response models for trigger management API.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ============================================================
# REQUEST SCHEMAS
# ============================================================


class TimeTriggerConfig(BaseModel):
    """Configuration for time-based triggers."""

    schedule_type: Literal["daily", "weekdays", "weekly", "monthly"] = "daily"
    hour: int = Field(ge=0, le=23, description="Hour (0-23)")
    minute: int = Field(ge=0, le=59, default=0, description="Minute (0-59)")
    day_of_week: Optional[int] = Field(
        None, ge=0, le=6, description="Day of week for weekly (0=Mon)"
    )
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month for monthly")
    timezone: str = Field(default="America/Los_Angeles", description="IANA timezone")


class EventTriggerConfig(BaseModel):
    """Configuration for event-based triggers."""

    event_type: str = Field(..., description="Event type to trigger on")
    conditions: dict[str, Any] = Field(default_factory=dict, description="Event filter conditions")
    delay_seconds: int = Field(default=0, ge=0, description="Debounce delay in seconds")


class DeadlineTriggerConfig(BaseModel):
    """Configuration for deadline-based triggers."""

    deadline_type: Literal["month_end", "quarter_end", "year_end", "custom"]
    custom_date: Optional[str] = Field(None, description="ISO date for custom deadlines")
    alert_days: list[int] = Field(default=[7, 3, 1], description="Days before deadline to alert")


class NoteTTLTriggerConfig(BaseModel):
    """Configuration for note TTL triggers."""

    alert_threshold: float = Field(
        default=0.25, ge=0, le=1, description="TTL fraction to trigger at"
    )
    min_priority: float = Field(default=0.5, ge=0, le=1, description="Minimum note priority")


class CreateTriggerRequest(BaseModel):
    """Request to create a new trigger."""

    trigger_type: Literal["time", "event", "deadline", "note_ttl"]
    action: str = Field(..., description="Action to execute (e.g., 'morning_check')")
    config: dict[str, Any] = Field(..., description="Trigger-specific configuration")
    description: str = Field(default="", description="Human-readable description")
    user_id: Optional[str] = Field(None, description="User ID for user-specific overrides")
    enabled: bool = Field(default=True, description="Whether trigger is active")


class UpdateTriggerRequest(BaseModel):
    """Request to update an existing trigger."""

    enabled: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class FireTriggerRequest(BaseModel):
    """Request to manually fire a trigger."""

    event_data: Optional[dict[str, Any]] = Field(
        None, description="Optional event data for testing"
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class TriggerResponse(BaseModel):
    """Single trigger response."""

    trigger_id: str
    org_id: str
    user_id: Optional[str]
    trigger_type: str
    action: str
    config: dict[str, Any]
    action_context: dict[str, Any] = {}
    description: str
    enabled: bool
    last_fired: Optional[str]
    next_fire: Optional[str]
    fire_count: int
    created_at: str
    updated_at: str
    created_by: str


class TriggerListResponse(BaseModel):
    """List of triggers response."""

    triggers: list[TriggerResponse]
    total: int


class TriggerFireResult(BaseModel):
    """Result of firing a trigger."""

    trigger_id: str
    success: bool
    fired_at: str
    duration_ms: float
    supervision_mode: Optional[str]
    message_generated: Optional[str]
    action_taken: Optional[str]
    error: Optional[str]


class TriggerHistoryEntry(BaseModel):
    """Single entry in trigger history."""

    fired_at: str
    success: bool
    duration_ms: float
    supervision_mode: Optional[str]
    error: Optional[str]


class TriggerHistoryResponse(BaseModel):
    """Trigger execution history."""

    trigger_id: str
    entries: list[TriggerHistoryEntry]
    total_fires: int
    success_rate: float


class SchedulerStatusResponse(BaseModel):
    """Scheduler status for health checks."""

    running: bool
    check_interval_seconds: int
    last_check: Optional[str]
    active_triggers: int
