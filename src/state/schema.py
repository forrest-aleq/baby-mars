"""
Baby MARS State Schema
======================

Implementation of the Three-Column Working Memory (Paper #8)
and supporting data structures for the cognitive loop.

All 20 research papers that affect state structure are implemented here.
"""

import uuid
from datetime import datetime, timedelta
from operator import add
from typing import Annotated, Literal, Optional, TypedDict

# ============================================================
# CONSTANTS FROM RESEARCH
# ============================================================

# Paper #9: Moral Asymmetry Multipliers
# MARS taxonomy: moral, competence, technical, preference, identity
CATEGORY_MULTIPLIERS = {
    "moral": {"success": 3.0, "failure": 10.0},  # Trust violations = massive impact
    "competence": {"success": 1.0, "failure": 2.0},  # How to do things
    "technical": {"success": 1.0, "failure": 1.5},  # Domain-specific facts
    "preference": {"success": 1.0, "failure": 1.0},  # Style choices
    "identity": {"success": 0.0, "failure": 0.0},  # IMMUTABLE - A.C.R.E. firewall
}

# Paper #10: Category-Specific Invalidation Thresholds (A.C.R.E.)
INVALIDATION_THRESHOLDS = {
    "moral": 0.95,  # Very hard to invalidate moral beliefs
    "competence": 0.75,  # Moderate threshold
    "technical": 0.70,  # Technical facts can be updated
    "preference": 0.60,  # Preferences are flexible
    "identity": 1.0,  # NEVER invalidate - immutable
}

# Paper #1: Autonomy Thresholds
AUTONOMY_THRESHOLDS = {
    "guidance_seeking": 0.4,  # Below this
    "action_proposal": 0.7,  # Between 0.4 and this
    "autonomous": 1.0,  # Above 0.7
}

# Paper #16: Difficulty Weights
DIFFICULTY_WEIGHTS = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.5, 5: 2.0}

# Paper #12: Peak-End Multiplier
PEAK_END_MULTIPLIER = 3.0
PEAK_INTENSITY_THRESHOLD = 0.7

# Learning rate for EMA updates
LEARNING_RATE = 0.15


# ============================================================
# COLUMN 1: ACTIVE TASKS (3-4 slots)
# Paper #8: Three-Column Working Memory
# ============================================================


class TaskState(TypedDict):
    """Current state of an active task"""

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
    """Generic entity in ambient context (vendors, projects, etc.)"""

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
    last_outcome: Optional[Literal["success", "failure", "neutral", "validation", "correction"]]


class BeliefState(TypedDict):
    """
    Complete belief representation with all research features.

    Papers implemented:
    - #1: Competence-Based Autonomy (strength → supervision)
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
# From cognitive loop
# ============================================================


class AppraisalResult(TypedDict):
    """Result of the appraisal node"""

    expectancy_violation: Optional[dict]
    face_threat: Optional[dict]
    goal_alignment: dict
    attributed_beliefs: list[str]
    recommended_action_type: Literal["guidance_needed", "propose_and_confirm", "execute_directly"]
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
    """Complete action plan"""

    action_type: str
    work_units: list[WorkUnit]
    requires_tools: list[str]
    estimated_difficulty: int


# ============================================================
# VALIDATION
# Paper #3: Self-Correcting Validation
# ============================================================


class ValidationResult(TypedDict):
    """Result from a single validator"""

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


# ============================================================
# CUSTOM REDUCERS
# ============================================================


def task_reducer(existing: list[ActiveTask], new: list[ActiveTask]) -> list[ActiveTask]:
    """
    Keep max 4 active tasks, priority-based replacement.
    Paper #8: Working memory capacity of 3-4 items.
    """
    # Merge by task_id, preferring new
    by_id = {t["task_id"]: t for t in existing}
    for t in new:
        by_id[t["task_id"]] = t

    combined = list(by_id.values())
    combined.sort(key=lambda t: t.get("priority", 0), reverse=True)
    return combined[:4]


def note_reducer(existing: list[Note], new: list[Note]) -> list[Note]:
    """
    Merge notes, expire TTL-exceeded ones.
    Paper #8: Notes with TTL.
    """
    import logging
    import os

    logger = logging.getLogger(__name__)

    now = datetime.now()
    is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"

    # Merge by note_id
    by_id = {n["note_id"]: n for n in existing}
    for n in new:
        by_id[n["note_id"]] = n

    # Filter expired
    valid = []
    for note in by_id.values():
        try:
            created = datetime.fromisoformat(note["created_at"])
            ttl = timedelta(hours=note["ttl_hours"])
            if now - created < ttl:
                valid.append(note)
        except (ValueError, KeyError) as e:
            # Log the error with context
            logger.warning(
                f"Invalid note data: note_id={note.get('note_id', 'unknown')}, "
                f"created_at={note.get('created_at', 'missing')}, "
                f"ttl_hours={note.get('ttl_hours', 'missing')}, error={e}"
            )
            # In production, drop invalid notes; otherwise keep for debugging
            if not is_production:
                valid.append(note)

    return valid


# ============================================================
# MAIN STATE OBJECT
# ============================================================


class BabyMARSState(TypedDict):
    """
    Complete cognitive state for Baby MARS.

    Implements all 20 research papers in a single state object
    that LangGraph can checkpoint and persist.
    """

    # ---- Identity ----
    thread_id: str
    org_id: str
    user_id: str

    # ---- Three-Column Working Memory (Paper #8) ----
    active_tasks: Annotated[list[ActiveTask], task_reducer]
    notes: Annotated[list[Note], note_reducer]
    objects: Objects

    # ---- Conversation ----
    messages: Annotated[list, add]  # LangGraph message format
    current_turn: int

    # ---- Cognitive Loop State ----
    current_context_key: str
    activated_beliefs: list[BeliefState]
    appraisal: Optional[AppraisalResult]
    selected_action: Optional[SelectedAction]

    # ---- Autonomy (Paper #1) ----
    supervision_mode: Literal["guidance_seeking", "action_proposal", "autonomous"]
    belief_strength_for_action: float

    # ---- HITL Approval ----
    approval_status: Optional[Literal["pending", "approved", "rejected", "no_action"]]
    approval_summary: Optional[str]

    # ---- Goal State ----
    active_goals: list[dict]
    goal_conflict_detected: bool

    # ---- Social Context (Paper #17) ----
    current_person: Optional[PersonObject]
    authority_context: dict

    # ---- Execution Results ----
    execution_results: list[dict]

    # ---- Validation (Paper #3) ----
    validation_results: list[ValidationResult]
    retry_count: int
    max_retries: int

    # ---- Event Log (Paper #7) ----
    events: Annotated[list[BeliefStrengthEvent], add]


# ============================================================
# FACTORY FUNCTIONS
# ============================================================


def generate_id() -> str:
    """Generate unique ID (full UUID to avoid collisions)"""
    return str(uuid.uuid4())


def create_initial_state(thread_id: str, org_id: str, user_id: str) -> BabyMARSState:
    """Create initial state for a new conversation"""
    return {
        "thread_id": thread_id,
        "org_id": org_id,
        "user_id": user_id,
        "active_tasks": [],
        "notes": [],
        "objects": {
            "people": [],
            "entities": [],
            "beliefs": [],
            "knowledge": [],
            "goals": [],
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "is_month_end": False,
                "is_quarter_end": False,
                "is_year_end": False,
                "days_until_deadline": None,
                "urgency_multiplier": 1.0,
            },
        },
        "messages": [],
        "current_turn": 0,
        "current_context_key": "*|*|*",
        "activated_beliefs": [],
        "appraisal": None,
        "selected_action": None,
        "supervision_mode": "guidance_seeking",
        "belief_strength_for_action": 0.0,
        "approval_status": None,
        "approval_summary": None,
        "active_goals": [],
        "goal_conflict_detected": False,
        "current_person": None,
        "authority_context": {},
        "execution_results": [],
        "validation_results": [],
        "retry_count": 0,
        "max_retries": 3,
        "events": [],
    }


def create_belief(
    statement: str,
    category: Literal["moral", "competence", "technical", "preference", "identity"],
    initial_strength: float = 0.5,
    context_key: str = "*|*|*",
) -> BeliefState:
    """Factory function to create a new belief with proper defaults"""
    belief_id = generate_id()
    now = datetime.now().isoformat()

    return {
        "belief_id": belief_id,
        "statement": statement,
        "category": category,
        "strength": initial_strength,
        "context_key": context_key,
        "context_states": {
            context_key: {
                "strength": initial_strength,
                "last_updated": now,
                "success_count": 0,
                "failure_count": 0,
                "last_outcome": None,
            }
        },
        "supports": [],
        "supported_by": [],
        "support_weights": {},
        "last_updated": now,
        "success_count": 0,
        "failure_count": 0,
        "is_end_memory_influenced": False,
        "peak_intensity": 0.0,
        "invalidation_threshold": INVALIDATION_THRESHOLDS[category],
        "is_distrusted": False,
        "moral_violation_count": 0,
    }


def create_memory(
    description: str,
    outcome: Literal["success", "failure", "neutral", "validation", "correction"],
    context_key: str,
    difficulty_level: int = 3,
    emotional_intensity: float = 0.5,
    is_end_memory: bool = False,
    related_beliefs: list[str] = None,
    related_persons: list[str] = None,
) -> Memory:
    """Factory function to create a new memory"""
    return {
        "memory_id": generate_id(),
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "outcome": outcome,
        "emotional_intensity": emotional_intensity,
        "is_end_memory": is_end_memory,
        "related_beliefs": related_beliefs or [],
        "related_persons": related_persons or [],
        "context_key": context_key,
        "difficulty_level": difficulty_level,
    }


def compute_relationship_value(
    authority: float, interaction_strength: float, context_relevance: float
) -> float:
    """
    Compute relationship value per Paper #17 formula.

    Formula: 0.6 * authority + 0.2 * interaction_strength + 0.2 * context_relevance

    Use this function instead of duplicating the formula to avoid stale values.
    """
    return 0.6 * authority + 0.2 * interaction_strength + 0.2 * context_relevance


def create_person(name: str, role: str, authority: float = 0.5) -> PersonObject:
    """Factory function to create a new person"""
    interaction_strength = 0.5
    context_relevance = 0.5
    return {
        "person_id": generate_id(),
        "name": name,
        "role": role,
        "authority": authority,
        "interaction_strength": interaction_strength,
        "context_relevance": context_relevance,
        "relationship_value": compute_relationship_value(
            authority, interaction_strength, context_relevance
        ),
        "preferences": [],
        "last_interaction": datetime.now().isoformat(),
    }
