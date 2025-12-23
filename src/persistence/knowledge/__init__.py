"""
Knowledge Persistence Package
=============================

CRUD operations for knowledge facts.
Facts are certain (no strength) and change via REPLACE, not learning.

Key operations:
- load_facts_for_context() - Mount query, gets all relevant facts
- load_facts_known_at() - Point-in-time query (what did we know at time T?)
- add_fact() - Insert new fact
- replace_fact() - Supersede old, insert new (the "replace" mechanism)
- delete_fact() - Soft delete with audit trail
- get_fact_history() - See how a fact evolved over time
- bulk_import_facts() - Efficient batch import
"""

from .bulk import (
    bulk_import_facts,
    export_facts,
    seed_global_facts,
    seed_industry_facts,
    set_org_industries,
)
from .core import (
    add_fact,
    delete_fact,
    init_knowledge_tables,
    load_facts_for_context,
    replace_fact,
)
from .exceptions import (
    DuplicateFactKeyError,
    FactAlreadySupersededError,
    FactNotFoundError,
    KnowledgeError,
    SourcePriorityError,
)
from .models import (
    SOURCE_PRIORITY,
    FactCorrection,
    KnowledgeFact,
    can_replace_source,
)
from .queries import (
    count_facts_by_scope,
    get_fact_by_key,
    get_fact_history,
    load_facts_known_at,
)

__all__ = [
    # Exceptions
    "KnowledgeError",
    "FactNotFoundError",
    "FactAlreadySupersededError",
    "SourcePriorityError",
    "DuplicateFactKeyError",
    # Models
    "KnowledgeFact",
    "FactCorrection",
    "SOURCE_PRIORITY",
    "can_replace_source",
    # Core operations
    "init_knowledge_tables",
    "load_facts_for_context",
    "add_fact",
    "replace_fact",
    "delete_fact",
    # Queries
    "get_fact_by_key",
    "count_facts_by_scope",
    "get_fact_history",
    "load_facts_known_at",
    # Bulk operations
    "seed_global_facts",
    "seed_industry_facts",
    "set_org_industries",
    "bulk_import_facts",
    "export_facts",
]
