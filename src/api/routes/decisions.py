"""
Decisions Routes
================

Decision lifecycle with idempotency and undo.
Per API_CONTRACT_V0.md section 3
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from ..schemas.decisions import (
    BeliefSnapshot,
    DecisionDetail,
    DecisionExecuteRequest,
    DecisionExecuteResponse,
    DecisionUndoResponse,
)

logger = logging.getLogger("baby_mars.api.decisions")

router = APIRouter()

# In-memory decision store (will be moved to persistence layer)
# Structure: {decision_id: DecisionDetail}
_decisions: dict[str, dict[str, Any]] = {}

# Idempotency tracking: {idempotency_key: (decision_id, created_at)}
# Keys are cleaned up after 24 hours
_idempotency_keys: dict[str, tuple[str, datetime]] = {}
IDEMPOTENCY_TTL_HOURS = 24

# Soft commit window in seconds
UNDO_WINDOW_SECONDS = 30


def _cleanup_expired_idempotency_keys() -> None:
    """Remove idempotency keys older than 24 hours."""
    cutoff = datetime.now() - timedelta(hours=IDEMPOTENCY_TTL_HOURS)
    expired = [k for k, (_, ts) in _idempotency_keys.items() if ts < cutoff]
    for key in expired:
        del _idempotency_keys[key]
    if expired:
        logger.debug(f"Cleaned up {len(expired)} expired idempotency keys")


def _get_decision_or_404(decision_id: str) -> dict[str, Any]:
    """Get decision or raise 404"""
    decision = _decisions.get(decision_id)
    if not decision:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "DECISION_NOT_FOUND",
                    "message": f"Decision {decision_id} not found",
                    "severity": "warning",
                }
            },
        )
    return decision


@router.get("/{decision_id}", response_model=DecisionDetail)
async def get_decision(decision_id: str) -> DecisionDetail:
    """
    Get decision detail with belief snapshot.

    Shows the beliefs AS THEY WERE when decision was created,
    per API_CONTRACT_V0.md section 4.3.
    """
    decision = _get_decision_or_404(decision_id)

    # Check if undo still available
    undo_available = False
    undo_expires_at = None

    if decision["status"] == "staged":
        expires = datetime.fromisoformat(decision["undo_expires_at"])
        if datetime.now() < expires:
            undo_available = True
            undo_expires_at = decision["undo_expires_at"]
        else:
            # Window expired, commit the decision
            decision["status"] = "committed"
            decision["updated_at"] = datetime.now().isoformat()

    return DecisionDetail(
        decision_id=decision["decision_id"],
        type=decision["type"],
        decision_type=decision["decision_type"],
        summary=decision["summary"],
        description=decision.get("description"),
        status=decision["status"],
        confidence=decision["confidence"],
        task_id=decision.get("task_id"),
        belief_snapshots=[BeliefSnapshot(**b) for b in decision.get("belief_snapshots", [])],
        reasoning=decision.get("reasoning"),
        options=decision.get("options", ["approve", "reject"]),
        executed_at=decision.get("executed_at"),
        executed_by=decision.get("executed_by"),
        result=decision.get("result"),
        undo_available=undo_available,
        undo_expires_at=undo_expires_at,
        created_at=decision["created_at"],
        updated_at=decision["updated_at"],
    )


@router.post("/{decision_id}/execute", response_model=DecisionExecuteResponse)
async def execute_decision(
    decision_id: str,
    request: DecisionExecuteRequest,
) -> DecisionExecuteResponse:
    """
    Execute a decision with idempotency.

    Per API_CONTRACT_V0.md section 3.1:
    - First request executes, returns was_replay=false
    - Subsequent requests return was_replay=true with same result
    - Decision ID tracked for 24 hours

    For soft decisions:
    - Stages the change (doesn't commit immediately)
    - 30-second undo window
    - Commits automatically after window
    """
    decision = _get_decision_or_404(decision_id)

    # Cleanup expired keys on each request
    _cleanup_expired_idempotency_keys()

    # Check idempotency
    if request.idempotency_key:
        existing_entry = _idempotency_keys.get(request.idempotency_key)
        if existing_entry:
            existing_decision_id, _ = existing_entry
            existing = _decisions.get(existing_decision_id)
            if existing:
                return DecisionExecuteResponse(
                    decision_id=existing_decision_id,
                    executed=True,
                    was_replay=True,
                    status=existing["status"],
                    undo_available=existing["status"] == "staged",
                    undo_expires_at=existing.get("undo_expires_at"),
                    result=existing.get("result"),
                    message="Duplicate request - returning previous result",
                )

    # Check if already decided
    if decision["status"] not in ("pending",):
        # Someone else already decided
        return DecisionExecuteResponse(
            decision_id=decision_id,
            executed=True,
            was_replay=True,
            status=decision["status"],
            result=decision.get("result"),
            message=f"Already {decision['status']} by {decision.get('executed_by', 'unknown')}",
        )

    # Validate choice
    if request.choice not in decision.get("options", ["approve", "reject"]):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_CHOICE",
                    "message": f"Invalid choice. Options: {decision['options']}",
                    "severity": "warning",
                }
            },
        )

    now = datetime.now()

    # Track idempotency with timestamp for TTL
    if request.idempotency_key:
        _idempotency_keys[request.idempotency_key] = (decision_id, datetime.now())

    # Handle rejection
    if request.choice == "reject":
        decision["status"] = "rejected"
        decision["executed_at"] = now.isoformat()
        decision["executed_by"] = "user"  # TODO: Get from auth
        decision["updated_at"] = now.isoformat()

        logger.info(f"Decision rejected: {decision_id}")

        return DecisionExecuteResponse(
            decision_id=decision_id,
            executed=True,
            was_replay=False,
            status="rejected",
            message="Decision rejected",
        )

    # Handle approval
    if decision["decision_type"] == "soft":
        # Soft decision: stage with undo window
        decision["status"] = "staged"
        decision["executed_at"] = now.isoformat()
        decision["executed_by"] = "user"
        decision["undo_expires_at"] = (now + timedelta(seconds=UNDO_WINDOW_SECONDS)).isoformat()
        decision["updated_at"] = now.isoformat()

        # TODO: Stage the actual change (don't commit to ERPNext yet)
        decision["result"] = {"staged": True, "action": request.choice}

        logger.info(f"Decision staged: {decision_id} (undo window: {UNDO_WINDOW_SECONDS}s)")

        # Schedule auto-commit after window
        asyncio.create_task(_auto_commit_decision(decision_id, UNDO_WINDOW_SECONDS))

        return DecisionExecuteResponse(
            decision_id=decision_id,
            executed=True,
            was_replay=False,
            status="staged",
            undo_available=True,
            undo_expires_at=decision["undo_expires_at"],
            result=decision["result"],
            message=f"Approved. You can undo within {UNDO_WINDOW_SECONDS} seconds.",
        )

    else:
        # Hard decision: commit immediately
        decision["status"] = "committed"
        decision["executed_at"] = now.isoformat()
        decision["executed_by"] = "user"
        decision["updated_at"] = now.isoformat()

        # TODO: Execute the actual change in ERPNext
        decision["result"] = {"committed": True, "action": request.choice}

        logger.info(f"Decision committed: {decision_id}")

        return DecisionExecuteResponse(
            decision_id=decision_id,
            executed=True,
            was_replay=False,
            status="committed",
            undo_available=False,
            result=decision["result"],
            message="Approved and executed.",
        )


async def _auto_commit_decision(decision_id: str, delay_seconds: int) -> None:
    """Auto-commit a staged decision after undo window expires."""
    try:
        await asyncio.sleep(delay_seconds)

        decision = _decisions.get(decision_id)
        if not decision:
            return

        # Only commit if still staged
        if decision["status"] == "staged":
            decision["status"] = "committed"
            decision["updated_at"] = datetime.now().isoformat()

            # TODO: Actually commit to ERPNext
            if decision.get("result") and isinstance(decision["result"], dict):
                decision["result"]["committed"] = True

            logger.info(f"Decision auto-committed: {decision_id}")
    except Exception as e:
        logger.error(f"Auto-commit failed for {decision_id}: {e}", exc_info=True)


@router.post("/{decision_id}/undo", response_model=DecisionUndoResponse)
async def undo_decision(decision_id: str) -> DecisionUndoResponse:
    """
    Undo a staged decision within the 30-second window.

    Per API_CONTRACT_V0.md section 3.2:
    - Only soft decisions can be undone
    - Must be within undo window
    - Rollback leaves no trace in books
    """
    decision = _get_decision_or_404(decision_id)

    # Check if undoable
    if decision["status"] != "staged":
        return DecisionUndoResponse(
            decision_id=decision_id,
            undone=False,
            message="Cannot undo - decision is not in staged state",
            reason=f"Current status: {decision['status']}",
        )

    # Check window
    expires = datetime.fromisoformat(decision["undo_expires_at"])
    if datetime.now() >= expires:
        # Window expired, auto-commit happened
        decision["status"] = "committed"
        decision["updated_at"] = datetime.now().isoformat()

        return DecisionUndoResponse(
            decision_id=decision_id,
            undone=False,
            message="Undo window expired - decision has been committed",
            reason="WINDOW_EXPIRED",
        )

    # Undo the decision
    decision["status"] = "undone"
    decision["updated_at"] = datetime.now().isoformat()

    # TODO: Rollback any staged changes

    logger.info(f"Decision undone: {decision_id}")

    return DecisionUndoResponse(
        decision_id=decision_id,
        undone=True,
        message="Decision undone. No changes were made.",
    )


# Internal function for creating decisions (called from action_proposal node)
def create_decision(
    decision_type: str,
    summary: str,
    confidence: float,
    is_soft: bool = True,
    task_id: Optional[str] = None,
    belief_snapshots: Optional[list[dict[str, Any]]] = None,
    reasoning: Optional[str] = None,
    options: Optional[list[str]] = None,
) -> str:
    """
    Create a new decision. Returns decision_id.

    Called from action_proposal node when supervision_mode == "action_proposal".
    """
    decision_id = f"decision_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    decision = {
        "decision_id": decision_id,
        "type": decision_type,
        "decision_type": "soft" if is_soft else "hard",
        "summary": summary,
        "status": "pending",
        "confidence": confidence,
        "task_id": task_id,
        "belief_snapshots": belief_snapshots or [],
        "reasoning": reasoning,
        "options": options or ["approve", "reject"],
        "created_at": now,
        "updated_at": now,
    }

    _decisions[decision_id] = decision

    logger.info(f"Decision created: {decision_id} ({decision_type})")

    return decision_id
