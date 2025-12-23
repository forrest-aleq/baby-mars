"""
Birth Persistence
==================

Save birth data to database (atomic write).
Called once at signup, never again.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from ..persistence.beliefs import save_beliefs_batch
from ..persistence.database import get_connection


async def persist_birth(
    person_id: str,
    org_id: str,
    person_data: dict,
    org_data: dict,
    beliefs: list[dict],
    apollo_data: Optional[dict] = None,
) -> bool:
    """
    Persist all birth data atomically.

    One transaction, all or nothing:
    1. UPSERT Organization
    2. CREATE Person
    3. CREATE all Beliefs

    Args:
        person_id: Unique person ID
        org_id: Organization ID
        person_data: Person info (name, email, role, etc.)
        org_data: Org info (name, industry, size)
        beliefs: List of belief dicts to persist
        apollo_data: Raw Apollo enrichment data

    Returns:
        True if successful, False otherwise
    """
    async with get_connection() as conn:
        async with conn.transaction():
            try:
                # 1. Upsert Organization
                await conn.execute(
                    """
                    INSERT INTO organizations (
                        org_id, name, industry, size, settings, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (org_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        industry = EXCLUDED.industry,
                        size = EXCLUDED.size
                """,
                    org_id,
                    org_data.get("name", "Unknown"),
                    org_data.get("industry", "general"),
                    org_data.get("size", "mid_market"),
                    json.dumps(org_data.get("settings", {})),
                    datetime.now(timezone.utc),
                )

                # 2. Insert Person (fail if exists - idempotency)
                await conn.execute(
                    """
                    INSERT INTO persons (
                        person_id, org_id, name, email, role, authority,
                        seniority, department, timezone, apollo_data,
                        birth_mode, salience, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (email) DO NOTHING
                """,
                    person_id,
                    org_id,
                    person_data.get("name", ""),
                    person_data.get("email", ""),
                    person_data.get("role", ""),
                    person_data.get("authority", 0.5),
                    person_data.get("seniority", ""),
                    person_data.get("department", ""),
                    person_data.get("timezone", ""),
                    json.dumps(apollo_data) if apollo_data else None,
                    person_data.get("birth_mode", "standard"),
                    person_data.get("salience", 0.5),
                    datetime.now(timezone.utc),
                )

                # 3. Persist all beliefs
                await save_beliefs_batch(org_id, beliefs)

                return True

            except Exception as e:
                print(f"Birth persistence error: {e}")
                raise  # Re-raise to rollback transaction


async def check_person_exists(email: str) -> bool:
    """Check if person already exists (idempotency check)."""
    async with get_connection() as conn:
        result = await conn.fetchval("SELECT 1 FROM persons WHERE email = $1", email)
        return result is not None


async def init_birth_tables() -> None:
    """Create birth-related tables if they don't exist."""
    async with get_connection() as conn:
        # Organizations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT,
                size TEXT,
                settings JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Persons table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                person_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL REFERENCES organizations(org_id),
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT,
                authority FLOAT DEFAULT 0.5,
                seniority TEXT,
                department TEXT,
                timezone TEXT,
                apollo_data JSONB,
                birth_mode TEXT,
                salience FLOAT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Index for email lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_persons_email
            ON persons(email)
        """)

        # Index for org lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_persons_org
            ON persons(org_id)
        """)
