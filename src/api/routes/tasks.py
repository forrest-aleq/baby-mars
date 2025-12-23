"""
Tasks Routes
============

Task management endpoints.
Per API_CONTRACT_V0.md section 2
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ..schemas.tasks import (
    TaskDecision,
    TaskDetail,
    TaskListResponse,
    TaskStatus,
    TaskSummary,
    TaskTimeline,
    TaskTimelineEntry,
)

logger = logging.getLogger("baby_mars.api.tasks")

router = APIRouter()

# In-memory task store (will be moved to persistence layer)
# Structure: {task_id: TaskDetail}
_tasks: dict[str, dict[str, Any]] = {}


def _get_task_or_404(task_id: str) -> dict[str, Any]:
    """Get task or raise 404"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task {task_id} not found",
                    "severity": "warning",
                }
            },
        )
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="Comma-separated statuses"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    """
    List tasks with filtering.

    Per API_CONTRACT_V0.md section 2.2, tasks have states:
    - pending: Queued, not started
    - running: Actively working
    - blocked: Waiting on external
    - paused: User paused
    - completed: Done successfully
    - failed: Unrecoverable error
    - superseded: Replaced
    """
    tasks = list(_tasks.values())

    # Filter by status
    if status:
        statuses = status.split(",")
        tasks = [t for t in tasks if t.get("status") in statuses]

    # Filter by source
    if source:
        tasks = [t for t in tasks if t.get("source") == source]

    # Sort by priority desc, then created_at desc
    tasks.sort(key=lambda t: (-t.get("priority", 0), t.get("created_at", "")), reverse=False)

    total = len(tasks)
    tasks = tasks[offset : offset + limit]

    return TaskListResponse(
        tasks=[
            TaskSummary(
                task_id=t["task_id"],
                type=t["type"],
                summary=t["summary"],
                status=t["status"],
                source=t["source"],
                priority=t["priority"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
                has_decisions=bool(t.get("decisions")),
                decision_count=len(t.get("decisions", [])),
                subtask_count=len(t.get("subtasks", [])),
                progress=t.get("progress"),
            )
            for t in tasks
        ],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str) -> TaskDetail:
    """
    Get full task detail with subtasks, timeline, and decisions.
    """
    task = _get_task_or_404(task_id)

    return TaskDetail(
        task_id=task["task_id"],
        type=task["type"],
        summary=task["summary"],
        description=task.get("description"),
        status=task["status"],
        source=task["source"],
        priority=task["priority"],
        difficulty=task.get("difficulty", 2),
        parent_id=task.get("parent_id"),
        subtasks=[TaskSummary(**st) for st in task.get("subtasks", [])],
        progress=task.get("progress"),
        current_step=task.get("current_step"),
        decisions=[TaskDecision(**d) for d in task.get("decisions", [])],
        timeline=[TaskTimelineEntry(**e) for e in task.get("timeline", [])],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        error=task.get("error"),
        recovery_actions=task.get("recovery_actions", []),
    )


@router.get("/{task_id}/timeline", response_model=TaskTimeline)
async def get_task_timeline(task_id: str) -> TaskTimeline:
    """
    Get just the timeline for refresh.

    Lighter endpoint for polling task progress.
    """
    task = _get_task_or_404(task_id)

    return TaskTimeline(
        task_id=task["task_id"],
        timeline=[TaskTimelineEntry(**e) for e in task.get("timeline", [])],
        status=task["status"],
        progress=task.get("progress"),
    )


@router.post("/{task_id}/pause")
async def pause_task(task_id: str) -> dict[str, str]:
    """
    Pause a running task.

    User can say "not now" and resume later.
    """
    task = _get_task_or_404(task_id)

    if task["status"] not in ("pending", "running", "blocked"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "CANNOT_PAUSE",
                    "message": f"Cannot pause task in {task['status']} state",
                    "severity": "info",
                }
            },
        )

    task["previous_status"] = task["status"]
    task["status"] = "paused"
    task["updated_at"] = datetime.now().isoformat()
    task["timeline"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "event": "Task paused",
            "actor": "user",
        }
    )

    logger.info(f"Task paused: {task_id}")

    return {"task_id": task_id, "status": "paused"}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str) -> dict[str, str]:
    """
    Resume a paused task.
    """
    task = _get_task_or_404(task_id)

    if task["status"] != "paused":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "NOT_PAUSED",
                    "message": "Task is not paused",
                    "severity": "info",
                }
            },
        )

    task["status"] = task.get("previous_status", "running")
    task["updated_at"] = datetime.now().isoformat()
    task["timeline"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "event": "Task resumed",
            "actor": "user",
        }
    )

    logger.info(f"Task resumed: {task_id}")

    return {"task_id": task_id, "status": task["status"]}


# Internal function for creating tasks (called from cognitive loop)
def create_task(
    task_type: str,
    summary: str,
    source: str = "system",
    priority: float = 0.5,
    difficulty: int = 2,
    parent_id: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Create a new task. Returns task_id.

    Called internally when:
    - System triggers task (lockbox, overdue, etc.)
    - User requests task
    - Aleq proposes task
    """
    import uuid

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    task = {
        "task_id": task_id,
        "type": task_type,
        "summary": summary,
        "description": description,
        "status": "pending",
        "source": source,
        "priority": priority,
        "difficulty": difficulty,
        "parent_id": parent_id,
        "subtasks": [],
        "decisions": [],
        "timeline": [
            {
                "timestamp": now,
                "event": "Task created",
                "actor": source,
            }
        ],
        "created_at": now,
        "updated_at": now,
    }

    _tasks[task_id] = task

    logger.info(f"Task created: {task_id} ({task_type})")

    return task_id


def update_task_status(
    task_id: str,
    status: TaskStatus,
    actor: str = "system",
    message: Optional[str] = None,
    progress: Optional[float] = None,
    current_step: Optional[str] = None,
) -> None:
    """Update task status and add timeline entry."""
    task = _tasks.get(task_id)
    if not task:
        return

    task["status"] = status
    task["updated_at"] = datetime.now().isoformat()

    if progress is not None:
        task["progress"] = progress
    if current_step:
        task["current_step"] = current_step

    event = message or f"Status changed to {status}"
    task["timeline"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "actor": actor,
        }
    )

    if status == "completed":
        task["completed_at"] = datetime.now().isoformat()
    elif status == "running" and not task.get("started_at"):
        task["started_at"] = datetime.now().isoformat()

    logger.info(f"Task updated: {task_id} -> {status}")
