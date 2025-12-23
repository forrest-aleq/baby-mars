"""
Knowledge Models
================

Data classes and constants for knowledge facts.

Source Priority (higher wins when upgrading):
- user: 100 (explicit user statement)
- admin: 90 (admin portal)
- integration: 70 (connected systems)
- apollo: 50 (enrichment API)
- inferred: 30 (derived from patterns)
- system: 10 (seeded at init)
- knowledge_pack: 10 (industry packs)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

# Type aliases for clarity
ScopeType = Literal["global", "industry", "org", "person"]
CategoryType = Literal[
    "accounting", "regulatory", "process", "entity", "temporal", "context"
]
SourceType = Literal[
    "system", "knowledge_pack", "apollo", "user", "admin", "inferred", "integration"
]
CorrectionType = Literal[
    "factual_error", "outdated", "more_specific", "scope_change", "source_upgrade"
]
CorrectorType = Literal["user", "admin", "system", "integration"]

# Source priority for replacement rules
SOURCE_PRIORITY = {
    "user": 100,
    "admin": 90,
    "integration": 70,
    "apollo": 50,
    "inferred": 30,
    "system": 10,
    "knowledge_pack": 10,
}


def can_replace_source(old_source: str, new_source: str) -> bool:
    """Check if new source can replace old source based on priority."""
    old_priority = SOURCE_PRIORITY.get(old_source, 0)
    new_priority = SOURCE_PRIORITY.get(new_source, 0)
    return new_priority >= old_priority


@dataclass
class KnowledgeFact:
    """A knowledge fact from the database."""

    id: str
    fact_key: str
    scope_type: ScopeType
    scope_id: Optional[str]
    statement: str
    category: CategoryType
    source_type: SourceType
    source_ref: dict
    status: str
    tags: list[str]
    confidence: float
    created_at: datetime
    valid_from: datetime
    valid_until: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert to dict for state storage."""
        return {
            "fact_id": self.id,
            "fact_key": self.fact_key,
            "scope": self.scope_type,
            "scope_id": self.scope_id,
            "statement": self.statement,
            "category": self.category,
            "source": self.source_type,
            "tags": self.tags,
        }


@dataclass
class FactCorrection:
    """Record of a fact being corrected."""

    id: str
    old_fact_id: str
    new_fact_id: Optional[str]
    corrected_by_type: str
    corrected_by_ref: Optional[str]
    reason: str
    correction_type: str
    created_at: datetime
