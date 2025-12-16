"""
Active Subgraph (Mount Contract)
=================================

The contract between Birth and the Cognitive Loop.

Birth writes → Neo4j (or in Baby MARS, in-memory structures)
Mount reads → ActiveSubgraph

This is what the cognitive loop gets to work with.
If Birth wrote it, Mount must provide it.
If Mount expects it, Birth must write it.
"""

from typing import TypedDict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..state.schema import (
    PersonObject,
    BeliefState,
)
from ..graphs.belief_graph import get_belief_graph


# ============================================================
# TYPE DEFINITIONS
# ============================================================

class CapabilityNode(TypedDict):
    """What Aleq CAN do - binary, not a belief"""
    capability_id: str
    enabled: bool
    category: str  # "connector", "feature"


class RelationshipEdge(TypedDict):
    """Org structure facts - not beliefs"""
    relationship_type: str  # "reports_to", "manages", "approves_for"
    source_id: str
    target_id: str
    properties: dict  # e.g., {"threshold": 10000, "domain": "expenses"}


class KnowledgeNode(TypedDict):
    """Certain facts - no strength"""
    knowledge_id: str
    statement: str
    scope: str  # "global", "industry:X", "org:X", "person:X"
    category: str  # "accounting", "regulatory", "operational"


class GoalNode(TypedDict):
    """What Aleq is trying to accomplish"""
    goal_id: str
    description: str
    priority: float  # 0.0-1.0
    status: str  # "standing", "activated", "completed"
    scope: str  # "org", "person", "task"


class StyleConfiguration(TypedDict):
    """How Aleq behaves - resolved from hierarchy"""
    tone: str
    verbosity: str
    formality: str
    proactivity: str
    pace: str
    certainty: str


class TemporalContext(TypedDict):
    """Current situation - computed at mount time"""
    current_time: str
    day_of_week: str
    time_of_day: str  # "morning", "afternoon", "evening"
    month_phase: str  # "month-end", "mid-month", "month-start"
    is_month_end: bool
    is_quarter_end: bool
    is_year_end: bool
    urgency_multiplier: float


# ============================================================
# ACTIVE SUBGRAPH (The Mount Result)
# ============================================================

@dataclass
class ActiveSubgraph:
    """
    The result of mounting - everything the cognitive loop needs.
    
    This is THE contract. The cognitive loop can rely on all
    these fields being present and valid.
    """
    
    # Identity
    person: PersonObject
    org_id: str
    org_name: str
    
    # The 6 Types
    capabilities: dict[str, bool] = field(default_factory=dict)
    relationships: list[RelationshipEdge] = field(default_factory=list)
    knowledge: list[KnowledgeNode] = field(default_factory=list)
    beliefs: list[BeliefState] = field(default_factory=list)  # Max 20, resolved
    goals: list[GoalNode] = field(default_factory=list)  # Max 10, active
    style: StyleConfiguration = field(default_factory=lambda: {
        "tone": "warm",
        "verbosity": "moderate", 
        "formality": "professional",
        "proactivity": "balanced",
        "pace": "normal",
        "certainty": "balanced",
    })
    
    # Computed at mount
    temporal: TemporalContext = field(default_factory=lambda: {
        "current_time": datetime.now().isoformat(),
        "day_of_week": datetime.now().strftime("%A"),
        "time_of_day": "morning",
        "month_phase": "mid-month",
        "is_month_end": False,
        "is_quarter_end": False,
        "is_year_end": False,
        "urgency_multiplier": 1.0,
    })
    
    # Personality (immutable beliefs - special handling)
    immutable_beliefs: list[BeliefState] = field(default_factory=list)
    
    # Validation state
    is_valid: bool = False
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)


# ============================================================
# MOUNT FUNCTION
# ============================================================

def mount_active_subgraph(
    state: dict,
    max_beliefs: int = 20,
    max_goals: int = 10,
    max_knowledge: int = 20,
) -> ActiveSubgraph:
    """
    Mount the active subgraph from state.
    
    This is the Baby MARS version - reads from in-memory state
    instead of Neo4j. The contract is the same.
    
    Args:
        state: BabyMARSState with birth data
        max_beliefs: Maximum beliefs to include (default 20)
        max_goals: Maximum active goals (default 10)
        max_knowledge: Maximum knowledge items (default 20)
        
    Returns:
        ActiveSubgraph ready for cognitive loop
    """
    
    subgraph = ActiveSubgraph(
        person=_extract_person(state),
        org_id=state.get("org_id", "unknown"),
        org_name=state.get("objects", {}).get("org_name", "Unknown Org"),
    )
    
    # Mount capabilities
    subgraph.capabilities = state.get("capabilities", {})
    
    # Mount relationships (from person object for now)
    # In full MARS this would be Neo4j edges
    subgraph.relationships = []
    
    # Mount knowledge
    knowledge_items = state.get("knowledge", [])
    subgraph.knowledge = [
        {"knowledge_id": f"k_{i}", "statement": k, "scope": "global", "category": "accounting"}
        for i, k in enumerate(knowledge_items[:max_knowledge])
    ]
    
    # Mount beliefs (resolved from graph)
    subgraph.beliefs, subgraph.immutable_beliefs = _resolve_beliefs(
        state.get("current_context_key", "*|*|*"),
        max_beliefs
    )
    
    # Mount goals
    goals = state.get("active_goals", [])
    subgraph.goals = goals[:max_goals]
    
    # Mount style
    subgraph.style = state.get("style", subgraph.style)
    
    # Compute temporal
    subgraph.temporal = _compute_temporal(state)
    
    # Validate
    _validate_subgraph(subgraph)
    
    return subgraph


def _extract_person(state: dict) -> PersonObject:
    """Extract person from state"""
    objects = state.get("objects", {})
    people = objects.get("people", [])
    
    if people:
        return people[0]
    
    # Fallback
    return {
        "id": "unknown",
        "name": "Unknown User",
        "role": "User",
        "authority": 0.5,
        "relationship_value": 0.5,
    }


def _resolve_beliefs(
    context_key: str,
    max_beliefs: int
) -> tuple[list[BeliefState], list[BeliefState]]:
    """
    Resolve beliefs by scope hierarchy.
    
    Returns: (mutable_beliefs, immutable_beliefs)
    """
    graph = get_belief_graph()
    
    # Get all beliefs
    all_beliefs = list(graph.beliefs.values())
    
    # Separate immutables
    immutables = [b for b in all_beliefs if b.get("immutable", False)]
    mutables = [b for b in all_beliefs if not b.get("immutable", False)]
    
    # Resolve mutables by scope (narrower wins)
    resolved = _scope_resolution(mutables, context_key)
    
    # Sort by strength and take top N
    resolved.sort(key=lambda b: b.get("strength", 0), reverse=True)
    
    return resolved[:max_beliefs], immutables


def _scope_resolution(beliefs: list[BeliefState], context_key: str) -> list[BeliefState]:
    """
    Resolve beliefs by scope - narrower scope wins.
    
    Scope hierarchy:
    *|*|* (global) < industry:X|*|* < org:X|*|* < person:X|*|* < context:X
    """
    # Group beliefs by their "topic" (we use belief_id prefix for now)
    # In real system this would be semantic grouping
    
    # For Baby MARS, just return all beliefs - let cognitive_activation filter
    return beliefs


def _compute_temporal(state: dict) -> TemporalContext:
    """Compute temporal context from current time and state"""
    now = datetime.now()
    
    # Determine time of day
    hour = now.hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"
    
    # Determine month phase
    day = now.day
    if day >= 25 or day <= 5:
        month_phase = "month-end"
    elif day >= 10 and day <= 20:
        month_phase = "mid-month"
    else:
        month_phase = "month-start"
    
    # Check period ends
    is_month_end = day >= 25
    is_quarter_end = is_month_end and now.month in [3, 6, 9, 12]
    is_year_end = is_quarter_end and now.month == 12
    
    # Urgency multiplier
    urgency = 1.0
    if is_year_end:
        urgency = 1.5
    elif is_quarter_end:
        urgency = 1.3
    elif is_month_end:
        urgency = 1.2
    
    return {
        "current_time": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "time_of_day": time_of_day,
        "month_phase": month_phase,
        "is_month_end": is_month_end,
        "is_quarter_end": is_quarter_end,
        "is_year_end": is_year_end,
        "urgency_multiplier": urgency,
    }


def _validate_subgraph(subgraph: ActiveSubgraph) -> None:
    """
    Validate the mounted subgraph.
    
    Validation ladder:
    - MUST HAVE: errors if missing
    - SHOULD HAVE: warnings if missing
    - NICE TO HAVE: proceed without
    """
    errors = []
    warnings = []
    
    # MUST HAVE
    if not subgraph.person or subgraph.person.get("id") == "unknown":
        errors.append("Person node missing or invalid")
    
    if not subgraph.org_id or subgraph.org_id == "unknown":
        errors.append("Organization ID missing")
    
    if not subgraph.capabilities:
        errors.append("No capabilities defined")
    
    if not subgraph.immutable_beliefs:
        errors.append("Immutable beliefs (personality) not loaded")
    
    # SHOULD HAVE
    if not subgraph.knowledge:
        warnings.append("No knowledge loaded - using defaults")
    
    if not subgraph.beliefs:
        warnings.append("No mutable beliefs loaded - will learn from scratch")
    
    if not subgraph.goals:
        warnings.append("No goals loaded - inferring from role")
    
    # NICE TO HAVE
    person = subgraph.person
    if person and not person.get("communication_preferences"):
        warnings.append("No communication preferences - using defaults")
    
    # Set validation state
    subgraph.validation_errors = errors
    subgraph.validation_warnings = warnings
    subgraph.is_valid = len(errors) == 0
    
    # Log warnings
    for warning in warnings:
        print(f"Mount warning: {warning}")


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def subgraph_to_state_updates(subgraph: ActiveSubgraph) -> dict:
    """
    Convert ActiveSubgraph to state update dict.
    
    This is what cognitive_activation returns to update state.
    """
    return {
        "activated_beliefs": subgraph.beliefs,
        "active_goals": subgraph.goals,
        "capabilities": subgraph.capabilities,
        "knowledge": [k["statement"] for k in subgraph.knowledge],
        "style": subgraph.style,
        "objects": {
            "people": [subgraph.person],
            "temporal": subgraph.temporal,
            "entities": [],
        },
        # Store immutables for personality gate
        "immutable_beliefs": subgraph.immutable_beliefs,
    }
