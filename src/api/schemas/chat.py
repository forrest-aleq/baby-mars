"""
Chat Schemas
============

Request/response models for chat endpoints.
Per API_CONTRACT_V0.md sections 1.1-1.4
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ContextPill(BaseModel):
    """
    Reference to an object to include in context.
    Per API_CONTRACT_V0.md section 1.2

    Budget: 10 items OR ~8K tokens, whichever hits first.
    """

    type: Literal["widget", "invoice", "customer", "task", "belief", "decision"]
    id: str


class Reference(BaseModel):
    """
    Backend-declared semantic reference for frontend highlighting.
    Per API_CONTRACT_V0.md section 1.3

    Intensity levels:
    - mention: Referenced in passing (subtle highlight, 2 sec)
    - focus: Talking about it (clear highlight, holds)
    - critical: Key thing (strong highlight, pulses, holds)
    """

    type: Literal["widget", "invoice", "customer", "task", "belief", "decision"]
    id: str
    intensity: Literal["mention", "focus", "critical"]


class MessageRequest(BaseModel):
    """Request to send a chat message"""

    session_id: str = Field(..., description="Session from /birth")
    message: str = Field(..., description="User's message")
    context_pills: list[ContextPill] = Field(
        default_factory=list, description="Objects to include in context"
    )
    stream: bool = Field(False, description="Stream response via SSE")


class MessageResponse(BaseModel):
    """Response from chat"""

    session_id: str
    response: str = Field(..., description="Aleq's response text")
    supervision_mode: Literal["guidance_seeking", "action_proposal", "autonomous"]
    belief_strength: float = Field(..., ge=0, le=1)
    approval_needed: bool = Field(False)
    approval_summary: Optional[str] = Field(
        None, description="Summary of proposed action if approval_needed"
    )
    references: list[Reference] = Field(
        default_factory=list, description="Objects referenced in response for highlighting"
    )
    context_budget: Optional[dict] = Field(
        None,
        description="Current context usage: {items: int, tokens: int, max_items: int, max_tokens: int}",
    )


class ChatInterruptRequest(BaseModel):
    """
    Request to interrupt current stream.
    Per API_CONTRACT_V0.md section 1.1
    """

    session_id: str
    action: Literal["stop", "pivot"] = Field(
        ..., description="stop: halt response, pivot: switch to new message"
    )
    new_message: Optional[str] = Field(None, description="New message if action=pivot")


class ChatInterruptResponse(BaseModel):
    """Response to interrupt request"""

    acknowledged: bool
    will_resume: bool = Field(
        False, description="True if context preserved and 'continue' will work"
    )
    partial_response: Optional[str] = Field(
        None, description="What was generated before interruption"
    )


class ApprovalRequest(BaseModel):
    """Request to approve/reject a proposed action"""

    session_id: str
    approved: bool
    feedback: Optional[str] = Field(None, description="Optional feedback for learning")
