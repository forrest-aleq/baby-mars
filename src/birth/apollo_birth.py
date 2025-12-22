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
from typing import Optional

from ..state.schema import BabyMARSState, PersonObject
from ..graphs.belief_graph import get_belief_graph, reset_belief_graph
from ..graphs.belief_graph_manager import get_belief_graph_manager

from .defaults import DEFAULT_CAPABILITIES, DEFAULT_STYLE
from .beliefs import IMMUTABLE_BELIEFS, seed_global_beliefs
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    load_industry_knowledge,
    create_org_knowledge,
    create_person_knowledge,
    facts_to_dicts,
)
from .knowledge_packs import (
    seed_industry_beliefs,
    seed_authority_beliefs,
    seed_preference_beliefs,
    infer_goals_from_role,
)


async def birth_from_apollo(
    email: str,
    message: str = "Hello, I need help with something.",
    persist: bool = True,
) -> BabyMARSState:
    """
    Full birth flow using Apollo API enrichment.

    IMPORTANT: This should only be called ONCE at signup.
    For subsequent messages, use mount() instead.

    The 6 Things seeded at birth:
    1. Capabilities - From defaults (Baby MARS) or Stargate (Full MARS)
    2. Relationships - Inferred from role/authority
    3. Knowledge - Facts from global + industry + Apollo (NO STRENGTH)
    4. Beliefs - Claims from industry + role + preferences (WITH STRENGTH)
    5. Goals - Standing goals from role
    6. Style - Defaults (will be personalized via learning)

    Args:
        email: Email address to look up
        message: Initial user message
        persist: Whether to persist to DB (False for testing)

    Returns:
        BabyMARSState ready for cognitive loop
    """
    from .enrichment import (
        enrich_from_apollo,
        map_industry_to_knowledge_pack,
        infer_authority_from_role,
        determine_org_size,
    )
    from .birth_system import calculate_salience, determine_birth_mode, create_initial_state, quick_birth
    from .persist import check_person_exists, persist_birth
    from .mount import mount

    # Step 0: Idempotency check
    if persist:
        try:
            if await check_person_exists(email):
                # Person already exists - use mount instead
                state = await mount(email, message)
                if state:
                    return state
        except Exception:
            pass  # DB not available, continue with in-memory birth

    # Reset belief graph for clean start
    reset_belief_graph()

    # Step 1: Apollo enrichment
    apollo = await enrich_from_apollo(email)

    if not apollo:
        # Fallback to quick_birth with minimal data
        return quick_birth(
            name=email.split("@")[0].title(),
            role="User",
            industry="general",
            message=message,
        )

    # Step 2: Calculate salience and birth mode
    org_size = determine_org_size(apollo.company.employee_count)
    authority = infer_authority_from_role(apollo.person.title, apollo.person.seniority)
    salience = calculate_salience(
        role=apollo.person.title,
        org_size=org_size,
        is_decision_maker=(authority >= 0.7)
    )
    birth_mode = determine_birth_mode(salience)

    # Step 3: Create IDs
    person_id = f"person_{apollo.person.id[:8]}" if apollo.person.id else f"person_{uuid.uuid4().hex[:8]}"
    org_id = f"org_{apollo.company.id[:8]}" if apollo.company.id else f"org_{uuid.uuid4().hex[:8]}"

    industry = apollo.company.industry or "general"

    # ============================================================
    # KNOWLEDGE SEEDING (Facts - NO strength)
    # ============================================================

    # Collect all knowledge facts
    knowledge_facts = []

    # Global knowledge (accounting fundamentals)
    knowledge_facts.extend(GLOBAL_KNOWLEDGE_FACTS)

    # Industry knowledge
    knowledge_facts.extend(load_industry_knowledge(industry))

    # Org-specific knowledge from Apollo
    knowledge_facts.extend(create_org_knowledge(
        org_id=org_id,
        org_name=apollo.company.name or "Unknown",
        industry=industry,
        size=org_size,
        apollo_data={
            "company": {
                "name": apollo.company.name,
                "industry": apollo.company.industry,
                "keywords": apollo.company.keywords,
            }
        },
    ))

    # Person-specific knowledge from Apollo
    knowledge_facts.extend(create_person_knowledge(
        person_id=person_id,
        org_id=org_id,
        name=apollo.person.name or email.split("@")[0].title(),
        email=email,
        role=apollo.person.title or "User",
        apollo_data={
            "person": {
                "name": apollo.person.name,
                "title": apollo.person.title,
                "seniority": apollo.person.seniority,
                "timezone": apollo.person.timezone,
                "location": f"{apollo.person.city}, {apollo.person.state}",
            },
            "rapport_hooks": apollo.rapport_hooks,
        },
    ))

    # Convert to dicts for storage
    knowledge = facts_to_dicts(knowledge_facts)

    # ============================================================
    # BELIEF SEEDING (Claims - WITH strength)
    # ============================================================

    graph = get_belief_graph()

    # Immutable beliefs first (personality, never change)
    for belief in IMMUTABLE_BELIEFS:
        graph.add_belief(belief)

    # Global beliefs (general accounting claims)
    seed_global_beliefs(graph)

    # Industry beliefs (claims about how this industry typically operates)
    seed_industry_beliefs(graph, industry, org_id)

    # Authority beliefs (claims about this person's capabilities)
    seed_authority_beliefs(graph, apollo.person.title, authority, person_id)

    # Preference beliefs (uncertain claims about preferences, will learn)
    seed_preference_beliefs(graph, person_id, {
        "person": {
            "seniority": apollo.person.seniority,
        }
    })

    # ============================================================
    # OTHER 4 THINGS
    # ============================================================

    # Capabilities (binary flags)
    capabilities = {**DEFAULT_CAPABILITIES}

    # Relationships (org structure facts)
    from .defaults import ROLE_HIERARCHY
    role_info = ROLE_HIERARCHY.get(apollo.person.title, {})
    relationships = {
        "reports_to": role_info.get("reports_to"),
        "manages": [],
        "approves_for": [],
        "authority": authority,
        "org_id": org_id,
    }

    # Goals (standing goals from role)
    goals = infer_goals_from_role(apollo.person.title, authority)

    # Style (defaults, will learn preferences)
    style = {**DEFAULT_STYLE}

    # ============================================================
    # BUILD PERSON AND STATE
    # ============================================================

    person: PersonObject = {
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

    # Apollo snapshot for persistence
    apollo_snapshot = {
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

    # ============================================================
    # BUILD BIRTH RESULT
    # ============================================================

    birth_result = {
        "birth_mode": birth_mode,
        "salience": salience,
        "person": person,
        "org": {
            "org_id": org_id,
            "org_name": apollo.company.name or "Unknown",
            "industry": industry,
            "size": org_size,
        },
        # The 6 Things
        "capabilities": capabilities,
        "relationships": relationships,
        "knowledge": knowledge,  # Facts, no strength
        "goals": goals,
        "style": style,
        # Stats
        "belief_count": len(graph.beliefs),
        "knowledge_count": len(knowledge),
        "immutable_count": len([b for b in graph.beliefs.values() if b.get("immutable")]),
        "apollo_data": apollo_snapshot,
    }

    # ============================================================
    # PERSIST TO DATABASE
    # ============================================================

    if persist:
        try:
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
                beliefs=list(graph.beliefs.values()),
                apollo_data=apollo_snapshot,
            )
        except Exception as e:
            print(f"Warning: Failed to persist birth: {e}")
            # Continue anyway - state is still valid in-memory

    # Populate belief graph manager cache
    manager = get_belief_graph_manager()
    manager._cache[org_id] = graph

    # ============================================================
    # CREATE INITIAL STATE
    # ============================================================

    now = datetime.now(timezone.utc)

    return {
        "messages": [{"role": "user", "content": message}],
        "org_id": org_id,
        "person": person,

        # The 6 Things
        "capabilities": capabilities,
        "relationships": relationships,
        "knowledge": knowledge,  # Facts (no strength)
        "activated_beliefs": list(graph.beliefs.values()),  # Claims (with strength)
        "active_goals": goals,
        "style": style,

        # Temporal (computed fresh)
        "temporal": {
            "current_time": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "time_of_day": "morning" if now.hour < 12 else ("afternoon" if now.hour < 17 else "evening"),
            "month_phase": "month-start" if now.day <= 5 else ("month-end" if now.day >= 25 else "mid-month"),
            "is_month_end": now.day >= 25,
            "is_quarter_end": now.month in (3, 6, 9, 12) and now.day >= 25,
            "is_year_end": now.month == 12 and now.day >= 25,
        },

        # Context
        "current_context_key": "*|*|*",

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
                "persons": [person],
                "entities": [],
                "beliefs_in_focus": [],
            },
        },

        # Cognitive loop state (initialized)
        "supervision_mode": None,
        "belief_strength_for_action": None,
        "selected_action": None,
        "execution_results": [],
        "response": None,
        "appraisal": None,
        "turn_number": 1,
        "gate_violation_detected": False,
        "feedback_events": [],

        # Birth metadata
        "birth_mode": birth_mode,
        "birth_salience": salience,
    }
