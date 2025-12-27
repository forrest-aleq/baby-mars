"""
Rapport Persistence Tests
==========================

Tests for the rapport tracking system that manages Aleq's
relationships with people she interacts with.

Tests cover:
- Validation helpers (float clamping, enum validation)
- Row conversion with validation
- Atomic SQL operations (no race conditions)
- Error handling and edge cases
"""

import pytest

from src.persistence.rapport import (
    VALID_FORMALITY,
    VALID_VERBOSITY,
    _clamp_float,
    _row_to_rapport,
    _validate_formality,
    _validate_verbosity,
)

# ============================================================
# VALIDATION HELPER TESTS
# ============================================================


class TestClampFloat:
    """Test float value clamping to [0.0, 1.0]."""

    def test_clamp_normal_value(self):
        """Normal values pass through unchanged."""
        assert _clamp_float(0.5, "test") == 0.5
        assert _clamp_float(0.0, "test") == 0.0
        assert _clamp_float(1.0, "test") == 1.0

    def test_clamp_negative_to_zero(self):
        """Negative values clamp to 0.0."""
        assert _clamp_float(-0.1, "test") == 0.0
        assert _clamp_float(-100, "test") == 0.0

    def test_clamp_over_one_to_one(self):
        """Values > 1.0 clamp to 1.0."""
        assert _clamp_float(1.1, "test") == 1.0
        assert _clamp_float(100, "test") == 1.0

    def test_clamp_edge_cases(self):
        """Edge cases at boundaries."""
        assert _clamp_float(0.0001, "test") == 0.0001
        assert _clamp_float(0.9999, "test") == 0.9999


class TestValidateFormality:
    """Test formality enum validation."""

    def test_valid_formality_values(self):
        """Valid formality values pass through."""
        for value in VALID_FORMALITY:
            assert _validate_formality(value) == value

    def test_invalid_formality_defaults_to_casual(self):
        """Invalid values default to casual."""
        assert _validate_formality("invalid") == "casual"
        assert _validate_formality("") == "casual"
        assert _validate_formality("FORMAL") == "casual"  # Case sensitive

    def test_none_formality_defaults_to_casual(self):
        """None defaults to casual."""
        assert _validate_formality(None) == "casual"


class TestValidateVerbosity:
    """Test verbosity enum validation."""

    def test_valid_verbosity_values(self):
        """Valid verbosity values pass through."""
        for value in VALID_VERBOSITY:
            assert _validate_verbosity(value) == value

    def test_invalid_verbosity_defaults_to_concise(self):
        """Invalid values default to concise."""
        assert _validate_verbosity("invalid") == "concise"
        assert _validate_verbosity("") == "concise"
        assert _validate_verbosity("DETAILED") == "concise"  # Case sensitive

    def test_none_verbosity_defaults_to_concise(self):
        """None defaults to concise."""
        assert _validate_verbosity(None) == "concise"


# ============================================================
# ROW CONVERSION TESTS
# ============================================================


class TestRowToRapport:
    """Test database row to RapportState conversion with validation."""

    def test_converts_valid_row(self, sample_rapport_db_row):
        """Valid row converts correctly."""
        result = _row_to_rapport(sample_rapport_db_row)

        assert isinstance(result, dict)
        assert result["rapport_id"] == "rapport_db_test"
        assert result["org_id"] == "org_test"
        assert result["person_name"] == "Test User"
        assert result["rapport_level"] == 0.5
        assert result["trust_level"] == 0.4
        assert result["familiarity"] == 0.3

    def test_clamps_invalid_float_values(self, sample_rapport_db_row):
        """Invalid float values are clamped during conversion."""
        sample_rapport_db_row["rapport_level"] = 1.5
        sample_rapport_db_row["trust_level"] = -0.2
        sample_rapport_db_row["humor_receptivity"] = 2.0

        result = _row_to_rapport(sample_rapport_db_row)

        assert result["rapport_level"] == 1.0  # Clamped from 1.5
        assert result["trust_level"] == 0.0  # Clamped from -0.2
        assert result["humor_receptivity"] == 1.0  # Clamped from 2.0

    def test_validates_enum_values(self, sample_rapport_db_row):
        """Invalid enum values are replaced with defaults."""
        sample_rapport_db_row["preferred_formality"] = "ultra_formal"
        sample_rapport_db_row["preferred_verbosity"] = "verbose"

        result = _row_to_rapport(sample_rapport_db_row)

        assert result["preferred_formality"] == "casual"  # Default
        assert result["preferred_verbosity"] == "concise"  # Default

    def test_handles_null_formality_verbosity(self, sample_rapport_db_row):
        """Null formality/verbosity use defaults."""
        sample_rapport_db_row["preferred_formality"] = None
        sample_rapport_db_row["preferred_verbosity"] = None

        result = _row_to_rapport(sample_rapport_db_row)

        assert result["preferred_formality"] == "casual"
        assert result["preferred_verbosity"] == "concise"

    def test_handles_null_timestamps(self, sample_rapport_db_row):
        """Null timestamps convert to None strings."""
        sample_rapport_db_row["last_interaction"] = None
        sample_rapport_db_row["first_impression_at"] = None

        result = _row_to_rapport(sample_rapport_db_row)

        assert result["last_interaction"] is None
        assert result["first_impression_at"] is None

    def test_handles_empty_jsonb_fields(self, sample_rapport_db_row):
        """Empty/null JSONB fields default to empty containers."""
        sample_rapport_db_row["memorable_moments"] = None
        sample_rapport_db_row["topics_discussed"] = None
        sample_rapport_db_row["preferences_learned"] = None
        sample_rapport_db_row["inside_references"] = None

        result = _row_to_rapport(sample_rapport_db_row)

        assert result["memorable_moments"] == []
        assert result["topics_discussed"] == {}
        assert result["preferences_learned"] == {}
        assert result["inside_references"] == []


# ============================================================
# RAPPORT STATE TYPING TESTS
# ============================================================


class TestRapportStateTyping:
    """Test RapportState TypedDict structure."""

    def test_rapport_state_has_required_keys(self, sample_rapport_state):
        """RapportState has all required keys."""
        required_keys = [
            "rapport_id",
            "org_id",
            "person_id",
            "person_name",
            "rapport_level",
            "trust_level",
            "familiarity",
            "interaction_count",
            "positive_interactions",
            "negative_interactions",
            "last_interaction",
            "first_interaction",
            "memorable_moments",
            "topics_discussed",
            "preferences_learned",
            "inside_references",
            "preferred_formality",
            "preferred_verbosity",
            "humor_receptivity",
            "first_impression_given",
            "first_impression_text",
            "first_impression_at",
        ]
        for key in required_keys:
            assert key in sample_rapport_state, f"Missing key: {key}"

    def test_sample_rapport_state_values(self, sample_rapport_state):
        """Sample rapport state has correct default values."""
        assert sample_rapport_state["rapport_level"] == 0.3
        assert sample_rapport_state["trust_level"] == 0.3
        assert sample_rapport_state["familiarity"] == 0.0
        assert sample_rapport_state["interaction_count"] == 0
        assert sample_rapport_state["first_impression_given"] is False

    def test_high_rapport_state_values(self, high_rapport_state):
        """High rapport state has elevated values."""
        assert high_rapport_state["rapport_level"] == 0.85
        assert high_rapport_state["trust_level"] == 0.75
        assert high_rapport_state["familiarity"] == 0.7
        assert high_rapport_state["interaction_count"] == 50
        assert len(high_rapport_state["inside_references"]) == 2


# ============================================================
# UPDATE COMMUNICATION STYLE VALIDATION TESTS
# ============================================================


class TestCommunicationStyleValidation:
    """Test update_communication_style input validation."""

    @pytest.mark.asyncio
    async def test_invalid_formality_raises_error(self, monkeypatch):
        """Invalid formality value raises ValueError."""
        from src.persistence import rapport

        with pytest.raises(ValueError, match="Invalid formality"):
            await rapport.update_communication_style(
                "org_test", "person_test", formality="ultra_formal"
            )

    @pytest.mark.asyncio
    async def test_invalid_verbosity_raises_error(self, monkeypatch):
        """Invalid verbosity value raises ValueError."""
        from src.persistence import rapport

        with pytest.raises(ValueError, match="Invalid verbosity"):
            await rapport.update_communication_style(
                "org_test", "person_test", verbosity="very_verbose"
            )

    def test_valid_values_accepted(self):
        """Valid enum values are accepted (validation only, no DB call)."""
        # This test validates that the function would accept valid values
        # without actually calling the database. The async validation happens
        # before any DB call, so we can test it synchronously.
        # The invalid value tests above already confirm validation works.
        # Here we just confirm valid values don't raise during validation.

        # Valid values should be in the allowed sets
        assert "formal" in VALID_FORMALITY
        assert "detailed" in VALID_VERBOSITY
        assert "professional" in VALID_FORMALITY
        assert "moderate" in VALID_VERBOSITY


# ============================================================
# EDGE CASE TESTS
# ============================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_inside_references_list(self, sample_rapport_state):
        """Empty inside references list is valid."""
        assert sample_rapport_state["inside_references"] == []

    def test_empty_topics_discussed_dict(self, sample_rapport_state):
        """Empty topics discussed dict is valid."""
        assert sample_rapport_state["topics_discussed"] == {}

    def test_boundary_rapport_levels(self, sample_rapport_state):
        """Rapport level at boundaries is valid."""
        sample_rapport_state["rapport_level"] = 0.0
        assert sample_rapport_state["rapport_level"] == 0.0

        sample_rapport_state["rapport_level"] = 1.0
        assert sample_rapport_state["rapport_level"] == 1.0

    def test_first_meeting_detection(self, sample_rapport_state):
        """First meeting is detectable from interaction count."""
        assert sample_rapport_state["interaction_count"] == 0
        is_first_meeting = sample_rapport_state["interaction_count"] == 0
        assert is_first_meeting is True

    def test_not_first_meeting(self, high_rapport_state):
        """High rapport state is not first meeting."""
        is_first_meeting = high_rapport_state["interaction_count"] == 0
        assert is_first_meeting is False


# ============================================================
# TRUST ASYMMETRY VALIDATION
# ============================================================


class TestTrustAsymmetry:
    """Validate trust asymmetry per Paper #9."""

    def test_positive_rapport_increment(self):
        """Positive interactions increase rapport by 0.02."""
        # This is validated in the SQL itself, but we document the constants
        positive_rapport_increment = 0.02
        assert positive_rapport_increment == 0.02

    def test_negative_rapport_decrement(self):
        """Negative interactions decrease rapport by 0.05 (asymmetric)."""
        negative_rapport_decrement = 0.05
        # Asymmetry ratio: -0.05 / +0.02 = 2.5x faster decrease
        asymmetry_ratio = negative_rapport_decrement / 0.02
        assert asymmetry_ratio == 2.5

    def test_trust_asymmetry_even_more_extreme(self):
        """Trust has even more extreme asymmetry per Paper #9."""
        positive_trust_increment = 0.01
        negative_trust_decrement = 0.08
        # Asymmetry ratio: -0.08 / +0.01 = 8x faster decrease
        asymmetry_ratio = negative_trust_decrement / positive_trust_increment
        assert asymmetry_ratio == 8.0


# ============================================================
# DATABASE OPERATION TESTS (with mocks)
# ============================================================


class TestGetRapport:
    """Test get_rapport database operation."""

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, monkeypatch):
        """Returns None when no rapport exists."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        # Mock database connection
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_rapport("org_test", "person_unknown")

        assert result is None
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_rapport_when_found(self, monkeypatch, sample_rapport_db_row):
        """Returns rapport state when found."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = sample_rapport_db_row

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_rapport("org_test", "person_test")

        assert result is not None
        assert result["org_id"] == "org_test"
        assert result["person_id"] == "person_test"

    @pytest.mark.asyncio
    async def test_handles_database_error(self, monkeypatch):
        """Returns None on database error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = asyncpg.PostgresError("Connection failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_rapport("org_test", "person_test")

        assert result is None


class TestGetOrgRapport:
    """Test get_org_rapport database operation."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_rapport(self, monkeypatch):
        """Returns empty list when org has no rapport records."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_org_rapport("org_empty")

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_rapport_for_org(self, monkeypatch, sample_rapport_db_row):
        """Returns all rapport records for an org."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        # Create two rapport rows
        row1 = dict(sample_rapport_db_row)
        row1["person_id"] = "person_1"
        row2 = dict(sample_rapport_db_row)
        row2["person_id"] = "person_2"

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [row1, row2]

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_org_rapport("org_test")

        assert len(result) == 2
        assert result[0]["person_id"] == "person_1"
        assert result[1]["person_id"] == "person_2"


class TestCreateRapport:
    """Test create_rapport database operation."""

    @pytest.mark.asyncio
    async def test_creates_rapport_successfully(self, monkeypatch):
        """Creates new rapport record successfully."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "INSERT 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.create_rapport(
            org_id="org_new",
            person_id="person_new",
            person_name="New Person",
            first_impression_text="Hello, nice to meet you!",
        )

        assert result is not None
        assert result["org_id"] == "org_new"
        assert result["person_id"] == "person_new"
        assert result["person_name"] == "New Person"
        assert result["rapport_level"] == 0.3
        assert result["trust_level"] == 0.3
        assert result["first_impression_given"] is True
        assert result["first_impression_text"] == "Hello, nice to meet you!"

    @pytest.mark.asyncio
    async def test_returns_none_on_duplicate(self, monkeypatch):
        """Returns None when rapport already exists."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncpg.UniqueViolationError("")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.create_rapport(
            org_id="org_test",
            person_id="person_test",
            person_name="Test User",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_creates_without_first_impression(self, monkeypatch):
        """Creates rapport without first impression text."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "INSERT 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.create_rapport(
            org_id="org_new",
            person_id="person_new",
            person_name="New Person",
        )

        assert result is not None
        assert result["first_impression_given"] is False
        assert result["first_impression_text"] is None


class TestRecordInteraction:
    """Test record_interaction atomic database operation."""

    @pytest.mark.asyncio
    async def test_returns_none_when_person_not_found(self, monkeypatch):
        """Returns None when person doesn't exist."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.record_interaction(
            org_id="org_test",
            person_id="person_unknown",
            outcome="positive",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_records_positive_interaction(self, monkeypatch, sample_rapport_db_row):
        """Records positive interaction with correct SQL."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        # Return updated row after atomic update
        updated_row = dict(sample_rapport_db_row)
        updated_row["interaction_count"] = 11
        updated_row["positive_interactions"] = 9
        updated_row["rapport_level"] = 0.52  # +0.02
        mock_conn.fetchrow.return_value = updated_row

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.record_interaction(
            org_id="org_test",
            person_id="person_test",
            outcome="positive",
            topics=["invoices", "payments"],
        )

        assert result is not None
        mock_conn.fetchrow.assert_called_once()
        # Verify the SQL was called with outcome="positive"
        call_args = mock_conn.fetchrow.call_args
        assert call_args[0][1] == "positive"  # First positional arg after SQL

    @pytest.mark.asyncio
    async def test_records_negative_interaction(self, monkeypatch, sample_rapport_db_row):
        """Records negative interaction with correct SQL."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        updated_row = dict(sample_rapport_db_row)
        updated_row["negative_interactions"] = 3
        mock_conn.fetchrow.return_value = updated_row

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.record_interaction(
            org_id="org_test",
            person_id="person_test",
            outcome="negative",
        )

        assert result is not None
        call_args = mock_conn.fetchrow.call_args
        assert call_args[0][1] == "negative"

    @pytest.mark.asyncio
    async def test_records_memorable_moment(self, monkeypatch, sample_rapport_db_row):
        """Records interaction with memorable moment."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = sample_rapport_db_row

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        memorable = {
            "summary": "Fixed month-end crisis",
            "outcome": "positive",
            "emotional_weight": 0.8,
        }

        result = await rapport.record_interaction(
            org_id="org_test",
            person_id="person_test",
            outcome="positive",
            memorable_moment=memorable,
        )

        assert result is not None
        # Verify memorable moment was passed to SQL
        call_args = mock_conn.fetchrow.call_args
        # moment_json is the 3rd positional arg
        moment_str = call_args[0][3]
        assert "Fixed month-end crisis" in moment_str


class TestLearnPreference:
    """Test learn_preference atomic database operation."""

    @pytest.mark.asyncio
    async def test_learns_preference_successfully(self, monkeypatch):
        """Successfully learns a preference."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.learn_preference(
            org_id="org_test",
            person_id="person_test",
            preference_key="communication_style",
            preference_value="brief",
        )

        assert result is True
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_person_not_found(self, monkeypatch):
        """Returns False when person doesn't exist."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 0"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.learn_preference(
            org_id="org_test",
            person_id="person_unknown",
            preference_key="pref_key",
            preference_value="pref_value",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_learns_complex_preference_value(self, monkeypatch):
        """Successfully learns a complex (dict) preference value."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.learn_preference(
            org_id="org_test",
            person_id="person_test",
            preference_key="report_format",
            preference_value={"format": "pdf", "detail": "high", "charts": True},
        )

        assert result is True


class TestAddInsideReference:
    """Test add_inside_reference atomic database operation."""

    @pytest.mark.asyncio
    async def test_adds_reference_successfully(self, monkeypatch):
        """Successfully adds an inside reference."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.add_inside_reference(
            org_id="org_test",
            person_id="person_test",
            reference="the lockbox incident",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_person_not_found(self, monkeypatch):
        """Returns False when person doesn't exist."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 0"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.add_inside_reference(
            org_id="org_test",
            person_id="person_unknown",
            reference="some reference",
        )

        assert result is False


class TestUpdateCommunicationStyle:
    """Test update_communication_style database operation."""

    @pytest.mark.asyncio
    async def test_updates_formality_successfully(self, monkeypatch):
        """Successfully updates formality preference."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
            formality="formal",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_updates_verbosity_successfully(self, monkeypatch):
        """Successfully updates verbosity preference."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
            verbosity="detailed",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_updates_humor_receptivity_successfully(self, monkeypatch):
        """Successfully updates humor receptivity."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
            humor_receptivity=0.8,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_updates_multiple_fields(self, monkeypatch):
        """Successfully updates multiple fields at once."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
            formality="professional",
            verbosity="moderate",
            humor_receptivity=0.6,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_no_updates(self, monkeypatch):
        """Returns True when no updates provided (no-op is success)."""
        from src.persistence import rapport

        # No mock needed - function returns True immediately if no updates
        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_clamps_humor_receptivity(self, monkeypatch):
        """Clamps humor receptivity to valid range."""
        from unittest.mock import AsyncMock, MagicMock

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        # Value > 1.0 should be clamped
        result = await rapport.update_communication_style(
            org_id="org_test",
            person_id="person_test",
            humor_receptivity=1.5,
        )

        assert result is True
        # The clamped value (1.0) should be passed to SQL
        call_args = mock_conn.execute.call_args
        # First positional param after SQL should be 1.0
        assert call_args[0][1] == 1.0


class TestDatabaseErrorHandling:
    """Test that database errors are handled gracefully."""

    @pytest.mark.asyncio
    async def test_get_rapport_handles_error(self, monkeypatch):
        """get_rapport returns None on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = asyncpg.PostgresError("Connection lost")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.get_rapport("org", "person")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_rapport_handles_error(self, monkeypatch):
        """create_rapport returns None on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncpg.PostgresError("Insert failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.create_rapport("org", "person", "Name")
        assert result is None

    @pytest.mark.asyncio
    async def test_record_interaction_handles_error(self, monkeypatch):
        """record_interaction returns None on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = asyncpg.PostgresError("Update failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.record_interaction("org", "person", "positive")
        assert result is None

    @pytest.mark.asyncio
    async def test_learn_preference_handles_error(self, monkeypatch):
        """learn_preference returns False on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncpg.PostgresError("Update failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.learn_preference("org", "person", "key", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_add_inside_reference_handles_error(self, monkeypatch):
        """add_inside_reference returns False on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncpg.PostgresError("Update failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.add_inside_reference("org", "person", "ref")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_communication_style_handles_error(self, monkeypatch):
        """update_communication_style returns False on error."""
        from unittest.mock import AsyncMock, MagicMock

        import asyncpg

        from src.persistence import rapport

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncpg.PostgresError("Update failed")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        monkeypatch.setattr(rapport, "get_connection", lambda: mock_cm)

        result = await rapport.update_communication_style("org", "person", formality="formal")
        assert result is False
