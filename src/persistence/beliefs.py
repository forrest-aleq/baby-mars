"""
Belief Persistence
===================

Save and load beliefs from Postgres.
One row per belief for queryability.
"""

import json
from typing import Optional
from datetime import datetime

from .database import get_connection


# ============================================================
# SHARED SQL AND HELPERS
# ============================================================

_UPSERT_SQL = """
    INSERT INTO beliefs (
        belief_id, org_id, statement, category, strength,
        context_key, context_states, supports, supported_by,
        support_weights, last_updated, success_count, failure_count,
        is_end_memory_influenced, peak_intensity, invalidation_threshold,
        is_distrusted, moral_violation_count, immutable, tags
    ) VALUES (
        $1, $2, $3, $4, $5,
        $6, $7, $8, $9,
        $10, $11, $12, $13,
        $14, $15, $16,
        $17, $18, $19, $20
    )
    ON CONFLICT (belief_id) DO UPDATE SET
        statement = EXCLUDED.statement,
        category = EXCLUDED.category,
        strength = EXCLUDED.strength,
        context_key = EXCLUDED.context_key,
        context_states = EXCLUDED.context_states,
        supports = EXCLUDED.supports,
        supported_by = EXCLUDED.supported_by,
        support_weights = EXCLUDED.support_weights,
        last_updated = EXCLUDED.last_updated,
        success_count = EXCLUDED.success_count,
        failure_count = EXCLUDED.failure_count,
        is_end_memory_influenced = EXCLUDED.is_end_memory_influenced,
        peak_intensity = EXCLUDED.peak_intensity,
        invalidation_threshold = EXCLUDED.invalidation_threshold,
        is_distrusted = EXCLUDED.is_distrusted,
        moral_violation_count = EXCLUDED.moral_violation_count,
        immutable = EXCLUDED.immutable,
        tags = EXCLUDED.tags
"""


def _prepare_belief_params(org_id: str, belief: dict) -> tuple:
    """Prepare parameters for belief upsert query"""
    return (
        belief.get("belief_id"),
        org_id,
        belief.get("statement", ""),
        belief.get("category", "competence"),
        belief.get("strength", 0.5),
        belief.get("context_key", "*|*|*"),
        json.dumps(belief.get("context_states", {})),
        belief.get("supports", []),
        belief.get("supported_by", []),
        json.dumps(belief.get("support_weights", {})),
        datetime.fromisoformat(belief.get("last_updated", datetime.now().isoformat())),
        belief.get("success_count", 0),
        belief.get("failure_count", 0),
        belief.get("is_end_memory_influenced", False),
        belief.get("peak_intensity", 0.0),
        belief.get("invalidation_threshold", 0.75),
        belief.get("is_distrusted", False),
        belief.get("moral_violation_count", 0),
        belief.get("immutable", False),
        belief.get("tags", []),
    )


def _row_to_belief(row) -> dict:
    """Convert database row to belief dict"""
    return {
        "belief_id": row["belief_id"],
        "statement": row["statement"],
        "category": row["category"],
        "strength": row["strength"],
        "context_key": row["context_key"],
        "context_states": json.loads(row["context_states"]) if row["context_states"] else {},
        "supports": list(row["supports"]) if row["supports"] else [],
        "supported_by": list(row["supported_by"]) if row["supported_by"] else [],
        "support_weights": json.loads(row["support_weights"]) if row["support_weights"] else {},
        "last_updated": row["last_updated"].isoformat() if row["last_updated"] else None,
        "success_count": row["success_count"],
        "failure_count": row["failure_count"],
        "is_end_memory_influenced": row["is_end_memory_influenced"],
        "peak_intensity": row["peak_intensity"],
        "invalidation_threshold": row["invalidation_threshold"],
        "is_distrusted": row["is_distrusted"],
        "moral_violation_count": row["moral_violation_count"],
        "immutable": row["immutable"],
        "tags": list(row["tags"]) if row["tags"] else [],
    }


# ============================================================
# SAVE FUNCTIONS
# ============================================================

async def save_belief(org_id: str, belief: dict) -> None:
    """
    Save or update a belief in the database.
    Called after every belief update for durability.
    """
    async with get_connection() as conn:
        await conn.execute(_UPSERT_SQL, *_prepare_belief_params(org_id, belief))


async def save_belief_with_conn(conn, org_id: str, belief: dict) -> None:
    """Save belief using existing connection (for transactions)"""
    await conn.execute(_UPSERT_SQL, *_prepare_belief_params(org_id, belief))


async def save_beliefs_batch(org_id: str, beliefs: list[dict]) -> None:
    """Save multiple beliefs in a single transaction"""
    async with get_connection() as conn:
        async with conn.transaction():
            for belief in beliefs:
                await save_belief_with_conn(conn, org_id, belief)


# ============================================================
# LOAD FUNCTIONS
# ============================================================

async def load_beliefs_for_org(org_id: str) -> list[dict]:
    """
    Load all beliefs for an organization.
    Used on cache miss to populate in-memory graph.
    """
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT
                belief_id, statement, category, strength,
                context_key, context_states, supports, supported_by,
                support_weights, last_updated, success_count, failure_count,
                is_end_memory_influenced, peak_intensity, invalidation_threshold,
                is_distrusted, moral_violation_count, immutable, tags
            FROM beliefs
            WHERE org_id = $1
            ORDER BY strength DESC
        """, org_id)

        return [_row_to_belief(row) for row in rows]


async def get_beliefs_by_category(
    org_id: str,
    category: str,
    min_strength: float = 0.0,
    limit: int = 50
) -> list[dict]:
    """Get beliefs filtered by category and minimum strength"""
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT
                belief_id, statement, category, strength,
                context_key, context_states, supports, supported_by,
                support_weights, last_updated, success_count, failure_count,
                is_end_memory_influenced, peak_intensity, invalidation_threshold,
                is_distrusted, moral_violation_count, immutable, tags
            FROM beliefs
            WHERE org_id = $1
              AND category = $2
              AND strength >= $3
            ORDER BY strength DESC
            LIMIT $4
        """, org_id, category, min_strength, limit)

        return [_row_to_belief(row) for row in rows]


# ============================================================
# DELETE FUNCTION
# ============================================================

async def delete_belief(org_id: str, belief_id: str) -> bool:
    """Delete a belief (rare - usually just update strength to 0)"""
    async with get_connection() as conn:
        result = await conn.execute("""
            DELETE FROM beliefs
            WHERE org_id = $1 AND belief_id = $2
        """, org_id, belief_id)
        return result == "DELETE 1"
