"""
First Impression Tests
=======================

Tests for Aleq's first impression greeting generation system.

The first impression is critical - research shows impressions form
in 7 seconds and are incredibly persistent. These tests verify:

1. Prompt generation is psychology-informed
2. Time-awareness is properly applied
3. Peer positioning (not assistant positioning)
4. Context personalization works correctly
"""


# ============================================================
# FIRST IMPRESSION PROMPT TESTS
# ============================================================


class TestFirstImpressionPrompt:
    """Test first impression prompt generation."""

    def test_prompt_includes_person_name(self):
        """Verify person's name appears in the prompt."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Alice Smith",
            person_role="CFO",
            industry="manufacturing",
            temporal=temporal,
        )

        assert "Alice Smith" in prompt

    def test_prompt_includes_role(self):
        """Verify role context is included."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Bob Jones",
            person_role="Controller",
            industry="healthcare",
            temporal=temporal,
        )

        assert "Controller" in prompt
        assert "healthcare" in prompt

    def test_prompt_includes_psychology_guidance(self):
        """Verify psychology-informed guidance is present."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "afternoon",
            "day_of_week": "Wednesday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 14,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test User",
            person_role="Analyst",
            industry="tech",
            temporal=temporal,
        )

        # Psychology principles should be mentioned
        assert "first impression" in prompt.lower()
        assert "warmth" in prompt.lower()
        assert "peer" in prompt.lower()

    def test_prompt_warns_against_generic_greetings(self):
        """Verify prompt warns against generic greetings."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Tuesday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 10,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test User",
            person_role="Manager",
            industry="retail",
            temporal=temporal,
        )

        # Should warn against generic greetings
        assert "generic" in prompt.lower()
        assert "SHOULD NOT" in prompt or "should not" in prompt.lower()

    def test_prompt_warns_against_sycophantic(self):
        """Verify prompt warns against sycophantic behavior."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test User",
            person_role="Manager",
            industry="finance",
            temporal=temporal,
        )

        # Should warn against being sycophantic
        assert "sycophantic" in prompt.lower()


class TestTimeAwareness:
    """Test time-aware context in first impression prompts."""

    def test_morning_context(self):
        """Morning time gets appropriate context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Tuesday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "morning" in prompt.lower()

    def test_early_morning_context(self):
        """Very early morning (before 7am) gets special context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Wednesday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 5,  # Very early
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "early" in prompt.lower()

    def test_late_evening_context(self):
        """Late evening (after 8pm) gets special context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "night",
            "day_of_week": "Thursday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 21,  # 9pm
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "evening" in prompt.lower() or "late" in prompt.lower()

    def test_weekend_context(self):
        """Weekend gets special context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "afternoon",
            "day_of_week": "Saturday",
            "is_weekend": True,
            "is_month_end": False,
            "hour": 14,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "weekend" in prompt.lower()

    def test_month_end_context(self):
        """Month-end period gets urgent context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Friday",
            "is_weekend": False,
            "is_month_end": True,
            "hour": 10,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Controller",
            industry="finance",
            temporal=temporal,
        )

        assert "month-end" in prompt.lower() or "crunch" in prompt.lower()

    def test_friday_context(self):
        """Friday gets week-wrap context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "afternoon",
            "day_of_week": "Friday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 15,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "friday" in prompt.lower()

    def test_monday_context(self):
        """Monday gets week-start context."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        assert "monday" in prompt.lower()


# ============================================================
# BIRTH STATE CREATION TESTS
# ============================================================


class TestBirthStateCreation:
    """Test create_birth_state function."""

    def test_creates_valid_state(self):
        """Birth state has required structure."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Alice Smith",
            person_role="CFO",
            industry="manufacturing",
        )

        assert "thread_id" in state
        assert "org_id" in state
        assert state["org_id"] == "org_test"
        assert "messages" in state
        assert "trigger_context" in state

    def test_thread_id_has_birth_prefix(self):
        """Thread ID includes 'birth' prefix."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Test",
            person_role="Role",
            industry="Industry",
        )

        assert state["thread_id"].startswith("birth_")

    def test_trigger_context_marks_as_first_meeting(self):
        """Trigger context marks this as a first meeting."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Test",
            person_role="Role",
            industry="Industry",
        )

        trigger_ctx = state["trigger_context"]
        assert trigger_ctx["trigger_type"] == "birth"
        assert trigger_ctx["is_first_meeting"] is True
        assert trigger_ctx["is_proactive"] is True

    def test_person_context_included(self):
        """Person context is included in trigger context."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Alice Smith",
            person_role="CFO",
            industry="manufacturing",
        )

        person_ctx = state["trigger_context"]["person_context"]
        assert person_ctx["name"] == "Alice Smith"
        assert person_ctx["role"] == "CFO"
        assert person_ctx["industry"] == "manufacturing"

    def test_message_marked_as_synthetic(self):
        """The synthetic message is marked appropriately."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Test",
            person_role="Role",
            industry="Industry",
        )

        assert len(state["messages"]) == 1
        msg = state["messages"][0]
        assert msg["role"] == "system"
        assert msg.get("is_synthetic") is True
        assert msg.get("is_first_impression") is True

    def test_temporal_context_included(self):
        """Temporal context is included in objects."""
        from src.scheduler.message_factory import create_birth_state

        state = create_birth_state(
            org_id="org_test",
            person_name="Test",
            person_role="Role",
            industry="Industry",
        )

        assert "objects" in state
        assert "temporal" in state["objects"]
        temporal = state["objects"]["temporal"]
        assert "time_of_day" in temporal
        assert "day_of_week" in temporal


# ============================================================
# PEER POSITIONING TESTS
# ============================================================


class TestPeerPositioning:
    """Test that prompts position Aleq as a peer, not an assistant."""

    def test_prompt_mentions_peer_language(self):
        """Prompt encourages peer language."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        # Should encourage peer language
        assert "peer" in prompt.lower()
        # Should discourage assistant positioning
        assert (
            "not an assistant" in prompt.lower()
            or "not assistant" in prompt.lower()
            or 'not "I\'m here to help you"' in prompt
        )

    def test_prompt_encourages_working_together_language(self):
        """Prompt encourages 'working together' over 'help you'."""
        from src.scheduler.message_factory import _create_first_impression_prompt

        temporal = {
            "time_of_day": "morning",
            "day_of_week": "Monday",
            "is_weekend": False,
            "is_month_end": False,
            "hour": 9,
        }

        prompt = _create_first_impression_prompt(
            person_name="Test",
            person_role="Manager",
            industry="tech",
            temporal=temporal,
        )

        # Should mention working together pattern
        assert "working together" in prompt.lower()
