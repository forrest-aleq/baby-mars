"""
Database Connection and Setup
==============================

Single DATABASE_URL for both LangGraph checkpoints and belief storage.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg
from asyncpg import Connection

# Load .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Connection pool singleton with lock for thread safety
_pool: Optional[asyncpg.Pool] = None
_pool_lock: asyncio.Lock = asyncio.Lock()


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

        # Notes table (TTL-based queue from Paper #8)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                note_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                ttl_hours INTEGER NOT NULL DEFAULT 24,
                priority FLOAT NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT 'system',
                context JSONB NOT NULL DEFAULT '{}'
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_org_id
            ON notes(org_id)
        """)

        # Scheduled triggers table (SYSTEM_PULSE)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_triggers (
                trigger_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                user_id TEXT,
                trigger_type TEXT NOT NULL,
                config JSONB NOT NULL,
                action TEXT NOT NULL,
                action_context JSONB NOT NULL DEFAULT '{}',
                description TEXT NOT NULL DEFAULT '',
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                last_fired TIMESTAMPTZ,
                next_fire TIMESTAMPTZ,
                fire_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_by TEXT NOT NULL DEFAULT 'system'
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_triggers_org_id
            ON scheduled_triggers(org_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_triggers_enabled
            ON scheduled_triggers(org_id, enabled)
        """)

        # ============================================================
        # RAPPORT TRACKING
        # ============================================================
        # Tracks relationship state between Aleq and each person.
        # This is what makes Aleq feel human - remembering people
        # and how the relationship has developed over time.

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS rapport (
                rapport_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                person_id TEXT NOT NULL,
                person_name TEXT NOT NULL,

                -- Core rapport metrics (0.0 to 1.0)
                rapport_level FLOAT NOT NULL DEFAULT 0.3,
                trust_level FLOAT NOT NULL DEFAULT 0.3,
                familiarity FLOAT NOT NULL DEFAULT 0.0,

                -- Interaction tracking
                interaction_count INTEGER NOT NULL DEFAULT 0,
                positive_interactions INTEGER NOT NULL DEFAULT 0,
                negative_interactions INTEGER NOT NULL DEFAULT 0,
                last_interaction TIMESTAMPTZ,
                first_interaction TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                -- Relationship memory
                memorable_moments JSONB NOT NULL DEFAULT '[]',
                topics_discussed JSONB NOT NULL DEFAULT '{}',
                preferences_learned JSONB NOT NULL DEFAULT '{}',
                inside_references JSONB NOT NULL DEFAULT '[]',

                -- Communication style adaptation
                preferred_formality TEXT DEFAULT 'casual',
                preferred_verbosity TEXT DEFAULT 'concise',
                humor_receptivity FLOAT NOT NULL DEFAULT 0.5,

                -- First impression record
                first_impression_given BOOLEAN NOT NULL DEFAULT FALSE,
                first_impression_text TEXT,
                first_impression_at TIMESTAMPTZ,

                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                UNIQUE(org_id, person_id)
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rapport_org_id
            ON rapport(org_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rapport_person_id
            ON rapport(org_id, person_id)
        """)


async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool (thread-safe with double-check locking)"""
    global _pool
    if _pool is None:
        async with _pool_lock:
            # Double-check after acquiring lock
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
async def get_connection() -> AsyncIterator[Connection[Any]]:
    """Get a database connection from pool"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
