"""
Chat Routes
===========

Chat endpoints with streaming, interruption, and context pills.
Per API_CONTRACT_V0.md sections 1.1-1.4
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, AsyncIterator, cast

from fastapi import APIRouter, HTTPException, Request
from langchain_core.runnables import RunnableConfig
from sse_starlette.sse import EventSourceResponse

from ...birth.birth_system import create_initial_state
from ...cognitive_loop.graph import invoke_cognitive_loop, stream_cognitive_loop
from ...observability import get_logger
from ...state.constants import APPROVAL_TIMEOUT_SECONDS
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
        # Primitive 1 (thread.create) or 2 (thread.load)
        thread_id = session.get("thread_id")  # None for new, existing for resume
        new_state = create_initial_state(birth_result, message, thread_id=thread_id)
        session["state"] = new_state
        # Store thread_id in session for future turns
        if not thread_id:
            session["thread_id"] = new_state["thread_id"]
    else:
        session["state"]["messages"].append({"role": "user", "content": message})
        # Handle both turn_number and current_turn for backwards compatibility
        if "turn_number" in session["state"]:
            session["state"]["turn_number"] += 1
        if "current_turn" in session["state"]:
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


def _build_message_response(
    session_id: str, result: BabyMARSState, session: dict[str, Any]
) -> MessageResponse:
    """Build MessageResponse from cognitive loop result."""
    supervision_mode = result.get("supervision_mode") or "guidance_seeking"
    belief_strength = result.get("belief_strength_for_action") or 0.0
    approval_needed = supervision_mode == "action_proposal"

    # Store approval timeout if action proposal is pending
    if approval_needed:
        session["approval_timeout_at"] = time.time() + APPROVAL_TIMEOUT_SECONDS
    else:
        session.pop("approval_timeout_at", None)

    # Get thread_id for forever conversations
    thread_id = result.get("thread_id") or session.get("thread_id", "unknown")

    logger.info(
        f"Message processed: session={session_id}, thread={thread_id}, mode={supervision_mode}"
    )

    return MessageResponse(
        session_id=session_id,
        thread_id=thread_id,
        response=str(result.get("final_response", "")),
        supervision_mode=supervision_mode,
        belief_strength=belief_strength,
        approval_needed=approval_needed,
        approval_summary=result.get("approval_summary") if approval_needed else None,
        references=_extract_references(result),
        context_budget=None,
    )


@router.post("", response_model=MessageResponse)
async def send_message(request_data: MessageRequest, request: Request) -> MessageResponse:
    """Send a message and run the full cognitive loop."""
    session = get_session(request, request_data.session_id)
    pending_message = session.pop("pending_message", None)
    if pending_message:
        request_data.message = f"{pending_message}\n\n{request_data.message}"

    try:
        # Forever conversations: if thread_id provided, use it for checkpoint resume
        resume_thread_id = request_data.thread_id
        if resume_thread_id:
            # Resume from checkpoint: only pass the new message, let LangGraph load the rest
            session["thread_id"] = resume_thread_id
            logger.info(f"Resuming conversation from thread_id={resume_thread_id}")
            # Minimal state - just the new message. LangGraph will merge with checkpoint.
            state = cast(
                BabyMARSState,
                {
                    "thread_id": resume_thread_id,
                    "messages": [{"role": "user", "content": request_data.message}],
                },
            )
        else:
            # New conversation: create full initial state
            state = _update_session_state(session, request_data.message, session["birth_result"])

        if request_data.context_pills:
            session["context_pills"] = [
                {"type": p.type, "id": p.id} for p in request_data.context_pills
            ]

        thread_id = resume_thread_id or state["thread_id"]
        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
        result = await invoke_cognitive_loop(
            state=state, graph=request.app.state.graph, config=config
        )
        session["state"] = result
        return _build_message_response(request_data.session_id, result, session)

    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        logger.error(f"Message processing failed: {e!r}\n{tb}")
        raise HTTPException(
            status_code=500,
            detail=_build_error_detail(
                "PROCESSING_FAILED", f"Failed to process message: {e!r}", retryable=True
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


def _build_complete_event(state: BabyMARSState, thread_id: str) -> dict[str, str]:
    """Build the 'complete' SSE event."""
    return {
        "event": "complete",
        "data": json.dumps(
            {
                "thread_id": state.get("thread_id", thread_id),
                "response": state.get("final_response", ""),
                "supervision_mode": state.get("supervision_mode", ""),
                "belief_strength": state.get("belief_strength_for_action", 0.0),
                "approval_needed": state.get("supervision_mode") == "action_proposal",
            }
        ),
    }


@router.post("/stream")
async def send_message_stream(
    request_data: MessageRequest, request: Request
) -> EventSourceResponse:
    """Send a message and stream the response via SSE."""
    session = get_session(request, request_data.session_id)
    session["interrupt_event"] = asyncio.Event()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        try:
            resume_thread_id = request_data.thread_id
            if resume_thread_id:
                session["thread_id"] = resume_thread_id
                logger.info(f"Resuming stream from thread_id={resume_thread_id}")

            state = _update_session_state(session, request_data.message, session["birth_result"])
            thread_id = resume_thread_id or state["thread_id"]
            config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

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

            yield _build_complete_event(state, thread_id)
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


def _check_approval_timeout(session: dict[str, Any]) -> None:
    """Check if approval has timed out and raise HTTPException if so."""
    timeout_at = session.get("approval_timeout_at")
    if timeout_at and time.time() > timeout_at:
        # Clear the timeout to prevent repeated errors
        session.pop("approval_timeout_at", None)
        raise HTTPException(
            status_code=408,
            detail={
                "error": {
                    "code": "APPROVAL_TIMEOUT",
                    "message": "Approval request has expired. Please send a new message.",
                    "severity": "warning",
                    "recoverable": True,
                    "timeout_seconds": APPROVAL_TIMEOUT_SECONDS,
                }
            },
        )


def _validate_approval_state(session: dict[str, Any]) -> BabyMARSState:
    """Validate session state for approval and return state or raise HTTPException."""
    # Check timeout first
    _check_approval_timeout(session)

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
        # Clear approval timeout since user responded
        session.pop("approval_timeout_at", None)

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
            thread_id=result.get("thread_id") or state["thread_id"],
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
