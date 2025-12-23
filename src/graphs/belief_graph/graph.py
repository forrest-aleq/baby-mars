"""
Belief Graph Implementation
============================

NetworkX-backed belief hierarchy with cascading updates.
Implements Papers #4, #9, #10, #11, #12.
"""

from datetime import datetime
from typing import Any, Literal, Optional, cast

import networkx as nx

from ...state.schema import (
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
from .serialization import (
    deserialize_graph,
    graph_from_dict,
    graph_to_dict,
    serialize_graph,
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

    def __init__(self) -> None:
        self.G = nx.DiGraph()
        self.beliefs: dict[str, BeliefState] = {}

    # ============================================================
    # GRAPH MANAGEMENT
    # ============================================================

    def add_belief(self, belief: dict[str, Any]) -> None:
        """Add belief node to graph. Accepts partial dict, fills in defaults."""
        if "supports" not in belief:
            belief["supports"] = []
        if "supported_by" not in belief:
            belief["supported_by"] = []
        if "support_weights" not in belief:
            belief["support_weights"] = {}

        self.beliefs[belief["belief_id"]] = cast(BeliefState, belief)
        self.G.add_node(
            belief["belief_id"], category=belief["category"], strength=belief["strength"]
        )

    def add_support_relationship(
        self, supporter_id: str, supported_id: str, weight: float = 0.8
    ) -> None:
        """
        Add SUPPORTS edge (Paper #11: Hierarchical Beliefs).

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
        self.beliefs[supporter_id]["supports"].append(supported_id)
        self.beliefs[supported_id]["supported_by"].append(supporter_id)
        self.beliefs[supported_id]["support_weights"][supporter_id] = weight

    def get_belief(self, belief_id: str) -> Optional[BeliefState]:
        """Get belief by ID."""
        return self.beliefs.get(belief_id)

    def get_all_beliefs(self) -> list[BeliefState]:
        """Get all beliefs."""
        return list(self.beliefs.values())

    def get_beliefs_by_category(self, category: str) -> list[BeliefState]:
        """Get all beliefs in a category."""
        return [b for b in self.beliefs.values() if b["category"] == category]

    # ============================================================
    # CONTEXT RESOLUTION (Paper #4)
    # ============================================================

    def resolve_belief_for_context(
        self, belief_id: str, context_key: str
    ) -> Optional[ContextState]:
        """
        Find the most specific matching belief state using backoff.
        (Paper #4: Context-Conditional Beliefs)
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None

        context_states = belief.get("context_states", {})

        if context_key in context_states:
            return context_states[context_key]

        ladder = self._build_backoff_ladder(context_key)
        for candidate in ladder:
            if candidate in context_states:
                return context_states[candidate]

        if not context_states:
            return {
                "strength": belief.get("strength", 0.5),
                "last_updated": belief.get("last_updated"),
                "success_count": belief.get("success_count", 0),
                "failure_count": belief.get("failure_count", 0),
                "last_outcome": None,
            }

        return None

    def _build_backoff_ladder(self, context_key: str) -> list[str]:
        """Generate progressively more general contexts."""
        parts = context_key.split("|")
        ladder = [context_key]

        for i in range(len(parts) - 1, 0, -1):
            generalized = "|".join(parts[:i] + ["*"] * (len(parts) - i))
            ladder.append(generalized)

        ladder.append("|".join(["*"] * len(parts)))
        return ladder

    def get_or_create_context_state(self, belief_id: str, context_key: str) -> ContextState:
        """Get existing context state or create new one."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")

        context_states = belief.get("context_states", {})
        if context_key in context_states:
            return context_states[context_key]

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
    # AUTONOMY (Paper #1)
    # ============================================================

    def get_autonomy_level(self, belief_id: str, context_key: str) -> str:
        """Map belief strength to supervision mode (Paper #1)."""
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
        """Compute aggregate autonomy level for multiple beliefs."""
        if not belief_ids:
            return ("guidance_seeking", 0.0)

        strengths = []
        for belief_id in belief_ids:
            state = self.resolve_belief_for_context(belief_id, context_key)
            if state:
                strengths.append(state["strength"])
            else:
                strengths.append(0.3)

        avg_strength = sum(strengths) / len(strengths)

        if avg_strength < AUTONOMY_THRESHOLDS["guidance_seeking"]:
            mode = "guidance_seeking"
        elif avg_strength < AUTONOMY_THRESHOLDS["action_proposal"]:
            mode = "action_proposal"
        else:
            mode = "autonomous"

        return (mode, avg_strength)

    # ============================================================
    # CASCADING UPDATES (Paper #11)
    # ============================================================

    def cascade_strength_update(
        self, belief_id: str, new_strength: float, _visited: Optional[set[str]] = None
    ) -> list[str]:
        """
        Update belief strength and cascade to all supported beliefs.
        (Paper #11: Hierarchical Beliefs)
        """
        if _visited is None:
            _visited = set()

        if belief_id in _visited:
            return []

        _visited.add(belief_id)

        belief = self.beliefs.get(belief_id)
        if not belief:
            return []

        old_strength = belief["strength"]
        belief["strength"] = new_strength
        self.G.nodes[belief_id]["strength"] = new_strength

        affected = [belief_id]

        for _, supported_id, data in self.G.out_edges(belief_id, data=True):
            if data.get("rel_type") != "SUPPORTS":
                continue

            weight = data.get("weight", 1.0)
            supported_belief = self.beliefs.get(supported_id)
            if not supported_belief:
                continue

            intrinsic = supported_belief["strength"]
            old_contribution = old_strength * weight * (1 - intrinsic)
            new_contribution = new_strength * weight * (1 - intrinsic)

            delta = new_contribution - old_contribution
            new_effective = max(0.0, min(1.0, intrinsic + delta))

            affected.extend(self.cascade_strength_update(supported_id, new_effective, _visited))

        return affected

    def compute_effective_strength(
        self, belief_id: str, _memo: Optional[dict[str, float]] = None
    ) -> float:
        """Compute effective strength including support (Paper #11)."""
        if _memo is None:
            _memo = {}

        if belief_id in _memo:
            return _memo[belief_id]

        belief = self.beliefs.get(belief_id)
        if not belief:
            return 0.0

        intrinsic = belief["strength"]

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
    # BELIEF UPDATES (Papers #1, #9, #12)
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
        """Update belief strength based on outcome."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")

        state = self.get_or_create_context_state(belief_id, context_key)
        old_strength = state["strength"]

        signal = self._compute_outcome_signal(outcome)
        category_mult = self._get_category_multiplier(belief["category"], signal)
        peak_end_mult = self._apply_peak_end_rule(belief, is_end_memory, emotional_intensity)
        difficulty_mult = DIFFICULTY_WEIGHTS.get(difficulty_level, 1.0)

        total_signal = signal * category_mult * peak_end_mult * difficulty_mult
        new_strength = max(0.0, min(1.0, old_strength + LEARNING_RATE * total_signal))

        self._update_state_counts(state, belief, signal, new_strength, outcome)
        self._check_moral_violation(belief, signal)

        belief["strength"] = new_strength
        belief["last_updated"] = datetime.now().isoformat()

        self.cascade_strength_update(belief_id, new_strength)

        return self._create_strength_event(
            belief_id,
            context_key,
            old_strength,
            new_strength,
            outcome,
            difficulty_level,
            category_mult,
            peak_end_mult,
        )

    def _compute_outcome_signal(self, outcome: str) -> float:
        """Map outcome to numerical signal."""
        signals = {
            "success": 1.0,
            "validation": 1.0,
            "neutral": 0.0,
            "failure": -1.0,
            "correction": -1.0,
        }
        return signals.get(outcome, 0.0)

    def _get_category_multiplier(self, category: str, signal: float) -> float:
        """Get category multiplier (Paper #9)."""
        multipliers = CATEGORY_MULTIPLIERS[category]
        return multipliers["success"] if signal > 0 else multipliers["failure"]

    def _apply_peak_end_rule(
        self, belief: BeliefState, is_end_memory: bool, emotional_intensity: float
    ) -> float:
        """Apply peak-end rule (Paper #12)."""
        if is_end_memory or emotional_intensity > PEAK_INTENSITY_THRESHOLD:
            belief["is_end_memory_influenced"] = True
            belief["peak_intensity"] = max(belief.get("peak_intensity", 0.0), emotional_intensity)
            return PEAK_END_MULTIPLIER
        return 1.0

    def _update_state_counts(
        self,
        state: ContextState,
        belief: BeliefState,
        signal: float,
        new_strength: float,
        outcome: str,
    ) -> None:
        """Update success/failure counts."""
        state["strength"] = new_strength
        state["last_updated"] = datetime.now().isoformat()
        state["last_outcome"] = cast(
            Literal["success", "failure", "neutral", "validation", "correction"], outcome
        )

        if signal > 0:
            state["success_count"] = state.get("success_count", 0) + 1
            belief["success_count"] = belief.get("success_count", 0) + 1
        elif signal < 0:
            state["failure_count"] = state.get("failure_count", 0) + 1
            belief["failure_count"] = belief.get("failure_count", 0) + 1

    def _check_moral_violation(self, belief: BeliefState, signal: float) -> None:
        """Check for moral violation circuit breaker (Paper #9)."""
        if belief["category"] == "moral" and signal < 0:
            belief["moral_violation_count"] = belief.get("moral_violation_count", 0) + 1
            if belief["moral_violation_count"] >= 2:
                belief["is_distrusted"] = True

    def _create_strength_event(
        self,
        belief_id: str,
        context_key: str,
        old_strength: float,
        new_strength: float,
        outcome: str,
        difficulty_level: int,
        category_mult: float,
        peak_end_mult: float,
    ) -> BeliefStrengthEvent:
        """Create immutable event (Paper #7)."""
        return {
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

    # ============================================================
    # A.C.R.E. INVALIDATION (Paper #10)
    # ============================================================

    def check_invalidation_allowed(
        self, belief_id: str, proposed_strength: float
    ) -> tuple[bool, Optional[str]]:
        """Check if invalidation is allowed (Paper #10)."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return (True, None)

        current = belief["strength"]
        threshold = belief.get(
            "invalidation_threshold", INVALIDATION_THRESHOLDS[belief["category"]]
        )

        if proposed_strength >= current - 0.1:
            return (True, None)

        if current >= threshold:
            return (
                False,
                f"Belief strength {current:.2f} exceeds invalidation threshold "
                f"{threshold:.2f} for {belief['category']} category. "
                "Human confirmation required.",
            )

        return (True, None)

    # ============================================================
    # ACTIVATION
    # ============================================================

    def get_activated_beliefs(
        self, context_key: str, min_strength: float = 0.3, limit: int = 20
    ) -> list[BeliefState]:
        """Get beliefs activated by this context."""
        activated = []

        for belief_id, belief in self.beliefs.items():
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

        activated.sort(key=lambda b: float(str(b.get("resolved_strength", 0))), reverse=True)
        return cast(list[BeliefState], activated[:limit])

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def serialize(self) -> str:
        """Serialize to JSON for Postgres storage."""
        return serialize_graph(self)

    @classmethod
    def deserialize(cls, json_str: str) -> "BeliefGraph":
        """Restore from Postgres JSON."""
        return deserialize_graph(json_str, cls)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return graph_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BeliefGraph":
        """Restore from dictionary."""
        return graph_from_dict(data, cls)
