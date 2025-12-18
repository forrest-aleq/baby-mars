"""
State Schema Tests
===================

Tests for the Baby MARS state schema including:
- UUID generation (full UUIDs, no truncation)
- Reducers (task_reducer, note_reducer)
- Factory functions
- Relationship value computation
"""

import pytest
from datetime import datetime, timedelta
import uuid


class TestUUIDGeneration:
    """Test UUID generation to ensure no truncation."""

    def test_generate_id_returns_full_uuid(self):
        """Ensure generate_id returns a full UUID, not truncated."""
        from src.state.schema import generate_id

        generated = generate_id()

        # Should be a valid UUID string
        parsed = uuid.UUID(generated)
        assert str(parsed) == generated

        # Should be full length (36 chars with hyphens)
        assert len(generated) == 36

    def test_generate_id_is_unique(self):
        """Ensure generate_id produces unique values."""
        from src.state.schema import generate_id

        ids = [generate_id() for _ in range(1000)]

        # All should be unique
        assert len(set(ids)) == 1000

    def test_belief_id_is_full_uuid(self, sample_belief):
        """Ensure beliefs get full UUID IDs."""
        belief_id = sample_belief["belief_id"]

        # Should be valid UUID
        parsed = uuid.UUID(belief_id)
        assert str(parsed) == belief_id

    def test_memory_id_is_full_uuid(self, sample_memory):
        """Ensure memories get full UUID IDs."""
        memory_id = sample_memory["memory_id"]

        # Should be valid UUID
        parsed = uuid.UUID(memory_id)
        assert str(parsed) == memory_id

    def test_person_id_is_full_uuid(self, sample_person):
        """Ensure persons get full UUID IDs."""
        person_id = sample_person["person_id"]

        # Should be valid UUID
        parsed = uuid.UUID(person_id)
        assert str(parsed) == person_id


class TestTaskReducer:
    """Test the task_reducer function."""

    def test_task_reducer_merges_by_id(self):
        """Tasks with same ID should be merged (new wins)."""
        from src.state.schema import task_reducer

        existing = [
            {"task_id": "t1", "description": "Old Task 1", "priority": 0.5},
            {"task_id": "t2", "description": "Task 2", "priority": 0.7},
        ]
        new = [
            {"task_id": "t1", "description": "Updated Task 1", "priority": 0.8},
        ]

        result = task_reducer(existing, new)

        # Should have t1 (updated) and t2
        assert len(result) == 2
        t1 = next(t for t in result if t["task_id"] == "t1")
        assert t1["description"] == "Updated Task 1"
        assert t1["priority"] == 0.8

    def test_task_reducer_limits_to_4(self):
        """Should keep max 4 tasks by priority."""
        from src.state.schema import task_reducer

        # Create 5 tasks with priorities 0.0, 0.1, 0.2, 0.3, 0.4
        existing = [
            {"task_id": f"t{i}", "priority": i * 0.1} for i in range(5)
        ]
        # Add one more with priority 0.6
        new = [
            {"task_id": "t5", "priority": 0.6},
        ]

        result = task_reducer(existing, new)

        # Should have exactly 4 tasks
        assert len(result) == 4

        # Should have highest priority ones (0.6, 0.4, 0.3, 0.2)
        priorities = sorted([t["priority"] for t in result], reverse=True)
        expected = [0.6, 0.4, 0.3, 0.2]
        assert priorities == pytest.approx(expected)

    def test_task_reducer_sorts_by_priority(self):
        """Result should be sorted by priority descending."""
        from src.state.schema import task_reducer

        existing = [
            {"task_id": "t1", "priority": 0.3},
            {"task_id": "t2", "priority": 0.9},
            {"task_id": "t3", "priority": 0.5},
        ]
        new = []

        result = task_reducer(existing, new)

        priorities = [t["priority"] for t in result]
        assert priorities == sorted(priorities, reverse=True)


class TestNoteReducer:
    """Test the note_reducer function."""

    def test_note_reducer_merges_by_id(self):
        """Notes with same ID should be merged (new wins)."""
        from src.state.schema import note_reducer

        now = datetime.now().isoformat()
        existing = [
            {"note_id": "n1", "content": "Old", "created_at": now, "ttl_hours": 24},
        ]
        new = [
            {"note_id": "n1", "content": "Updated", "created_at": now, "ttl_hours": 24},
        ]

        result = note_reducer(existing, new)

        assert len(result) == 1
        assert result[0]["content"] == "Updated"

    def test_note_reducer_expires_old_notes(self):
        """Notes past TTL should be expired."""
        from src.state.schema import note_reducer

        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        new_time = datetime.now().isoformat()

        existing = [
            {"note_id": "n1", "content": "Expired", "created_at": old_time, "ttl_hours": 24},
            {"note_id": "n2", "content": "Valid", "created_at": new_time, "ttl_hours": 24},
        ]
        new = []

        result = note_reducer(existing, new)

        # Only valid note should remain
        assert len(result) == 1
        assert result[0]["note_id"] == "n2"

    def test_note_reducer_handles_invalid_dates(self, monkeypatch):
        """Invalid date notes should be handled gracefully."""
        from src.state.schema import note_reducer
        import os

        # Not in production - keep invalid notes
        monkeypatch.setenv("ENVIRONMENT", "development")

        existing = [
            {"note_id": "n1", "content": "Bad date", "created_at": "not-a-date", "ttl_hours": 24},
        ]
        new = []

        result = note_reducer(existing, new)

        # In dev, should keep invalid note
        assert len(result) == 1

    def test_note_reducer_drops_invalid_in_production(self, monkeypatch):
        """Invalid notes should be dropped in production."""
        from src.state.schema import note_reducer

        monkeypatch.setenv("ENVIRONMENT", "production")

        existing = [
            {"note_id": "n1", "content": "Bad date", "created_at": "not-a-date", "ttl_hours": 24},
        ]
        new = []

        result = note_reducer(existing, new)

        # In production, should drop invalid note
        assert len(result) == 0


class TestRelationshipValue:
    """Test the relationship value computation."""

    def test_compute_relationship_value_formula(self):
        """Test the weighted relationship value formula."""
        from src.state.schema import compute_relationship_value

        # Formula: 0.6*authority + 0.2*interaction + 0.2*context
        result = compute_relationship_value(
            authority=1.0,
            interaction_strength=0.5,
            context_relevance=0.5
        )

        expected = 0.6 * 1.0 + 0.2 * 0.5 + 0.2 * 0.5
        assert result == pytest.approx(expected)

    def test_compute_relationship_value_zeros(self):
        """Test with all zeros."""
        from src.state.schema import compute_relationship_value

        result = compute_relationship_value(0.0, 0.0, 0.0)
        assert result == 0.0

    def test_compute_relationship_value_max(self):
        """Test with all max values."""
        from src.state.schema import compute_relationship_value

        result = compute_relationship_value(1.0, 1.0, 1.0)
        assert result == pytest.approx(1.0)

    def test_create_person_uses_compute_function(self):
        """Ensure create_person uses the compute function."""
        from src.state.schema import create_person, compute_relationship_value

        person = create_person("Test", "Role", authority=0.8)

        expected = compute_relationship_value(0.8, 0.5, 0.5)
        assert person["relationship_value"] == pytest.approx(expected)


class TestCreateBelief:
    """Test the create_belief factory function."""

    def test_create_belief_sets_defaults(self):
        """Test that create_belief sets all required fields."""
        from src.state.schema import create_belief

        belief = create_belief(
            statement="Test statement",
            category="competence"
        )

        assert belief["statement"] == "Test statement"
        assert belief["category"] == "competence"
        assert belief["strength"] == 0.5  # default
        assert belief["context_key"] == "*|*|*"  # default
        assert belief["supports"] == []
        assert belief["supported_by"] == []
        assert belief["support_weights"] == {}
        assert belief["is_distrusted"] == False
        assert belief["moral_violation_count"] == 0

    def test_create_belief_respects_category_threshold(self):
        """Different categories should have different invalidation thresholds."""
        from src.state.schema import create_belief, INVALIDATION_THRESHOLDS

        moral = create_belief("Moral belief", "moral")
        technical = create_belief("Technical belief", "technical")
        identity = create_belief("Identity belief", "identity")

        assert moral["invalidation_threshold"] == INVALIDATION_THRESHOLDS["moral"]
        assert technical["invalidation_threshold"] == INVALIDATION_THRESHOLDS["technical"]
        assert identity["invalidation_threshold"] == INVALIDATION_THRESHOLDS["identity"]

    def test_create_belief_initializes_context_state(self):
        """Should initialize context_states with the given context."""
        from src.state.schema import create_belief

        belief = create_belief(
            statement="Test",
            category="competence",
            initial_strength=0.8,
            context_key="test|*|*"
        )

        assert "test|*|*" in belief["context_states"]
        context_state = belief["context_states"]["test|*|*"]
        assert context_state["strength"] == 0.8
        assert context_state["success_count"] == 0
        assert context_state["failure_count"] == 0


class TestCreateInitialState:
    """Test the create_initial_state factory function."""

    def test_create_initial_state_sets_ids(self):
        """Should set all ID fields."""
        from src.state.schema import create_initial_state

        state = create_initial_state(
            thread_id="thread-1",
            org_id="org-1",
            user_id="user-1"
        )

        assert state["thread_id"] == "thread-1"
        assert state["org_id"] == "org-1"
        assert state["user_id"] == "user-1"

    def test_create_initial_state_initializes_lists(self):
        """Should initialize all list fields as empty."""
        from src.state.schema import create_initial_state

        state = create_initial_state("t", "o", "u")

        assert state["active_tasks"] == []
        assert state["notes"] == []
        assert state["messages"] == []
        assert state["activated_beliefs"] == []
        assert state["active_goals"] == []
        assert state["execution_results"] == []
        assert state["validation_results"] == []
        assert state["events"] == []

    def test_create_initial_state_sets_supervision_mode(self):
        """New states should start in guidance_seeking mode."""
        from src.state.schema import create_initial_state

        state = create_initial_state("t", "o", "u")

        assert state["supervision_mode"] == "guidance_seeking"
        assert state["belief_strength_for_action"] == 0.0

    def test_create_initial_state_initializes_temporal(self):
        """Should have temporal context with defaults."""
        from src.state.schema import create_initial_state

        state = create_initial_state("t", "o", "u")

        temporal = state["objects"]["temporal"]
        assert temporal["is_month_end"] == False
        assert temporal["is_quarter_end"] == False
        assert temporal["is_year_end"] == False
        assert temporal["urgency_multiplier"] == 1.0


class TestCategoryMultipliers:
    """Test the category multiplier constants."""

    def test_moral_has_asymmetric_multipliers(self):
        """Moral failures should have higher impact than successes."""
        from src.state.schema import CATEGORY_MULTIPLIERS

        moral = CATEGORY_MULTIPLIERS["moral"]
        assert moral["failure"] > moral["success"]
        assert moral["failure"] == 10.0
        assert moral["success"] == 3.0

    def test_identity_has_zero_multipliers(self):
        """Identity beliefs should be immutable (zero multipliers)."""
        from src.state.schema import CATEGORY_MULTIPLIERS

        identity = CATEGORY_MULTIPLIERS["identity"]
        assert identity["success"] == 0.0
        assert identity["failure"] == 0.0

    def test_preference_has_symmetric_multipliers(self):
        """Preference beliefs should update symmetrically."""
        from src.state.schema import CATEGORY_MULTIPLIERS

        preference = CATEGORY_MULTIPLIERS["preference"]
        assert preference["success"] == preference["failure"]
        assert preference["success"] == 1.0


class TestInvalidationThresholds:
    """Test the A.C.R.E. invalidation threshold constants."""

    def test_identity_cannot_be_invalidated(self):
        """Identity beliefs should have threshold of 1.0."""
        from src.state.schema import INVALIDATION_THRESHOLDS

        assert INVALIDATION_THRESHOLDS["identity"] == 1.0

    def test_moral_hard_to_invalidate(self):
        """Moral beliefs should be hard to invalidate."""
        from src.state.schema import INVALIDATION_THRESHOLDS

        assert INVALIDATION_THRESHOLDS["moral"] >= 0.9

    def test_preference_easier_to_invalidate(self):
        """Preference beliefs should be easiest to invalidate."""
        from src.state.schema import INVALIDATION_THRESHOLDS

        thresholds = INVALIDATION_THRESHOLDS
        assert thresholds["preference"] < thresholds["competence"]
        assert thresholds["preference"] < thresholds["moral"]


class TestAutonomyThresholds:
    """Test the autonomy threshold constants."""

    def test_guidance_seeking_lowest(self):
        """Guidance seeking should be the lowest threshold."""
        from src.state.schema import AUTONOMY_THRESHOLDS

        assert AUTONOMY_THRESHOLDS["guidance_seeking"] == 0.4

    def test_action_proposal_middle(self):
        """Action proposal should be middle threshold."""
        from src.state.schema import AUTONOMY_THRESHOLDS

        assert AUTONOMY_THRESHOLDS["action_proposal"] == 0.7

    def test_autonomous_highest(self):
        """Autonomous should be highest threshold."""
        from src.state.schema import AUTONOMY_THRESHOLDS

        assert AUTONOMY_THRESHOLDS["autonomous"] == 1.0
