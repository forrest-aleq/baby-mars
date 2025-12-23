"""
Stargate Executor
==================

Executes Baby MARS work units via Stargate.
"""

from typing import Optional

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
        work_unit: dict,
        org_id: str,
        user_id: str,
        turn_id: Optional[str] = None,
    ) -> dict:
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

    def _transform_response(self, response: dict, capability_key: str) -> dict:
        """Transform Stargate response to Baby MARS format."""
        if response.get("success", False):
            return {
                "success": True,
                "result": response.get("outputs", {}),
                "message": f"Executed {capability_key}",
                "capability_key": capability_key,
                "execution_logs": response.get("execution_logs", []),
            }
        else:
            error = response.get("error", {})
            return {
                "success": False,
                "result": None,
                "message": error.get("message", "Stargate execution failed"),
                "capability_key": capability_key,
                "error_type": error.get("error_type", "ExecutionError"),
                "error_code": error.get("error_code", "UNKNOWN"),
                "retry_strategy": error.get("retry_strategy", "DO_NOT_RETRY"),
            }

    async def execute_batch(
        self,
        work_units: list[dict],
        org_id: str,
        user_id: str,
        turn_id: Optional[str] = None,
    ) -> list[dict]:
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
                retry_strategy = result.get("retry_strategy", "DO_NOT_RETRY")
                if retry_strategy == "DO_NOT_RETRY":
                    break

        return results


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


async def execute_work_unit(
    work_unit: dict,
    org_id: str,
    user_id: str,
    turn_id: Optional[str] = None,
) -> dict:
    """Execute a single work unit via Stargate."""
    executor = StargateExecutor()
    return await executor.execute(work_unit, org_id, user_id, turn_id)


async def execute_capability(
    capability_key: str,
    org_id: str,
    user_id: str,
    args: dict,
    turn_id: Optional[str] = None,
) -> dict:
    """Execute a Stargate capability directly."""
    client = get_stargate_client()
    return await client.execute(capability_key, org_id, user_id, args, turn_id)


async def is_stargate_available() -> bool:
    """Check if Stargate is available and healthy."""
    try:
        client = get_stargate_client()
        health = await client.health_check()
        return health.get("status") == "healthy"
    except Exception:
        return False
