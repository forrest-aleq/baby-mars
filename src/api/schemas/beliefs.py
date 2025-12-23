"""
Belief Schemas
==============

Request/response models for belief system.
Per API_CONTRACT_V0.md section 4
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

BeliefCategory = Literal[
    "moral",  # Ethical beliefs (immutable identity)
    "competence",  # How to do things
    "technical",  # Domain-specific facts
    "preference",  # Style choices
    "identity",  # Core identity (immutable)
    "threshold",  # Policy thresholds (special handling)
]

BeliefStatus = Literal[
    "active",  # Current and used
    "superseded",  # Replaced by newer belief
    "invalidated",  # Proven wrong, no replacement
    "disputed",  # User challenged, under review
    "archived",  # No longer relevant
]


class BeliefEvidence(BaseModel):
    """Evidence supporting or challenging a belief"""

    evidence_id: str
    type: Literal["supporting", "challenging"]
    source: str = Field(..., description="Where this came from")
    description: str
    timestamp: str
    weight: float = Field(1.0, ge=0, le=1, description="How much this evidence counts")


class BeliefVersion(BaseModel):
    """Historical version of a belief"""

    version: int
    statement: str
    strength: float
    changed_at: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class BeliefResponse(BaseModel):
    """Basic belief info for lists"""

    belief_id: str
    statement: str
    category: BeliefCategory
    strength: float = Field(..., ge=0, le=1)
    context_key: str = Field("*|*|*", description="Context pattern: client|period|amount")
    status: BeliefStatus = "active"
    is_immutable: bool = False


class BeliefDetailResponse(BaseModel):
    """Full belief detail with history"""

    belief_id: str
    statement: str
    category: BeliefCategory
    strength: float
    context_key: str
    status: BeliefStatus

    # Mutability
    is_immutable: bool = False
    requires_role: Optional[str] = Field(
        None, description="Role required to modify (for thresholds)"
    )

    # History
    versions: list[BeliefVersion] = Field(default_factory=list)
    current_version: int = 1

    # Evidence
    evidence: list[BeliefEvidence] = Field(default_factory=list)

    # Relationships
    supports: list[str] = Field(default_factory=list, description="Belief IDs this supports")
    supported_by: list[str] = Field(
        default_factory=list, description="Belief IDs that support this"
    )

    # Metadata
    source: str = Field(..., description="Origin: system, user, inferred, etc.")
    created_at: str
    updated_at: str

    # Challenge info (if disputed)
    challenge_count: int = 0
    active_challenge: Optional[str] = None


class BeliefChallengeRequest(BaseModel):
    """
    Request to challenge a belief.
    Per API_CONTRACT_V0.md section 4.1

    Users cannot directly edit beliefs. They challenge.
    """

    reason: str = Field(..., min_length=10, description="Why this belief seems wrong")
    evidence: Optional[str] = Field(None, description="Supporting evidence for the challenge")


class BeliefChallengeResponse(BaseModel):
    """Response from belief challenge"""

    challenge_id: str
    belief_id: str

    # Result
    accepted: bool = Field(..., description="Whether the challenge was accepted for review")
    belief_updated: bool = Field(False, description="Whether the belief strength changed")

    # New state
    new_strength: Optional[float] = Field(None, description="Belief's new strength if updated")
    new_status: Optional[BeliefStatus] = Field(None, description="Belief's new status if changed")

    # Evidence shown
    existing_evidence: list[BeliefEvidence] = Field(
        default_factory=list, description="Evidence that was shown to user"
    )

    message: str = Field(..., description="Explanation of what happened")


class ThresholdResponse(BaseModel):
    """Threshold belief (special type)"""

    belief_id: str
    name: str = Field(..., description="Threshold name: cross_entity_limit, etc.")
    value: float
    unit: Optional[str] = Field(None, description="Unit: USD, days, etc.")

    # Policy
    requires_role: str = Field("controller", description="Who can change")
    effective_from: str

    # Audit
    last_changed_by: Optional[str] = None
    last_changed_at: Optional[str] = None
    change_reason: Optional[str] = None
