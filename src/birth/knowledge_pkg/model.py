"""
Knowledge Fact Model
=====================

The KnowledgeFact dataclass represents certain facts (no strength).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional


@dataclass
class KnowledgeFact:
    """
    A certain fact. No strength because it's not uncertain.

    Examples:
    - "Debits must equal credits" (global, accounting)
    - "ASC 606 governs revenue recognition" (global, regulatory)
    - "Company fiscal year ends December 31" (org, temporal)
    - "User timezone is America/New_York" (person, context)
    """

    fact_id: str
    statement: str
    scope: Literal["global", "industry", "org", "person"]
    scope_id: Optional[str] = None  # org_id or person_id if scoped
    category: str = "general"  # accounting, regulatory, process, entity, temporal
    source: str = "system"  # system, apollo, user, inferred
    tags: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def matches_scope(
        self, org_id: Optional[str], person_id: Optional[str]
    ) -> bool:
        """Check if this fact applies to the given scope."""
        if self.scope == "global":
            return True
        if self.scope == "industry":
            return True  # Industry facts apply to matching industries
        if self.scope == "org":
            return self.scope_id == org_id
        if self.scope == "person":
            return self.scope_id == person_id
        return False
