"""
Stargate Connector
===================

Baby MARS execution layer via Stargate Lite.
Based on Stargate Integration Contract v1.1 (November 2025).

Stargate provides 295 capabilities across 20+ platforms:
- QuickBooks, NetSuite, Stripe, Bill.com (financial)
- Plaid, Ramp, Mercury, Brex, Chase (banking)
- HubSpot, Gmail, Slack (communication)
- Linear, Asana, ClickUp, Monday, Notion (productivity)
- Google Workspace, Microsoft 365 (documents)
- Hyperbrowser (browser automation)
"""

import os
import uuid
import time
import httpx
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..observability import get_logger, get_metrics, traced, timed

logger = get_logger("stargate")
metrics = get_metrics()


# ============================================================
# CONTRACT: Error Taxonomy (from Stargate Integration Contract v1.1)
# ============================================================

class RetryStrategy(Enum):
    """Stargate retry strategies."""
    DO_NOT_RETRY = "DO_NOT_RETRY"
    RETRY_AFTER_DELAY = "RETRY_AFTER_DELAY"
    RETRY_WITH_BACKOFF = "RETRY_WITH_BACKOFF"


# Error type to retry strategy mapping (per contract)
ERROR_RETRY_MAP = {
    "CredentialMissingError": RetryStrategy.DO_NOT_RETRY,
    "CredentialInvalidError": RetryStrategy.DO_NOT_RETRY,
    "PermissionDeniedError": RetryStrategy.DO_NOT_RETRY,
    "NotFoundError": RetryStrategy.DO_NOT_RETRY,
    "ValidationError": RetryStrategy.DO_NOT_RETRY,
    "RateLimitError": RetryStrategy.RETRY_AFTER_DELAY,
    "NetworkError": RetryStrategy.RETRY_WITH_BACKOFF,
    "ExecutionError": RetryStrategy.RETRY_WITH_BACKOFF,  # Conditional
}


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class StargateConfig:
    """Stargate connection configuration."""
    base_url: str
    api_key: str
    timeout: float = 30.0
    max_retries: int = 3
    backoff_base: float = 2.0


def get_stargate_config() -> StargateConfig:
    """Get Stargate config from environment."""
    base_url = os.environ.get("STARGATE_URL")
    api_key = os.environ.get("STARGATE_API_KEY", "")

    if not base_url:
        raise ValueError(
            "STARGATE_URL environment variable is required. "
            "Set it to your Stargate instance (e.g., http://localhost:8001)"
        )

    return StargateConfig(
        base_url=base_url,
        api_key=api_key,
        timeout=float(os.environ.get("STARGATE_TIMEOUT", "30")),
    )


# ============================================================
# CONTRACT: Work Unit to Capability Mapping
# ============================================================

# Maps Baby MARS work unit (tool, verb) to Stargate capability_key
# Per contract Section 9.3, use namespaced keys (qb.*, stripe.*, etc.)
CAPABILITY_MAP = {
    # === QuickBooks (qb.*) ===
    ("erp", "process_invoice"): "qb.bill.create",
    ("erp", "create_record"): "qb.vendor.create",
    ("erp", "query_records"): "qb.query",
    ("erp", "post_journal_entry"): "qb.journal.create",
    ("erp", "create_vendor"): "qb.vendor.create",
    ("erp", "get_vendor"): "qb.vendor.get",
    ("erp", "list_vendors"): "qb.vendor.list",
    ("erp", "create_bill"): "qb.bill.create",
    ("erp", "get_bill"): "qb.bill.get",
    ("erp", "create_invoice"): "qb.invoice.create",
    ("erp", "get_invoice"): "qb.invoice.get",
    ("erp", "list_invoices"): "qb.invoice.list",
    ("erp", "create_payment"): "qb.payment.create",
    ("erp", "get_account"): "qb.account.get",
    ("erp", "list_accounts"): "qb.account.list",
    ("erp", "get_report"): "qb.report.profit_loss",
    ("erp", "create_customer"): "qb.customer.create",
    ("erp", "get_customer"): "qb.customer.get",
    ("erp", "list_customers"): "qb.customer.list",

    # === Stripe (stripe.*) ===
    ("stripe", "create_payment"): "stripe.payment.create",
    ("stripe", "create_customer"): "stripe.customer.create",
    ("stripe", "get_customer"): "stripe.customer.get",
    ("stripe", "refund"): "stripe.refund.create",
    ("stripe", "get_balance"): "stripe.balance.get",
    ("stripe", "create_invoice"): "stripe.invoice.create",
    ("stripe", "create_subscription"): "stripe.subscription.create",
    ("stripe", "list_payouts"): "stripe.payout.list",

    # === Bill.com (billcom.*) ===
    ("billcom", "create_bill"): "billcom.bill.create",
    ("billcom", "send_payment"): "billcom.payment.send",
    ("billcom", "approve_bill"): "billcom.bill.approve",
    ("billcom", "create_vendor"): "billcom.vendor.create",

    # === NetSuite (netsuite.*) ===
    ("netsuite", "query"): "netsuite.query",
    ("netsuite", "create_journal"): "netsuite.journal.create",
    ("netsuite", "create_vendor"): "netsuite.vendor.create",
    ("netsuite", "create_bill"): "netsuite.bill.create",

    # === Banking ===
    ("bank", "process_payment"): "qb.payment.create",
    ("bank", "reconcile_account"): "qb.query",
    ("bank", "get_balance"): "plaid.balance.get",
    ("bank", "list_transactions"): "plaid.transaction.list",
    ("bank", "initiate_transfer"): "mercury.transfer.create",

    # === Documents / OCR ===
    ("documents", "extract_data"): "ocr.extract",
    ("documents", "validate_document"): "ocr.validate",
    ("documents", "upload"): "gdrive.file.upload",
    ("documents", "download"): "gdrive.file.download",
    ("documents", "list"): "gdrive.file.list",

    # === Email (Gmail) ===
    ("email", "send_notification"): "gmail.send",
    ("email", "send"): "gmail.send",
    ("email", "read"): "gmail.read",
    ("email", "draft"): "gmail.draft",

    # === Slack ===
    ("slack", "send_message"): "slack.message.send",
    ("slack", "send_dm"): "slack.message.direct",
    ("slack", "upload_file"): "slack.file.upload",
    ("slack", "create_channel"): "slack.channel.create",

    # === CRM (HubSpot) ===
    ("crm", "create_contact"): "hubspot.contact.create",
    ("crm", "get_contact"): "hubspot.contact.get",
    ("crm", "update_contact"): "hubspot.contact.update",
    ("crm", "create_deal"): "hubspot.deal.create",
    ("crm", "create_company"): "hubspot.company.create",

    # === Project Management ===
    ("linear", "create_issue"): "linear.issue.create",
    ("asana", "create_task"): "asana.task.create",
    ("clickup", "create_task"): "clickup.task.create",
    ("notion", "create_page"): "notion.page.create",

    # === Workflow (internal) ===
    ("workflow", "approve_transaction"): "qb.payment.create",
    ("workflow", "escalate_issue"): "slack.message.send",
    ("workflow", "query_records"): "qb.query",

    # === Browser Automation ===
    ("browser", "navigate"): "browser.navigate",
    ("browser", "click"): "browser.click",
    ("browser", "fill_form"): "browser.fill_form",
    ("browser", "extract_data"): "browser.extract_data",
    ("browser", "extract_table"): "browser.extract_table",
    ("browser", "login"): "browser.login_with_credentials",
}


def map_work_unit_to_capability(tool: str, verb: str) -> str:
    """
    Map a Baby MARS work unit to a Stargate capability key.

    Args:
        tool: The tool category (erp, bank, email, etc.)
        verb: The action verb (create_record, send, etc.)

    Returns:
        Stargate capability key (always returns something)
    """
    key = (tool.lower(), verb.lower())

    if key in CAPABILITY_MAP:
        return CAPABILITY_MAP[key]

    # Construct capability from tool.verb pattern
    return f"{tool.lower()}.{verb.lower()}"


# ============================================================
# CONTRACT: Stargate Client (per Integration Contract v1.1)
# ============================================================

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
                }
            )
        return self._client

    async def close(self):
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
        args: dict,
        turn_id: Optional[str] = None,
    ) -> dict:
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
        # Generate turn_id if not provided (for idempotency)
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

        # Execute with retry logic (per Contract Section 3.3)
        return await self._execute_with_retry(request_body)

    async def _execute_with_retry(self, request_body: dict) -> dict:
        """Execute with retry logic per contract."""
        capability_key = request_body["capability_key"]
        backoff = self.config.backoff_base

        for attempt in range(self.config.max_retries):
            try:
                client = await self._get_client()
                response = await client.post("/api/v1/execute", json=request_body)

                # Parse response
                result = response.json()

                # Check for success
                if result.get("success", False):
                    metrics.increment(
                        "stargate_calls",
                        capability=capability_key,
                        status="success",
                    )
                    logger.info(
                        "Stargate execution succeeded",
                        capability=capability_key,
                        attempt=attempt + 1,
                    )
                    return result

                # Handle error response (per Contract Section 3)
                error = result.get("error", {})
                error_type = error.get("error_type", "ExecutionError")
                retry_strategy = ERROR_RETRY_MAP.get(error_type, RetryStrategy.DO_NOT_RETRY)

                metrics.increment(
                    "stargate_errors",
                    capability=capability_key,
                    error_type=error_type,
                )

                logger.warning(
                    "Stargate execution failed",
                    capability=capability_key,
                    error_type=error_type,
                    retry_strategy=retry_strategy.value,
                    attempt=attempt + 1,
                )

                # DO_NOT_RETRY - permanent failure
                if retry_strategy == RetryStrategy.DO_NOT_RETRY:
                    return result

                # RETRY_AFTER_DELAY - rate limit
                if retry_strategy == RetryStrategy.RETRY_AFTER_DELAY:
                    retry_after = error.get("details", {}).get("retry_after", 60)
                    if attempt < self.config.max_retries - 1:
                        logger.info(f"Rate limited, waiting {retry_after}s")
                        time.sleep(retry_after)
                        continue
                    return result

                # RETRY_WITH_BACKOFF - transient error
                if retry_strategy == RetryStrategy.RETRY_WITH_BACKOFF:
                    if attempt < self.config.max_retries - 1:
                        wait_time = backoff ** attempt
                        logger.info(f"Retrying with backoff: {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    return result

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Stargate HTTP error",
                    capability=capability_key,
                    status_code=e.response.status_code,
                )
                metrics.increment("stargate_errors", type="http")

                if attempt < self.config.max_retries - 1:
                    time.sleep(backoff ** attempt)
                    continue

                return {
                    "success": False,
                    "capability_key": capability_key,
                    "error": {
                        "error_type": "NetworkError",
                        "error_code": "HTTP_ERROR",
                        "message": f"HTTP {e.response.status_code}",
                        "retry_strategy": "RETRY_WITH_BACKOFF",
                    }
                }

            except httpx.RequestError as e:
                logger.error(
                    "Stargate connection error",
                    capability=capability_key,
                    error=str(e),
                )
                metrics.increment("stargate_errors", type="connection")

                if attempt < self.config.max_retries - 1:
                    time.sleep(backoff ** attempt)
                    continue

                return {
                    "success": False,
                    "capability_key": capability_key,
                    "error": {
                        "error_type": "NetworkError",
                        "error_code": "CONNECTION_ERROR",
                        "message": str(e),
                        "retry_strategy": "RETRY_WITH_BACKOFF",
                    }
                }

        # Should not reach here
        return {
            "success": False,
            "capability_key": capability_key,
            "error": {
                "error_type": "ExecutionError",
                "error_code": "MAX_RETRIES",
                "message": "Max retries exceeded",
            }
        }

    async def health_check(self) -> dict:
        """Check Stargate health (per Contract Section 7.1)."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.json()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def list_capabilities(self) -> list[dict]:
        """List available Stargate capabilities."""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/capabilities")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list capabilities: {e}")
            return []


# Singleton client
_stargate_client: Optional[StargateClient] = None


def get_stargate_client() -> StargateClient:
    """Get the Stargate client singleton."""
    global _stargate_client
    if _stargate_client is None:
        _stargate_client = StargateClient()
    return _stargate_client


async def reset_stargate_client():
    """Reset the Stargate client (for testing)."""
    global _stargate_client
    if _stargate_client:
        await _stargate_client.close()
    _stargate_client = None


# ============================================================
# EXECUTION LAYER
# ============================================================

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

        # Map to Stargate capability
        capability_key = map_work_unit_to_capability(tool, verb)

        # Build args from entities and slots
        args = {**entities, **slots}

        # Execute via Stargate
        response = await self.client.execute(
            capability_key=capability_key,
            org_id=org_id,
            user_id=user_id,
            args=args,
            turn_id=turn_id,
        )

        # Transform Stargate response to Baby MARS format
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
            # Use indexed turn_id for idempotency per work unit
            wu_turn_id = f"{turn_id}:{i}" if turn_id else None

            result = await self.execute(wu, org_id, user_id, wu_turn_id)
            results.append({
                "unit_id": wu.get("unit_id", f"wu_{i}"),
                "tool": wu.get("tool", "unknown"),
                "verb": wu.get("verb", "unknown"),
                **result,
            })

            # Stop on failure (unless retryable)
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
