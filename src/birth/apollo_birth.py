"""
Apollo-Enriched Birth
======================

Full birth flow using Apollo API for person/company enrichment.

Birth happens ONCE at signup. The 6 things are seeded:
1. Capabilities - Binary flags (from Stargate/defaults)
2. Relationships - Org structure (inferred from role)
3. Knowledge - Certain facts (NO strength)
4. Beliefs - Uncertain claims (WITH strength)
5. Goals - Standing goals (from role)
6. Style - Default configuration

Mount happens EVERY message - use mount() instead.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from ..graphs.belief_graph import BeliefGraph, get_belief_graph, reset_belief_graph
from ..graphs.belief_graph_manager import get_belief_graph_manager
from ..state.schema import BabyMARSState, PersonObject
from .beliefs import IMMUTABLE_BELIEFS, seed_global_beliefs
from .defaults import DEFAULT_CAPABILITIES, DEFAULT_STYLE, ROLE_HIERARCHY
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    KnowledgeFact,
    create_org_knowledge,
    create_person_knowledge,
    facts_to_dicts,
    load_industry_knowledge,
)
from .knowledge_packs import (
    infer_goals_from_role,
    seed_authority_beliefs,
    seed_industry_beliefs,
    seed_preference_beliefs,
)


def _collect_knowledge_facts(
    org_id: str, person_id: str, industry: str, email: str, apollo: Any, org_size: str
) -> list[dict[str, Any]]:
    """Collect knowledge facts from global, industry, org, and person sources."""
    facts: list[KnowledgeFact] = list(GLOBAL_KNOWLEDGE_FACTS)
    facts.extend(load_industry_knowledge(industry))
    facts.extend(create_org_knowledge(
        org_id, apollo.company.name or "Unknown", industry, org_size,
        {"company": {"name": apollo.company.name, "industry": apollo.company.industry,
                     "keywords": apollo.company.keywords}},
    ))
    facts.extend(create_person_knowledge(
        person_id, org_id, apollo.person.name or email.split("@")[0].title(), email,
        apollo.person.title or "User",
        {"person": {"name": apollo.person.name, "title": apollo.person.title,
                    "seniority": apollo.person.seniority, "timezone": apollo.person.timezone,
                    "location": f"{apollo.person.city}, {apollo.person.state}"},
         "rapport_hooks": apollo.rapport_hooks},
    ))
    return facts_to_dicts(facts)


def _seed_beliefs(
    graph: BeliefGraph,
    industry: str,
    org_id: str,
    person_id: str,
    apollo: Any,
    authority: float,
) -> None:
    """Seed all belief types into the graph."""
    # Immutable beliefs first (personality, never change)
    for belief in IMMUTABLE_BELIEFS:
        graph.add_belief(belief)

    # Global beliefs (general accounting claims)
    seed_global_beliefs(graph)

    # Industry beliefs
    seed_industry_beliefs(graph, industry, org_id)

    # Authority beliefs
    seed_authority_beliefs(graph, apollo.person.title, authority, person_id)

    # Preference beliefs
    seed_preference_beliefs(
        graph,
        person_id,
        {"person": {"seniority": apollo.person.seniority}},
    )


def _build_relationships(role: str, authority: float, org_id: str) -> dict[str, Any]:
    """Build relationships dict from role info."""
    role_info = ROLE_HIERARCHY.get(role, {})
    return {
        "reports_to": role_info.get("reports_to"),
        "manages": [],
        "approves_for": [],
        "authority": authority,
        "org_id": org_id,
    }


def _build_apollo_snapshot(apollo: Any) -> dict[str, Any]:
    """Build Apollo data snapshot for persistence."""
    return {
        "person": {
            "name": apollo.person.name,
            "title": apollo.person.title,
            "seniority": apollo.person.seniority,
            "location": f"{apollo.person.city}, {apollo.person.state}",
            "timezone": apollo.person.timezone,
        },
        "company": {
            "name": apollo.company.name,
            "industry": apollo.company.industry,
            "size": apollo.company.employee_count,
            "keywords": apollo.company.keywords[:5] if apollo.company.keywords else [],
        },
        "rapport_hooks": apollo.rapport_hooks,
    }


def _build_temporal_context(now: datetime) -> dict[str, Any]:
    """Build temporal context dict."""
    return {
        "current_time": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "time_of_day": (
            "morning" if now.hour < 12 else ("afternoon" if now.hour < 17 else "evening")
        ),
        "month_phase": (
            "month-start" if now.day <= 5 else ("month-end" if now.day >= 25 else "mid-month")
        ),
        "is_month_end": now.day >= 25,
        "is_quarter_end": now.month in (3, 6, 9, 12) and now.day >= 25,
        "is_year_end": now.month == 12 and now.day >= 25,
    }


def _create_ids(apollo: Any) -> tuple[str, str]:
    """Create person_id and org_id from Apollo data."""
    person_id = (
        f"person_{apollo.person.id[:8]}"
        if apollo.person.id
        else f"person_{uuid.uuid4().hex[:8]}"
    )
    org_id = (
        f"org_{apollo.company.id[:8]}"
        if apollo.company.id
        else f"org_{uuid.uuid4().hex[:8]}"
    )
    return person_id, org_id


def _build_person_object(
    person_id: str,
    apollo: Any,
    email: str,
    authority: float,
    style: dict[str, Any],
) -> PersonObject:
    """Build the person object for state."""
    return {
        "id": person_id,
        "name": apollo.person.name or email.split("@")[0].title(),
        "role": apollo.person.title or "User",
        "authority": authority,
        "relationship_value": 0.5,
        "interaction_count": 0,
        "last_interaction": None,
        "expertise_areas": [],
        "communication_preferences": {**style},
    }


async def _persist_birth_data(
    person_id: str,
    org_id: str,
    person: PersonObject,
    email: str,
    apollo: Any,
    industry: str,
    org_size: str,
    birth_mode: str,
    salience: float,
    beliefs: list[dict[str, Any]],
) -> None:
    """Persist birth data to database."""
    from .persist import persist_birth

    apollo_snapshot = _build_apollo_snapshot(apollo)
    await persist_birth(
        person_id=person_id,
        org_id=org_id,
        person_data={
            "name": person["name"],
            "email": email,
            "role": person["role"],
            "authority": person["authority"],
            "seniority": apollo.person.seniority,
            "department": apollo.person.department,
            "timezone": apollo.person.timezone,
            "birth_mode": birth_mode,
            "salience": salience,
        },
        org_data={
            "name": apollo.company.name or "Unknown",
            "industry": industry,
            "size": org_size,
        },
        beliefs=beliefs,
        apollo_data=apollo_snapshot,
    )


def _build_working_memory(message: str, person: PersonObject, now: datetime) -> dict[str, Any]:
    """Build working memory structure."""
    return {
        "active_tasks": [{
            "task_id": f"task_{uuid.uuid4().hex[:8]}", "description": message,
            "priority": 0.8, "created_at": now.isoformat(), "status": "active",
        }],
        "notes": [],
        "objects": {"persons": [person], "entities": [], "beliefs_in_focus": []},
    }


def _build_initial_state(
    message: str, org_id: str, person: PersonObject, capabilities: dict[str, bool],
    relationships: dict[str, Any], knowledge: list[dict[str, Any]], beliefs: list[dict[str, Any]],
    goals: list[dict[str, Any]], style: dict[str, Any], birth_mode: str, salience: float,
) -> dict[str, Any]:
    """Build the initial BabyMARSState dict."""
    now = datetime.now(timezone.utc)
    return {
        "messages": [{"role": "user", "content": message}], "org_id": org_id, "person": person,
        "capabilities": capabilities, "relationships": relationships, "knowledge": knowledge,
        "activated_beliefs": beliefs, "active_goals": goals, "style": style,
        "temporal": _build_temporal_context(now), "current_context_key": "*|*|*",
        "working_memory": _build_working_memory(message, person, now),
        "supervision_mode": None, "belief_strength_for_action": None, "selected_action": None,
        "execution_results": [], "response": None, "appraisal": None, "turn_number": 1,
        "gate_violation_detected": False, "feedback_events": [],
        "birth_mode": birth_mode, "birth_salience": salience,
    }


async def _check_existing_person(email: str, message: str) -> BabyMARSState | None:
    """Check if person exists and return mounted state if so."""
    from .mount import mount
    from .persist import check_person_exists
    try:
        if await check_person_exists(email):
            return await mount(email, message)
    except Exception:
        pass
    return None


async def birth_from_apollo(
    email: str, message: str = "Hello, I need help with something.", persist: bool = True
) -> BabyMARSState:
    """Birth flow using Apollo API. Called ONCE at signup; use mount() for subsequent messages."""
    from .birth_system import calculate_salience, determine_birth_mode, quick_birth
    from .enrichment import determine_org_size, enrich_from_apollo, infer_authority_from_role

    if persist:
        if existing := await _check_existing_person(email, message):
            return existing

    reset_belief_graph()
    apollo = await enrich_from_apollo(email)
    if not apollo:
        return quick_birth(email.split("@")[0].title(), "User", "general", message)

    # Calculate parameters and create IDs
    org_size = determine_org_size(apollo.company.employee_count)
    authority = infer_authority_from_role(apollo.person.title, apollo.person.seniority)
    salience = calculate_salience(apollo.person.title, org_size, authority >= 0.7)
    birth_mode = determine_birth_mode(salience)
    person_id, org_id = _create_ids(apollo)
    industry = apollo.company.industry or "general"

    # Seed knowledge and beliefs
    knowledge = _collect_knowledge_facts(org_id, person_id, industry, email, apollo, org_size)
    graph = get_belief_graph()
    _seed_beliefs(graph, industry, org_id, person_id, apollo, authority)

    # Build the 6 things
    caps, rels = {**DEFAULT_CAPABILITIES}, _build_relationships(apollo.person.title, authority, org_id)
    goals, style = infer_goals_from_role(apollo.person.title, authority), {**DEFAULT_STYLE}
    person, beliefs = _build_person_object(person_id, apollo, email, authority, style), list(graph.beliefs.values())

    if persist:
        try:
            await _persist_birth_data(person_id, org_id, person, email, apollo, industry, org_size, birth_mode, salience, beliefs)
        except Exception as e:
            print(f"Warning: Failed to persist birth: {e}")

    get_belief_graph_manager()._cache[org_id] = graph
    return _build_initial_state(message, org_id, person, caps, rels, knowledge, beliefs, goals, style, birth_mode, salience)
