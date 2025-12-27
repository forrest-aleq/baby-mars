"""
Stargate Executor
==================

Executes Baby MARS work units via Stargate.
"""

from typing import Any, Optional, cast

from .capability_map import map_work_unit_to_capability
from .client import StargateClient
from .singleton import get_stargate_client


class StargateExecutor:
    """
    Executes Baby MARS work units via Stargate.

    This is the ONLY execution path - no mocks.
    """

    def __init__(self, client: Optional[StargateClient] = None):
        self.client = client or get_stargate_client()

    async def execute(
        self,
        work_unit: dict[str, Any],
        org_id: str,
        user_id: str,
        turn_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a work unit via Stargate.

        Args:
            work_unit: Baby MARS work unit with tool, verb, entities, slots
            org_id: Organization ID
            user_id: User ID
            turn_id: Optional turn ID for idempotency

        Returns:
            Execution result with success, result, message
        """
        tool = work_unit.get("tool", "unknown")
        verb = work_unit.get("verb", "unknown")
        entities = work_unit.get("entities", {})
        slots = work_unit.get("slots", {})

        capability_key = map_work_unit_to_capability(tool, verb)
        args = {**entities, **slots}

        response = await self.client.execute(
            capability_key=capability_key,
            org_id=org_id,
            user_id=user_id,
            args=args,
            turn_id=turn_id,
        )

        return self._transform_response(response, capability_key)

    def _transform_response(self, response: dict[str, Any], capability_key: str) -> dict[str, Any]:
        """Transform Stargate response to Baby MARS format."""
        # Per Stargate API v2.0: status is "success" or "error"
        if response.get("status") == "success":
            return {
                "success": True,
                "result": response.get("outputs", {}),
                "message": f"Executed {capability_key}",
                "capability_key": capability_key,
                "tool_used": response.get("tool_used", capability_key),
                "logs": response.get("logs", []),
            }
        else:
            # Error fields are at top level per Stargate API v2.0
            return {
                "success": False,
                "result": None,
                "message": response.get("error_message", "Stargate execution failed"),
                "capability_key": capability_key,
                "error_code": response.get("error_code", "EXTERNAL_API_ERROR"),
                "retry_strategy": response.get("retry_strategy", "none"),
            }

    async def execute_batch(
        self,
        work_units: list[dict[str, Any]],
        org_id: str,
        user_id: str,
        turn_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Execute multiple work units."""
        results = []

        for i, wu in enumerate(work_units):
            wu_turn_id = f"{turn_id}:{i}" if turn_id else None
            result = await self.execute(wu, org_id, user_id, wu_turn_id)

            results.append(
                {
                    "unit_id": wu.get("unit_id", f"wu_{i}"),
                    "tool": wu.get("tool", "unknown"),
                    "verb": wu.get("verb", "unknown"),
                    **result,
                }
            )

            if not result.get("success", False):
                retry_strategy = result.get("retry_strategy", "none")
                # Stop batch on non-retryable errors
                if retry_strategy in ("none", "human_intervention"):
                    break

        return results


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


async def execute_work_unit(
    work_unit: dict[str, Any],
    org_id: str,
    user_id: str,
    turn_id: Optional[str] = None,
) -> dict[str, Any]:
    """Execute a single work unit via Stargate."""
    executor = StargateExecutor()
    return await executor.execute(work_unit, org_id, user_id, turn_id)


async def execute_capability(
    capability_key: str,
    org_id: str,
    user_id: str,
    args: dict[str, Any],
    turn_id: Optional[str] = None,
) -> dict[str, Any]:
    """Execute a Stargate capability directly."""
    client = get_stargate_client()
    return cast(
        dict[str, Any], await client.execute(capability_key, org_id, user_id, args, turn_id)
    )


async def is_stargate_available() -> bool:
    """Check if Stargate is available and healthy."""
    try:
        client = get_stargate_client()
        health = await client.health_check()
        return health.get("status") == "healthy"
    except Exception:
        return False
