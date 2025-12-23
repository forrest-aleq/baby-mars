"""
Knowledge System Package
=========================

Certain facts with NO strength. Knowledge is not uncertain.

MARS distinguishes:
- Knowledge: "ASC 606 governs revenue recognition" (fact, no strength)
- Belief: "This client follows ASC 606 correctly" (claim, strength 0.7)

Knowledge is:
- Scoped: global -> industry -> org -> person (narrower wins)
- Changed via REPLACE (delete + insert), not learning
- Used as CONTEXT in cognitive loop, not for autonomy decisions

The learning loop NEVER touches knowledge. Only beliefs learn.
"""

from .creation import create_org_knowledge, create_person_knowledge
from .global_facts import GLOBAL_KNOWLEDGE_FACTS
from .industry_packs import (
    INDUSTRY_KNOWLEDGE_PACKS,
    get_industry_from_apollo,
    load_industry_knowledge,
)
from .model import KnowledgeFact
from .resolution import (
    dicts_to_facts,
    facts_to_dicts,
    knowledge_to_context_string,
    resolve_knowledge,
)

__all__ = [
    # Model
    "KnowledgeFact",
    # Data
    "GLOBAL_KNOWLEDGE_FACTS",
    "INDUSTRY_KNOWLEDGE_PACKS",
    # Industry functions
    "get_industry_from_apollo",
    "load_industry_knowledge",
    # Creation
    "create_org_knowledge",
    "create_person_knowledge",
    # Resolution
    "resolve_knowledge",
    "knowledge_to_context_string",
    "facts_to_dicts",
    "dicts_to_facts",
]
