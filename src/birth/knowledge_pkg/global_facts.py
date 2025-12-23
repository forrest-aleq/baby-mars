"""
Global Knowledge Facts
=======================

Accounting fundamentals that are FACTS, not beliefs.
No strength, no learning.
"""

from .model import KnowledgeFact

GLOBAL_KNOWLEDGE_FACTS = [
    KnowledgeFact(
        fact_id="global_double_entry",
        statement="Every journal entry must have balanced debits and credits",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "fundamental"],
    ),
    KnowledgeFact(
        fact_id="global_fiscal_periods",
        statement="Fiscal year consists of 12 monthly accounting periods",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "temporal"],
    ),
    KnowledgeFact(
        fact_id="global_accrual_basis",
        statement="GAAP requires accrual basis accounting for most entities",
        scope="global",
        category="regulatory",
        source="system",
        tags=["gaap", "fundamental"],
    ),
    KnowledgeFact(
        fact_id="global_materiality",
        statement="Materiality thresholds determine disclosure requirements",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "audit"],
    ),
    KnowledgeFact(
        fact_id="global_internal_controls",
        statement="Internal controls are required to prevent fraud and errors",
        scope="global",
        category="regulatory",
        source="system",
        tags=["sox", "controls"],
    ),
    KnowledgeFact(
        fact_id="global_audit_trail",
        statement="All transactions require supporting documentation",
        scope="global",
        category="accounting",
        source="system",
        tags=["audit", "compliance"],
    ),
]
