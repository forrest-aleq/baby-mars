"""
Stargate Configuration
=======================

Configuration, enums, and error taxonomy for Stargate.
"""

import os
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Stargate retry strategies."""

    DO_NOT_RETRY = "DO_NOT_RETRY"
    RETRY_AFTER_DELAY = "RETRY_AFTER_DELAY"
    RETRY_WITH_BACKOFF = "RETRY_WITH_BACKOFF"


# Error codes per Stargate API v2.0
# retry_strategy comes from Stargate response directly:
# - "human_intervention" -> user needs to connect/fix something
# - "backoff" -> retry with exponential backoff
# - "none" -> don't retry
ERROR_CODES = {
    "CREDENTIAL_MISSING",
    "CREDENTIAL_INVALID",
    "RATE_LIMIT",
    "VALIDATION_ERROR",
    "NOT_FOUND",
    "EXTERNAL_API_ERROR",
}


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

    # Validate STARGATE_TIMEOUT
    timeout_str = os.environ.get("STARGATE_TIMEOUT", "30")
    try:
        timeout = float(timeout_str)
        if timeout <= 0:
            raise ValueError("must be positive")
    except ValueError as e:
        raise ValueError(f"STARGATE_TIMEOUT must be a positive number, got '{timeout_str}': {e}")

    return StargateConfig(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
    )
