"""
Pydantic Models for Claude Structured Outputs
===============================================

Defines response schemas for Claude's structured output feature.
Used by cognitive loop nodes for reliable JSON responses.
"""

from typing import Any, Optional

from pydantic import BaseModel


class AppraisalOutput(BaseModel):
    """Structured output for appraisal node"""

    face_threat_level: float  # 0.0-1.0
    expectancy_violation: Optional[str]
    goal_alignment: dict[str, float]  # goal_id -> alignment score
    urgency: float  # 0.0-1.0
    uncertainty_areas: list[str]
    recommended_approach: str  # "seek_guidance", "propose_action", "execute"
    relevant_belief_ids: list[str]
    difficulty_assessment: int  # 1-5
    involves_ethical_beliefs: bool
    reasoning: str


class ActionSelectionOutput(BaseModel):
    """Structured output for action selection node"""

    action_type: str
    work_units: list[dict[str, Any]]
    tool_requirements: list[str]
    confidence: float
    requires_human_approval: bool
    approval_reason: Optional[str]
    estimated_difficulty: int


class ValidationOutput(BaseModel):
    """Structured output for validation node"""

    all_passed: bool
    results: list[dict[str, Any]]  # ValidationResult items
    recommended_action: str  # "proceed", "retry", "escalate"
    fix_suggestions: list[str]


class ResponseOutput(BaseModel):
    """Structured output for response generation"""

    main_content: str
    tone: str  # "professional", "explanatory", "apologetic", etc.
    action_items: list[str] = []
    questions: list[str] = []  # For guidance_seeking mode
    confirmation_prompt: Optional[str] = None  # For action_proposal mode
    awaiting_input: bool = False


class DialecticalOutput(BaseModel):
    """Structured output for dialectical resolution"""

    synthesis: str
    chosen_goal_id: str
    deferred_goal_ids: list[str]
    resolution_reasoning: str
    requires_human_input: bool


class EntityExtractionOutput(BaseModel):
    """Structured output for entity extraction from messages (Phase 2)"""

    client_name: Optional[str] = None  # Customer/client name if mentioned
    invoice_ids: list[str] = []  # Invoice or payment IDs
    amounts: list[float] = []  # Dollar amounts mentioned
    period: Optional[str] = None  # "month-end", "quarter-end", "year-end", or None
    action_type: Optional[str] = None  # "payment", "invoice", "lockbox", etc.
    urgency: str = "normal"  # "urgent", "normal", "low"
