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
