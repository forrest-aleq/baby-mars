"""
Database Connection and Setup
==============================

Single DATABASE_URL for both LangGraph checkpoints and belief storage.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg

# Connection pool singleton
_pool: Optional[asyncpg.Pool] = None


def get_database_url() -> str:
    """Get database URL from environment"""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql://user:pass@localhost:5432/baby_mars"
        )
    return url


async def init_database() -> None:
    """
    Initialize database: create tables if not exist.
    Call this on application startup.
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Beliefs table (one row per belief)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS beliefs (
                belief_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                statement TEXT NOT NULL,
                category TEXT NOT NULL,
                strength FLOAT NOT NULL DEFAULT 0.5,
                context_key TEXT NOT NULL DEFAULT '*|*|*',
                context_states JSONB NOT NULL DEFAULT '{}',
                supports TEXT[] NOT NULL DEFAULT '{}',
                supported_by TEXT[] NOT NULL DEFAULT '{}',
                support_weights JSONB NOT NULL DEFAULT '{}',
                last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                is_end_memory_influenced BOOLEAN NOT NULL DEFAULT FALSE,
                peak_intensity FLOAT NOT NULL DEFAULT 0.0,
                invalidation_threshold FLOAT NOT NULL DEFAULT 0.75,
                is_distrusted BOOLEAN NOT NULL DEFAULT FALSE,
                moral_violation_count INTEGER NOT NULL DEFAULT 0,
                immutable BOOLEAN NOT NULL DEFAULT FALSE,
                tags TEXT[] NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Index for fast org lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_beliefs_org_id
            ON beliefs(org_id)
        """)

        # Index for category queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_beliefs_org_category
            ON beliefs(org_id, category)
        """)

        # Index for strength-based queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_beliefs_org_strength
            ON beliefs(org_id, strength DESC)
        """)

        # Memories table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                outcome TEXT NOT NULL,
                emotional_intensity FLOAT NOT NULL DEFAULT 0.5,
                is_end_memory BOOLEAN NOT NULL DEFAULT FALSE,
                related_beliefs TEXT[] NOT NULL DEFAULT '{}',
                related_persons TEXT[] NOT NULL DEFAULT '{}',
                context_key TEXT NOT NULL DEFAULT '*|*|*',
                difficulty_level INTEGER NOT NULL DEFAULT 3,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Index for memory lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_org_id
            ON memories(org_id)
        """)

        # Feedback events table (immutable audit log)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_events (
                event_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                trigger TEXT NOT NULL,
                outcome_type TEXT NOT NULL,
                belief_updates JSONB NOT NULL DEFAULT '[]',
                context_key TEXT NOT NULL DEFAULT '*|*|*',
                supervision_mode TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_events_org_id
            ON feedback_events(org_id)
        """)


async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            get_database_url(),
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    """Close connection pool (call on shutdown)"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """Get a database connection from pool"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
