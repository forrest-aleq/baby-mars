"""
Pulse Executor
==============

Executes triggers by invoking the cognitive loop and handling results.
Routes proactive messages based on autonomy/supervision mode.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from ..observability import get_logger
from .message_factory import create_trigger_state
from .persistence import get_trigger, update_trigger_fired
from .triggers import TriggerResult

logger = get_logger(__name__)

# Delayed trigger queue (trigger_id -> scheduled task)
_delayed_triggers: dict[str, asyncio.Task[Any]] = {}


async def execute_trigger(
    trigger_id: str,
    event_data: Optional[dict[str, Any]] = None,
) -> TriggerResult:
    """
    Execute a trigger by invoking the cognitive loop.

    Args:
        trigger_id: ID of trigger to execute
        event_data: Optional event data for event-based triggers

    Returns:
        TriggerResult with execution outcome
    """
    start_time = datetime.now(ZoneInfo("UTC"))

    # Load trigger
    trigger = await get_trigger(trigger_id)
    if not trigger:
        return _error_result(trigger_id, start_time, "Trigger not found")

    if not trigger["enabled"]:
        return _error_result(trigger_id, start_time, "Trigger disabled")

    logger.info(
        f"Executing trigger {trigger_id}: {trigger['action']} " f"(type: {trigger['trigger_type']})"
    )

    try:
        # Create synthetic state for cognitive loop
        state = create_trigger_state(trigger, event_data)

        # Invoke cognitive loop
        result_state = await _invoke_cognitive_loop(state)

        # Handle result based on supervision mode
        supervision_mode = result_state.get("supervision_mode", "guidance_seeking")
        await _handle_result(trigger, result_state, supervision_mode)

        # Update trigger fired status
        await update_trigger_fired(trigger_id)

        # Build result
        duration = (datetime.now(ZoneInfo("UTC")) - start_time).total_seconds() * 1000

        return {
            "trigger_id": trigger_id,
            "success": True,
            "fired_at": start_time.isoformat(),
            "duration_ms": duration,
            "supervision_mode": supervision_mode,
            "message_generated": result_state.get("generated_response"),
            "action_taken": result_state.get("selected_action", {}).get("action_type"),
            "error": None,
        }

    except Exception as e:
        logger.error(f"Trigger execution failed: {trigger_id}: {e}", exc_info=True)
        return _error_result(trigger_id, start_time, str(e))


async def _invoke_cognitive_loop(state: Any) -> Any:
    """
    Invoke the cognitive loop with synthetic state.

    This is where the trigger's synthetic message flows through
    the full cognitive architecture.
    """
    # Import here to avoid circular imports
    from ..cognitive_loop.graph import create_graph_in_memory

    graph = create_graph_in_memory()

    # Run the graph
    result = await graph.ainvoke(
        state,
        {"configurable": {"thread_id": state["thread_id"]}},  # type: ignore[arg-type]
    )

    return result


async def _handle_result(
    trigger: Any,
    result_state: Any,
    supervision_mode: str,
) -> None:
    """
    Handle cognitive loop result based on supervision mode.

    - autonomous: Execute action and notify user
    - action_proposal: Notify user with proposal, await approval
    - guidance_seeking: Just inform user, no action
    """
    org_id = trigger["org_id"]
    user_id = trigger.get("user_id")

    response = result_state.get("generated_response", "")
    selected_action = result_state.get("selected_action")

    if supervision_mode == "autonomous":
        # Action was already executed in cognitive loop
        # Just notify user of what happened
        if response:
            await _publish_notification(org_id, user_id, response, "info")

    elif supervision_mode == "action_proposal":
        # Propose action to user, await approval
        if selected_action:
            await _publish_proposal(org_id, user_id, response, selected_action)
        elif response:
            await _publish_notification(org_id, user_id, response, "proposal")

    else:  # guidance_seeking
        # Just inform, don't take action
        if response:
            await _publish_notification(org_id, user_id, response, "info")


async def _publish_notification(
    org_id: str,
    user_id: Optional[str],
    message: str,
    notification_type: str,
) -> None:
    """
    Publish notification to user via SSE.

    Uses the existing publish_aleq_message infrastructure.
    """
    try:
        from ..api.routes.events import publish_aleq_message

        await publish_aleq_message(
            org_id=org_id,
            user_id=user_id,
            message=message,
            message_type=notification_type,
            source="system_pulse",
        )
        logger.debug(f"Published {notification_type} notification to {org_id}")

    except ImportError:
        logger.warning("SSE events not available - notification not sent")
    except Exception as e:
        logger.error(f"Failed to publish notification: {e}")


async def _publish_proposal(
    org_id: str,
    user_id: Optional[str],
    message: str,
    action: dict[str, Any],
) -> None:
    """
    Publish action proposal to user for approval.
    """
    try:
        from ..api.routes.events import publish_aleq_message

        await publish_aleq_message(
            org_id=org_id,
            user_id=user_id,
            message=message,
            message_type="action_proposal",
            source="system_pulse",
            metadata={"proposed_action": action},
        )
        logger.debug(f"Published action proposal to {org_id}")

    except ImportError:
        logger.warning("SSE events not available - proposal not sent")
    except Exception as e:
        logger.error(f"Failed to publish proposal: {e}")


async def schedule_delayed_trigger(
    trigger_id: str,
    delay_seconds: int,
    event_data: Optional[dict[str, Any]] = None,
) -> None:
    """
    Schedule a trigger to fire after a delay.

    Used for debouncing event triggers.
    """
    # Cancel existing delayed trigger if any
    if trigger_id in _delayed_triggers:
        _delayed_triggers[trigger_id].cancel()

    async def delayed_execute() -> None:
        await asyncio.sleep(delay_seconds)
        await execute_trigger(trigger_id, event_data)
        _delayed_triggers.pop(trigger_id, None)

    task = asyncio.create_task(delayed_execute())
    _delayed_triggers[trigger_id] = task
    logger.debug(f"Scheduled trigger {trigger_id} to fire in {delay_seconds}s")


def cancel_delayed_trigger(trigger_id: str) -> bool:
    """Cancel a pending delayed trigger."""
    if trigger_id in _delayed_triggers:
        _delayed_triggers[trigger_id].cancel()
        del _delayed_triggers[trigger_id]
        return True
    return False


def _error_result(
    trigger_id: str,
    start_time: datetime,
    error: str,
) -> TriggerResult:
    """Create error result."""
    duration = (datetime.now(ZoneInfo("UTC")) - start_time).total_seconds() * 1000
    return {
        "trigger_id": trigger_id,
        "success": False,
        "fired_at": start_time.isoformat(),
        "duration_ms": duration,
        "supervision_mode": None,
        "message_generated": None,
        "action_taken": None,
        "error": error,
    }
