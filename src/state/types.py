"""
State Types
============

TypedDicts for Baby MARS state structure.
Implements Three-Column Working Memory (Paper #8) and supporting structures.
"""

from typing import Literal, Optional, TypedDict


# ============================================================
# COLUMN 1: ACTIVE TASKS (3-4 slots)
# Paper #8: Three-Column Working Memory
# ============================================================


class TaskState(TypedDict):
    """Current state of an active task."""

    status: Literal["planning", "executing", "blocked", "awaiting_input", "complete"]
    current_step: Optional[str]
    blocking_reason: Optional[str]
    progress: float  # 0.0-1.0


class ActiveTask(TypedDict):
    """
    An item currently being worked on.
    Limited to 3-4 simultaneous tasks per Paper #8.
    """

    task_id: str
    description: str
    state: TaskState
    dependencies: list[str]
    history: list[dict]  # TaskEvents
    started_at: str  # ISO datetime
    estimated_duration_minutes: Optional[int]
    priority: float  # 0.0-1.0
    difficulty_level: int  # 1-5 per Paper #16


# ============================================================
# COLUMN 2: NOTES (acknowledged queue with TTL)
# Paper #8: Three-Column Working Memory
# ============================================================


class Note(TypedDict):
    """
    Acknowledged item in queue with time-to-live.
    Represents things to address later but not forget.
    """

    note_id: str
    content: str
    created_at: str  # ISO datetime
    ttl_hours: int
    priority: float  # Base priority, escalates as TTL expires
    source: Literal["user", "system", "inferred"]
    context: dict  # Relevant context when noted


# ============================================================
# COLUMN 3: OBJECTS (ambient context)
# Paper #8 + Paper #17
# ============================================================


class PersonObject(TypedDict):
    """
    Person in ambient context.
    Paper #17: Social Awareness and Relationship Dynamics
    """

    person_id: str
    name: str
    role: str
    authority: float  # 0.0-1.0, learned through preemption
    interaction_strength: float  # Frequency of positive interactions
    context_relevance: float  # Relevance to current context
    relationship_value: float  # 0.6*authority + 0.2*interaction + 0.2*context
    preferences: list[str]
    last_interaction: str


class EntityObject(TypedDict):
    """Generic entity in ambient context (vendors, projects, etc.)."""

    entity_id: str
    name: str
    entity_type: str
    salience: float
    properties: dict


class TemporalContext(TypedDict):
    """
    Time-based context affecting urgency and behavior.
    Paper #18: Time-Based Context Activation
    """

    current_time: str
    is_month_end: bool
    is_quarter_end: bool
    is_year_end: bool
    days_until_deadline: Optional[int]
    urgency_multiplier: float  # 1.0 normal, 1.5 elevated, 2.0 critical


class Objects(TypedDict):
    """
    Complete ambient context - Column 3 of working memory.
    Populated via salience-based selection from knowledge graph.
    """

    people: list[PersonObject]
    entities: list[EntityObject]
    beliefs: list[dict]  # BeliefState objects
    knowledge: list[dict]  # Relevant workflows/rules
    goals: list[dict]  # Active goals
    temporal: TemporalContext


# ============================================================
# BELIEF SYSTEM
# Papers #1, #4, #9, #10, #11, #12
# ============================================================


class ContextState(TypedDict):
    """
    Belief state for a specific context.
    Paper #4: Context-Conditional Beliefs
    """

    strength: float  # 0.0-1.0
    last_updated: str  # ISO datetime
    success_count: int
    failure_count: int
    last_outcome: Optional[
        Literal["success", "failure", "neutral", "validation", "correction"]
    ]


class BeliefState(TypedDict):
    """
    Complete belief representation with all research features.

    Papers implemented:
    - #1: Competence-Based Autonomy (strength -> supervision)
    - #4: Context-Conditional Beliefs (context_states, backoff)
    - #9: Moral Asymmetry (category multipliers, is_distrusted)
    - #10: A.C.R.E. (invalidation_threshold)
    - #11: Hierarchical Beliefs (supports, supported_by)
    - #12: Peak-End Rule (is_end_memory_influenced, peak_intensity)
    """

    belief_id: str
    statement: str
    category: Literal["moral", "competence", "technical", "preference", "identity"]

    # Core strength (Paper #1)
    strength: float  # 0.0-1.0, intrinsic strength

    # Context conditioning (Paper #4)
    context_key: str  # Default context, e.g., "*|*|*"
    context_states: dict[str, ContextState]  # context_key -> state

    # Hierarchy (Paper #11)
    supports: list[str]  # belief_ids this belief supports
    supported_by: list[str]  # belief_ids that support this belief
    support_weights: dict[str, float]  # belief_id -> weight

    # Temporal (Paper #12)
    last_updated: str
    success_count: int
    failure_count: int
    is_end_memory_influenced: bool
    peak_intensity: float

    # Category thresholds (Paper #10 - A.C.R.E.)
    invalidation_threshold: float

    # Moral asymmetry (Paper #9)
    is_distrusted: bool  # Permanent circuit breaker
    moral_violation_count: int


# ============================================================
# MEMORY SYSTEM
# Papers #12, #13
# ============================================================


class Memory(TypedDict):
    """
    Episodic memory with peak-end weighting.

    Papers implemented:
    - #12: Peak-End Rule (emotional_intensity, is_end_memory)
    - #13: Interference-Based Decay (related_beliefs for similarity)
    """

    memory_id: str
    description: str
    timestamp: str
    outcome: Literal["success", "failure", "neutral", "validation", "correction"]
    emotional_intensity: float  # 0.0-1.0
    is_end_memory: bool  # End of conversation/branch
    related_beliefs: list[str]
    related_persons: list[str]
    context_key: str
    difficulty_level: int


# ============================================================
# SOCIAL GRAPH
# Paper #17
# ============================================================


class PersonRelationship(TypedDict):
    """
    Person-to-person relationship for authority and conflict resolution.
    Paper #17: Social Awareness and Relationship Dynamics
    """

    source_person_id: str
    target_person_id: str
    authority_differential: float  # How much source outranks target
    domain: str  # Where this authority applies
    interaction_count: int
    last_preemption: Optional[str]  # When source overrode target's guidance


# ============================================================
# APPRAISAL RESULT
# ============================================================


class AppraisalResult(TypedDict):
    """Result of the appraisal node."""

    expectancy_violation: Optional[dict]
    face_threat: Optional[dict]
    goal_alignment: dict
    attributed_beliefs: list[str]
    recommended_action_type: Literal[
        "guidance_needed", "propose_and_confirm", "execute_directly"
    ]
    difficulty: int
    involves_ethical_beliefs: bool


# ============================================================
# ACTION
# PTD Architecture (Paper #20)
# ============================================================


class WorkUnit(TypedDict):
    """
    Semantic work unit from Planner.
    Paper #20: Planner-Translator-Driver Architecture
    """

    unit_id: str
    tool: str  # Which surface (api, web, database, etc.)
    verb: str  # Semantic action (create_record, fill_form, etc.)
    entities: dict  # What to operate on
    slots: dict  # Parameters
    constraints: list[dict]  # Verification requirements


class SelectedAction(TypedDict):
    """Complete action plan."""

    action_type: str
    work_units: list[WorkUnit]
    requires_tools: list[str]
    estimated_difficulty: int


# ============================================================
# VALIDATION
# Paper #3: Self-Correcting Validation
# ============================================================


class ValidationResult(TypedDict):
    """Result from a single validator."""

    validator: str
    passed: bool
    severity: float  # 0.0-1.0 if failed
    message: str
    fix_hint: Optional[str]


# ============================================================
# EVENT LOG
# Paper #7: Moral Asymmetry with Event Sourcing
# ============================================================


class BeliefStrengthEvent(TypedDict):
    """
    Immutable event recording belief strength change.
    Paper #7: Event Sourcing for audit trail
    """

    event_id: str
    event_type: Literal["belief_strength_update"]
    belief_id: str
    context_key: str
    old_strength: float
    new_strength: float
    outcome: str
    difficulty_level: int
    category_multiplier: float
    peak_end_multiplier: float
    timestamp: str


class FeedbackEvent(TypedDict):
    """
    Event recording outcome-based learning.
    Used by the feedback node to log what happened.
    """

    event_id: str
    timestamp: str
    trigger: str  # What triggered the feedback
    outcome_type: str  # "success", "partial_success", "failure"
    belief_updates: list[dict]  # List of belief update records
    context_key: str
    supervision_mode: str
