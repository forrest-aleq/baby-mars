"""
Stargate Singleton
===================

Singleton pattern for Stargate client.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import StargateClient

_stargate_client: Optional["StargateClient"] = None


def get_stargate_client() -> "StargateClient":
    """Get the Stargate client singleton."""
    global _stargate_client
    if _stargate_client is None:
        from .client import StargateClient
        _stargate_client = StargateClient()
    return _stargate_client


async def reset_stargate_client() -> None:
    """Reset the Stargate client (for testing)."""
    global _stargate_client
    if _stargate_client:
        await _stargate_client.close()
    _stargate_client = None


def set_stargate_client(client: "StargateClient") -> None:
    """Set the Stargate client singleton (for testing)."""
    global _stargate_client
    _stargate_client = client
