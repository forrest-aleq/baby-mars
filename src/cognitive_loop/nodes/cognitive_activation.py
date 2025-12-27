"""
Cognitive Activation Node
==========================

Loads cognitive context from graphs.
Implements the "fetch_active_subgraph" pattern.

This is the first step in the cognitive loop - it retrieves
relevant beliefs, memories, and social context for the current
interaction.
"""

from typing import Any, Optional, cast

from ...claude_models import EntityExtractionOutput
from ...claude_singleton import get_claude_client
from ...graphs.belief_graph import BeliefGraph
from ...graphs.belief_graph_manager import get_org_belief_graph
from ...graphs.social_graph import SocialGraph
from ...observability import get_logger
from ...persistence.rapport import RapportState, get_rapport
from ...scheduler.time_awareness import build_temporal_context
from ...state.schema import (
    BabyMARSState,
    Objects,
)

logger = get_logger(__name__)

# ============================================================
# GRAPH LOADING
# ============================================================

# Social graphs still use simple in-memory cache (less critical than beliefs)
_social_graphs: dict[str, SocialGraph] = {}


async def load_belief_graph(org_id: str) -> BeliefGraph:
    """Load belief graph for organization (uses LRU-cached manager)"""
    return await get_org_belief_graph(org_id)


async def load_social_graph(org_id: str) -> SocialGraph:
    """Load social graph for organization"""
    if org_id not in _social_graphs:
        from ...graphs.social_graph import SocialGraph

        _social_graphs[org_id] = SocialGraph()
    return _social_graphs[org_id]


# ============================================================
# ENTITY EXTRACTION (Phase 2)
# ============================================================


async def extract_entities(message: dict[str, Any]) -> Optional[EntityExtractionOutput]:
    """
    Extract entities from message using Claude.
    Returns structured entities for context building.
    """
    if not message:
        return None

    content = message.get("content", "")
    if isinstance(content, list):
        content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))

    if not content.strip():
        return None

    try:
        client = get_claude_client()
        return await client.complete_structured(
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract entities from this accounting/finance message:

<message>
{content}
</message>

Extract:
- client_name: Customer or company name if mentioned
- invoice_ids: Any invoice numbers, payment IDs, or reference numbers
- amounts: Dollar amounts mentioned (as floats)
- period: "month-end", "quarter-end", "year-end" if relevant, or null
- action_type: "payment", "invoice", "lockbox", "reconciliation", etc.
- urgency: "urgent" if time-sensitive, "normal" otherwise

Return null for any field not found in the message.""",
                }
            ],
            response_model=EntityExtractionOutput,
            temperature=0.0,
            node_name="cognitive_activation",
        )
    except Exception as e:
        logger.warning(f"Entity extraction failed, using fallback: {e}")
        return None


def _amount_range(amounts: list[float]) -> str:
    """Convert amounts to range bucket for context key."""
    if not amounts:
        return "*"
    max_amount = max(amounts)
    if max_amount >= 1_000_000:
        return ">1M"
    elif max_amount >= 100_000:
        return ">100K"
    elif max_amount >= 10_000:
        return ">10K"
    elif max_amount >= 1_000:
        return ">1K"
    return "<1K"


# ============================================================
# CONTEXT KEY BUILDING
# ============================================================


def build_context_key(entities: Optional[EntityExtractionOutput]) -> str:
    """
    Build context key from extracted entities.
    Format: "client|period|amount_range"
    """
    if not entities:
        return "*|*|*"

    client = entities.client_name or "*"
    period = entities.period or "*"
    amount = _amount_range(entities.amounts)

    return f"{client}|{period}|{amount}"


def entities_to_entity_objects(entities: Optional[EntityExtractionOutput]) -> list[Any]:
    """Convert extracted entities to EntityObject format for objects.entities."""
    if not entities:
        return []
    from ...state.schema import generate_id

    result: list[Any] = []
    if entities.client_name:
        result.append(
            {
                "entity_id": generate_id(),
                "name": entities.client_name,
                "entity_type": "client",
                "salience": 0.9,
                "properties": {},
            }
        )
    for inv_id in entities.invoice_ids:
        result.append(
            {
                "entity_id": generate_id(),
                "name": inv_id,
                "entity_type": "invoice",
                "salience": 0.8,
                "properties": {},
            }
        )
    if entities.action_type:
        result.append(
            {
                "entity_id": generate_id(),
                "name": entities.action_type,
                "entity_type": "action",
                "salience": 0.7,
                "properties": {"urgency": entities.urgency},
            }
        )
    return result


def detect_goal_conflict(goals: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Detect conflicts between active goals.

    Returns conflict details if found, None otherwise.
    """
    if len(goals) < 2:
        return None

    # Check for explicit conflicts (marked in goal metadata)
    for i, goal_a in enumerate(goals):
        for goal_b in goals[i + 1 :]:
            conflicts_with = goal_a.get("conflicts_with", [])
            if goal_b.get("goal_id") in conflicts_with:
                return {"type": "explicit_conflict", "goal_a": goal_a, "goal_b": goal_b}

    # Check for resource conflicts (same resource, different objectives)
    resources_used: dict[str, dict[str, Any]] = {}
    for goal in goals:
        for resource in goal.get("resources", []):
            if resource in resources_used:
                return {
                    "type": "resource_conflict",
                    "resource": resource,
                    "goal_a": resources_used[resource],
                    "goal_b": goal,
                }
            resources_used[resource] = goal

    return None


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict[str, Any]:
    """Cognitive Activation: load beliefs, people, entities, and rapport for current context."""
    org_id = state.get("org_id", "default")
    user_id = state.get("user_id", "")
    org_timezone = str(state.get("org_timezone", "America/Los_Angeles"))
    belief_graph = await load_belief_graph(org_id)
    social_graph = await load_social_graph(org_id)

    # Extract entities and build context key (Phase 2: Claude-based NER)
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}
    entities = await extract_entities(last_message)
    context_key = build_context_key(entities)

    # Activate relevant beliefs
    activated_beliefs = belief_graph.get_activated_beliefs(
        context_key=context_key, min_strength=0.3, limit=20
    )

    # ============================================================
    # LOAD RAPPORT: Get relationship state with current person
    # ============================================================
    # This is what makes Aleq feel human - she remembers people
    # and adapts based on the relationship history.
    rapport: Optional[RapportState] = None
    if user_id and user_id != "system":
        try:
            rapport = await get_rapport(org_id, user_id)
            if rapport:
                logger.debug(
                    f"Loaded rapport for {rapport['person_name']}: "
                    f"rapport={rapport['rapport_level']:.2f}, "
                    f"familiarity={rapport['familiarity']:.2f}, "
                    f"interactions={rapport['interaction_count']}"
                )
        except Exception as e:
            logger.warning(f"Failed to load rapport: {e}")

    # Build Objects column (Paper #8)
    objects: Objects = {
        "people": cast(list[Any], _load_salient_people(social_graph)[:10]),
        "entities": entities_to_entity_objects(entities),
        "beliefs": cast(list[dict[str, Any]], activated_beliefs[:20]),
        "knowledge": [],
        "goals": state.get("active_goals", []),
        "temporal": build_temporal_context(org_timezone),
    }

    goal_conflict = detect_goal_conflict(state.get("active_goals", []))

    # Build result with rapport context
    result: dict[str, Any] = {
        "current_context_key": context_key,
        "activated_beliefs": activated_beliefs,
        "objects": objects,
        "goal_conflict_detected": goal_conflict is not None,
        "current_turn": state.get("current_turn", 0) + 1,
    }

    # Add rapport context if available - this influences response generation
    if rapport:
        result["rapport_context"] = {
            "person_name": rapport["person_name"],
            "rapport_level": rapport["rapport_level"],
            "trust_level": rapport["trust_level"],
            "familiarity": rapport["familiarity"],
            "interaction_count": rapport["interaction_count"],
            "preferred_formality": rapport["preferred_formality"],
            "preferred_verbosity": rapport["preferred_verbosity"],
            "humor_receptivity": rapport["humor_receptivity"],
            "inside_references": rapport["inside_references"],
            "topics_discussed": rapport["topics_discussed"],
            "is_first_meeting": rapport["interaction_count"] == 0,
            "memorable_moments": rapport["memorable_moments"][-3:],  # Last 3 moments
        }

    return result


def _load_salient_people(social_graph: SocialGraph) -> list[dict[str, Any]]:
    """Load people with high relationship value."""
    people = []
    for person_id, person in social_graph.persons.items():
        rv = social_graph.compute_relationship_value(person_id)
        if rv > 0.4:
            people.append({**person, "relationship_value": rv})
    people.sort(key=lambda p: float(str(p.get("relationship_value", 0))), reverse=True)
    return people
