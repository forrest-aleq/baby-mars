"""
Baby MARS Birth System
=======================

In-memory initialization of the 6 types for new people/orgs.
This is the Baby MARS version - uses Apollo API for enrichment.

The 6 Things:
1. Capabilities - What Aleq CAN do (binary)
2. Relationships - Org structure facts
3. Knowledge - Certain facts (no strength)
4. Beliefs - Uncertain claims WITH strength (0.0-1.0)
5. Goals - What to accomplish (has priority)
6. Style - How to behave (configuration)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, cast

from ..graphs.belief_graph import get_belief_graph, reset_belief_graph
from ..state.schema import BabyMARSState, PersonObject
from .beliefs import (
    IMMUTABLE_BELIEFS,
    seed_global_beliefs,
    seed_role_beliefs,
)
from .defaults import (
    DEFAULT_CAPABILITIES,
    DEFAULT_STYLE,
    ROLE_GOALS,
    ROLE_HIERARCHY,
    ROLE_STYLE_OVERRIDES,
)
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    facts_to_dicts,
    load_industry_knowledge,
)
from .knowledge_packs import seed_industry_beliefs


def calculate_salience(
    role: str, org_size: str = "mid_market", is_decision_maker: bool = False
) -> float:
    """
    Calculate salience score for birth mode selection.

    salience = (future_interaction × 0.4) + (incentive_value × 0.4) + (deviation × 0.2)
    """
    role_scores = {
        "CFO": 0.9,
        "CEO": 0.95,
        "COO": 0.85,
        "Controller": 0.8,
        "VP Finance": 0.75,
        "Director": 0.7,
        "Manager": 0.6,
        "Senior Accountant": 0.5,
        "Staff Accountant": 0.4,
        "AP Specialist": 0.35,
        "AR Specialist": 0.35,
    }

    size_multipliers = {"smb": 0.8, "mid_market": 1.0, "enterprise": 1.2}

    base = role_scores.get(role, 0.5)
    multiplier = size_multipliers.get(org_size, 1.0)
    decision_bonus = 0.1 if is_decision_maker else 0.0

    return min(1.0, (base * multiplier) + decision_bonus)


def determine_birth_mode(salience: float) -> str:
    """
    Determine birth mode from salience.

    - FULL (salience >= 0.7): 20-25 beliefs, all pillars
    - STANDARD (0.4-0.7): 10-15 beliefs
    - MICRO (< 0.4): 5-8 beliefs, no LLM
    """
    if salience >= 0.7:
        return "full"
    elif salience >= 0.4:
        return "standard"
    return "micro"


def _seed_beliefs(
    graph: Any, birth_mode: str, industry: str, org_id: str, role: str, person_id: str
) -> None:
    """Seed beliefs based on birth mode."""
    for belief in IMMUTABLE_BELIEFS:
        graph.add_belief(belief)
    seed_global_beliefs(graph)
    if birth_mode in ("full", "standard"):
        seed_industry_beliefs(graph, industry, org_id)
    if birth_mode == "full":
        seed_role_beliefs(graph, role, person_id)


def _build_person_object(
    person_id: str, name: str, role: str, role_info: dict[str, Any]
) -> PersonObject:
    """Build the person object with role-appropriate settings."""
    return cast(
        PersonObject,
        {
            "id": person_id,
            "name": name,
            "role": role,
            "authority": role_info["authority"],
            "relationship_value": 0.5,
            "interaction_count": 0,
            "last_interaction": "",
            "expertise_areas": [],
            "communication_preferences": {**DEFAULT_STYLE, **ROLE_STYLE_OVERRIDES.get(role, {})},
        },
    )


def birth_person(
    person_id: str,
    name: str,
    email: str,
    role: str,
    org_id: str,
    org_name: str,
    industry: str = "general",
    birth_mode: str = "standard",
) -> dict[str, Any]:
    """Birth a new person into the system. Creates the 6 types and seeds initial beliefs."""
    graph = get_belief_graph()
    _seed_beliefs(graph, birth_mode, industry, org_id, role, person_id)

    role_info = ROLE_HIERARCHY.get(role, {"reports_to": None, "authority": 0.5})
    person = _build_person_object(person_id, name, role, role_info)
    goals = ROLE_GOALS.get(
        role,
        [
            {
                "goal_id": "default_accuracy",
                "description": "Complete tasks accurately",
                "priority": 0.9,
            }
        ],
    )
    knowledge = facts_to_dicts(list(GLOBAL_KNOWLEDGE_FACTS) + load_industry_knowledge(industry))

    return {
        "birth_mode": birth_mode,
        "salience": calculate_salience(role),
        "person": person,
        "org": {"org_id": org_id, "org_name": org_name, "industry": industry},
        "capabilities": {**DEFAULT_CAPABILITIES},
        "relationships": {
            "reports_to": role_info["reports_to"],
            "authority": role_info["authority"],
            "org_id": org_id,
        },
        "knowledge": knowledge,
        "goals": goals,
        "style": {**DEFAULT_STYLE, **ROLE_STYLE_OVERRIDES.get(role, {})},
        "belief_count": len(graph.beliefs),
        "immutable_count": len([b for b in graph.beliefs.values() if b.get("immutable")]),
    }


def _build_working_memory(
    initial_message: str, person: dict[str, Any], now: datetime
) -> dict[str, Any]:
    """Build the three-column working memory structure (Paper #8)."""
    return {
        "active_tasks": [
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "description": initial_message,
                "priority": 0.8,
                "created_at": now.isoformat(),
                "status": "active",
            }
        ],
        "notes": [],
        "objects": {
            "persons": [person],
            "entities": [],
            "beliefs_in_focus": [],
            "temporal": {
                "current_time": now.isoformat(),
                "day_of_week": now.strftime("%A"),
                "is_month_end": now.day >= 25,
                "is_quarter_end": now.month in (3, 6, 9, 12) and now.day >= 25,
            },
        },
    }


def create_initial_state(
    birth_result: dict[str, Any],
    initial_message: str,
    thread_id: str | None = None,
) -> BabyMARSState:
    """Create initial cognitive state from birth result."""
    now = datetime.now(timezone.utc)
    thread_id = thread_id or f"thread_{uuid.uuid4().hex[:12]}"
    person = birth_result["person"]
    user_id = person.get("id", person.get("person_id", ""))

    return cast(
        BabyMARSState,
        {
            "thread_id": thread_id,
            "user_id": user_id,
            "org_timezone": birth_result.get("org", {}).get("timezone", "America/Los_Angeles"),
            "messages": [{"role": "user", "content": initial_message}],
            "org_id": birth_result["org"]["org_id"],
            "person": person,
            "activated_beliefs": list(get_belief_graph().beliefs.values()),
            "current_context_key": "*|*|*",
            "active_goals": birth_result["goals"],
            "working_memory": _build_working_memory(initial_message, person, now),
            "capabilities": birth_result["capabilities"],
            "style": birth_result["style"],
            "supervision_mode": None,
            "belief_strength_for_action": None,
            "selected_action": None,
            "execution_results": [],
            "response": None,
            "appraisal": None,
            "turn_number": 1,
            "gate_violation_detected": False,
            "feedback_events": [],
        },
    )


def quick_birth(
    name: str,
    role: str = "Controller",
    industry: str = "general",
    message: str = "Hello, I need help with something.",
) -> BabyMARSState:
    """Quick birth for testing - creates person and initial state in one call."""
    reset_belief_graph()

    person_id = f"person_{uuid.uuid4().hex[:8]}"
    org_id = f"org_{uuid.uuid4().hex[:8]}"

    birth_result = birth_person(
        person_id=person_id,
        name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        role=role,
        org_id=org_id,
        org_name="Test Organization",
        industry=industry,
    )

    return create_initial_state(birth_result, message)
