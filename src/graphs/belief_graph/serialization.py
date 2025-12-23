"""
Belief Graph Serialization
===========================

Serialization and deserialization for belief graphs.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import BeliefGraph


def serialize_graph(graph: "BeliefGraph") -> str:
    """Serialize graph to JSON for Postgres storage."""
    return json.dumps(
        {
            "nodes": {n: dict(d) for n, d in graph.G.nodes(data=True)},
            "edges": [(u, v, dict(d)) for u, v, d in graph.G.edges(data=True)],
            "beliefs": graph.beliefs,
        },
        default=str,
    )


def deserialize_graph(json_str: str, graph_cls: type) -> "BeliefGraph":
    """Restore graph from Postgres JSON."""
    data = json.loads(json_str)
    graph = graph_cls()

    for node_id, attrs in data.get("nodes", {}).items():
        graph.G.add_node(node_id, **attrs)

    for source, target, attrs in data.get("edges", []):
        graph.G.add_edge(source, target, **attrs)

    graph.beliefs = data.get("beliefs", {})
    return graph


def graph_to_dict(graph: "BeliefGraph") -> dict:
    """Convert graph to dictionary (for non-JSON storage)."""
    return {
        "nodes": dict(graph.G.nodes(data=True)),
        "edges": list(graph.G.edges(data=True)),
        "beliefs": graph.beliefs,
    }


def graph_from_dict(data: dict, graph_cls: type) -> "BeliefGraph":
    """Restore graph from dictionary."""
    graph = graph_cls()

    for node_id, attrs in data.get("nodes", {}).items():
        graph.G.add_node(node_id, **attrs)

    for source, target, attrs in data.get("edges", []):
        graph.G.add_edge(source, target, **attrs)

    graph.beliefs = data.get("beliefs", {})
    return graph
