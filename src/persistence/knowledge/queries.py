"""
Knowledge Queries
=================

Query helpers and point-in-time queries for knowledge facts.
"""

from datetime import datetime
from typing import Optional

from ..database import get_connection
from .core import _row_to_fact
from .models import KnowledgeFact


async def get_fact_by_key(
    fact_key: str,
    scope_type: str,
    scope_id: Optional[str] = None,
) -> Optional[KnowledgeFact]:
    """Get a specific active fact by key and scope."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM knowledge_facts
            WHERE fact_key = $1
            AND scope_type = $2
            AND COALESCE(scope_id, '') = COALESCE($3, '')
            AND status = 'active'
        """,
            fact_key,
            scope_type,
            scope_id,
        )

        if not row:
            return None

        return _row_to_fact(row)


async def count_facts_by_scope(org_id: str) -> dict:
    """Get count of active facts by scope for an org."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT scope_type, COUNT(*) as count
            FROM knowledge_facts
            WHERE status = 'active'
            AND (
                scope_type = 'global'
                OR (scope_type = 'org' AND scope_id = $1)
            )
            GROUP BY scope_type
        """,
            org_id,
        )

        return {r["scope_type"]: r["count"] for r in rows}


async def get_fact_history(
    fact_key: str,
    scope_type: str,
    scope_id: Optional[str] = None,
) -> list[dict]:
    """
    Get the full history of a fact (all versions).

    Follows the supersession chain to show how a fact evolved.
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            WITH RECURSIVE fact_chain AS (
                SELECT f.*, 1::BIGINT as version_num
                FROM knowledge_facts f
                WHERE f.fact_key = $1
                AND f.scope_type = $2
                AND COALESCE(f.scope_id, '') = COALESCE($3, '')
                AND f.superseded_by IS NULL

                UNION ALL

                SELECT f.*, fc.version_num + 1
                FROM knowledge_facts f
                JOIN fact_chain fc ON f.superseded_by = fc.id
            )
            SELECT
                id, statement, status, source_type, created_at,
                valid_until, supersession_reason, version_num
            FROM fact_chain
            ORDER BY version_num ASC
        """,
            fact_key,
            scope_type,
            scope_id,
        )

        return [_row_to_history_dict(r) for r in rows]


async def load_facts_known_at(
    org_id: str,
    as_of: datetime,
    person_id: Optional[str] = None,
    max_facts: int = 30,
) -> list[KnowledgeFact]:
    """
    Load facts as they were known at a specific point in time.

    This is critical for:
    - Audit trails ("what did the system know when it made that decision?")
    - Debugging ("why did it do X on Tuesday?")
    - Compliance ("prove what facts were active during that period")
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
            WHERE created_at <= $5
            AND valid_from <= $5
            AND (
                -- Still active now (wasn't superseded/deleted)
                (status = 'active' AND (valid_until IS NULL OR valid_until > $5))
                -- OR was superseded/deleted AFTER our point in time
                OR (status IN ('superseded', 'deleted') AND updated_at > $5)
            )
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

        rows = await conn.fetch(query, industry_list, org_id, person_id, max_facts, as_of)
        return [_row_to_fact(r) for r in rows]


def _row_to_history_dict(r: dict) -> dict:
    """Convert database row to history dict."""
    return {
        "id": str(r["id"]),
        "statement": r["statement"],
        "status": r["status"],
        "source_type": r["source_type"],
        "created_at": r["created_at"].isoformat(),
        "valid_until": r["valid_until"].isoformat() if r["valid_until"] else None,
        "supersession_reason": r["supersession_reason"],
        "version": r["version_num"],
    }
