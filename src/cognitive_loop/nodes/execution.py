"""
Execution Node
===============

Executes work units via Stargate Lite.
Implements the PTD Driver layer (Paper #20).

Stargate provides 295 capabilities across 20+ platforms.
This is the ONLY execution path - no mocks.

Requires:
    STARGATE_URL=http://localhost:8001
    STARGATE_API_KEY=your-api-key
"""

import uuid

from ...connectors.stargate import (
    StargateExecutor,
    get_stargate_client,
    map_work_unit_to_capability,
)
from ...observability import get_logger, get_metrics
from ...state.schema import BabyMARSState, WorkUnit

logger = get_logger("execution")
metrics = get_metrics()


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict:
    """
    Execution Node

    Executes work units via Stargate:
    1. Get org_id and user_id from state
    2. Execute each work unit in sequence
    3. Stop on permanent failure, retry transient errors
    4. Return results for verification

    Per Stargate Integration Contract v1.1:
    - Uses turn_id for idempotency
    - Follows retry strategies from error taxonomy
    - Handles all 295 capabilities
    """

    selected_action = state.get("selected_action")

    if not selected_action:
        logger.warning("No action selected for execution")
        return {
            "execution_results": [
                {
                    "success": False,
                    "message": "No action selected for execution",
                    "error_type": "ValidationError",
                }
            ]
        }

    work_units = selected_action.get("work_units", [])

    if not work_units:
        logger.info("No work units to execute")
        return {
            "execution_results": [
                {
                    "success": True,
                    "message": "No work units to execute",
                }
            ]
        }

    # Get org and user IDs
    org_id = state.get("org_id", "default")
    person = state.get("person", {})
    user_id = person.get("person_id", "default")

    # Generate turn_id for this execution (idempotency)
    turn_id = state.get("turn_id") or str(uuid.uuid4())

    logger.info(
        "Executing work units via Stargate",
        org_id=org_id,
        user_id=user_id,
        turn_id=turn_id,
        work_unit_count=len(work_units),
    )

    # Execute via Stargate
    executor = StargateExecutor()
    results = await executor.execute_batch(
        work_units=work_units,
        org_id=org_id,
        user_id=user_id,
        turn_id=turn_id,
    )

    # Log results
    success_count = sum(1 for r in results if r.get("success", False))
    failure_count = len(results) - success_count

    logger.info(
        "Execution complete",
        success_count=success_count,
        failure_count=failure_count,
        total=len(results),
    )

    metrics.increment("work_units_executed", count=len(results))
    metrics.increment("work_units_succeeded", count=success_count)
    metrics.increment("work_units_failed", count=failure_count)

    return {
        "execution_results": results,
        "turn_id": turn_id,
    }


# ============================================================
# HEALTH CHECK
# ============================================================


async def check_stargate_health() -> dict:
    """Check if Stargate is available and healthy."""
    try:
        client = get_stargate_client()
        health = await client.health_check()

        if health.get("status") == "healthy":
            return {
                "stargate": "connected",
                "redis": health.get("redis", "unknown"),
                "database": health.get("database", "unknown"),
            }
        else:
            return {
                "stargate": "unhealthy",
                "error": health.get("error", "Unknown error"),
            }
    except Exception as e:
        return {
            "stargate": "disconnected",
            "error": str(e),
        }


# ============================================================
# CAPABILITY INFO
# ============================================================


def get_capability_for_work_unit(work_unit: WorkUnit) -> str:
    """Get the Stargate capability key for a work unit."""
    tool = work_unit.get("tool", "unknown")
    verb = work_unit.get("verb", "unknown")
    return map_work_unit_to_capability(tool, verb)


async def list_available_capabilities() -> list[dict]:
    """List all available Stargate capabilities."""
    try:
        client = get_stargate_client()
        return await client.list_capabilities()
    except Exception as e:
        logger.error(f"Failed to list capabilities: {e}")
        return []
