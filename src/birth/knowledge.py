"""
Knowledge System
=================

Certain facts with NO strength. Knowledge is not uncertain.

This module re-exports from knowledge_pkg for backwards compatibility.
"""

# Re-export everything from the package
from .knowledge_pkg import (
    GLOBAL_KNOWLEDGE_FACTS,
    INDUSTRY_KNOWLEDGE_PACKS,
    KnowledgeFact,
    create_org_knowledge,
    create_person_knowledge,
    dicts_to_facts,
    facts_to_dicts,
    get_industry_from_apollo,
    knowledge_to_context_string,
    load_industry_knowledge,
    resolve_knowledge,
)

__all__ = [
    "KnowledgeFact",
    "GLOBAL_KNOWLEDGE_FACTS",
    "INDUSTRY_KNOWLEDGE_PACKS",
    "get_industry_from_apollo",
    "load_industry_knowledge",
    "create_org_knowledge",
    "create_person_knowledge",
    "resolve_knowledge",
    "knowledge_to_context_string",
    "facts_to_dicts",
    "dicts_to_facts",
]
