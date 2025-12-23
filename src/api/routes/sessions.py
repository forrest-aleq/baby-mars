"""
Sessions Routes
===============

Session management endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ...observability import get_logger

logger = get_logger("baby_mars.api.sessions")

router = APIRouter()


@router.get("/{session_id}")
async def get_session(session_id: str, request: Request) -> dict[str, Any]:
    """Get session information"""
    session = request.app.state.sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found or expired",
                    "severity": "warning",
                    "recoverable": True,
                    "actions": [
                        {"label": "Start new session", "action": "new_session"},
                    ],
                }
            },
        )

    state = session.get("state")
    birth = session.get("birth_result", {})

    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "message_count": session["message_count"],
        "org_id": birth.get("org", {}).get("org_id"),
        "org_name": birth.get("org", {}).get("name"),
        "person_id": birth.get("person", {}).get("person_id"),
        "person_name": birth.get("person", {}).get("name"),
        "supervision_mode": state.get("supervision_mode") if state else None,
        "active_context_pills": len(session.get("context_pills", [])),
        "has_pending_approval": state.get("supervision_mode") == "action_proposal"
        if state
        else False,
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str, request: Request) -> dict[str, str]:
    """Delete a session"""
    # Use atomic pop to avoid race condition between check and delete
    session = request.app.state.sessions.pop(session_id, None)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                    "severity": "info",
                }
            },
        )

    logger.info(f"Session deleted: {session_id}")

    return {"status": "deleted", "session_id": session_id}


@router.get("/{session_id}/context")
async def get_session_context(session_id: str, request: Request) -> dict[str, Any]:
    """
    Get current context pills and budget.

    Shows what's currently in Aleq's working memory.
    """
    session = request.app.state.sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                    "severity": "warning",
                }
            },
        )

    pills = session.get("context_pills", [])

    # Calculate rough token budget (placeholder)
    estimated_tokens = len(pills) * 500  # Rough estimate per item

    return {
        "session_id": session_id,
        "context_pills": pills,
        "budget": {
            "items": len(pills),
            "max_items": 10,
            "estimated_tokens": estimated_tokens,
            "max_tokens": 8000,
        },
    }


@router.get("/{session_id}/history")
async def get_session_history(session_id: str, request: Request, limit: int = 20) -> dict[str, Any]:
    """
    Get conversation history for session.

    Per API_CONTRACT_V0.md section 1.4, history has relevance decay:
    - Last 24h: Full context
    - Last 7d: Summarized
    - Last 30d: Key decisions only
    """
    session = request.app.state.sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                    "severity": "warning",
                }
            },
        )

    state = session.get("state")
    if not state:
        return {"session_id": session_id, "messages": []}

    messages = state.get("messages", [])

    # Return most recent messages (full history management in Phase 2)
    return {
        "session_id": session_id,
        "messages": messages[-limit:],
        "total": len(messages),
        "has_more": len(messages) > limit,
    }
