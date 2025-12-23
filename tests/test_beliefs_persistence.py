"""
Beliefs Persistence Tests
==========================

Tests for the database persistence layer including:
- Belief save/load operations
- SQL parameter preparation
- Row-to-belief conversion
- Batch operations
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest


class TestPrepareBeliefParams:
    """Test the _prepare_belief_params helper."""

    def test_prepare_params_with_full_belief(self):
        """Should prepare all parameters correctly."""
        from src.persistence.beliefs import _prepare_belief_params
        from src.state.schema import create_belief

        belief = create_belief("Test statement", "competence", 0.75)
        belief["tags"] = ["test", "accounting"]

        params = _prepare_belief_params("org-1", belief)

        assert params[0] == belief["belief_id"]  # belief_id
        assert params[1] == "org-1"  # org_id
        assert params[2] == "Test statement"  # statement
        assert params[3] == "competence"  # category
        assert params[4] == 0.75  # strength

    def test_prepare_params_with_defaults(self):
        """Should use defaults for missing fields."""
        from src.persistence.beliefs import _prepare_belief_params

        minimal_belief = {
            "belief_id": "test-id-123",
        }

        params = _prepare_belief_params("org-1", minimal_belief)

        assert params[0] == "test-id-123"
        assert params[2] == ""  # statement default
        assert params[3] == "competence"  # category default
        assert params[4] == 0.5  # strength default
        assert params[5] == "*|*|*"  # context_key default

    def test_prepare_params_serializes_json(self):
        """Should serialize dict/list fields to JSON."""
        from src.persistence.beliefs import _prepare_belief_params

        belief = {
            "belief_id": "test-123",
            "context_states": {"*|*|*": {"strength": 0.5}},
            "support_weights": {"other-id": 0.8},
        }

        params = _prepare_belief_params("org-1", belief)

        # context_states is param 6
        context_states = params[6]
        assert isinstance(context_states, str)
        parsed = json.loads(context_states)
        assert parsed == {"*|*|*": {"strength": 0.5}}


class TestRowToBelief:
    """Test the _row_to_belief conversion."""

    def test_row_to_belief_basic(self, sample_belief_row):
        """Should convert row to belief dict."""
        from src.persistence.beliefs import _row_to_belief

        belief = _row_to_belief(sample_belief_row)

        assert belief["belief_id"] == "test-belief-001"
        assert belief["statement"] == "Test belief from DB"
        assert belief["category"] == "competence"
        assert belief["strength"] == 0.75

    def test_row_to_belief_parses_json(self, sample_belief_row):
        """Should parse JSON fields."""
        from src.persistence.beliefs import _row_to_belief

        sample_belief_row["context_states"] = '{"*|*|*": {"strength": 0.8}}'
        sample_belief_row["support_weights"] = '{"supporter-id": 0.9}'

        belief = _row_to_belief(sample_belief_row)

        assert belief["context_states"] == {"*|*|*": {"strength": 0.8}}
        assert belief["support_weights"] == {"supporter-id": 0.9}

    def test_row_to_belief_handles_null_json(self, sample_belief_row):
        """Should handle null JSON fields."""
        from src.persistence.beliefs import _row_to_belief

        sample_belief_row["context_states"] = None
        sample_belief_row["support_weights"] = None

        belief = _row_to_belief(sample_belief_row)

        assert belief["context_states"] == {}
        assert belief["support_weights"] == {}

    def test_row_to_belief_converts_arrays(self, sample_belief_row):
        """Should convert PostgreSQL arrays to lists."""
        from src.persistence.beliefs import _row_to_belief

        sample_belief_row["supports"] = ["id-1", "id-2"]
        sample_belief_row["supported_by"] = ["id-3"]
        sample_belief_row["tags"] = ["tag1", "tag2"]

        belief = _row_to_belief(sample_belief_row)

        assert belief["supports"] == ["id-1", "id-2"]
        assert belief["supported_by"] == ["id-3"]
        assert belief["tags"] == ["tag1", "tag2"]

    def test_row_to_belief_handles_null_arrays(self, sample_belief_row):
        """Should handle null arrays."""
        from src.persistence.beliefs import _row_to_belief

        sample_belief_row["supports"] = None
        sample_belief_row["supported_by"] = None
        sample_belief_row["tags"] = None

        belief = _row_to_belief(sample_belief_row)

        assert belief["supports"] == []
        assert belief["supported_by"] == []
        assert belief["tags"] == []

    def test_row_to_belief_formats_datetime(self, sample_belief_row):
        """Should format datetime as ISO string."""
        from src.persistence.beliefs import _row_to_belief

        now = datetime.now()
        sample_belief_row["last_updated"] = now

        belief = _row_to_belief(sample_belief_row)

        assert belief["last_updated"] == now.isoformat()


class TestSaveBelief:
    """Test belief save operations."""

    @pytest.mark.asyncio
    async def test_save_belief_executes_upsert(self, mock_database_url):
        """save_belief should execute upsert SQL."""
        from src.persistence.beliefs import save_belief
        from src.state.schema import create_belief

        belief = create_belief("Test", "competence")

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            await save_belief("org-1", belief)

            mock_conn.execute.assert_called_once()
            # First arg should be the SQL
            sql = mock_conn.execute.call_args[0][0]
            assert "INSERT INTO beliefs" in sql
            assert "ON CONFLICT" in sql

    @pytest.mark.asyncio
    async def test_save_belief_with_conn(self, mock_database_url):
        """save_belief_with_conn should use provided connection."""
        from src.persistence.beliefs import save_belief_with_conn
        from src.state.schema import create_belief

        mock_conn = AsyncMock()
        belief = create_belief("Test", "competence")

        await save_belief_with_conn(mock_conn, "org-1", belief)

        mock_conn.execute.assert_called_once()


class TestSaveBeliefsBatch:
    """Test batch save operations."""

    @pytest.mark.asyncio
    async def test_batch_save_uses_transaction(self, mock_database_url):
        """Batch save should use a transaction."""
        from src.persistence.beliefs import save_beliefs_batch
        from src.state.schema import create_belief

        beliefs = [
            create_belief("B1", "competence"),
            create_belief("B2", "technical"),
        ]

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_transaction = AsyncMock()
            mock_conn.transaction.return_value.__aenter__ = AsyncMock()
            mock_conn.transaction.return_value.__aexit__ = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            await save_beliefs_batch("org-1", beliefs)

            # Should have called transaction
            mock_conn.transaction.assert_called_once()
            # Should have executed for each belief
            assert mock_conn.execute.call_count == 2


class TestLoadBeliefs:
    """Test belief load operations."""

    @pytest.mark.asyncio
    async def test_load_beliefs_for_org(self, mock_database_url, sample_belief_row):
        """load_beliefs_for_org should query and convert rows."""
        from src.persistence.beliefs import load_beliefs_for_org

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [sample_belief_row]

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            beliefs = await load_beliefs_for_org("org-1")

            mock_conn.fetch.assert_called_once()
            sql = mock_conn.fetch.call_args[0][0]
            assert "SELECT" in sql
            assert "WHERE org_id = $1" in sql

            assert len(beliefs) == 1
            assert beliefs[0]["belief_id"] == "test-belief-001"

    @pytest.mark.asyncio
    async def test_load_beliefs_empty_org(self, mock_database_url):
        """Should return empty list for org with no beliefs."""
        from src.persistence.beliefs import load_beliefs_for_org

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = []

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            beliefs = await load_beliefs_for_org("org-1")

            assert beliefs == []


class TestGetBeliefsByCategory:
    """Test category-filtered queries."""

    @pytest.mark.asyncio
    async def test_get_beliefs_by_category(self, mock_database_url, sample_belief_row):
        """Should filter by category and minimum strength."""
        from src.persistence.beliefs import get_beliefs_by_category

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [sample_belief_row]

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            beliefs = await get_beliefs_by_category(
                "org-1", category="moral", min_strength=0.5, limit=10
            )

            # Check query parameters
            call_args = mock_conn.fetch.call_args
            sql = call_args[0][0]
            params = call_args[0][1:]

            assert "category = $2" in sql
            assert "strength >= $3" in sql
            assert params[0] == "org-1"
            assert params[1] == "moral"
            assert params[2] == 0.5


class TestDeleteBelief:
    """Test belief deletion."""

    @pytest.mark.asyncio
    async def test_delete_belief_success(self, mock_database_url):
        """delete_belief should return True on success."""
        from src.persistence.beliefs import delete_belief

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "DELETE 1"

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            result = await delete_belief("org-1", "belief-123")

            assert result == True

    @pytest.mark.asyncio
    async def test_delete_belief_not_found(self, mock_database_url):
        """delete_belief should return False when not found."""
        from src.persistence.beliefs import delete_belief

        with patch("src.persistence.beliefs.get_connection") as mock_ctx:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "DELETE 0"

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            result = await delete_belief("org-1", "non-existent")

            assert result == False


class TestUpsertSQL:
    """Test the upsert SQL constant."""

    def test_upsert_sql_has_all_fields(self):
        """_UPSERT_SQL should include all belief fields."""
        from src.persistence.beliefs import _UPSERT_SQL

        required_fields = [
            "belief_id",
            "org_id",
            "statement",
            "category",
            "strength",
            "context_key",
            "context_states",
            "supports",
            "supported_by",
            "support_weights",
            "last_updated",
            "success_count",
            "failure_count",
            "is_end_memory_influenced",
            "peak_intensity",
            "invalidation_threshold",
            "is_distrusted",
            "moral_violation_count",
            "immutable",
            "tags",
        ]

        for field in required_fields:
            assert field in _UPSERT_SQL

    def test_upsert_sql_has_on_conflict(self):
        """_UPSERT_SQL should have ON CONFLICT clause."""
        from src.persistence.beliefs import _UPSERT_SQL

        assert "ON CONFLICT (belief_id) DO UPDATE SET" in _UPSERT_SQL
