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

from .apollo_birth import birth_from_apollo
from .beliefs import IMMUTABLE_BELIEFS
from .birth_system import (
    birth_person,
    calculate_salience,
    create_initial_state,
    determine_birth_mode,
    quick_birth,
)
from .defaults import (
    DEFAULT_CAPABILITIES,
    DEFAULT_STYLE,
    ROLE_GOALS,
    ROLE_HIERARCHY,
)
from .knowledge import (
    GLOBAL_KNOWLEDGE_FACTS,
    INDUSTRY_KNOWLEDGE_PACKS,
    KnowledgeFact,
    create_org_knowledge,
    create_person_knowledge,
    knowledge_to_context_string,
    load_industry_knowledge,
    resolve_knowledge,
)
from .knowledge_packs import (
    infer_goals_from_role,
    seed_authority_beliefs,
    seed_industry_beliefs,
    seed_preference_beliefs,
)
from .mount import mount
from .persist import check_person_exists, init_birth_tables, persist_birth

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
