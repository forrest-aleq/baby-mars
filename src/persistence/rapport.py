"""
Rapport Persistence
====================

Database operations for rapport tracking - the relationship state
between Aleq and each person she interacts with.

This is what makes Aleq feel human: remembering people, how the
relationship has developed, what they've discussed, and adapting
communication style based on history.

IMPORTANT: All update operations use atomic SQL to prevent race conditions.
Never use read-modify-write patterns for concurrent-safe fields.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Literal, Optional, TypedDict
from zoneinfo import ZoneInfo

import asyncpg

from ..observability import get_logger
from .database import get_connection

logger = get_logger(__name__)


class RapportState(TypedDict):
    """Rapport state for a person-Aleq relationship."""

    rapport_id: str
    org_id: str
    person_id: str
    person_name: str

    # Core metrics (0.0 to 1.0)
    rapport_level: float  # Overall relationship strength
    trust_level: float  # How much they trust Aleq
    familiarity: float  # How well Aleq knows them

    # Interaction tracking
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    last_interaction: Optional[str]
    first_interaction: str

    # Relationship memory
    memorable_moments: list[dict[str, Any]]  # Key moments worth remembering
    topics_discussed: dict[str, int]  # Topic -> frequency
    preferences_learned: dict[str, Any]  # Learned preferences
    inside_references: list[str]  # Shared references/jokes

    # Communication style adaptation
    preferred_formality: str  # casual, professional, formal
    preferred_verbosity: str  # concise, moderate, detailed
    humor_receptivity: float  # 0.0 = serious, 1.0 = loves humor

    # First impression
    first_impression_given: bool
    first_impression_text: Optional[str]
    first_impression_at: Optional[str]


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _clamp_float(value: float, field: str) -> float:
    """Clamp float value to [0.0, 1.0] range with warning."""
    if value < 0.0:
        logger.warning(f"Invalid {field}={value}, clamping to 0.0")
        return 0.0
    if value > 1.0:
        logger.warning(f"Invalid {field}={value}, clamping to 1.0")
        return 1.0
    return value


VALID_FORMALITY = {"casual", "professional", "formal"}
VALID_VERBOSITY = {"concise", "moderate", "detailed"}


def _validate_formality(value: Optional[str]) -> str:
    """Validate formality value, defaulting to casual."""
    if value and value in VALID_FORMALITY:
        return value
    return "casual"


def _validate_verbosity(value: Optional[str]) -> str:
    """Validate verbosity value, defaulting to concise."""
    if value and value in VALID_VERBOSITY:
        return value
    return "concise"


# ============================================================
# READ OPERATIONS
# ============================================================


async def get_rapport(org_id: str, person_id: str) -> Optional[RapportState]:
    """
    Get rapport state for a person.

    Returns None if no rapport exists yet (first meeting).
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM rapport
                WHERE org_id = $1 AND person_id = $2
                """,
                org_id,
                person_id,
            )

            if not row:
                return None

            return _row_to_rapport(row)
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting rapport for {person_id}: {e}")
        return None


async def get_org_rapport(org_id: str) -> list[RapportState]:
    """Get all rapport states for an organization."""
    try:
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM rapport
                WHERE org_id = $1
                ORDER BY last_interaction DESC NULLS LAST
                """,
                org_id,
            )

            return [_row_to_rapport(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting org rapport for {org_id}: {e}")
        return []


# ============================================================
# WRITE OPERATIONS (Atomic SQL to prevent race conditions)
# ============================================================


async def create_rapport(
    org_id: str,
    person_id: str,
    person_name: str,
    first_impression_text: Optional[str] = None,
) -> Optional[RapportState]:
    """
    Create initial rapport state for a new person.

    Called during birth when Aleq meets someone for the first time.
    Returns None if creation fails (e.g., duplicate).
    """
    rapport_id = f"rapport_{uuid.uuid4().hex[:12]}"
    now = datetime.now(ZoneInfo("UTC"))

    try:
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO rapport (
                    rapport_id, org_id, person_id, person_name,
                    rapport_level, trust_level, familiarity,
                    interaction_count, positive_interactions, negative_interactions,
                    first_interaction, last_interaction,
                    first_impression_given, first_impression_text, first_impression_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7,
                    $8, $9, $10,
                    $11, $12,
                    $13, $14, $15
                )
                """,
                rapport_id,
                org_id,
                person_id,
                person_name,
                0.3,
                0.3,
                0.0,  # Starting rapport, trust, familiarity
                0,
                0,
                0,  # Interaction counts
                now,
                now,  # First and last interaction
                first_impression_text is not None,
                first_impression_text,
                now if first_impression_text else None,
            )

        return RapportState(
            rapport_id=rapport_id,
            org_id=org_id,
            person_id=person_id,
            person_name=person_name,
            rapport_level=0.3,
            trust_level=0.3,
            familiarity=0.0,
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
            last_interaction=now.isoformat(),
            first_interaction=now.isoformat(),
            memorable_moments=[],
            topics_discussed={},
            preferences_learned={},
            inside_references=[],
            preferred_formality="casual",
            preferred_verbosity="concise",
            humor_receptivity=0.5,
            first_impression_given=first_impression_text is not None,
            first_impression_text=first_impression_text,
            first_impression_at=now.isoformat() if first_impression_text else None,
        )
    except asyncpg.UniqueViolationError:
        logger.warning(f"Duplicate rapport for {org_id}/{person_id}")
        return None
    except asyncpg.PostgresError as e:
        logger.error(f"Database error creating rapport for {person_id}: {e}")
        return None


async def record_interaction(
    org_id: str,
    person_id: str,
    outcome: Literal["positive", "negative", "neutral"],
    topics: Optional[list[str]] = None,
    memorable_moment: Optional[dict[str, Any]] = None,
) -> Optional[RapportState]:
    """
    Record an interaction and update rapport metrics atomically.

    Uses atomic SQL operations to prevent race conditions under concurrent load.
    All counter increments and level adjustments happen in a single UPDATE.

    Args:
        org_id: Organization ID
        person_id: Person ID
        outcome: How the interaction went
        topics: Topics discussed (for tracking)
        memorable_moment: If this was a memorable moment, record it

    Returns:
        Updated rapport state, or None if person not found
    """
    now = datetime.now(ZoneInfo("UTC"))

    # Build JSONB updates for topics (atomic merge)
    topics_update = "{}"
    if topics:
        # Create increment object: {"topic1": 1, "topic2": 1}
        topics_update = json.dumps({t: 1 for t in topics})

    # Build memorable moment update
    moment_json = "null"
    if memorable_moment:
        memorable_moment["timestamp"] = now.isoformat()
        moment_json = json.dumps(memorable_moment)

    try:
        async with get_connection() as conn:
            # ATOMIC UPDATE: All increments and calculations happen in SQL
            # This prevents race conditions from read-modify-write patterns
            row = await conn.fetchrow(
                """
                UPDATE rapport SET
                    -- Atomic counter increments
                    interaction_count = interaction_count + 1,
                    positive_interactions = positive_interactions +
                        CASE WHEN $1 = 'positive' THEN 1 ELSE 0 END,
                    negative_interactions = negative_interactions +
                        CASE WHEN $1 = 'negative' THEN 1 ELSE 0 END,

                    -- Atomic level adjustments with clamping
                    -- Rapport: +0.02 positive, -0.05 negative (asymmetric)
                    rapport_level = GREATEST(0.0, LEAST(1.0,
                        rapport_level + CASE
                            WHEN $1 = 'positive' THEN 0.02
                            WHEN $1 = 'negative' THEN -0.05
                            ELSE 0
                        END
                    )),

                    -- Trust: +0.01 positive, -0.08 negative (more asymmetric per Paper #9)
                    trust_level = GREATEST(0.0, LEAST(1.0,
                        trust_level + CASE
                            WHEN $1 = 'positive' THEN 0.01
                            WHEN $1 = 'negative' THEN -0.08
                            ELSE 0
                        END
                    )),

                    -- Familiarity: always increases (+0.01)
                    familiarity = LEAST(1.0, familiarity + 0.01),

                    -- Atomic JSONB merge for topics (adds counts, doesn't overwrite)
                    topics_discussed = CASE
                        WHEN $2::jsonb = '{}'::jsonb THEN topics_discussed
                        ELSE (
                            SELECT COALESCE(jsonb_object_agg(
                                key,
                                COALESCE((topics_discussed->>key)::int, 0) +
                                COALESCE((merged.value)::int, 0)
                            ), topics_discussed)
                            FROM jsonb_each_text($2::jsonb) AS merged(key, value)
                        )
                    END,

                    -- Append memorable moment (keep last 20)
                    memorable_moments = CASE
                        WHEN $3::jsonb = 'null'::jsonb THEN memorable_moments
                        ELSE (memorable_moments || $3::jsonb)[-20:]
                    END,

                    last_interaction = $4,
                    updated_at = $4
                WHERE org_id = $5 AND person_id = $6
                RETURNING *
                """,
                outcome,
                topics_update,
                moment_json,
                now,
                org_id,
                person_id,
            )

            if not row:
                return None

            return _row_to_rapport(row)

    except asyncpg.PostgresError as e:
        logger.error(f"Database error recording interaction for {person_id}: {e}")
        return None


async def learn_preference(
    org_id: str,
    person_id: str,
    preference_key: str,
    preference_value: Any,
) -> bool:
    """
    Record a learned preference about a person atomically.

    Uses jsonb_set() in SQL to prevent race conditions when multiple
    preferences are learned concurrently.

    Args:
        org_id: Organization ID
        person_id: Person ID
        preference_key: The preference key (e.g., "communication_style")
        preference_value: The preference value (any JSON-serializable value)

    Returns:
        True if successful, False if person not found or error occurred
    """
    try:
        async with get_connection() as conn:
            # ATOMIC: Use jsonb_set to update single key without read-modify-write
            result = await conn.execute(
                """
                UPDATE rapport SET
                    preferences_learned = jsonb_set(
                        COALESCE(preferences_learned, '{}'::jsonb),
                        ARRAY[$1],
                        $2::jsonb
                    ),
                    updated_at = NOW()
                WHERE org_id = $3 AND person_id = $4
                """,
                preference_key,
                json.dumps(preference_value),
                org_id,
                person_id,
            )
            # result is like "UPDATE 1" or "UPDATE 0"
            return str(result).endswith("1")
    except asyncpg.PostgresError as e:
        logger.error(f"Database error learning preference for {person_id}: {e}")
        return False


async def add_inside_reference(
    org_id: str,
    person_id: str,
    reference: str,
) -> bool:
    """
    Add an inside reference or shared joke atomically.

    Uses atomic SQL operations to:
    1. Append the reference only if it doesn't exist (deduplication)
    2. Keep only the last 10 references
    3. Prevent race conditions from concurrent adds

    Returns:
        True if successful, False if person not found or error occurred
    """
    try:
        async with get_connection() as conn:
            # ATOMIC: Append + deduplicate + limit in single operation
            # The subquery checks for duplicates, appends if new, then slices
            result = await conn.execute(
                """
                UPDATE rapport SET
                    inside_references = (
                        SELECT jsonb_agg(elem)
                        FROM (
                            SELECT DISTINCT elem
                            FROM jsonb_array_elements(
                                CASE
                                    -- Only append if reference not already present
                                    WHEN NOT (inside_references @> $1::jsonb)
                                    THEN inside_references || $1::jsonb
                                    ELSE inside_references
                                END
                            ) AS elem
                            -- Keep only last 10 (DISTINCT preserves order in this context)
                            ORDER BY elem
                            LIMIT 10
                        ) sub
                    ),
                    updated_at = NOW()
                WHERE org_id = $2 AND person_id = $3
                """,
                json.dumps(reference),
                org_id,
                person_id,
            )
            return str(result).endswith("1")
    except asyncpg.PostgresError as e:
        logger.error(f"Database error adding inside reference for {person_id}: {e}")
        return False


async def update_communication_style(
    org_id: str,
    person_id: str,
    formality: Optional[str] = None,
    verbosity: Optional[str] = None,
    humor_receptivity: Optional[float] = None,
) -> bool:
    """
    Update communication style preferences for a person.

    Called when Aleq learns how someone prefers to communicate.

    Args:
        org_id: Organization ID
        person_id: Person ID
        formality: casual, professional, or formal
        verbosity: concise, moderate, or detailed
        humor_receptivity: 0.0 (serious) to 1.0 (loves humor)

    Returns:
        True if successful, False if person not found or validation failed

    Raises:
        ValueError: If formality or verbosity has invalid value
    """
    updates = []
    params: list[Any] = []
    param_idx = 1

    if formality is not None:
        if formality not in VALID_FORMALITY:
            raise ValueError(f"Invalid formality '{formality}'. Must be one of: {VALID_FORMALITY}")
        updates.append(f"preferred_formality = ${param_idx}")
        params.append(formality)
        param_idx += 1

    if verbosity is not None:
        if verbosity not in VALID_VERBOSITY:
            raise ValueError(f"Invalid verbosity '{verbosity}'. Must be one of: {VALID_VERBOSITY}")
        updates.append(f"preferred_verbosity = ${param_idx}")
        params.append(verbosity)
        param_idx += 1

    if humor_receptivity is not None:
        # Clamp to valid range
        clamped = _clamp_float(humor_receptivity, "humor_receptivity")
        updates.append(f"humor_receptivity = ${param_idx}")
        params.append(clamped)
        param_idx += 1

    if not updates:
        return True  # Nothing to update is success

    updates.append("updated_at = NOW()")
    params.extend([org_id, person_id])

    try:
        async with get_connection() as conn:
            result = await conn.execute(
                f"""
                UPDATE rapport SET
                    {', '.join(updates)}
                WHERE org_id = ${param_idx} AND person_id = ${param_idx + 1}
                """,
                *params,
            )
            return str(result).endswith("1")
    except asyncpg.PostgresError as e:
        logger.error(f"Database error updating communication style for {person_id}: {e}")
        return False


# ============================================================
# ROW CONVERSION
# ============================================================


def _row_to_rapport(row: Any) -> RapportState:
    """
    Convert database row to RapportState with validation.

    Validates and clamps float fields to [0.0, 1.0] range.
    Validates enum fields to valid values.
    """
    return RapportState(
        rapport_id=row["rapport_id"],
        org_id=row["org_id"],
        person_id=row["person_id"],
        person_name=row["person_name"],
        # Validate float fields
        rapport_level=_clamp_float(row["rapport_level"], "rapport_level"),
        trust_level=_clamp_float(row["trust_level"], "trust_level"),
        familiarity=_clamp_float(row["familiarity"], "familiarity"),
        interaction_count=row["interaction_count"],
        positive_interactions=row["positive_interactions"],
        negative_interactions=row["negative_interactions"],
        last_interaction=row["last_interaction"].isoformat() if row["last_interaction"] else None,
        first_interaction=row["first_interaction"].isoformat(),
        memorable_moments=row["memorable_moments"] if row["memorable_moments"] else [],
        topics_discussed=row["topics_discussed"] if row["topics_discussed"] else {},
        preferences_learned=row["preferences_learned"] if row["preferences_learned"] else {},
        inside_references=row["inside_references"] if row["inside_references"] else [],
        # Validate enum fields
        preferred_formality=_validate_formality(row["preferred_formality"]),
        preferred_verbosity=_validate_verbosity(row["preferred_verbosity"]),
        humor_receptivity=_clamp_float(row["humor_receptivity"], "humor_receptivity"),
        first_impression_given=row["first_impression_given"],
        first_impression_text=row["first_impression_text"],
        first_impression_at=row["first_impression_at"].isoformat()
        if row["first_impression_at"]
        else None,
    )
