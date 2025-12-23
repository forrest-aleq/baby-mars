"""
Chat Routes
===========

Chat endpoints with streaming, interruption, and context pills.
Per API_CONTRACT_V0.md sections 1.1-1.4
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, cast

from fastapi import APIRouter, HTTPException, Request
from langchain_core.runnables import RunnableConfig
from sse_starlette.sse import EventSourceResponse

from ...birth.birth_system import create_initial_state
from ...cognitive_loop.graph import invoke_cognitive_loop, stream_cognitive_loop
from ..schemas.chat import (
    ApprovalRequest,
    ChatInterruptRequest,
    ChatInterruptResponse,
    MessageRequest,
    MessageResponse,
    Reference,
)

logger = logging.getLogger("baby_mars.api.chat")

router = APIRouter()


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
    """
    Send a message and get a response.

    Runs the full cognitive loop:
    1. Cognitive Activation (load beliefs, context)
    2. Appraisal (analyze situation)
    3. Action Selection (determine autonomy)
    4. Execution (if autonomous)
    5. Verification
    6. Feedback (update beliefs)
    7. Response Generation
    8. Personality Gate (validate against immutable beliefs)

    If stream=true, use /chat/stream instead for SSE.
    """
    session = get_session(request, request_data.session_id)

    # Check for pending message from pivot interrupt
    pending_message = session.pop("pending_message", None)
    if pending_message:
        # Merge pending message with current request
        request_data.message = f"{pending_message}\n\n{request_data.message}"

    try:
        # Create or update state
        if session["state"] is None:
            session["state"] = create_initial_state(session["birth_result"], request_data.message)
        else:
            session["state"]["messages"].append({"role": "user", "content": request_data.message})
            session["state"]["current_turn"] += 1

        session["message_count"] += 1

        # Store context pills in state
        if request_data.context_pills:
            session["context_pills"] = [
                {"type": p.type, "id": p.id} for p in request_data.context_pills
            ]
            # TODO: Resolve pills to actual data and add to state

        # Run cognitive loop
        config = cast(
            RunnableConfig, {"configurable": {"thread_id": session["state"]["thread_id"]}}
        )

        result = await invoke_cognitive_loop(
            state=session["state"],
            graph=request.app.state.graph,
            config=config,
        )

        # Update session
        session["state"] = result

        # Extract response
        final_response = str(result.get("final_response", ""))
        supervision_mode = result.get("supervision_mode") or "guidance_seeking"
        belief_strength = result.get("belief_strength_for_action") or 0.0

        # Check for approval
        approval_needed = supervision_mode == "action_proposal"
        approval_summary = result.get("approval_summary") if approval_needed else None

        # Extract references for highlighting (referenced_objects may not exist in state)
        references: list[Reference] = []
        referenced_objs: list[dict[str, Any]] = result.get("referenced_objects") or []  # type: ignore[assignment]
        for ref in referenced_objs:
            references.append(
                Reference(
                    type=ref.get("type", "widget"),
                    id=ref.get("id", ""),
                    intensity=ref.get("intensity", "mention"),
                )
            )

        logger.info(
            f"Message processed: session={request_data.session_id}, "
            f"mode={supervision_mode}, strength={belief_strength:.2f}"
        )

        return MessageResponse(
            session_id=request_data.session_id,
            response=final_response,
            supervision_mode=supervision_mode,
            belief_strength=belief_strength,
            approval_needed=approval_needed,
            approval_summary=approval_summary,
            references=references,
            context_budget=None,
        )

    except Exception as e:
        logger.error(f"Message processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "PROCESSING_FAILED",
                    "message": f"Failed to process message: {str(e)}",
                    "severity": "error",
                    "recoverable": True,
                    "retryable": True,
                    "retry": {"after_seconds": 2, "max_attempts": 3, "strategy": "exponential"},
                    "actions": [
                        {"label": "Try again", "action": "retry"},
                    ],
                }
            },
        )


@router.post("/stream")
async def send_message_stream(
    request_data: MessageRequest, request: Request
) -> EventSourceResponse:
    """
    Send a message and stream the response via SSE.

    Events:
    - node_start: {node: "name"} - Node execution started
    - node_end: {node: "name", supervision_mode: "..."} - Node completed
    - token: {text: "..."} - Response token
    - complete: {response, mode, belief_strength, approval_needed} - Done
    - error: {message: "..."} - Error occurred

    Supports interruption via /chat/interrupt endpoint.
    """
    session = get_session(request, request_data.session_id)

    # Create interrupt event for this stream
    session["interrupt_event"] = asyncio.Event()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        try:
            # Create or update state
            if session["state"] is None:
                session["state"] = create_initial_state(
                    session["birth_result"], request_data.message
                )
            else:
                session["state"]["messages"].append(
                    {"role": "user", "content": request_data.message}
                )
                session["state"]["current_turn"] += 1

            session["message_count"] += 1

            config = cast(
                RunnableConfig, {"configurable": {"thread_id": session["state"]["thread_id"]}}
            )

            # Stream events from cognitive loop
            async for event in stream_cognitive_loop(
                state=session["state"],
                graph=request.app.state.graph,
                config=config,
            ):
                # Check for interruption
                if session["interrupt_event"].is_set():
                    yield {
                        "event": "interrupted",
                        "data": json.dumps(
                            {
                                "partial_response": session["state"].get("final_response", ""),
                                "will_resume": True,
                            }
                        ),
                    }
                    return

                event_type = event.get("event", "")

                if event_type == "on_chain_start":
                    node_name = event.get("name", "unknown")
                    yield {"event": "node_start", "data": json.dumps({"node": node_name})}

                elif event_type == "on_chain_end":
                    node_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", {})

                    if isinstance(output, dict):
                        session["state"].update(output)

                    yield {
                        "event": "node_end",
                        "data": json.dumps(
                            {
                                "node": node_name,
                                "supervision_mode": session["state"].get("supervision_mode"),
                            }
                        ),
                    }

                elif event_type == "on_llm_stream":
                    chunk = event.get("data", {}).get("chunk", "")
                    if chunk:
                        yield {"event": "token", "data": json.dumps({"text": chunk})}

            # Send completion
            yield {
                "event": "complete",
                "data": json.dumps(
                    {
                        "response": session["state"].get("final_response", ""),
                        "supervision_mode": session["state"].get("supervision_mode", ""),
                        "belief_strength": session["state"].get("belief_strength_for_action", 0.0),
                        "approval_needed": session["state"].get("supervision_mode")
                        == "action_proposal",
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
        finally:
            # Clean up interrupt event
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


@router.post("/approve", response_model=MessageResponse)
async def approve_action(request_data: ApprovalRequest, request: Request) -> MessageResponse:
    """
    Approve or reject a proposed action.

    When supervision_mode is "action_proposal", the system pauses
    for explicit human approval before executing.
    """
    session = get_session(request, request_data.session_id)

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

    try:
        # Update approval status
        state["approval_status"] = "approved" if request_data.approved else "rejected"

        # Add feedback as note
        if request_data.feedback:
            import uuid

            state["notes"].append(
                {
                    "note_id": f"approval_feedback_{uuid.uuid4().hex[:8]}",
                    "content": request_data.feedback,
                    "created_at": datetime.now().isoformat(),
                    "ttl_hours": 24,
                    "priority": 0.8,
                    "source": "user",
                    "context": {"approval": request_data.approved},
                }
            )

        # Continue cognitive loop
        config = cast(RunnableConfig, {"configurable": {"thread_id": state["thread_id"]}})

        result = await invoke_cognitive_loop(
            state=state,
            graph=request.app.state.graph,
            config=config,
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
            detail={
                "error": {
                    "code": "APPROVAL_FAILED",
                    "message": "Failed to process approval",
                    "severity": "error",
                    "recoverable": True,
                    "retryable": True,
                }
            },
        )
