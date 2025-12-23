"""
Stargate Client
================

HTTP client for Stargate Lite.
Implements Stargate Integration Contract v1.1.
"""

import asyncio
import uuid
from typing import Any, Optional

import httpx

from ...observability import get_logger, get_metrics, timed, traced
from .config import (
    ERROR_RETRY_MAP,
    RetryStrategy,
    StargateConfig,
    get_stargate_config,
)

logger = get_logger("stargate")
metrics = get_metrics()


class StargateClient:
    """
    HTTP client for Stargate Lite.

    Implements Stargate Integration Contract v1.1:
    - POST /api/v1/execute with capability_key, org_id, user_id, turn_id, args
    - Error taxonomy with retry strategies
    - Automatic retry with backoff
    - Idempotency via turn_id
    """

    def __init__(self, config: Optional[StargateConfig] = None):
        self.config = config or get_stargate_config()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers={
                    "X-API-Key": self.config.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @traced("stargate.execute")
    @timed("stargate_execute")
    async def execute(
        self,
        capability_key: str,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        turn_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a Stargate capability (per Contract Section 2.1).

        Args:
            capability_key: Stargate capability (e.g., "qb.vendor.create")
            org_id: Organization ID for credential lookup
            user_id: User ID for credential lookup
            args: Arguments for the capability
            turn_id: Optional turn ID for idempotency (required for mutations)

        Returns:
            Stargate response with success, outputs, or error
        """
        if turn_id is None:
            turn_id = str(uuid.uuid4())

        request_body = {
            "capability_key": capability_key,
            "org_id": org_id,
            "user_id": user_id,
            "turn_id": turn_id,
            "args": args,
        }

        logger.info(
            "Executing Stargate capability",
            capability=capability_key,
            org_id=org_id,
            turn_id=turn_id,
        )

        return await self._execute_with_retry(request_body)

    async def _execute_with_retry(self, request_body: dict[str, Any]) -> dict[str, Any]:
        """Execute with retry logic per contract."""
        capability_key = request_body["capability_key"]
        backoff = self.config.backoff_base

        for attempt in range(self.config.max_retries):
            try:
                result = await self._try_execute(request_body)

                if result.get("success", False):
                    self._log_success(capability_key, attempt)
                    return result

                should_continue = await self._handle_error(result, capability_key, attempt, backoff)
                if not should_continue:
                    return result

            except httpx.HTTPStatusError as e:
                error_result = await self._handle_http_error(e, capability_key, attempt, backoff)
                if error_result:
                    return error_result

            except httpx.RequestError as e:
                error_result = await self._handle_request_error(e, capability_key, attempt, backoff)
                if error_result:
                    return error_result

        return self._max_retries_error(capability_key)

    async def _try_execute(self, request_body: dict[str, Any]) -> dict[str, Any]:
        """Attempt a single execution."""
        client = await self._get_client()
        response = await client.post("/api/v1/execute", json=request_body)
        response.raise_for_status()  # Ensure HTTP errors are raised
        result: dict[str, Any] = response.json()
        return result

    def _log_success(self, capability_key: str, attempt: int) -> None:
        """Log successful execution."""
        metrics.increment("stargate_calls", capability=capability_key, status="success")
        logger.info(
            "Stargate execution succeeded",
            capability=capability_key,
            attempt=attempt + 1,
        )

    async def _handle_error(
        self, result: dict[str, Any], capability_key: str, attempt: int, backoff: float
    ) -> bool:
        """Handle error response. Returns True if should continue retrying."""
        error = result.get("error", {})
        error_type = error.get("error_type", "ExecutionError")
        retry_strategy = ERROR_RETRY_MAP.get(error_type, RetryStrategy.DO_NOT_RETRY)

        metrics.increment("stargate_errors", capability=capability_key, error_type=error_type)
        logger.warning(
            "Stargate execution failed",
            capability=capability_key,
            error_type=error_type,
            retry_strategy=retry_strategy.value,
            attempt=attempt + 1,
        )

        if retry_strategy == RetryStrategy.DO_NOT_RETRY:
            return False

        if retry_strategy == RetryStrategy.RETRY_AFTER_DELAY:
            retry_after = error.get("details", {}).get("retry_after", 60)
            if attempt < self.config.max_retries - 1:
                logger.info(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return True
            return False

        if retry_strategy == RetryStrategy.RETRY_WITH_BACKOFF:
            if attempt < self.config.max_retries - 1:
                wait_time = backoff**attempt
                logger.info(f"Retrying with backoff: {wait_time}s")
                await asyncio.sleep(wait_time)
                return True
            return False

        return False

    async def _handle_http_error(
        self, e: httpx.HTTPStatusError, capability_key: str, attempt: int, backoff: float
    ) -> Optional[dict[str, Any]]:
        """Handle HTTP errors. Returns error dict if should stop, None to continue."""
        logger.error(
            "Stargate HTTP error",
            capability=capability_key,
            status_code=e.response.status_code,
        )
        metrics.increment("stargate_errors", type="http")

        if attempt < self.config.max_retries - 1:
            await asyncio.sleep(backoff**attempt)
            return None

        return {
            "success": False,
            "capability_key": capability_key,
            "error": {
                "error_type": "NetworkError",
                "error_code": "HTTP_ERROR",
                "message": f"HTTP {e.response.status_code}",
                "retry_strategy": "RETRY_WITH_BACKOFF",
            },
        }

    async def _handle_request_error(
        self, e: httpx.RequestError, capability_key: str, attempt: int, backoff: float
    ) -> Optional[dict[str, Any]]:
        """Handle request errors. Returns error dict if should stop, None to continue."""
        logger.error("Stargate connection error", capability=capability_key, error=str(e))
        metrics.increment("stargate_errors", type="connection")

        if attempt < self.config.max_retries - 1:
            await asyncio.sleep(backoff**attempt)
            return None

        return {
            "success": False,
            "capability_key": capability_key,
            "error": {
                "error_type": "NetworkError",
                "error_code": "CONNECTION_ERROR",
                "message": str(e),
                "retry_strategy": "RETRY_WITH_BACKOFF",
            },
        }

    def _max_retries_error(self, capability_key: str) -> dict[str, Any]:
        """Return max retries exceeded error."""
        return {
            "success": False,
            "capability_key": capability_key,
            "error": {
                "error_type": "ExecutionError",
                "error_code": "MAX_RETRIES",
                "message": "Max retries exceeded",
            },
        }

    async def health_check(self) -> dict[str, Any]:
        """Check Stargate health (per Contract Section 7.1)."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            result: dict[str, Any] = response.json()
            return result
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def list_capabilities(self) -> list[dict[str, Any]]:
        """List available Stargate capabilities."""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/capabilities")
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result
        except Exception as e:
            logger.error(f"Failed to list capabilities: {e}")
            return []
