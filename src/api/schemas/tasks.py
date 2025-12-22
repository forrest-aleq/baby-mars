"""
Task Schemas
============

Request/response models for task management.
Per API_CONTRACT_V0.md section 2
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from .common import PaginatedResponse


TaskStatus = Literal[
    "pending",      # Queued, not started
    "running",      # Actively working
    "blocked",      # Waiting on external (decision, data, human)
    "paused",       # User explicitly paused
    "completed",    # Done successfully
    "failed",       # Unrecoverable error
    "superseded",   # Replaced by newer task
]

TaskSource = Literal[
    "system",       # Auto-triggered (lockbox, overdue, etc.)
    "user",         # User requested
    "aleq",         # Aleq proposed
]


class TaskTimelineEntry(BaseModel):
    """Single entry in task timeline"""
    timestamp: str
    event: str = Field(..., description="What happened")
    actor: str = Field(..., description="Who/what did it: 'aleq', 'system', user_id")
    details: Optional[dict] = None


class TaskSummary(BaseModel):
    """Task summary for list views"""
    task_id: str
    type: str = Field(..., description="Task type: lockbox, collection, close, etc.")
    summary: str = Field(..., description="Human-readable summary")
    status: TaskStatus
    source: TaskSource
    priority: float = Field(..., ge=0, le=1)
    created_at: str
    updated_at: str
    has_decisions: bool = Field(False, description="Has pending decisions")
    decision_count: int = Field(0)
    subtask_count: int = Field(0)
    progress: Optional[float] = Field(None, ge=0, le=1, description="0-1 if trackable")


class TaskDecision(BaseModel):
    """Decision summary within task context"""
    decision_id: str
    type: str
    summary: str
    status: Literal["pending", "approved", "rejected", "expired"]
    created_at: str
    confidence: Optional[float] = Field(None, ge=0, le=1)


class TaskDetail(BaseModel):
    """Full task detail"""
    task_id: str
    type: str
    summary: str
    description: Optional[str] = None
    status: TaskStatus
    source: TaskSource
    priority: float
    difficulty: int = Field(..., ge=1, le=5)

    # Tree structure
    parent_id: Optional[str] = None
    subtasks: list["TaskSummary"] = Field(default_factory=list)

    # Progress
    progress: Optional[float] = None
    current_step: Optional[str] = None

    # Decisions
    decisions: list[TaskDecision] = Field(default_factory=list)

    # Timeline
    timeline: list[TaskTimelineEntry] = Field(default_factory=list)

    # Metadata
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Error info (if failed)
    error: Optional[dict] = None
    recovery_actions: list[dict] = Field(default_factory=list)


class TaskTimeline(BaseModel):
    """Just the timeline for refresh"""
    task_id: str
    timeline: list[TaskTimelineEntry]
    status: TaskStatus
    progress: Optional[float] = None


class TaskListResponse(PaginatedResponse):
    """Paginated task list"""
    tasks: list[TaskSummary]


class TaskProgressEvent(BaseModel):
    """
    SSE progress event for long-running tasks.
    Per API_CONTRACT_V0.md section 2.4
    """
    task_id: str
    stage: int
    stage_name: str
    stage_total: int
    stage_progress: float = Field(..., ge=0, le=1)
    detail: Optional[dict] = None
    message: str


class TaskMilestoneEvent(BaseModel):
    """Milestone event for stage completion"""
    task_id: str
    type: Literal["stage_complete", "checkpoint", "error_recovered"]
    stage: int
    stage_name: str
    summary: str
    next_stage: Optional[str] = None
    requires_action: bool = False


# Allow forward reference for subtasks
TaskDetail.model_rebuild()
