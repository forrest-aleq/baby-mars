"""
Baby MARS Birth System
=======================

Birth writes ONCE at signup, Mount reads EVERY message.

The 6 Things:
1. Capabilities - Binary flags (can/can't)
2. Relationships - Org structure facts
3. Knowledge - Certain facts (NO strength)
4. Beliefs - Uncertain claims (WITH strength)
5. Goals - What to accomplish (priority)
6. Style - How to behave (configuration)
"""

from .birth_system import (
    birth_person,
    create_initial_state,
    quick_birth,
    calculate_salience,
    determine_birth_mode,
)
from .defaults import (
    DEFAULT_CAPABILITIES,
    DEFAULT_STYLE,
    ROLE_HIERARCHY,
    ROLE_GOALS,
)
from .beliefs import IMMUTABLE_BELIEFS
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    INDUSTRY_KNOWLEDGE_PACKS,
    KnowledgeFact,
    load_industry_knowledge,
    create_org_knowledge,
    create_person_knowledge,
    resolve_knowledge,
    knowledge_to_context_string,
)
from .knowledge_packs import (
    seed_industry_beliefs,
    seed_authority_beliefs,
    seed_preference_beliefs,
    infer_goals_from_role,
)
from .apollo_birth import birth_from_apollo
from .mount import mount
from .persist import persist_birth, check_person_exists, init_birth_tables

__all__ = [
    # Birth functions
    "birth_person",
    "create_initial_state",
    "quick_birth",
    "birth_from_apollo",
    "calculate_salience",
    "determine_birth_mode",
    # Mount functions
    "mount",
    # Knowledge (facts, no strength)
    "GLOBAL_KNOWLEDGE_FACTS",
    "INDUSTRY_KNOWLEDGE_PACKS",
    "KnowledgeFact",
    "load_industry_knowledge",
    "create_org_knowledge",
    "create_person_knowledge",
    "resolve_knowledge",
    "knowledge_to_context_string",
    # Beliefs (claims, with strength)
    "IMMUTABLE_BELIEFS",
    "seed_industry_beliefs",
    "seed_authority_beliefs",
    "seed_preference_beliefs",
    "infer_goals_from_role",
    # Persistence
    "persist_birth",
    "check_person_exists",
    "init_birth_tables",
    # Constants
    "DEFAULT_CAPABILITIES",
    "DEFAULT_STYLE",
    "ROLE_HIERARCHY",
    "ROLE_GOALS",
]
