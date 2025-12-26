"""
Chat Routes
===========

Chat endpoints with streaming, interruption, and context pills.
Per API_CONTRACT_V0.md sections 1.1-1.4
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, cast

from fastapi import APIRouter, HTTPException, Request
from langchain_core.runnables import RunnableConfig
from sse_starlette.sse import EventSourceResponse

from ...birth.birth_system import create_initial_state
from ...cognitive_loop.graph import invoke_cognitive_loop, stream_cognitive_loop
from ...observability import get_logger
from ...state.schema import BabyMARSState
from ..schemas.chat import (
    ApprovalRequest,
    ChatInterruptRequest,
    ChatInterruptResponse,
    MessageRequest,
    MessageResponse,
    Reference,
)

logger = get_logger("baby_mars.api.chat")

router = APIRouter()


def _update_session_state(
    session: dict[str, Any], message: str, birth_result: Any
) -> BabyMARSState:
    """Create or update session state with new message."""
    if session["state"] is None:
        session["state"] = create_initial_state(birth_result, message)
    else:
        session["state"]["messages"].append({"role": "user", "content": message})
        session["state"]["current_turn"] += 1
    session["message_count"] += 1
    return cast(BabyMARSState, session["state"])


def _extract_references(result: BabyMARSState) -> list[Reference]:
    """Extract references from cognitive loop result."""
    references: list[Reference] = []
    referenced_objs: list[dict[str, Any]] = cast(
        list[dict[str, Any]], result.get("referenced_objects") or []
    )
    for ref in referenced_objs:
        references.append(
            Reference(
                type=ref.get("type", "widget"),
                id=ref.get("id", ""),
                intensity=ref.get("intensity", "mention"),
            )
        )
    return references


def _build_error_detail(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    """Build error detail dict for HTTPException."""
    detail: dict[str, Any] = {
        "error": {"code": code, "message": message, "severity": "error", "recoverable": True}
    }
    if retryable:
        detail["error"]["retryable"] = True
        detail["error"]["retry"] = {
            "after_seconds": 2,
            "max_attempts": 3,
            "strategy": "exponential",
        }
        detail["error"]["actions"] = [{"label": "Try again", "action": "retry"}]
    return detail


def get_session(request: Request, session_id: str) -> dict[str, Any]:
    """Get session or raise 404"""
    session: dict[str, Any] | None = request.app.state.sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found. Did it expire?",
                    "severity": "error",
                    "recoverable": True,
                    "actions": [
                        {"label": "Start new session", "action": "new_session"},
                    ],
                }
            },
        )
    return session


@router.post("", response_model=MessageResponse)
async def send_message(request_data: MessageRequest, request: Request) -> MessageResponse:
    """Send a message and run the full cognitive loop."""
    session = get_session(request, request_data.session_id)
    pending_message = session.pop("pending_message", None)
    if pending_message:
        request_data.message = f"{pending_message}\n\n{request_data.message}"

    try:
        state = _update_session_state(session, request_data.message, session["birth_result"])
        if request_data.context_pills:
            session["context_pills"] = [
                {"type": p.type, "id": p.id} for p in request_data.context_pills
            ]

        config = cast(RunnableConfig, {"configurable": {"thread_id": state["thread_id"]}})
        result = await invoke_cognitive_loop(
            state=state, graph=request.app.state.graph, config=config
        )
        session["state"] = result

        supervision_mode = result.get("supervision_mode") or "guidance_seeking"
        belief_strength = result.get("belief_strength_for_action") or 0.0
        approval_needed = supervision_mode == "action_proposal"

        logger.info(
            f"Message processed: session={request_data.session_id}, mode={supervision_mode}, strength={belief_strength:.2f}"
        )

        return MessageResponse(
            session_id=request_data.session_id,
            response=str(result.get("final_response", "")),
            supervision_mode=supervision_mode,
            belief_strength=belief_strength,
            approval_needed=approval_needed,
            approval_summary=result.get("approval_summary") if approval_needed else None,
            references=_extract_references(result),
            context_budget=None,
        )

    except Exception as e:
        logger.error(f"Message processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=_build_error_detail(
                "PROCESSING_FAILED", f"Failed to process message: {e}", retryable=True
            ),
        )


def _process_stream_event(event: dict[str, Any], state: BabyMARSState) -> dict[str, str] | None:
    """Process a single stream event and return SSE dict or None."""
    event_type = event.get("event", "")
    if event_type == "on_chain_start":
        return {"event": "node_start", "data": json.dumps({"node": event.get("name", "unknown")})}
    elif event_type == "on_chain_end":
        output = event.get("data", {}).get("output", {})
        if isinstance(output, dict):
            state.update(cast(BabyMARSState, output))
        return {
            "event": "node_end",
            "data": json.dumps(
                {
                    "node": event.get("name", "unknown"),
                    "supervision_mode": state.get("supervision_mode"),
                }
            ),
        }
    elif event_type == "on_llm_stream":
        chunk = event.get("data", {}).get("chunk", "")
        if chunk:
            return {"event": "token", "data": json.dumps({"text": chunk})}
    return None


@router.post("/stream")
async def send_message_stream(
    request_data: MessageRequest, request: Request
) -> EventSourceResponse:
    """Send a message and stream the response via SSE."""
    session = get_session(request, request_data.session_id)
    session["interrupt_event"] = asyncio.Event()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        try:
            state = _update_session_state(session, request_data.message, session["birth_result"])
            config = cast(RunnableConfig, {"configurable": {"thread_id": state["thread_id"]}})

            async for event in stream_cognitive_loop(
                state=state, graph=request.app.state.graph, config=config
            ):
                if session["interrupt_event"].is_set():
                    yield {
                        "event": "interrupted",
                        "data": json.dumps(
                            {
                                "partial_response": state.get("final_response", ""),
                                "will_resume": True,
                            }
                        ),
                    }
                    return
                sse_event = _process_stream_event(event, state)
                if sse_event:
                    yield sse_event

            yield {
                "event": "complete",
                "data": json.dumps(
                    {
                        "response": state.get("final_response", ""),
                        "supervision_mode": state.get("supervision_mode", ""),
                        "belief_strength": state.get("belief_strength_for_action", 0.0),
                        "approval_needed": state.get("supervision_mode") == "action_proposal",
                    }
                ),
            }
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
        finally:
            session["interrupt_event"] = None

    return EventSourceResponse(event_generator())


@router.post("/interrupt", response_model=ChatInterruptResponse)
async def interrupt_stream(
    request_data: ChatInterruptRequest, request: Request
) -> ChatInterruptResponse:
    """
    Interrupt current streaming response.

    Per API_CONTRACT_V0.md section 1.1:
    - stop: Halt response, context preserved
    - pivot: Switch to processing new_message

    If action=pivot and new_message provided, immediately starts
    processing the new message after interruption.
    """
    session = get_session(request, request_data.session_id)

    interrupt_event = session.get("interrupt_event")
    if not interrupt_event:
        return ChatInterruptResponse(
            acknowledged=False,
            will_resume=False,
            partial_response=None,
        )

    # Signal interruption
    interrupt_event.set()

    # Get partial response
    partial = session["state"].get("final_response", "") if session["state"] else None

    # If pivoting, queue the new message
    if request_data.action == "pivot" and request_data.new_message:
        # The new message will be processed in the next request
        session["pending_message"] = request_data.new_message

    return ChatInterruptResponse(
        acknowledged=True,
        will_resume=request_data.action == "stop",
        partial_response=partial,
    )


def _validate_approval_state(session: dict[str, Any]) -> BabyMARSState:
    """Validate session state for approval and return state or raise HTTPException."""
    state = session.get("state")
    if not state:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "NO_ACTIVE_STATE",
                    "message": "No conversation state found",
                    "severity": "warning",
                }
            },
        )
    if state.get("supervision_mode") != "action_proposal":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "NO_PENDING_APPROVAL",
                    "message": "No action waiting for approval",
                    "severity": "info",
                }
            },
        )
    return cast(BabyMARSState, state)


def _add_feedback_note(state: BabyMARSState, feedback: str, approved: bool) -> None:
    """Add approval feedback as a note to state."""
    import uuid

    state["notes"].append(
        {
            "note_id": f"approval_feedback_{uuid.uuid4().hex[:8]}",
            "content": feedback,
            "created_at": datetime.now().isoformat(),
            "ttl_hours": 24,
            "priority": 0.8,
            "source": "user",
            "context": {"approval": approved},
        }
    )


@router.post("/approve", response_model=MessageResponse)
async def approve_action(request_data: ApprovalRequest, request: Request) -> MessageResponse:
    """Approve or reject a proposed action."""
    session = get_session(request, request_data.session_id)
    state = _validate_approval_state(session)

    try:
        state["approval_status"] = "approved" if request_data.approved else "rejected"
        if request_data.feedback:
            _add_feedback_note(state, request_data.feedback, request_data.approved)

        config = cast(RunnableConfig, {"configurable": {"thread_id": state["thread_id"]}})
        result = await invoke_cognitive_loop(
            state=state, graph=request.app.state.graph, config=config
        )
        session["state"] = result

        logger.info(
            f"Approval processed: session={request_data.session_id}, approved={request_data.approved}"
        )

        return MessageResponse(
            session_id=request_data.session_id,
            response=str(result.get("final_response", "")),
            supervision_mode=result.get("supervision_mode") or "guidance_seeking",
            belief_strength=result.get("belief_strength_for_action") or 0.0,
            approval_needed=False,
            approval_summary=None,
            references=[],
            context_budget=None,
        )
    except Exception as e:
        logger.error(f"Approval processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=_build_error_detail(
                "APPROVAL_FAILED", "Failed to process approval", retryable=True
            ),
        )
