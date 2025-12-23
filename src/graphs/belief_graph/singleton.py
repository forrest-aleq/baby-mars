"""
Belief Graph Singleton
=======================

Thread-safe singleton access to the belief graph.
"""

import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .graph import BeliefGraph

_belief_graph: Optional["BeliefGraph"] = None
_belief_graph_lock: threading.Lock = threading.Lock()


def get_belief_graph() -> "BeliefGraph":
    """Get singleton belief graph instance (thread-safe)."""
    global _belief_graph
    if _belief_graph is None:
        with _belief_graph_lock:
            # Double-check after acquiring lock
            if _belief_graph is None:
                from .graph import BeliefGraph
                _belief_graph = BeliefGraph()
    return _belief_graph


def reset_belief_graph() -> None:
    """Reset the singleton (for testing)."""
    global _belief_graph
    with _belief_graph_lock:
        _belief_graph = None


def set_belief_graph(graph: "BeliefGraph") -> None:
    """Set the singleton to a specific graph instance."""
    global _belief_graph
    with _belief_graph_lock:
        _belief_graph = graph
