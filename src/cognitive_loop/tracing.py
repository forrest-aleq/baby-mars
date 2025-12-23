"""
LangSmith Tracing Integration
==============================

Provides LangSmith callback injection for the cognitive loop.
"""

import os
from typing import TYPE_CHECKING

from ..observability import get_logger

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler

logger = get_logger(__name__)


def get_langsmith_callbacks() -> list["BaseCallbackHandler"]:
    """Get LangSmith callbacks if configured."""
    if not os.getenv("LANGSMITH_API_KEY"):
        return []

    try:
        from langsmith import Client
        from langsmith.run_helpers import get_current_run_tree

        # Check if we're already in a traced context
        if get_current_run_tree():
            return []

        # LangSmith auto-traces via env vars, but we can add explicit tracer
        from langchain_core.tracers import LangChainTracer

        project = os.getenv("LANGSMITH_PROJECT", "baby-mars")
        return [LangChainTracer(project_name=project, client=Client())]
    except ImportError:
        logger.debug("LangSmith not available - install langsmith for tracing")
        return []
    except Exception as e:
        logger.debug(f"LangSmith tracer init failed: {e}")
        return []
