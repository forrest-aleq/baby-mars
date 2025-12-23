"""
Knowledge Bulk Operations
=========================

Efficient batch operations for knowledge facts.
"""

from datetime import datetime, timezone
from typing import Any, Literal, Optional, cast

from asyncpg import Connection

from ..database import get_connection
from .core import add_fact, replace_fact
from .exceptions import DuplicateFactKeyError
from .models import can_replace_source


async def seed_global_facts(facts: list[dict[str, Any]]) -> int:
    """
    Seed global facts (system init).

    Only inserts if fact_key doesn't already exist.
    Returns count of new facts inserted.
    """
    async with get_connection() as conn:
        count = 0
        for fact in facts:
            existing = await conn.fetchval(
                """
                SELECT 1 FROM knowledge_facts
                WHERE fact_key = $1 AND scope_type = 'global' AND status = 'active'
                """,
                fact["fact_key"],
            )
            if not existing:
                await add_fact(
                    fact_key=fact["fact_key"],
                    statement=fact["statement"],
                    scope_type="global",
                    category=fact.get("category", "accounting"),
                    source_type="system",
                    tags=fact.get("tags", []),
                )
                count += 1
        return count


async def seed_industry_facts(industry: str, facts: list[dict[str, Any]]) -> int:
    """
    Seed facts for an industry.

    Only inserts if fact_key doesn't already exist for this industry.
    """
    async with get_connection() as conn:
        count = 0
        for fact in facts:
            existing = await conn.fetchval(
                """
                SELECT 1 FROM knowledge_facts
                WHERE fact_key = $1 AND scope_type = 'industry'
                AND scope_id = $2 AND status = 'active'
                """,
                fact["fact_key"],
                industry,
            )
            if not existing:
                await add_fact(
                    fact_key=fact["fact_key"],
                    statement=fact["statement"],
                    scope_type="industry",
                    scope_id=industry,
                    category=fact.get("category", "regulatory"),
                    source_type="knowledge_pack",
                    tags=fact.get("tags", []),
                )
                count += 1
        return count


async def set_org_industries(org_id: str, industries: list[str], source: str = "apollo") -> None:
    """Set the industries for an org (used for industry fact resolution)."""
    async with get_connection() as conn:
        await conn.execute("DELETE FROM org_industries WHERE org_id = $1", org_id)

        for i, industry in enumerate(industries):
            await conn.execute(
                """
                INSERT INTO org_industries (org_id, industry, is_primary, source)
                VALUES ($1, $2, $3, $4)
            """,
                org_id,
                industry,
                i == 0,
                source,
            )


async def bulk_import_facts(
    facts: list[dict[str, Any]],
    source_type: Literal["system", "knowledge_pack", "apollo", "admin", "integration"] = "admin",
    on_conflict: Literal["skip", "replace", "error"] = "skip",
) -> dict[str, Any]:
    """
    Efficiently import many facts at once.

    Args:
        facts: List of fact dicts with keys:
            - fact_key (required)
            - statement (required)
            - scope_type (required)
            - scope_id (optional)
            - category (optional, defaults to 'accounting')
            - tags (optional)
            - valid_from (optional)
            - valid_until (optional)
        source_type: Source for all imported facts
        on_conflict: What to do if fact_key already exists in scope:
            - skip: Ignore the new fact
            - replace: Supersede existing with new
            - error: Raise DuplicateFactKeyError

    Returns:
        {"inserted": N, "skipped": N, "replaced": N, "errors": [...]}
    """
    results: dict[str, Any] = {"inserted": 0, "skipped": 0, "replaced": 0, "errors": []}

    async with get_connection() as conn:
        async with conn.transaction():
            for fact in facts:
                try:
                    result = await _import_single_fact(conn, fact, source_type, on_conflict)
                    results[result] += 1
                except DuplicateFactKeyError:
                    raise
                except Exception as e:
                    results["errors"].append(
                        {"fact_key": fact.get("fact_key", "unknown"), "error": str(e)}
                    )

    return results


async def _import_single_fact(
    conn: Connection[Any],
    fact: dict[str, Any],
    source_type: Literal["system", "knowledge_pack", "apollo", "admin", "integration"],
    on_conflict: Literal["skip", "replace", "error"],
) -> str:
    """Import a single fact. Returns 'inserted', 'skipped', or 'replaced'."""
    fact_key = fact["fact_key"]
    scope_type = fact["scope_type"]
    scope_id = fact.get("scope_id")

    existing = await conn.fetchrow(
        """
        SELECT id, source_type FROM knowledge_facts
        WHERE fact_key = $1
        AND scope_type = $2
        AND COALESCE(scope_id, '') = COALESCE($3, '')
        AND status = 'active'
        FOR UPDATE
    """,
        fact_key,
        scope_type,
        scope_id,
    )

    if existing:
        if on_conflict == "skip":
            return "skipped"
        elif on_conflict == "error":
            raise DuplicateFactKeyError(fact_key, scope_type, scope_id)
        elif on_conflict == "replace":
            if not can_replace_source(existing["source_type"], source_type):
                raise ValueError(f"Cannot replace {existing['source_type']} with {source_type}")
            # Cast source_type to the corrected_by_type Literal (user/admin/system/integration)
            corrected_by = cast(
                Literal["user", "admin", "system", "integration"],
                source_type if source_type in ("user", "admin", "system", "integration") else "system",
            )
            await replace_fact(
                old_fact_id=str(existing["id"]),
                new_statement=fact["statement"],
                reason="Bulk import replacement",
                correction_type="source_upgrade",
                corrected_by_type=corrected_by,
            )
            return "replaced"

    await conn.execute(
        """
        INSERT INTO knowledge_facts (
            fact_key, scope_type, scope_id, statement, category,
            source_type, tags, valid_from, valid_until
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """,
        fact_key,
        scope_type,
        scope_id,
        fact["statement"],
        fact.get("category", "accounting"),
        source_type,
        fact.get("tags", []),
        fact.get("valid_from", datetime.now(timezone.utc)),
        fact.get("valid_until"),
    )
    return "inserted"


async def export_facts(
    scope_type: Optional[str] = None,
    scope_id: Optional[str] = None,
    include_superseded: bool = False,
) -> list[dict[str, Any]]:
    """
    Export facts for backup or migration.

    Returns list of fact dicts suitable for bulk_import_facts.
    """
    async with get_connection() as conn:
        conditions = []
        params = []
        param_num = 1

        if not include_superseded:
            conditions.append("status = 'active'")

        if scope_type:
            conditions.append(f"scope_type = ${param_num}")
            params.append(scope_type)
            param_num += 1

        if scope_id:
            conditions.append(f"scope_id = ${param_num}")
            params.append(scope_id)
            param_num += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        rows = await conn.fetch(
            f"""
            SELECT
                fact_key, scope_type, scope_id, statement, category,
                source_type, tags, valid_from, valid_until, status,
                created_at, metadata
            FROM knowledge_facts
            WHERE {where_clause}
            ORDER BY scope_type, scope_id, fact_key, created_at
        """,
            *params,
        )

        return [_row_to_export_dict(r) for r in rows]


def _row_to_export_dict(r: Any) -> dict[str, Any]:
    """Convert database row to export dict."""
    return {
        "fact_key": r["fact_key"],
        "scope_type": r["scope_type"],
        "scope_id": r["scope_id"],
        "statement": r["statement"],
        "category": r["category"],
        "source_type": r["source_type"],
        "tags": r["tags"] or [],
        "valid_from": r["valid_from"].isoformat() if r["valid_from"] else None,
        "valid_until": r["valid_until"].isoformat() if r["valid_until"] else None,
        "status": r["status"],
        "created_at": r["created_at"].isoformat(),
        "metadata": r["metadata"] or {},
    }
