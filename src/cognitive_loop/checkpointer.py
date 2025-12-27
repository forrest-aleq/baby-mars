"""
Checkpointer Management
========================

Singleton management for LangGraph checkpointers (sync and async).
Handles Postgres connection lifecycle.
"""

import os
from typing import Any, Optional, Union

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ..observability import get_logger

logger = get_logger(__name__)


# ============================================================
# SYNC CHECKPOINTER
# ============================================================

_checkpointer: Optional[PostgresSaver] = None
_checkpointer_ctx: Optional[Any] = None


def cleanup_checkpointer() -> None:
    """
    Clean up checkpointer on application shutdown.

    Call this during application shutdown or register with atexit.
    """
    global _checkpointer, _checkpointer_ctx
    if _checkpointer is not None and _checkpointer_ctx is not None:
        try:
            _checkpointer_ctx.__exit__(None, None, None)
        except Exception:
            logger.debug("Error during checkpointer cleanup", exc_info=True)
        finally:
            _checkpointer = None
            _checkpointer_ctx = None


def get_checkpointer() -> PostgresSaver:
    """
    Get or create the Postgres checkpointer.
    Calls setup() on first use to create tables.

    Note: The checkpointer stays alive for the application lifetime.
    Use cleanup_checkpointer() on application shutdown to properly release resources.
    """
    global _checkpointer, _checkpointer_ctx
    if _checkpointer is None:
        postgres_url = os.environ.get("DATABASE_URL")
        if not postgres_url:
            raise ValueError(
                "DATABASE_URL environment variable required for persistence. "
                "Use create_graph_in_memory() for testing without a database."
            )
        _checkpointer_ctx = PostgresSaver.from_conn_string(postgres_url)
        _checkpointer = _checkpointer_ctx.__enter__()
        _checkpointer.setup()

        import atexit

        atexit.register(cleanup_checkpointer)
    return _checkpointer


def reset_sync_checkpointer() -> None:
    """Reset the sync checkpointer singleton (for testing or URL changes)."""
    global _checkpointer, _checkpointer_ctx
    if _checkpointer is not None:
        cleanup_checkpointer()


# ============================================================
# ASYNC CHECKPOINTER
# ============================================================

_async_checkpointer: Optional[AsyncPostgresSaver] = None
_async_checkpointer_ctx: Optional[Any] = None


async def get_async_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the async Postgres checkpointer.
    Must be called from within an async context.
    """
    global _async_checkpointer, _async_checkpointer_ctx
    if _async_checkpointer is None:
        postgres_url = os.environ.get("DATABASE_URL")
        if not postgres_url:
            raise ValueError(
                "DATABASE_URL environment variable required for persistence. "
                "Use create_graph_in_memory() for testing without a database."
            )
        _async_checkpointer_ctx = AsyncPostgresSaver.from_conn_string(postgres_url)
        _async_checkpointer = await _async_checkpointer_ctx.__aenter__()
        await _async_checkpointer.setup()
    return _async_checkpointer


async def cleanup_async_checkpointer() -> None:
    """Clean up async checkpointer on application shutdown."""
    global _async_checkpointer, _async_checkpointer_ctx
    if _async_checkpointer is not None and _async_checkpointer_ctx is not None:
        try:
            await _async_checkpointer_ctx.__aexit__(None, None, None)
        except Exception:
            logger.debug("Error during async checkpointer cleanup", exc_info=True)
        finally:
            _async_checkpointer = None
            _async_checkpointer_ctx = None


async def reset_async_checkpointer() -> None:
    """Reset the async checkpointer singleton (for testing or URL changes)."""
    global _async_checkpointer, _async_checkpointer_ctx
    if _async_checkpointer is not None:
        await cleanup_async_checkpointer()


# ============================================================
# TYPE ALIAS FOR CONVENIENCE
# ============================================================

CheckpointerType = Union[MemorySaver, PostgresSaver, AsyncPostgresSaver]
