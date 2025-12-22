"""
Decision Schemas
================

Request/response models for decision lifecycle.
Per API_CONTRACT_V0.md section 3
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


DecisionStatus = Literal[
    "pending",              # Awaiting user action
    "staged",               # Approved, in soft-commit window
    "committed",            # Finalized
    "undone",               # Rolled back during window
    "rejected",             # User rejected
    "expired",              # Never decided (past escalation)
]

DecisionType = Literal[
    "soft",     # Can be undone within 30 seconds
    "hard",     # Requires explicit confirmation, no undo
]


class BeliefSnapshot(BaseModel):
    """Snapshot of belief at decision time"""
    belief_id: str
    statement: str
    strength: float
    version: int


class DecisionDetail(BaseModel):
    """Full decision detail"""
    decision_id: str
    type: str = Field(..., description="Domain type: payment, categorization, close, etc.")
    decision_type: DecisionType = Field(..., description="soft or hard")

    summary: str = Field(..., description="Human-readable summary")
    description: Optional[str] = None

    status: DecisionStatus
    confidence: float = Field(..., ge=0, le=1, description="Aleq's confidence")

    # Context
    task_id: Optional[str] = None

    # What Aleq based this on
    belief_snapshots: list[BeliefSnapshot] = Field(
        default_factory=list,
        description="Beliefs as they were when decision was created"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Aleq's reasoning for this recommendation"
    )

    # Options
    options: list[str] = Field(
        default_factory=lambda: ["approve", "reject"],
        description="Available choices"
    )

    # Execution info
    executed_at: Optional[str] = None
    executed_by: Optional[str] = None
    result: Optional[dict] = None

    # Undo window (for soft decisions)
    undo_available: bool = False
    undo_expires_at: Optional[str] = None

    # Timestamps
    created_at: str
    updated_at: str


class DecisionExecuteRequest(BaseModel):
    """Request to execute a decision"""
    choice: str = Field("approve", description="The option chosen")
    idempotency_key: Optional[str] = Field(
        None,
        description="Client-provided key for deduplication"
    )
    feedback: Optional[str] = Field(
        None,
        description="Optional feedback for learning"
    )


class DecisionExecuteResponse(BaseModel):
    """Response from decision execution"""
    decision_id: str
    executed: bool
    was_replay: bool = Field(
        False,
        description="True if this was a duplicate request"
    )
    status: DecisionStatus

    # For soft decisions
    undo_available: bool = False
    undo_expires_at: Optional[str] = None

    # Result
    result: Optional[dict] = None
    message: Optional[str] = None


class DecisionUndoResponse(BaseModel):
    """Response from undo attempt"""
    decision_id: str
    undone: bool
    message: str

    # If undo failed
    reason: Optional[str] = None


class DecisionAlreadyDecided(BaseModel):
    """Response when someone else already decided"""
    decision_id: str
    already_decided: bool = True
    decided_by: str
    decided_at: str
    result: Optional[dict] = None
