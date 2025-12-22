"""
Knowledge Persistence Layer
============================

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

Source Priority (higher wins when upgrading):
- user: 100 (explicit user statement)
- admin: 90 (admin portal)
- integration: 70 (connected systems)
- apollo: 50 (enrichment API)
- inferred: 30 (derived from patterns)
- system: 10 (seeded at init)
- knowledge_pack: 10 (industry packs)
"""

import json
from datetime import datetime, timezone
from typing import Optional, Literal
from dataclasses import dataclass, asdict
from uuid import UUID

from .database import get_connection


# ============================================================
# EXCEPTIONS
# ============================================================

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


# ============================================================
# SOURCE PRIORITY
# ============================================================

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


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class KnowledgeFact:
    """A knowledge fact from the database."""
    id: str
    fact_key: str
    scope_type: Literal["global", "industry", "org", "person"]
    scope_id: Optional[str]
    statement: str
    category: Literal["accounting", "regulatory", "process", "entity", "temporal", "context"]
    source_type: Literal["system", "knowledge_pack", "apollo", "user", "admin", "inferred", "integration"]
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


# ============================================================
# INITIALIZATION
# ============================================================

async def init_knowledge_tables() -> None:
    """Create knowledge tables if they don't exist."""
    async with get_connection() as conn:
        # Read and execute the SQL schema
        import os
        schema_path = os.path.join(os.path.dirname(__file__), "knowledge_schema.sql")

        # For now, create tables inline (schema file is reference)
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


# ============================================================
# CORE OPERATIONS
# ============================================================

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
        # Get org's industries
        industries = await conn.fetch(
            "SELECT industry FROM org_industries WHERE org_id = $1",
            org_id
        )
        industry_list = [r["industry"] for r in industries]

        # Build the query
        # CRITICAL: Check both valid_from AND valid_until for temporal validity
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

        return [
            KnowledgeFact(
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
            for r in rows
        ]


async def add_fact(
    fact_key: str,
    statement: str,
    scope_type: Literal["global", "industry", "org", "person"],
    category: Literal["accounting", "regulatory", "process", "entity", "temporal", "context"],
    source_type: Literal["system", "knowledge_pack", "apollo", "user", "admin", "inferred", "integration"],
    scope_id: Optional[str] = None,
    source_ref: Optional[dict] = None,
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
        row = await conn.fetchrow("""
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
    correction_type: Literal["factual_error", "outdated", "more_specific", "scope_change", "source_upgrade"],
    corrected_by_type: Literal["user", "admin", "system", "integration"],
    corrected_by_ref: Optional[str] = None,
    force_source_downgrade: bool = False,
) -> str:
    """
    Replace a fact with a new version.

    This is the "replace" mechanism - old fact is superseded, new fact created.
    Full audit trail maintained. Uses row-level locking to prevent race conditions.

    Args:
        old_fact_id: The fact to replace
        new_statement: The new statement text
        reason: Why it's being replaced
        correction_type: Category of correction
        corrected_by_type: Source type of the correction
        corrected_by_ref: Reference to corrector (user_id, etc.)
        force_source_downgrade: Allow replacing higher-priority source (admin override)

    Returns the new fact's ID.

    Raises:
        FactNotFoundError: If fact doesn't exist
        FactAlreadySupersededError: If fact was already replaced (race condition)
        SourcePriorityError: If trying to replace with lower-priority source
    """
    async with get_connection() as conn:
        async with conn.transaction():
            # Get the old fact WITH ROW LOCK to prevent race conditions
            old_fact = await conn.fetchrow(
                "SELECT * FROM knowledge_facts WHERE id = $1 FOR UPDATE",
                old_fact_id
            )

            if not old_fact:
                raise FactNotFoundError(old_fact_id)

            if old_fact["status"] != "active":
                raise FactAlreadySupersededError(old_fact_id, old_fact["status"])

            # Check source priority (unless forced)
            if not force_source_downgrade:
                if not can_replace_source(old_fact["source_type"], corrected_by_type):
                    raise SourcePriorityError(old_fact["source_type"], corrected_by_type)

            # Create new fact
            new_fact_id = await conn.fetchval("""
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

            # Supersede old fact
            await conn.execute("""
                UPDATE knowledge_facts
                SET status = 'superseded',
                    superseded_by = $1,
                    supersession_reason = $2,
                    valid_until = NOW(),
                    updated_at = NOW()
                WHERE id = $3
            """, new_fact_id, reason, old_fact_id)

            # Log the correction
            await conn.execute("""
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
    deleted_by_type: Literal["user", "admin", "system", "integration"],
    deleted_by_ref: Optional[str] = None,
) -> None:
    """
    Soft delete a fact.

    Fact is marked as deleted, not removed. Full audit trail maintained.
    """
    async with get_connection() as conn:
        async with conn.transaction():
            await conn.execute("""
                UPDATE knowledge_facts
                SET status = 'deleted',
                    deleted_at = NOW(),
                    supersession_reason = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, reason, fact_id)

            await conn.execute("""
                INSERT INTO knowledge_corrections (
                    old_fact_id, new_fact_id, corrected_by_type, corrected_by_ref,
                    reason, correction_type
                )
                VALUES ($1, NULL, $2, $3, $4, 'factual_error')
            """, fact_id, deleted_by_type, deleted_by_ref, reason)


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
        rows = await conn.fetch("""
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
        """, fact_key, scope_type, scope_id)

        return [
            {
                "id": str(r["id"]),
                "statement": r["statement"],
                "status": r["status"],
                "source_type": r["source_type"],
                "created_at": r["created_at"].isoformat(),
                "valid_until": r["valid_until"].isoformat() if r["valid_until"] else None,
                "supersession_reason": r["supersession_reason"],
                "version": r["version_num"],
            }
            for r in rows
        ]


# ============================================================
# BULK OPERATIONS
# ============================================================

async def seed_global_facts(facts: list[dict]) -> int:
    """
    Seed global facts (system init).

    Only inserts if fact_key doesn't already exist.
    Returns count of new facts inserted.
    """
    async with get_connection() as conn:
        count = 0
        for fact in facts:
            existing = await conn.fetchval(
                "SELECT 1 FROM knowledge_facts WHERE fact_key = $1 AND scope_type = 'global' AND status = 'active'",
                fact["fact_key"]
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


async def seed_industry_facts(industry: str, facts: list[dict]) -> int:
    """
    Seed facts for an industry.

    Only inserts if fact_key doesn't already exist for this industry.
    """
    async with get_connection() as conn:
        count = 0
        for fact in facts:
            existing = await conn.fetchval(
                "SELECT 1 FROM knowledge_facts WHERE fact_key = $1 AND scope_type = 'industry' AND scope_id = $2 AND status = 'active'",
                fact["fact_key"], industry
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
        # Clear existing
        await conn.execute("DELETE FROM org_industries WHERE org_id = $1", org_id)

        # Insert new
        for i, industry in enumerate(industries):
            await conn.execute("""
                INSERT INTO org_industries (org_id, industry, is_primary, source)
                VALUES ($1, $2, $3, $4)
            """, org_id, industry, i == 0, source)


# ============================================================
# QUERY HELPERS
# ============================================================

async def get_fact_by_key(
    fact_key: str,
    scope_type: str,
    scope_id: Optional[str] = None,
) -> Optional[KnowledgeFact]:
    """Get a specific active fact by key and scope."""
    async with get_connection() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM knowledge_facts
            WHERE fact_key = $1
            AND scope_type = $2
            AND COALESCE(scope_id, '') = COALESCE($3, '')
            AND status = 'active'
        """, fact_key, scope_type, scope_id)

        if not row:
            return None

        return KnowledgeFact(
            id=str(row["id"]),
            fact_key=row["fact_key"],
            scope_type=row["scope_type"],
            scope_id=row["scope_id"],
            statement=row["statement"],
            category=row["category"],
            source_type=row["source_type"],
            source_ref=row["source_ref"] or {},
            status=row["status"],
            tags=row["tags"] or [],
            confidence=row["confidence"],
            created_at=row["created_at"],
            valid_from=row["valid_from"],
            valid_until=row["valid_until"],
        )


async def count_facts_by_scope(org_id: str) -> dict:
    """Get count of active facts by scope for an org."""
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT scope_type, COUNT(*) as count
            FROM knowledge_facts
            WHERE status = 'active'
            AND (
                scope_type = 'global'
                OR (scope_type = 'org' AND scope_id = $1)
            )
            GROUP BY scope_type
        """, org_id)

        return {r["scope_type"]: r["count"] for r in rows}


# ============================================================
# POINT-IN-TIME QUERIES
# ============================================================

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

    Returns facts that were:
    - Created before as_of AND
    - Either still active at as_of OR superseded/deleted after as_of
    """
    async with get_connection() as conn:
        # Get org's industries (as they were at that time - simplified, assumes stable)
        industries = await conn.fetch(
            "SELECT industry FROM org_industries WHERE org_id = $1",
            org_id
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

        return [
            KnowledgeFact(
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
            for r in rows
        ]


# ============================================================
# BULK OPERATIONS (EFFICIENT)
# ============================================================

async def bulk_import_facts(
    facts: list[dict],
    source_type: Literal["system", "knowledge_pack", "apollo", "admin", "integration"] = "admin",
    on_conflict: Literal["skip", "replace", "error"] = "skip",
) -> dict:
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
    results = {"inserted": 0, "skipped": 0, "replaced": 0, "errors": []}

    async with get_connection() as conn:
        async with conn.transaction():
            for fact in facts:
                try:
                    fact_key = fact["fact_key"]
                    scope_type = fact["scope_type"]
                    scope_id = fact.get("scope_id")

                    # Check for existing active fact
                    existing = await conn.fetchrow("""
                        SELECT id, source_type FROM knowledge_facts
                        WHERE fact_key = $1
                        AND scope_type = $2
                        AND COALESCE(scope_id, '') = COALESCE($3, '')
                        AND status = 'active'
                        FOR UPDATE
                    """, fact_key, scope_type, scope_id)

                    if existing:
                        if on_conflict == "skip":
                            results["skipped"] += 1
                            continue
                        elif on_conflict == "error":
                            raise DuplicateFactKeyError(fact_key, scope_type, scope_id)
                        elif on_conflict == "replace":
                            # Check source priority
                            if not can_replace_source(existing["source_type"], source_type):
                                results["errors"].append({
                                    "fact_key": fact_key,
                                    "error": f"Cannot replace {existing['source_type']} with {source_type}"
                                })
                                continue

                            # Supersede existing
                            await replace_fact(
                                old_fact_id=str(existing["id"]),
                                new_statement=fact["statement"],
                                reason="Bulk import replacement",
                                correction_type="source_upgrade",
                                corrected_by_type=source_type,
                            )
                            results["replaced"] += 1
                            continue

                    # Insert new fact
                    await conn.execute("""
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
                    results["inserted"] += 1

                except DuplicateFactKeyError:
                    raise
                except Exception as e:
                    results["errors"].append({
                        "fact_key": fact.get("fact_key", "unknown"),
                        "error": str(e)
                    })

    return results


async def export_facts(
    scope_type: Optional[str] = None,
    scope_id: Optional[str] = None,
    include_superseded: bool = False,
) -> list[dict]:
    """
    Export facts for backup or migration.

    Args:
        scope_type: Filter by scope type (None = all)
        scope_id: Filter by scope ID (None = all)
        include_superseded: Include superseded/deleted facts

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

        rows = await conn.fetch(f"""
            SELECT
                fact_key, scope_type, scope_id, statement, category,
                source_type, tags, valid_from, valid_until, status,
                created_at, metadata
            FROM knowledge_facts
            WHERE {where_clause}
            ORDER BY scope_type, scope_id, fact_key, created_at
        """, *params)

        return [
            {
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
            for r in rows
        ]
