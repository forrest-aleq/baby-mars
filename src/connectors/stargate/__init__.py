"""
Stargate Connector Package
===========================

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

from .capability_map import CAPABILITY_MAP, map_work_unit_to_capability
from .client import StargateClient
from .config import (
    ERROR_CODES,
    RetryStrategy,
    StargateConfig,
    get_stargate_config,
)
from .executor import (
    StargateExecutor,
    execute_capability,
    execute_work_unit,
    is_stargate_available,
)
from .singleton import get_stargate_client, reset_stargate_client, set_stargate_client

__all__ = [
    # Config
    "StargateConfig",
    "get_stargate_config",
    "RetryStrategy",
    "ERROR_CODES",
    # Capability mapping
    "CAPABILITY_MAP",
    "map_work_unit_to_capability",
    # Client
    "StargateClient",
    # Singleton
    "get_stargate_client",
    "reset_stargate_client",
    "set_stargate_client",
    # Executor
    "StargateExecutor",
    "execute_work_unit",
    "execute_capability",
    "is_stargate_available",
]
