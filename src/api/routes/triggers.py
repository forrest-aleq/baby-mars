"""
Triggers Routes
===============

API endpoints for managing proactive triggers.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ...observability import get_logger
from ...scheduler import get_pulse_scheduler
from ...scheduler.defaults import seed_org_triggers
from ...scheduler.executor import execute_trigger
from ...scheduler.persistence import (
    create_trigger,
    delete_trigger,
    get_trigger,
    load_org_triggers,
    save_trigger,
)
from ..auth import get_current_org
from ..schemas.triggers import (
    CreateTriggerRequest,
    FireTriggerRequest,
    SchedulerStatusResponse,
    TriggerFireResult,
    TriggerListResponse,
    TriggerResponse,
    UpdateTriggerRequest,
)

logger = get_logger("baby_mars.api.triggers")

router = APIRouter()


@router.get("", response_model=TriggerListResponse)
async def list_triggers(
    org_id: str = Depends(get_current_org),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
) -> TriggerListResponse:
    """
    List all triggers for the organization.

    Optionally filter by user_id, trigger_type, or enabled status.
    """
    triggers = await load_org_triggers(org_id)

    # Apply filters
    if user_id is not None:
        triggers = [t for t in triggers if t.get("user_id") == user_id]
    if trigger_type is not None:
        triggers = [t for t in triggers if t["trigger_type"] == trigger_type]
    if enabled is not None:
        triggers = [t for t in triggers if t["enabled"] == enabled]

    return TriggerListResponse(
        triggers=[TriggerResponse(**t) for t in triggers],
        total=len(triggers),
    )


@router.post("", response_model=TriggerResponse)
async def create_new_trigger(
    request: CreateTriggerRequest,
    org_id: str = Depends(get_current_org),
) -> TriggerResponse:
    """
    Create a new trigger for the organization.
    """
    trigger = create_trigger(
        org_id=org_id,
        trigger_type=request.trigger_type,
        action=request.action,
        config=request.config,
        description=request.description,
        user_id=request.user_id,
        created_by="user",
    )
    trigger["enabled"] = request.enabled

    await save_trigger(trigger)
    logger.info(f"Created trigger {trigger['trigger_id']} for org {org_id}")

    return TriggerResponse(**trigger)


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    org_id: str = Depends(get_current_org),
) -> SchedulerStatusResponse:
    """
    Get SYSTEM_PULSE scheduler status.
    """
    scheduler = get_pulse_scheduler()
    status = scheduler.get_status()

    # Count active triggers for this org
    triggers = await load_org_triggers(org_id)
    active_count = sum(1 for t in triggers if t["enabled"])

    return SchedulerStatusResponse(
        running=status["running"],
        check_interval_seconds=status["check_interval_seconds"],
        last_check=status["last_check"],
        active_triggers=active_count,
    )


@router.post("/seed", response_model=dict)
async def seed_default_triggers(
    org_id: str = Depends(get_current_org),
    timezone: str = Query("America/Los_Angeles", description="Org timezone"),
) -> dict:
    """
    Seed default triggers for the organization.

    Use this during org setup or to reset to defaults.
    """
    count = await seed_org_triggers(org_id, timezone)
    return {"seeded": count, "org_id": org_id}


@router.get("/{trigger_id}", response_model=TriggerResponse)
async def get_trigger_by_id(
    trigger_id: str = Path(..., description="Trigger ID"),
    org_id: str = Depends(get_current_org),
) -> TriggerResponse:
    """
    Get a specific trigger by ID.
    """
    trigger = await get_trigger(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    if trigger["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Trigger belongs to different org")

    return TriggerResponse(**trigger)


@router.patch("/{trigger_id}", response_model=TriggerResponse)
async def update_trigger_by_id(
    request: UpdateTriggerRequest,
    trigger_id: str = Path(..., description="Trigger ID"),
    org_id: str = Depends(get_current_org),
) -> TriggerResponse:
    """
    Update an existing trigger.

    Can update enabled status, config, or description.
    """
    trigger = await get_trigger(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    if trigger["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Trigger belongs to different org")

    # Apply updates
    if request.enabled is not None:
        trigger["enabled"] = request.enabled
    if request.config is not None:
        trigger["config"].update(request.config)
    if request.description is not None:
        trigger["description"] = request.description

    await save_trigger(trigger)
    logger.info(f"Updated trigger {trigger_id}")

    return TriggerResponse(**trigger)


@router.delete("/{trigger_id}")
async def delete_trigger_by_id(
    trigger_id: str = Path(..., description="Trigger ID"),
    org_id: str = Depends(get_current_org),
) -> dict:
    """
    Delete a trigger.
    """
    trigger = await get_trigger(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    if trigger["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Trigger belongs to different org")

    await delete_trigger(trigger_id)
    logger.info(f"Deleted trigger {trigger_id}")

    return {"deleted": trigger_id}


@router.post("/{trigger_id}/fire", response_model=TriggerFireResult)
async def fire_trigger_now(
    trigger_id: str = Path(..., description="Trigger ID"),
    request: Optional[FireTriggerRequest] = None,
    org_id: str = Depends(get_current_org),
) -> TriggerFireResult:
    """
    Manually fire a trigger (for testing/debugging).
    """
    trigger = await get_trigger(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    if trigger["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Trigger belongs to different org")

    event_data = request.event_data if request else None
    result = await execute_trigger(trigger_id, event_data)

    logger.info(f"Manually fired trigger {trigger_id}: success={result['success']}")

    return TriggerFireResult(**result)
