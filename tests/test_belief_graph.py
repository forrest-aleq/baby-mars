"""
Belief Graph Tests
===================

Tests for the BeliefGraph class including:
- Graph management (add, get, relationships)
- Context resolution with backoff
- Autonomy level computation
- Cascading strength updates
- Belief updates from outcomes
- A.C.R.E. invalidation checks
- Serialization/deserialization
"""

import pytest
from datetime import datetime


class TestBeliefGraphBasics:
    """Test basic belief graph operations."""

    def test_add_belief(self, empty_belief_graph, sample_belief):
        """Can add a belief to the graph."""
        empty_belief_graph.add_belief(sample_belief)

        assert sample_belief["belief_id"] in empty_belief_graph.beliefs
        assert empty_belief_graph.G.has_node(sample_belief["belief_id"])

    def test_add_belief_initializes_missing_fields(self, empty_belief_graph):
        """add_belief should initialize missing list/dict fields."""
        minimal_belief = {
            "belief_id": "test-123",
            "statement": "Test",
            "category": "competence",
            "strength": 0.5,
        }

        empty_belief_graph.add_belief(minimal_belief)
        belief = empty_belief_graph.get_belief("test-123")

        assert belief["supports"] == []
        assert belief["supported_by"] == []
        assert belief["support_weights"] == {}

    def test_get_belief(self, populated_belief_graph, sample_belief):
        """Can retrieve a belief by ID."""
        result = populated_belief_graph.get_belief(sample_belief["belief_id"])

        assert result is not None
        assert result["statement"] == sample_belief["statement"]

    def test_get_belief_returns_none_for_missing(self, empty_belief_graph):
        """get_belief returns None for non-existent ID."""
        result = empty_belief_graph.get_belief("non-existent-id")
        assert result is None

    def test_get_all_beliefs(self, populated_belief_graph):
        """get_all_beliefs returns all beliefs."""
        beliefs = populated_belief_graph.get_all_beliefs()

        assert len(beliefs) == 2

    def test_get_beliefs_by_category(self, populated_belief_graph):
        """Can filter beliefs by category."""
        moral_beliefs = populated_belief_graph.get_beliefs_by_category("moral")
        competence_beliefs = populated_belief_graph.get_beliefs_by_category("competence")

        assert len(moral_beliefs) == 1
        assert len(competence_beliefs) == 1
        assert moral_beliefs[0]["category"] == "moral"


class TestSupportRelationships:
    """Test belief support relationships (Paper #11)."""

    def test_add_support_relationship(self, hierarchical_belief_graph):
        """Can add support relationships."""
        graph, foundation, derived1, _ = hierarchical_belief_graph

        # Check graph edges
        assert graph.G.has_edge(foundation["belief_id"], derived1["belief_id"])

        # Check belief metadata
        assert derived1["belief_id"] in foundation["supports"]
        assert foundation["belief_id"] in derived1["supported_by"]

    def test_add_support_relationship_invalid_supporter(self, populated_belief_graph, sample_belief):
        """Should raise error for non-existent supporter."""
        with pytest.raises(ValueError, match="Supporter belief"):
            populated_belief_graph.add_support_relationship(
                "non-existent",
                sample_belief["belief_id"],
                0.8
            )

    def test_add_support_relationship_invalid_supported(self, populated_belief_graph, sample_belief):
        """Should raise error for non-existent supported belief."""
        with pytest.raises(ValueError, match="Supported belief"):
            populated_belief_graph.add_support_relationship(
                sample_belief["belief_id"],
                "non-existent",
                0.8
            )

    def test_support_weight_stored(self, hierarchical_belief_graph):
        """Support weight should be stored in belief metadata."""
        graph, foundation, derived1, _ = hierarchical_belief_graph

        weight = derived1["support_weights"].get(foundation["belief_id"])
        assert weight == 0.9  # Set in fixture


class TestContextResolution:
    """Test context-conditional belief resolution (Paper #4)."""

    def test_resolve_exact_context(self, empty_belief_graph, sample_belief):
        """Should resolve exact context match."""
        empty_belief_graph.add_belief(sample_belief)

        result = empty_belief_graph.resolve_belief_for_context(
            sample_belief["belief_id"],
            sample_belief["context_key"]
        )

        assert result is not None
        assert result["strength"] == sample_belief["strength"]

    def test_resolve_with_backoff(self, empty_belief_graph):
        """Should use backoff ladder for non-exact matches."""
        from src.state.schema import create_belief

        belief = create_belief(
            statement="Test",
            category="competence",
            initial_strength=0.8,
            context_key="*|*|*"  # Global context
        )
        empty_belief_graph.add_belief(belief)

        # Query with specific context should backoff to global
        result = empty_belief_graph.resolve_belief_for_context(
            belief["belief_id"],
            "ClientA|month-end|>10K"
        )

        assert result is not None
        assert result["strength"] == 0.8

    def test_backoff_ladder_generation(self, empty_belief_graph):
        """Test the backoff ladder generation."""
        ladder = empty_belief_graph._build_backoff_ladder("ClientA|month-end|>10K")

        expected = [
            "ClientA|month-end|>10K",  # Exact
            "ClientA|month-end|*",      # Drop amount
            "ClientA|*|*",              # Drop period
            "*|*|*"                     # Global
        ]
        assert ladder == expected

    def test_resolve_returns_none_for_missing_belief(self, empty_belief_graph):
        """Should return None for non-existent belief."""
        result = empty_belief_graph.resolve_belief_for_context(
            "non-existent",
            "*|*|*"
        )
        assert result is None


class TestGetOrCreateContextState:
    """Test context state creation."""

    def test_get_existing_context_state(self, empty_belief_graph, sample_belief):
        """Should return existing context state."""
        empty_belief_graph.add_belief(sample_belief)

        state = empty_belief_graph.get_or_create_context_state(
            sample_belief["belief_id"],
            sample_belief["context_key"]
        )

        assert state["strength"] == sample_belief["strength"]

    def test_create_new_context_state(self, empty_belief_graph, sample_belief):
        """Should create new context state if not exists."""
        empty_belief_graph.add_belief(sample_belief)

        state = empty_belief_graph.get_or_create_context_state(
            sample_belief["belief_id"],
            "new|context|key"
        )

        assert state is not None
        assert state["success_count"] == 0
        assert state["failure_count"] == 0

    def test_new_context_inherits_from_parent(self, empty_belief_graph):
        """New context should inherit strength from parent context."""
        from src.state.schema import create_belief

        belief = create_belief(
            statement="Test",
            category="competence",
            initial_strength=0.9,
            context_key="*|*|*"
        )
        empty_belief_graph.add_belief(belief)

        state = empty_belief_graph.get_or_create_context_state(
            belief["belief_id"],
            "specific|*|*"
        )

        # Should inherit from parent (*|*|*)
        assert state["strength"] == 0.9


class TestAutonomyLevel:
    """Test autonomy level computation (Paper #1)."""

    def test_low_strength_guidance_seeking(self, empty_belief_graph):
        """Low strength should result in guidance_seeking."""
        from src.state.schema import create_belief

        belief = create_belief("Test", "competence", initial_strength=0.3)
        empty_belief_graph.add_belief(belief)

        level = empty_belief_graph.get_autonomy_level(
            belief["belief_id"],
            belief["context_key"]
        )

        assert level == "guidance_seeking"

    def test_medium_strength_action_proposal(self, empty_belief_graph):
        """Medium strength should result in action_proposal."""
        from src.state.schema import create_belief

        belief = create_belief("Test", "competence", initial_strength=0.5)
        empty_belief_graph.add_belief(belief)

        level = empty_belief_graph.get_autonomy_level(
            belief["belief_id"],
            belief["context_key"]
        )

        assert level == "action_proposal"

    def test_high_strength_autonomous(self, empty_belief_graph):
        """High strength should result in autonomous."""
        from src.state.schema import create_belief

        belief = create_belief("Test", "competence", initial_strength=0.85)
        empty_belief_graph.add_belief(belief)

        level = empty_belief_graph.get_autonomy_level(
            belief["belief_id"],
            belief["context_key"]
        )

        assert level == "autonomous"

    def test_missing_belief_guidance_seeking(self, empty_belief_graph):
        """Missing belief should default to guidance_seeking."""
        level = empty_belief_graph.get_autonomy_level(
            "non-existent",
            "*|*|*"
        )

        assert level == "guidance_seeking"

    def test_aggregate_autonomy(self, empty_belief_graph):
        """Test aggregate autonomy for multiple beliefs."""
        from src.state.schema import create_belief

        belief1 = create_belief("B1", "competence", initial_strength=0.8)
        belief2 = create_belief("B2", "competence", initial_strength=0.6)
        empty_belief_graph.add_belief(belief1)
        empty_belief_graph.add_belief(belief2)

        mode, avg = empty_belief_graph.get_aggregate_autonomy(
            [belief1["belief_id"], belief2["belief_id"]],
            "*|*|*"
        )

        assert avg == pytest.approx(0.7)
        assert mode == "autonomous"  # >= 0.7


class TestCascadingUpdates:
    """Test cascading strength updates (Paper #11)."""

    def test_cascade_updates_supported_beliefs(self, hierarchical_belief_graph):
        """Updating foundation should cascade to derived beliefs."""
        graph, foundation, derived1, derived2 = hierarchical_belief_graph

        # Update foundation
        affected = graph.cascade_strength_update(
            foundation["belief_id"],
            0.5  # Decrease from 0.95
        )

        # Should affect all three beliefs
        assert len(affected) >= 2
        assert foundation["belief_id"] in affected

    def test_cascade_prevents_infinite_loops(self, hierarchical_belief_graph):
        """Cascade should handle cycles gracefully."""
        graph, foundation, derived1, _ = hierarchical_belief_graph

        # Add reverse relationship to create cycle
        graph.add_support_relationship(
            derived1["belief_id"],
            foundation["belief_id"],
            0.3
        )

        # Should not infinite loop
        affected = graph.cascade_strength_update(foundation["belief_id"], 0.8)

        assert foundation["belief_id"] in affected

    def test_compute_effective_strength(self, hierarchical_belief_graph):
        """Test effective strength computation with support."""
        graph, foundation, derived1, _ = hierarchical_belief_graph

        effective = graph.compute_effective_strength(derived1["belief_id"])

        # Should be > intrinsic due to support
        intrinsic = derived1["strength"]
        assert effective >= intrinsic


class TestBeliefOutcomeUpdates:
    """Test belief updates from outcomes (Papers #1, #9, #12)."""

    def test_success_increases_strength(self, empty_belief_graph, sample_belief):
        """Success outcome should increase belief strength."""
        empty_belief_graph.add_belief(sample_belief)
        initial_strength = sample_belief["strength"]

        event = empty_belief_graph.update_belief_from_outcome(
            sample_belief["belief_id"],
            sample_belief["context_key"],
            outcome="success",
            difficulty_level=3
        )

        new_strength = sample_belief["strength"]
        assert new_strength > initial_strength
        assert event["old_strength"] == initial_strength
        assert event["new_strength"] == new_strength

    def test_failure_decreases_strength(self, empty_belief_graph, sample_belief):
        """Failure outcome should decrease belief strength."""
        empty_belief_graph.add_belief(sample_belief)
        initial_strength = sample_belief["strength"]

        empty_belief_graph.update_belief_from_outcome(
            sample_belief["belief_id"],
            sample_belief["context_key"],
            outcome="failure",
            difficulty_level=3
        )

        new_strength = sample_belief["strength"]
        assert new_strength < initial_strength

    def test_moral_failure_asymmetric(self, empty_belief_graph, sample_moral_belief):
        """Moral failures should have larger impact than successes."""
        empty_belief_graph.add_belief(sample_moral_belief)

        # Record baseline
        baseline = sample_moral_belief["strength"]

        # Apply failure
        empty_belief_graph.update_belief_from_outcome(
            sample_moral_belief["belief_id"],
            "*|*|*",
            outcome="failure",
            difficulty_level=3
        )

        failure_drop = baseline - sample_moral_belief["strength"]

        # Reset
        sample_moral_belief["strength"] = baseline
        sample_moral_belief["context_states"]["*|*|*"]["strength"] = baseline

        # Apply success
        empty_belief_graph.update_belief_from_outcome(
            sample_moral_belief["belief_id"],
            "*|*|*",
            outcome="success",
            difficulty_level=3
        )

        success_increase = sample_moral_belief["strength"] - baseline

        # Failure impact should be greater (10x multiplier vs 3x)
        assert failure_drop > success_increase

    def test_peak_end_multiplier(self, empty_belief_graph, sample_belief):
        """High emotional intensity should apply peak-end multiplier."""
        empty_belief_graph.add_belief(sample_belief)
        initial = sample_belief["strength"]

        empty_belief_graph.update_belief_from_outcome(
            sample_belief["belief_id"],
            sample_belief["context_key"],
            outcome="success",
            difficulty_level=3,
            is_end_memory=True,
            emotional_intensity=0.9
        )

        assert sample_belief["is_end_memory_influenced"] == True
        assert sample_belief["peak_intensity"] >= 0.9

    def test_success_count_increments(self, empty_belief_graph, sample_belief):
        """Success should increment success_count."""
        empty_belief_graph.add_belief(sample_belief)

        empty_belief_graph.update_belief_from_outcome(
            sample_belief["belief_id"],
            sample_belief["context_key"],
            outcome="success",
            difficulty_level=3
        )

        assert sample_belief["success_count"] == 1

    def test_failure_count_increments(self, empty_belief_graph, sample_belief):
        """Failure should increment failure_count."""
        empty_belief_graph.add_belief(sample_belief)

        empty_belief_graph.update_belief_from_outcome(
            sample_belief["belief_id"],
            sample_belief["context_key"],
            outcome="failure",
            difficulty_level=3
        )

        assert sample_belief["failure_count"] == 1


class TestACREInvalidation:
    """Test A.C.R.E. invalidation checks (Paper #10)."""

    def test_allows_small_decrease(self, empty_belief_graph, sample_belief):
        """Small strength decrease should be allowed."""
        empty_belief_graph.add_belief(sample_belief)

        allowed, reason = empty_belief_graph.check_invalidation_allowed(
            sample_belief["belief_id"],
            sample_belief["strength"] - 0.05  # Small decrease
        )

        assert allowed == True

    def test_blocks_large_decrease_above_threshold(self, empty_belief_graph):
        """Large decrease of high-strength belief should be blocked."""
        from src.state.schema import create_belief

        belief = create_belief("Test", "moral", initial_strength=0.98)
        empty_belief_graph.add_belief(belief)

        allowed, reason = empty_belief_graph.check_invalidation_allowed(
            belief["belief_id"],
            0.5  # Large decrease
        )

        assert allowed == False
        assert "threshold" in reason.lower()

    def test_identity_always_blocked(self, empty_belief_graph, sample_identity_belief):
        """Identity beliefs should never be invalidated."""
        empty_belief_graph.add_belief(sample_identity_belief)

        allowed, reason = empty_belief_graph.check_invalidation_allowed(
            sample_identity_belief["belief_id"],
            0.1  # Try to invalidate
        )

        # Identity has threshold 1.0, so any significant decrease is blocked
        assert allowed == False


class TestActivation:
    """Test belief activation."""

    def test_get_activated_beliefs(self, populated_belief_graph):
        """Should return beliefs above minimum strength."""
        activated = populated_belief_graph.get_activated_beliefs(
            "*|*|*",
            min_strength=0.5
        )

        # Both beliefs in fixture have strength >= 0.5
        assert len(activated) >= 1

    def test_activated_beliefs_sorted(self, populated_belief_graph):
        """Activated beliefs should be sorted by strength."""
        activated = populated_belief_graph.get_activated_beliefs(
            "*|*|*",
            min_strength=0.0
        )

        strengths = [b["resolved_strength"] for b in activated]
        assert strengths == sorted(strengths, reverse=True)

    def test_distrusted_beliefs_excluded(self, populated_belief_graph, sample_belief):
        """Distrusted beliefs should not be activated."""
        sample_belief["is_distrusted"] = True

        activated = populated_belief_graph.get_activated_beliefs("*|*|*")

        ids = [b["belief_id"] for b in activated]
        assert sample_belief["belief_id"] not in ids


class TestSerialization:
    """Test graph serialization/deserialization."""

    def test_serialize_deserialize_roundtrip(self, hierarchical_belief_graph):
        """Graph should survive serialization roundtrip."""
        graph, foundation, derived1, derived2 = hierarchical_belief_graph

        # Serialize
        json_str = graph.serialize()

        # Deserialize
        from src.graphs.belief_graph import BeliefGraph
        restored = BeliefGraph.deserialize(json_str)

        # Verify beliefs
        assert len(restored.beliefs) == len(graph.beliefs)
        assert foundation["belief_id"] in restored.beliefs

        # Verify edges
        assert restored.G.has_edge(foundation["belief_id"], derived1["belief_id"])

    def test_to_dict_from_dict_roundtrip(self, hierarchical_belief_graph):
        """Graph should survive dict roundtrip."""
        graph, foundation, _, _ = hierarchical_belief_graph

        # To dict
        data = graph.to_dict()

        # From dict
        from src.graphs.belief_graph import BeliefGraph
        restored = BeliefGraph.from_dict(data)

        assert len(restored.beliefs) == len(graph.beliefs)


class TestSingleton:
    """Test singleton behavior."""

    def test_get_belief_graph_singleton(self):
        """get_belief_graph should return same instance."""
        from src.graphs.belief_graph import get_belief_graph

        graph1 = get_belief_graph()
        graph2 = get_belief_graph()

        assert graph1 is graph2

    def test_reset_belief_graph(self):
        """reset_belief_graph should clear singleton."""
        from src.graphs.belief_graph import get_belief_graph, reset_belief_graph

        graph1 = get_belief_graph()
        reset_belief_graph()
        graph2 = get_belief_graph()

        assert graph1 is not graph2


class TestSeedInitialBeliefs:
    """Test initial belief seeding."""

    def test_seed_creates_beliefs(self):
        """seed_initial_beliefs should populate the graph."""
        from src.graphs.belief_graph import seed_initial_beliefs, BeliefGraph

        graph = BeliefGraph()
        seed_initial_beliefs(graph)

        assert len(graph.beliefs) > 0

    def test_seed_creates_identity_beliefs(self):
        """Should create immutable identity beliefs."""
        from src.graphs.belief_graph import seed_initial_beliefs, BeliefGraph

        graph = BeliefGraph()
        seed_initial_beliefs(graph)

        identity_beliefs = graph.get_beliefs_by_category("identity")
        assert len(identity_beliefs) >= 1

    def test_seed_creates_support_relationships(self):
        """Should create support relationships."""
        from src.graphs.belief_graph import seed_initial_beliefs, BeliefGraph

        graph = BeliefGraph()
        seed_initial_beliefs(graph)

        # Check that graph has edges
        assert graph.G.number_of_edges() > 0

    def test_seed_uses_mars_taxonomy(self):
        """Should use MARS taxonomy (moral, competence, technical, preference, identity)."""
        from src.graphs.belief_graph import seed_initial_beliefs, BeliefGraph

        graph = BeliefGraph()
        seed_initial_beliefs(graph)

        categories = set(b["category"] for b in graph.beliefs.values())

        # Should use MARS categories, not old ones
        assert "moral" in categories or "identity" in categories
        assert "ethical" not in categories
        assert "procedural" not in categories
