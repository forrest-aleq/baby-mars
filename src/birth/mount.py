"""
Mount System
=============

Load ActiveSubgraph for a person on each message.
Birth writes to DB once, Mount reads every message.

The 6 Things loaded at mount:
1. Capabilities - Binary flags (from Stargate/config)
2. Relationships - Org structure facts
3. Knowledge - Certain facts (NO strength)
4. Beliefs - Uncertain claims (WITH strength)
5. Goals - Standing + activated
6. Style - Resolved by hierarchy

Plus computed:
7. Temporal context - Current time situation
"""

from datetime import datetime, timezone
from typing import Optional

from ..graphs.belief_graph_manager import get_org_belief_graph
from ..persistence.database import get_connection
from ..state.schema import BabyMARSState, PersonObject
from .defaults import DEFAULT_CAPABILITIES, DEFAULT_STYLE
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    KnowledgeFact,
    create_org_knowledge,
    create_person_knowledge,
    facts_to_dicts,
    load_industry_knowledge,
    resolve_knowledge,
)
from .mount_models import ActiveSubgraph, TemporalContext

# Re-export for backwards compatibility
__all__ = ["ActiveSubgraph", "TemporalContext", "mount", "compute_temporal_context"]


def compute_temporal_context(org_timezone: Optional[str] = None) -> TemporalContext:
    """
    Compute current temporal context.

    This is recalculated on every mount - not stored.
    """
    now = datetime.now(timezone.utc)
    hour = now.hour

    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    day = now.day
    if day <= 5:
        month_phase = "month-start"
    elif day >= 25:
        month_phase = "month-end"
    else:
        month_phase = "mid-month"

    is_quarter_end = now.month in (3, 6, 9, 12) and day >= 25
    is_year_end = now.month == 12 and day >= 25

    return TemporalContext(
        current_time=now.isoformat(),
        day_of_week=now.strftime("%A"),
        time_of_day=time_of_day,
        month_phase=month_phase,
        quarter_phase="Q-close" if is_quarter_end else "normal",
        is_month_end=day >= 25,
        is_quarter_end=is_quarter_end,
        is_year_end=is_year_end,
        fiscal_events=[],
    )


async def load_person(email: str) -> Optional[dict]:
    """Load person from database by email."""
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT person_id, org_id, name, email, role, authority,
                       seniority, department, timezone, apollo_data
                FROM persons WHERE email = $1
            """,
                email,
            )

            if not row:
                return None

            return {
                "id": row["person_id"],
                "org_id": row["org_id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "authority": row["authority"] or 0.5,
                "seniority": row["seniority"],
                "department": row["department"],
                "timezone": row["timezone"],
                "apollo_data": row["apollo_data"],
            }
    except Exception as e:
        print(f"Error loading person: {e}")
        return None


async def load_org(org_id: str) -> Optional[dict]:
    """Load organization from database."""
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT org_id, name, industry, size, settings
                FROM organizations WHERE org_id = $1
            """,
                org_id,
            )

            if not row:
                return None

            return {
                "org_id": row["org_id"],
                "name": row["name"],
                "industry": row["industry"],
                "size": row["size"],
                "settings": row["settings"],
            }
    except Exception as e:
        print(f"Error loading org: {e}")
        return None


async def load_capabilities(org_id: str) -> dict:
    """
    Load capabilities for an org.

    Capabilities are binary - can or can't.
    In Baby MARS, we use defaults. Full MARS queries Stargate.
    """
    # TODO: Query Stargate for actual connected systems
    return {**DEFAULT_CAPABILITIES}


async def load_relationships(person_id: str, org_id: str, role: str, authority: float) -> dict:
    """
    Load relationships for a person.

    Relationships are FACTS about org structure.
    """
    # Infer from role
    from .defaults import ROLE_HIERARCHY

    role_info = ROLE_HIERARCHY.get(role, {})

    return {
        "reports_to": role_info.get("reports_to"),
        "manages": [],  # TODO: Load from relationships table
        "approves_for": [],
        "org_id": org_id,
        "authority": authority,
    }


async def load_knowledge(
    org_id: str,
    person_id: str,
    industry: str,
    apollo_data: Optional[dict] = None,
) -> list[dict]:
    """
    Load knowledge facts for this context.

    Knowledge = certain facts, NO strength.
    Scoped: global → industry → org → person
    """
    all_facts: list[KnowledgeFact] = []

    # Global knowledge (always present)
    all_facts.extend(GLOBAL_KNOWLEDGE_FACTS)

    # Industry knowledge
    all_facts.extend(load_industry_knowledge(industry))

    # Org-specific knowledge
    org_name = "Unknown"
    if apollo_data and "company" in apollo_data:
        org_name = apollo_data["company"].get("name", "Unknown")

    all_facts.extend(
        create_org_knowledge(
            org_id=org_id,
            org_name=org_name,
            industry=industry,
            size="mid_market",  # TODO: Get from org
            apollo_data=apollo_data,
        )
    )

    # Person-specific knowledge
    if apollo_data:
        person_name = apollo_data.get("person", {}).get("name", "User")
        person_email = apollo_data.get("person", {}).get("email", "")
        person_role = apollo_data.get("person", {}).get("title", "User")

        all_facts.extend(
            create_person_knowledge(
                person_id=person_id,
                org_id=org_id,
                name=person_name,
                email=person_email,
                role=person_role,
                apollo_data=apollo_data,
            )
        )

    # Resolve by scope (narrower wins)
    resolved = resolve_knowledge(all_facts, org_id, person_id)

    # Convert to dicts for state storage (max 20)
    return facts_to_dicts(resolved[:20])


async def load_beliefs(org_id: str, max_beliefs: int = 20) -> list[dict]:
    """
    Load beliefs from the belief graph.

    Beliefs = uncertain claims WITH strength.
    These are what the learning loop updates.
    """
    belief_graph = await get_org_belief_graph(org_id)
    beliefs = list(belief_graph.beliefs.values())

    # Sort by strength (highest first) and return top N
    beliefs.sort(key=lambda b: b.get("strength", 0), reverse=True)

    return beliefs[:max_beliefs]


async def load_goals(person_id: str, org_id: str, role: str, authority: float) -> list[dict]:
    """
    Load active goals for a person.

    Goals have priority, not strength. They're not beliefs.
    """
    from .knowledge_packs import infer_goals_from_role

    # Standing goals from role
    standing = infer_goals_from_role(role, authority)

    # TODO: Load activated goals from temporal context
    # TODO: Load explicit goals from user statements

    return standing[:10]  # Max 10 active goals


def resolve_style(
    person: dict,
    org: Optional[dict],
    temporal: TemporalContext,
) -> dict:
    """
    Resolve style by hierarchy: global → org → person → temporal.

    Style is configuration, not beliefs. Narrower scope wins.
    """
    style = {**DEFAULT_STYLE}

    # Org-level overrides
    if org and org.get("settings", {}).get("style"):
        style.update(org["settings"]["style"])

    # Role-level overrides
    from .defaults import ROLE_STYLE_OVERRIDES

    role = person.get("role", "")
    if role in ROLE_STYLE_OVERRIDES:
        style.update(ROLE_STYLE_OVERRIDES[role])

    # Person-level overrides (from communication_preferences)
    if person.get("communication_preferences"):
        style.update(person["communication_preferences"])

    # Temporal adjustments
    if temporal.is_month_end:
        style["pace"] = "deliberate"
        style["certainty"] = "hedged"

    if temporal.time_of_day == "evening":
        style["verbosity"] = "concise"

    return style


def validate_mount(
    person: dict,
    org: dict,
    knowledge: list,
    beliefs: list,
) -> list[str]:
    """
    Validate the mount is complete.

    Returns list of warnings (empty = all good).
    """
    warnings = []

    if not person:
        warnings.append("CRITICAL: Person not found")

    if not org:
        warnings.append("WARNING: Org not found, using defaults")

    if len(knowledge) < 5:
        warnings.append("WARNING: Limited knowledge loaded")

    if len(beliefs) < 5:
        warnings.append("WARNING: Limited beliefs loaded")

    # Check for immutable beliefs
    immutable_count = sum(1 for b in beliefs if b.get("immutable"))
    if immutable_count == 0:
        warnings.append("WARNING: No immutable beliefs found")

    return warnings


async def mount(email: str, message: str) -> Optional[BabyMARSState]:
    """
    Mount ActiveSubgraph for a person.

    This is called on EVERY message to load the current state.
    Birth writes once, Mount reads every time.

    The 6 things loaded:
    1. Capabilities - Binary flags
    2. Relationships - Org structure
    3. Knowledge - Facts (no strength)
    4. Beliefs - Claims (with strength)
    5. Goals - Active goals
    6. Style - Resolved configuration

    Plus computed temporal context.

    Args:
        email: Person's email
        message: The user's message

    Returns:
        BabyMARSState ready for cognitive loop, or None if person not found
    """
    import uuid

    # Load person
    person = await load_person(email)
    if not person:
        return None

    org_id = person["org_id"]
    person_id = person["id"]

    # Load org
    org = await load_org(org_id) or {
        "org_id": org_id,
        "name": "Unknown",
        "industry": "general",
        "size": "mid_market",
        "settings": {},
    }

    industry = org.get("industry", "general")
    apollo_data = person.get("apollo_data")

    # Compute temporal context (always fresh)
    temporal = compute_temporal_context(person.get("timezone"))

    # Load the 6 things
    capabilities = await load_capabilities(org_id)
    relationships = await load_relationships(
        person_id, org_id, person.get("role", ""), person.get("authority", 0.5)
    )
    knowledge = await load_knowledge(org_id, person_id, industry, apollo_data)
    beliefs = await load_beliefs(org_id)
    goals = await load_goals(
        person_id, org_id, person.get("role", ""), person.get("authority", 0.5)
    )
    style = resolve_style(person, org, temporal)

    # Validate mount
    warnings = validate_mount(person, org, knowledge, beliefs)
    for w in warnings:
        print(f"Mount: {w}")

    # Build person object for state
    person_obj: PersonObject = {
        "id": person_id,
        "name": person["name"],
        "role": person.get("role", "User"),
        "authority": person.get("authority", 0.5),
        "relationship_value": 0.5,
        "interaction_count": 0,
        "last_interaction": None,
        "expertise_areas": [],
        "communication_preferences": style,
    }

    # Build initial state with all 6 things
    now = datetime.now(timezone.utc)

    return {
        "messages": [{"role": "user", "content": message}],
        "org_id": org_id,
        "person": person_obj,
        # The 6 Things
        "capabilities": capabilities,
        "relationships": relationships,
        "knowledge": knowledge,  # NEW: Facts, no strength
        "activated_beliefs": beliefs,  # Claims, with strength
        "active_goals": goals,
        "style": style,
        # Context
        "current_context_key": "*|*|*",
        "temporal": {
            "current_time": temporal.current_time,
            "day_of_week": temporal.day_of_week,
            "time_of_day": temporal.time_of_day,
            "month_phase": temporal.month_phase,
            "is_month_end": temporal.is_month_end,
            "is_quarter_end": temporal.is_quarter_end,
            "is_year_end": temporal.is_year_end,
        },
        # Working memory
        "working_memory": {
            "active_tasks": [
                {
                    "task_id": f"task_{uuid.uuid4().hex[:8]}",
                    "description": message,
                    "priority": 0.8,
                    "created_at": now.isoformat(),
                    "status": "active",
                }
            ],
            "notes": [],
            "objects": {
                "persons": [person_obj],
                "entities": [],
                "beliefs_in_focus": [],
            },
        },
        # Cognitive loop state
        "supervision_mode": None,
        "belief_strength_for_action": None,
        "selected_action": None,
        "execution_results": [],
        "response": None,
        "appraisal": None,
        "turn_number": 1,
        "gate_violation_detected": False,
        "feedback_events": [],
    }
