"""
Claude Client Singleton
========================

Singleton access and convenience functions for Claude client.
"""

from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from .claude_client import ClaudeClient

T = TypeVar("T", bound=BaseModel)

_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get singleton Claude client instance."""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client


def reset_claude_client() -> None:
    """Reset the singleton (for testing)."""
    global _client
    _client = None


async def complete(messages: list[dict[str, Any]], **kwargs: Any) -> str:
    """Convenience function for basic completion."""
    return await get_claude_client().complete(messages, **kwargs)


async def complete_structured(
    messages: list[dict[str, Any]], response_model: type[T], **kwargs: Any
) -> T:
    """Convenience function for structured completion."""
    return await get_claude_client().complete_structured(messages, response_model, **kwargs)
