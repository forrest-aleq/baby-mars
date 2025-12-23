"""
Belief Graph Helpers
====================

Helper functions for creating belief hierarchies.
"""

from typing import TYPE_CHECKING, Any, Optional, cast

from ...state.schema import BeliefState

if TYPE_CHECKING:
    from .graph import BeliefGraph


def create_belief_hierarchy(
    foundation: BeliefState,
    derived: list[BeliefState],
    weights: Optional[list[float]] = None,
) -> "BeliefGraph":
    """
    Helper to create a belief hierarchy.

    Example:
        graph = create_belief_hierarchy(
            foundation=create_belief("Maintain client confidentiality", "ethical"),
            derived=[
                create_belief("Redact client names from reports", "procedural"),
                create_belief("Encrypt client data", "procedural")
            ],
            weights=[0.9, 0.8]
        )
    """
    from .graph import BeliefGraph

    if weights is None:
        weights = [0.8] * len(derived)

    graph = BeliefGraph()
    graph.add_belief(cast(dict[str, Any], foundation))

    for belief, weight in zip(derived, weights):
        graph.add_belief(cast(dict[str, Any], belief))
        graph.add_support_relationship(foundation["belief_id"], belief["belief_id"], weight)

    return graph
