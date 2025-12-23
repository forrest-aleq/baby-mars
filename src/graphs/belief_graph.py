"""
Belief Graph Implementation
============================

NetworkX-backed belief hierarchy with cascading updates.
Implements Papers #4, #9, #10, #11, #12.

The graph is stored in memory during operation and serialized
to Postgres JSON for persistence between sessions.
"""

import json
from datetime import datetime
from typing import Optional

import networkx as nx

from ..state.schema import (
    AUTONOMY_THRESHOLDS,
    CATEGORY_MULTIPLIERS,
    DIFFICULTY_WEIGHTS,
    INVALIDATION_THRESHOLDS,
    LEARNING_RATE,
    PEAK_END_MULTIPLIER,
    PEAK_INTENSITY_THRESHOLD,
    BeliefState,
    BeliefStrengthEvent,
    ContextState,
    generate_id,
)


class BeliefGraph:
    """
    NetworkX-backed belief hierarchy with cascading updates.

    Implements:
    - Paper #4: Context-Conditional Beliefs (backoff resolution)
    - Paper #9: Moral Asymmetry (category multipliers)
    - Paper #10: A.C.R.E. (invalidation thresholds)
    - Paper #11: Hierarchical Beliefs (cascading updates)
    - Paper #12: Peak-End Rule (memory weighting)
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self.beliefs: dict[str, BeliefState] = {}

    # ============================================================
    # GRAPH MANAGEMENT
    # ============================================================

    def add_belief(self, belief: BeliefState) -> None:
        """Add belief node to graph"""
        # Ensure required list/dict fields exist
        if "supports" not in belief:
            belief["supports"] = []
        if "supported_by" not in belief:
            belief["supported_by"] = []
        if "support_weights" not in belief:
            belief["support_weights"] = {}

        self.beliefs[belief["belief_id"]] = belief
        self.G.add_node(
            belief["belief_id"], category=belief["category"], strength=belief["strength"]
        )

    def add_support_relationship(
        self, supporter_id: str, supported_id: str, weight: float = 0.8
    ) -> None:
        """
        Add SUPPORTS edge.
        Paper #11: Hierarchical Beliefs

        Args:
            supporter_id: The belief providing support (foundation)
            supported_id: The belief receiving support (derived)
            weight: Strength of support relationship (0.0-1.0)
        """
        if supporter_id not in self.beliefs:
            raise ValueError(f"Supporter belief {supporter_id} not found")
        if supported_id not in self.beliefs:
            raise ValueError(f"Supported belief {supported_id} not found")

        self.G.add_edge(supporter_id, supported_id, weight=weight, rel_type="SUPPORTS")

        # Update belief metadata
        self.beliefs[supporter_id]["supports"].append(supported_id)
        self.beliefs[supported_id]["supported_by"].append(supporter_id)
        self.beliefs[supported_id]["support_weights"][supporter_id] = weight

    def get_belief(self, belief_id: str) -> Optional[BeliefState]:
        """Get belief by ID"""
        return self.beliefs.get(belief_id)

    def get_all_beliefs(self) -> list[BeliefState]:
        """Get all beliefs"""
        return list(self.beliefs.values())

    def get_beliefs_by_category(self, category: str) -> list[BeliefState]:
        """Get all beliefs in a category"""
        return [b for b in self.beliefs.values() if b["category"] == category]

    # ============================================================
    # CONTEXT RESOLUTION
    # Paper #4: Context-Conditional Beliefs
    # ============================================================

    def resolve_belief_for_context(
        self, belief_id: str, context_key: str
    ) -> Optional[ContextState]:
        """
        Find the most specific matching belief state using backoff.

        Paper #4: Context-Conditional Beliefs
        Implements hierarchical backoff from specific to general context.

        Args:
            belief_id: The belief to resolve
            context_key: Current context (e.g., "ClientA|month-end|>10K")

        Returns:
            The most specific matching ContextState, or None
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None

        context_states = belief.get("context_states", {})

        # Try exact match first
        if context_key in context_states:
            return context_states[context_key]

        # Build backoff ladder
        ladder = self._build_backoff_ladder(context_key)

        for candidate in ladder:
            if candidate in context_states:
                return context_states[candidate]

        # Fallback to top-level belief strength if no context states
        if not context_states:
            return {
                "strength": belief.get("strength", 0.5),
                "last_updated": belief.get("last_updated"),
                "success_count": belief.get("success_count", 0),
                "failure_count": belief.get("failure_count", 0),
                "last_outcome": None,
            }

        # No match found
        return None

    def _build_backoff_ladder(self, context_key: str) -> list[str]:
        """
        Generate progressively more general contexts.

        Example for "ClientA|month-end|>10K":
        1. ClientA|month-end|>10K (exact)
        2. ClientA|month-end|* (drop amount)
        3. ClientA|*|* (drop period)
        4. *|*|* (global default)
        """
        parts = context_key.split("|")
        ladder = [context_key]  # Start with exact

        # Drop dimensions right to left
        for i in range(len(parts) - 1, 0, -1):
            generalized = "|".join(parts[:i] + ["*"] * (len(parts) - i))
            ladder.append(generalized)

        # Add global default
        ladder.append("|".join(["*"] * len(parts)))

        return ladder

    def get_or_create_context_state(self, belief_id: str, context_key: str) -> ContextState:
        """Get existing context state or create new one with statistical admission"""
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")

        context_states = belief.get("context_states", {})

        if context_key in context_states:
            return context_states[context_key]

        # Create new context state with default strength from parent
        parent_state = self.resolve_belief_for_context(belief_id, context_key)
        initial_strength = parent_state["strength"] if parent_state else 0.5

        new_state: ContextState = {
            "strength": initial_strength,
            "last_updated": datetime.now().isoformat(),
            "success_count": 0,
            "failure_count": 0,
            "last_outcome": None,
        }

        belief["context_states"][context_key] = new_state
        return new_state

    # ============================================================
    # AUTONOMY
    # Paper #1: Competence-Based Autonomy
    # ============================================================

    def get_autonomy_level(self, belief_id: str, context_key: str) -> str:
        """
        Map belief strength to supervision mode.

        Paper #1: Competence-Based Autonomy
        - strength < 0.4: guidance_seeking
        - 0.4 <= strength < 0.7: action_proposal
        - strength >= 0.7: autonomous
        """
        context_state = self.resolve_belief_for_context(belief_id, context_key)

        if not context_state:
            return "guidance_seeking"

        strength = context_state.get("strength", 0.0)

        if strength < AUTONOMY_THRESHOLDS["guidance_seeking"]:
            return "guidance_seeking"
        elif strength < AUTONOMY_THRESHOLDS["action_proposal"]:
            return "action_proposal"
        else:
            return "autonomous"

    def get_aggregate_autonomy(self, belief_ids: list[str], context_key: str) -> tuple[str, float]:
        """
        Compute aggregate autonomy level for multiple beliefs.
        Returns (supervision_mode, average_strength).
        """
        if not belief_ids:
            return ("guidance_seeking", 0.0)

        strengths = []
        for belief_id in belief_ids:
            state = self.resolve_belief_for_context(belief_id, context_key)
            if state:
                strengths.append(state["strength"])
            else:
                strengths.append(0.3)  # Low default for missing

        avg_strength = sum(strengths) / len(strengths)

        if avg_strength < AUTONOMY_THRESHOLDS["guidance_seeking"]:
            mode = "guidance_seeking"
        elif avg_strength < AUTONOMY_THRESHOLDS["action_proposal"]:
            mode = "action_proposal"
        else:
            mode = "autonomous"

        return (mode, avg_strength)

    # ============================================================
    # CASCADING UPDATES
    # Paper #11: Hierarchical Beliefs
    # ============================================================

    def cascade_strength_update(
        self, belief_id: str, new_strength: float, _visited: set = None
    ) -> list[str]:
        """
        Update belief strength and cascade to all supported beliefs.

        Paper #11: Hierarchical Beliefs with Cascading Strength Updates

        Returns list of all affected belief IDs.
        """
        if _visited is None:
            _visited = set()

        if belief_id in _visited:
            return []  # Prevent infinite loops

        _visited.add(belief_id)

        belief = self.beliefs.get(belief_id)
        if not belief:
            return []

        old_strength = belief["strength"]
        belief["strength"] = new_strength
        self.G.nodes[belief_id]["strength"] = new_strength

        affected = [belief_id]

        # Find all beliefs this one supports
        for _, supported_id, data in self.G.out_edges(belief_id, data=True):
            if data.get("rel_type") != "SUPPORTS":
                continue

            weight = data.get("weight", 1.0)
            supported_belief = self.beliefs.get(supported_id)
            if not supported_belief:
                continue

            # Compute new effective strength
            intrinsic = supported_belief["strength"]
            old_contribution = old_strength * weight * (1 - intrinsic)
            new_contribution = new_strength * weight * (1 - intrinsic)

            delta = new_contribution - old_contribution
            new_effective = max(0.0, min(1.0, intrinsic + delta))

            # Recursive cascade
            affected.extend(self.cascade_strength_update(supported_id, new_effective, _visited))

        return affected

    def compute_effective_strength(self, belief_id: str, _memo: dict = None) -> float:
        """
        Compute effective strength including support from foundational beliefs.

        Paper #11: Hierarchical Beliefs

        Formula:
        effective = intrinsic + Σ(source_strength × weight × (1 - intrinsic))
        """
        if _memo is None:
            _memo = {}

        if belief_id in _memo:
            return _memo[belief_id]

        belief = self.beliefs.get(belief_id)
        if not belief:
            return 0.0

        intrinsic = belief["strength"]

        # Compute contributions from supporting beliefs
        total_contribution = 0.0
        for supporter_id in belief.get("supported_by", []):
            supporter_strength = self.compute_effective_strength(supporter_id, _memo)
            weight = belief.get("support_weights", {}).get(supporter_id, 1.0)

            contribution = supporter_strength * weight * (1.0 - intrinsic)
            total_contribution += contribution

        effective = min(1.0, max(0.0, intrinsic + total_contribution))
        _memo[belief_id] = effective

        return effective

    # ============================================================
    # BELIEF UPDATES FROM OUTCOMES
    # Papers #1, #9, #12
    # ============================================================

    def update_belief_from_outcome(
        self,
        belief_id: str,
        context_key: str,
        outcome: str,
        difficulty_level: int,
        is_end_memory: bool = False,
        emotional_intensity: float = 0.5,
    ) -> BeliefStrengthEvent:
        """
        Update belief strength based on outcome.

        Implements:
        - Paper #1: EMA updates based on outcome
        - Paper #9: Moral Asymmetry (category multipliers)
        - Paper #12: Peak-End Rule (intensity/end weighting)

        Returns immutable event for audit trail (Paper #7).
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")

        # Get or create context state
        state = self.get_or_create_context_state(belief_id, context_key)
        old_strength = state["strength"]

        # Outcome signal
        outcome_signals = {
            "success": 1.0,
            "validation": 1.0,
            "neutral": 0.0,
            "failure": -1.0,
            "correction": -1.0,
        }
        signal = outcome_signals.get(outcome, 0.0)

        # Category multiplier (Paper #9)
        category = belief["category"]
        multipliers = CATEGORY_MULTIPLIERS[category]
        category_mult = multipliers["success"] if signal > 0 else multipliers["failure"]

        # Peak-End multiplier (Paper #12)
        peak_end_mult = 1.0
        if is_end_memory or emotional_intensity > PEAK_INTENSITY_THRESHOLD:
            peak_end_mult = PEAK_END_MULTIPLIER
            belief["is_end_memory_influenced"] = True
            belief["peak_intensity"] = max(belief.get("peak_intensity", 0.0), emotional_intensity)

        # Difficulty weight (Paper #16)
        difficulty_mult = DIFFICULTY_WEIGHTS.get(difficulty_level, 1.0)

        # EMA update
        total_signal = signal * category_mult * peak_end_mult * difficulty_mult
        new_strength = max(0.0, min(1.0, old_strength + LEARNING_RATE * total_signal))

        # Update state
        state["strength"] = new_strength
        state["last_updated"] = datetime.now().isoformat()
        state["last_outcome"] = outcome

        if signal > 0:
            state["success_count"] = state.get("success_count", 0) + 1
            belief["success_count"] = belief.get("success_count", 0) + 1
        elif signal < 0:
            state["failure_count"] = state.get("failure_count", 0) + 1
            belief["failure_count"] = belief.get("failure_count", 0) + 1

        # Check for moral violation circuit breaker (Paper #9)
        if category == "ethical" and signal < 0:
            belief["moral_violation_count"] = belief.get("moral_violation_count", 0) + 1
            if belief["moral_violation_count"] >= 2:
                belief["is_distrusted"] = True

        # Update belief's base strength
        belief["strength"] = new_strength
        belief["last_updated"] = datetime.now().isoformat()

        # Cascade to supported beliefs (Paper #11)
        self.cascade_strength_update(belief_id, new_strength)

        # Create immutable event (Paper #7)
        event: BeliefStrengthEvent = {
            "event_id": generate_id(),
            "event_type": "belief_strength_update",
            "belief_id": belief_id,
            "context_key": context_key,
            "old_strength": old_strength,
            "new_strength": new_strength,
            "outcome": outcome,
            "difficulty_level": difficulty_level,
            "category_multiplier": category_mult,
            "peak_end_multiplier": peak_end_mult,
            "timestamp": datetime.now().isoformat(),
        }

        return event

    # ============================================================
    # A.C.R.E. - CATEGORY-SPECIFIC INVALIDATION
    # Paper #10
    # ============================================================

    def check_invalidation_allowed(
        self, belief_id: str, proposed_strength: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check if invalidation is allowed for this belief.

        Paper #10: Category-Specific Invalidation Thresholds

        Returns (allowed, reason_if_not_allowed)
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return (True, None)

        current = belief["strength"]
        threshold = belief.get(
            "invalidation_threshold", INVALIDATION_THRESHOLDS[belief["category"]]
        )

        # Only check if trying to significantly weaken
        if proposed_strength >= current - 0.1:
            return (True, None)

        # If current strength is above threshold, require confirmation
        if current >= threshold:
            return (
                False,
                f"Belief strength {current:.2f} exceeds invalidation threshold {threshold:.2f} for {belief['category']} category. Human confirmation required.",
            )

        return (True, None)

    # ============================================================
    # ACTIVATION
    # ============================================================

    def get_activated_beliefs(
        self, context_key: str, min_strength: float = 0.3, limit: int = 20
    ) -> list[BeliefState]:
        """
        Get beliefs activated by this context.
        Returns beliefs sorted by resolved strength.
        """
        activated = []

        for belief_id, belief in self.beliefs.items():
            # Skip distrusted beliefs
            if belief.get("is_distrusted"):
                continue

            state = self.resolve_belief_for_context(belief_id, context_key)
            if state and state.get("strength", 0) >= min_strength:
                activated.append(
                    {
                        **belief,
                        "resolved_strength": state["strength"],
                        "resolved_context": context_key,
                    }
                )

        # Sort by strength
        activated.sort(key=lambda b: b["resolved_strength"], reverse=True)

        return activated[:limit]

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def serialize(self) -> str:
        """Serialize to JSON for Postgres storage"""
        return json.dumps(
            {
                "nodes": {n: dict(d) for n, d in self.G.nodes(data=True)},
                "edges": [(u, v, dict(d)) for u, v, d in self.G.edges(data=True)],
                "beliefs": self.beliefs,
            },
            default=str,
        )

    @classmethod
    def deserialize(cls, json_str: str) -> "BeliefGraph":
        """Restore from Postgres JSON"""
        data = json.loads(json_str)
        graph = cls()

        for node_id, attrs in data.get("nodes", {}).items():
            graph.G.add_node(node_id, **attrs)

        for source, target, attrs in data.get("edges", []):
            graph.G.add_edge(source, target, **attrs)

        graph.beliefs = data.get("beliefs", {})
        return graph

    def to_dict(self) -> dict:
        """Convert to dictionary (for non-JSON storage)"""
        return {
            "nodes": dict(self.G.nodes(data=True)),
            "edges": list(self.G.edges(data=True)),
            "beliefs": self.beliefs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BeliefGraph":
        """Restore from dictionary"""
        graph = cls()

        for node_id, attrs in data.get("nodes", {}).items():
            graph.G.add_node(node_id, **attrs)

        for source, target, attrs in data.get("edges", []):
            graph.G.add_edge(source, target, **attrs)

        graph.beliefs = data.get("beliefs", {})
        return graph


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def create_belief_hierarchy(
    foundation: BeliefState, derived: list[BeliefState], weights: list[float] = None
) -> BeliefGraph:
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
    if weights is None:
        weights = [0.8] * len(derived)

    graph = BeliefGraph()
    graph.add_belief(foundation)

    for belief, weight in zip(derived, weights):
        graph.add_belief(belief)
        graph.add_support_relationship(foundation["belief_id"], belief["belief_id"], weight)

    return graph


# ============================================================
# SINGLETON INSTANCE
# ============================================================

import threading

_belief_graph: Optional[BeliefGraph] = None
_belief_graph_lock: threading.Lock = threading.Lock()


def get_belief_graph() -> BeliefGraph:
    """Get singleton belief graph instance (thread-safe)"""
    global _belief_graph
    if _belief_graph is None:
        with _belief_graph_lock:
            # Double-check after acquiring lock
            if _belief_graph is None:
                _belief_graph = BeliefGraph()
    return _belief_graph


def reset_belief_graph() -> None:
    """Reset the singleton (for testing)"""
    global _belief_graph
    with _belief_graph_lock:
        _belief_graph = None


# ============================================================
# SEED INITIAL BELIEFS
# ============================================================


def seed_initial_beliefs(graph: Optional[BeliefGraph] = None) -> BeliefGraph:
    """
    Seed the belief graph with initial beliefs for testing/development.

    These represent the "25-year-old finance hire" baseline.

    MARS taxonomy: moral, competence, technical, preference, identity
    """
    if graph is None:
        graph = get_belief_graph()

    # Core accounting beliefs using MARS taxonomy
    core_beliefs = [
        # IDENTITY beliefs (immutable, strength locked)
        {
            "belief_id": "identity_honest",
            "category": "identity",
            "statement": "I never assist with fraud or deception",
            "scope": "*|*|*",
            "strength": 1.0,
            "immutable": True,
            "invalidatable": False,
            "tags": ["identity", "core"],
        },
        {
            "belief_id": "identity_acknowledge_uncertainty",
            "category": "identity",
            "statement": "I acknowledge when I am uncertain",
            "scope": "*|*|*",
            "strength": 1.0,
            "immutable": True,
            "invalidatable": False,
            "tags": ["identity", "core"],
        },
        {
            "belief_id": "identity_escalate",
            "category": "identity",
            "statement": "I escalate issues beyond my authority",
            "scope": "*|*|*",
            "strength": 1.0,
            "immutable": True,
            "invalidatable": False,
            "tags": ["identity", "core"],
        },
        # MORAL beliefs (hard to change, 10x failure multiplier)
        {
            "belief_id": "moral_confidentiality",
            "category": "moral",
            "statement": "Client and company financial information must be kept confidential",
            "scope": "*|*|*",
            "strength": 0.98,
            "immutable": False,
            "invalidatable": False,
            "tags": ["moral", "core"],
        },
        {
            "belief_id": "moral_accuracy",
            "category": "moral",
            "statement": "Financial records must be accurate and truthful",
            "scope": "*|*|*",
            "strength": 0.95,
            "immutable": False,
            "invalidatable": False,
            "tags": ["moral", "gaap"],
        },
        # COMPETENCE beliefs (how to do things)
        {
            "belief_id": "competence_authorization",
            "category": "competence",
            "statement": "All transactions require proper authorization",
            "scope": "*|*|*",
            "strength": 0.9,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "controls"],
        },
        {
            "belief_id": "competence_segregation",
            "category": "competence",
            "statement": "Segregation of duties must be maintained for key processes",
            "scope": "*|*|*",
            "strength": 0.85,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "controls"],
        },
        {
            "belief_id": "competence_3way_match",
            "category": "competence",
            "statement": "Invoices should be matched to PO and receiving report before payment",
            "scope": "invoice_processing|*|*",
            "strength": 0.8,
            "immutable": False,
            "invalidatable": True,
            "tags": ["competence", "ap"],
        },
        {
            "belief_id": "competence_cutoff",
            "category": "competence",
            "statement": "Transactions must be recorded in the correct period",
            "scope": "month_end|*|*",
            "strength": 0.9,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "close"],
        },
        {
            "belief_id": "competence_reconciliation",
            "category": "competence",
            "statement": "All balance sheet accounts should be reconciled monthly",
            "scope": "month_end|*|*",
            "strength": 0.85,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "close"],
        },
        # TECHNICAL beliefs (domain facts)
        {
            "belief_id": "technical_gl_coding",
            "category": "technical",
            "statement": "Invoices must have appropriate GL coding before posting",
            "scope": "invoice_processing|*|*",
            "strength": 0.85,
            "immutable": False,
            "invalidatable": False,
            "tags": ["technical", "gl"],
        },
        # PREFERENCE beliefs (style, flexible)
        {
            "belief_id": "preference_professional",
            "category": "preference",
            "statement": "Communication should be professional and clear",
            "scope": "*|*|*",
            "strength": 0.8,
            "immutable": False,
            "invalidatable": True,
            "tags": ["preference", "style"],
        },
        {
            "belief_id": "preference_concise",
            "category": "preference",
            "statement": "Explanations should be thorough but concise",
            "scope": "*|*|*",
            "strength": 0.7,
            "immutable": False,
            "invalidatable": True,
            "tags": ["preference", "style"],
        },
    ]

    for belief in core_beliefs:
        graph.add_belief(belief)

    # Add support relationships (moral beliefs support competence beliefs)
    graph.add_support_relationship("moral_accuracy", "technical_gl_coding", 0.8)
    graph.add_support_relationship("moral_accuracy", "competence_cutoff", 0.9)
    graph.add_support_relationship("competence_authorization", "competence_3way_match", 0.85)

    return graph
