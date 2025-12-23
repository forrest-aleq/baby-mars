"""
Belief Graph Package
====================

NetworkX-backed belief hierarchy with cascading updates.
Implements Papers #4, #9, #10, #11, #12.
"""

from .graph import BeliefGraph
from .helpers import create_belief_hierarchy
from .seed import CORE_BELIEFS, SUPPORT_RELATIONSHIPS, seed_initial_beliefs
from .serialization import (
    deserialize_graph,
    graph_from_dict,
    graph_to_dict,
    serialize_graph,
)
from .singleton import get_belief_graph, reset_belief_graph, set_belief_graph

__all__ = [
    # Core class
    "BeliefGraph",
    # Singleton access
    "get_belief_graph",
    "reset_belief_graph",
    "set_belief_graph",
    # Serialization
    "serialize_graph",
    "deserialize_graph",
    "graph_to_dict",
    "graph_from_dict",
    # Seed data
    "seed_initial_beliefs",
    "CORE_BELIEFS",
    "SUPPORT_RELATIONSHIPS",
    # Helpers
    "create_belief_hierarchy",
]
