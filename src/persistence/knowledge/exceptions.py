"""
Knowledge Exceptions
====================

Exception classes for knowledge operations.
"""

from typing import Optional


class KnowledgeError(Exception):
    """Base exception for knowledge operations."""

    pass


class FactNotFoundError(KnowledgeError):
    """Raised when a fact is not found."""

    def __init__(self, fact_id: str):
        self.fact_id = fact_id
        super().__init__(f"Fact not found: {fact_id}")


class FactAlreadySupersededError(KnowledgeError):
    """Raised when trying to replace an already-superseded fact."""

    def __init__(self, fact_id: str, current_status: str):
        self.fact_id = fact_id
        self.current_status = current_status
        super().__init__(f"Cannot replace fact {fact_id}: already {current_status}")


class SourcePriorityError(KnowledgeError):
    """Raised when trying to replace with lower-priority source."""

    def __init__(self, old_source: str, new_source: str):
        self.old_source = old_source
        self.new_source = new_source
        super().__init__(f"Cannot replace {old_source} source with {new_source} (lower priority)")


class DuplicateFactKeyError(KnowledgeError):
    """Raised when inserting a duplicate active fact key in same scope."""

    def __init__(self, fact_key: str, scope_type: str, scope_id: Optional[str]):
        self.fact_key = fact_key
        self.scope_type = scope_type
        self.scope_id = scope_id
        super().__init__(f"Active fact already exists: {fact_key} in {scope_type}/{scope_id}")
