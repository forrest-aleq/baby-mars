"""
Stargate Connector
===================

This module re-exports from stargate/ package for backwards compatibility.
"""

# Re-export everything from the package
from .stargate import (
    CAPABILITY_MAP,
    ERROR_RETRY_MAP,
    RetryStrategy,
    StargateClient,
    StargateConfig,
    StargateExecutor,
    execute_capability,
    execute_work_unit,
    get_stargate_client,
    get_stargate_config,
    is_stargate_available,
    map_work_unit_to_capability,
    reset_stargate_client,
    set_stargate_client,
)

__all__ = [
    "StargateConfig",
    "get_stargate_config",
    "RetryStrategy",
    "ERROR_RETRY_MAP",
    "CAPABILITY_MAP",
    "map_work_unit_to_capability",
    "StargateClient",
    "get_stargate_client",
    "reset_stargate_client",
    "set_stargate_client",
    "StargateExecutor",
    "execute_work_unit",
    "execute_capability",
    "is_stargate_available",
]
