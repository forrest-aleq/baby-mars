"""
Knowledge Core Operations
=========================

CRUD operations for knowledge facts.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from ..database import get_connection
from .exceptions import (
    FactAlreadySupersededError,
    FactNotFoundError,
    SourcePriorityError,
)
from .models import (
    CategoryType,
    CorrectionType,
    CorrectorType,
    KnowledgeFact,
    ScopeType,
    SourceType,
    can_replace_source,
)


async def init_knowledge_tables() -> None:
    """Create knowledge tables if they don't exist."""
    async with get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_facts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                fact_key TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_id TEXT,
                statement TEXT NOT NULL,
                category TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_ref JSONB DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'active',
                superseded_by UUID,
                supersedes UUID,
                supersession_reason TEXT,
                valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                valid_until TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                deleted_at TIMESTAMPTZ,
                tags TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                confidence FLOAT DEFAULT 1.0
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS org_industries (
                org_id TEXT NOT NULL,
                industry TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                source TEXT NOT NULL,
                confidence FLOAT DEFAULT 1.0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (org_id, industry)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_corrections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                old_fact_id UUID NOT NULL,
                new_fact_id UUID,
                corrected_by_type TEXT NOT NULL,
                corrected_by_ref TEXT,
                reason TEXT NOT NULL,
                correction_type TEXT NOT NULL,
                context JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_scope
            ON knowledge_facts(scope_type, scope_id)
            WHERE status = 'active'
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_org
            ON knowledge_facts(scope_id)
            WHERE scope_type = 'org' AND status = 'active'
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_org_industries_org
            ON org_industries(org_id)
        """)


async def load_facts_for_context(
    org_id: str,
    person_id: Optional[str] = None,
    max_facts: int = 30,
) -> list[KnowledgeFact]:
    """
    Load all relevant facts for a mount context.

    This is THE mount query - called on every message.
    Returns facts from all applicable scopes, narrower first.
    """
    async with get_connection() as conn:
        industries = await conn.fetch(
            "SELECT industry FROM org_industries WHERE org_id = $1", org_id
        )
        industry_list = [r["industry"] for r in industries]

        query = """
            SELECT
                id, fact_key, scope_type, scope_id, statement, category,
                source_type, source_ref, status, tags, confidence,
                created_at, valid_from, valid_until
            FROM knowledge_facts
            WHERE status = 'active'
            AND valid_from <= NOW()
            AND (valid_until IS NULL OR valid_until > NOW())
            AND (
                scope_type = 'global'
                OR (scope_type = 'industry' AND scope_id = ANY($1))
                OR (scope_type = 'org' AND scope_id = $2)
                OR (scope_type = 'person' AND scope_id = $3)
            )
            ORDER BY
                CASE scope_type
                    WHEN 'person' THEN 1
                    WHEN 'org' THEN 2
                    WHEN 'industry' THEN 3
                    WHEN 'global' THEN 4
                END,
                category,
                created_at DESC
            LIMIT $4
        """

        rows = await conn.fetch(query, industry_list, org_id, person_id, max_facts)
        return [_row_to_fact(r) for r in rows]


async def add_fact(
    fact_key: str,
    statement: str,
    scope_type: ScopeType,
    category: CategoryType,
    source_type: SourceType,
    scope_id: Optional[str] = None,
    source_ref: Optional[dict[str, Any]] = None,
    tags: Optional[list[str]] = None,
    confidence: float = 1.0,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
) -> str:
    """
    Add a new knowledge fact.

    Returns the new fact's ID.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO knowledge_facts (
                fact_key, scope_type, scope_id, statement, category,
                source_type, source_ref, tags, confidence, valid_from, valid_until
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """,
            fact_key,
            scope_type,
            scope_id,
            statement,
            category,
            source_type,
            json.dumps(source_ref or {}),
            tags or [],
            confidence,
            valid_from or datetime.now(timezone.utc),
            valid_until,
        )
        return str(row["id"])


async def replace_fact(
    old_fact_id: str,
    new_statement: str,
    reason: str,
    correction_type: CorrectionType,
    corrected_by_type: CorrectorType,
    corrected_by_ref: Optional[str] = None,
    force_source_downgrade: bool = False,
) -> str:
    """
    Replace a fact with a new version.

    Uses row-level locking to prevent race conditions.
    Returns the new fact's ID.
    """
    async with get_connection() as conn:
        async with conn.transaction():
            old_fact = await conn.fetchrow(
                "SELECT * FROM knowledge_facts WHERE id = $1 FOR UPDATE", old_fact_id
            )

            if not old_fact:
                raise FactNotFoundError(old_fact_id)

            if old_fact["status"] != "active":
                raise FactAlreadySupersededError(old_fact_id, old_fact["status"])

            if not force_source_downgrade:
                if not can_replace_source(old_fact["source_type"], corrected_by_type):
                    raise SourcePriorityError(old_fact["source_type"], corrected_by_type)

            new_fact_id = await conn.fetchval(
                """
                INSERT INTO knowledge_facts (
                    fact_key, scope_type, scope_id, statement, category,
                    source_type, source_ref, supersedes, tags, metadata, confidence
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """,
                old_fact["fact_key"],
                old_fact["scope_type"],
                old_fact["scope_id"],
                new_statement,
                old_fact["category"],
                corrected_by_type,
                json.dumps({"correction_of": old_fact_id, "corrected_by": corrected_by_ref}),
                old_fact_id,
                old_fact["tags"],
                old_fact["metadata"],
                old_fact["confidence"],
            )

            await conn.execute(
                """
                UPDATE knowledge_facts
                SET status = 'superseded',
                    superseded_by = $1,
                    supersession_reason = $2,
                    valid_until = NOW(),
                    updated_at = NOW()
                WHERE id = $3
            """,
                new_fact_id,
                reason,
                old_fact_id,
            )

            await conn.execute(
                """
                INSERT INTO knowledge_corrections (
                    old_fact_id, new_fact_id, corrected_by_type, corrected_by_ref,
                    reason, correction_type
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                old_fact_id,
                new_fact_id,
                corrected_by_type,
                corrected_by_ref,
                reason,
                correction_type,
            )

            return str(new_fact_id)


async def delete_fact(
    fact_id: str,
    reason: str,
    deleted_by_type: CorrectorType,
    deleted_by_ref: Optional[str] = None,
) -> None:
    """Soft delete a fact with audit trail."""
    async with get_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE knowledge_facts
                SET status = 'deleted',
                    deleted_at = NOW(),
                    supersession_reason = $1,
                    updated_at = NOW()
                WHERE id = $2
            """,
                reason,
                fact_id,
            )

            await conn.execute(
                """
                INSERT INTO knowledge_corrections (
                    old_fact_id, new_fact_id, corrected_by_type, corrected_by_ref,
                    reason, correction_type
                )
                VALUES ($1, NULL, $2, $3, $4, 'factual_error')
            """,
                fact_id,
                deleted_by_type,
                deleted_by_ref,
                reason,
            )


def _row_to_fact(r: Any) -> KnowledgeFact:
    """Convert database row to KnowledgeFact."""
    return KnowledgeFact(
        id=str(r["id"]),
        fact_key=r["fact_key"],
        scope_type=r["scope_type"],
        scope_id=r["scope_id"],
        statement=r["statement"],
        category=r["category"],
        source_type=r["source_type"],
        source_ref=r["source_ref"] or {},
        status=r["status"],
        tags=r["tags"] or [],
        confidence=r["confidence"],
        created_at=r["created_at"],
        valid_from=r["valid_from"],
        valid_until=r["valid_until"],
    )
