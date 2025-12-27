"""
Main State Object
==================

BabyMARSState - the complete cognitive state for Baby MARS.
Implements all 20 research papers in a single state object
that LangGraph can checkpoint and persist.
"""

from operator import add
from typing import Annotated, Any, Literal, Optional, TypedDict

from .reducers import note_reducer, task_reducer
from .types import (
    ActiveTask,
    AppraisalResult,
    BeliefState,
    BeliefStrengthEvent,
    Note,
    Objects,
    PersonObject,
    SelectedAction,
    ValidationResult,
)


class BabyMARSState(TypedDict):
    """
    Complete cognitive state for Baby MARS.

    Implements all 20 research papers in a single state object
    that LangGraph can checkpoint and persist.
    """

    # ---- Identity ----
    thread_id: str
    org_id: str
    org_timezone: str  # IANA timezone for the org (e.g., "America/Los_Angeles")
    user_id: str

    # ---- Three-Column Working Memory (Paper #8) ----
    active_tasks: Annotated[list[ActiveTask], task_reducer]
    notes: Annotated[list[Note], note_reducer]
    objects: Objects

    # ---- Conversation ----
    messages: Annotated[list[dict[str, Any]], add]  # LangGraph message format
    current_turn: int

    # ---- Cognitive Loop State ----
    current_context_key: str
    activated_beliefs: list[BeliefState]
    appraisal: Optional[AppraisalResult]
    selected_action: Optional[SelectedAction]

    # ---- Autonomy (Paper #1) ----
    supervision_mode: Optional[Literal["guidance_seeking", "action_proposal", "autonomous"]]
    belief_strength_for_action: Optional[float]

    # ---- HITL Approval ----
    approval_status: Optional[Literal["pending", "approved", "rejected", "no_action"]]
    approval_summary: Optional[str]

    # ---- Goal State ----
    active_goals: list[dict[str, Any]]
    goal_conflict_detected: bool

    # ---- Social Context (Paper #17) ----
    current_person: Optional[PersonObject]
    authority_context: dict[str, Any]

    # ---- Execution Results ----
    execution_results: list[dict[str, Any]]

    # ---- Validation (Paper #3) ----
    validation_results: list[ValidationResult]
    retry_count: int
    max_retries: int

    # ---- Event Log (Paper #7) ----
    events: Annotated[list[BeliefStrengthEvent], add]

    # ---- SYSTEM_PULSE Trigger Context ----
    trigger_context: Optional[dict[str, Any]]

    # ---- Rapport Context (Relationship Memory) ----
    rapport_context: Optional[dict[str, Any]]

    # ---- Final Response ----
    final_response: Optional[str]
