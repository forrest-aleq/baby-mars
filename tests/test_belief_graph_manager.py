"""
Belief Graph Manager Tests
===========================

Tests for the BeliefGraphManager LRU cache including:
- Cache hits and misses
- LRU eviction
- Per-org isolation
- Database loading
- Thread-safe operations

Note: Some async tests are skipped on Python 3.14 due to pytest-asyncio compatibility issues.
"""

import sys
from unittest.mock import AsyncMock, patch

import pytest

# Skip async tests on Python 3.14 due to pytest-asyncio compatibility issues
SKIP_ASYNC = sys.version_info >= (3, 14)
pytestmark_async = pytest.mark.skipif(SKIP_ASYNC, reason="pytest-asyncio hangs on Python 3.14")


class TestBeliefGraphManagerBasics:
    """Test basic manager operations."""

    def test_manager_initialization(self):
        """Manager should initialize with empty cache."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager(max_size=10)

        assert manager.cache_size == 0
        assert manager.cached_orgs == []

    def test_manager_max_size(self):
        """Manager should respect max_size parameter."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager(max_size=5)

        assert manager.max_size == 5


class TestCacheOperations:
    """Test LRU cache operations."""

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_get_graph_cache_miss(self):
        """First access should load from DB (cache miss)."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            graph = await manager.get_graph("org-1")

            mock_load.assert_called_once_with("org-1")
            assert "org-1" in manager.cached_orgs

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_get_graph_cache_hit(self):
        """Second access should use cache (cache hit)."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            # First access - cache miss
            graph1 = await manager.get_graph("org-1")

            # Second access - cache hit
            graph2 = await manager.get_graph("org-1")

            # Should only load once
            assert mock_load.call_count == 1
            assert graph1 is graph2

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Oldest accessed org should be evicted when cache full."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager(max_size=2)

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            # Fill cache
            await manager.get_graph("org-1")
            await manager.get_graph("org-2")

            assert manager.cache_size == 2

            # Access org-1 to make it most recently used
            await manager.get_graph("org-1")

            # Add org-3 - should evict org-2 (least recently used)
            await manager.get_graph("org-3")

            assert manager.cache_size == 2
            assert "org-1" in manager.cached_orgs
            assert "org-3" in manager.cached_orgs
            assert "org-2" not in manager.cached_orgs

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_move_to_end_on_access(self):
        """Accessing an org should move it to end (most recently used)."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager(max_size=3)

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            # Add orgs in order
            await manager.get_graph("org-1")
            await manager.get_graph("org-2")
            await manager.get_graph("org-3")

            # Access org-1 (should move to end)
            await manager.get_graph("org-1")

            # org-2 should now be oldest
            orgs = manager.cached_orgs
            assert orgs[0] == "org-2"
            assert orgs[-1] == "org-1"


class TestOrgIsolation:
    """Test per-org belief graph isolation."""

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_separate_graphs_per_org(self):
        """Each org should have its own belief graph."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.side_effect = lambda org_id: BeliefGraph()

            graph1 = await manager.get_graph("org-1")
            graph2 = await manager.get_graph("org-2")

            # Should be different instances
            assert graph1 is not graph2

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_modifications_isolated(self):
        """Modifications to one org's graph should not affect others."""
        from src.graphs.belief_graph_manager import BeliefGraphManager
        from src.state.schema import create_belief

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.side_effect = lambda org_id: BeliefGraph()

            graph1 = await manager.get_graph("org-1")
            graph2 = await manager.get_graph("org-2")

            # Add belief to org-1
            belief = create_belief("Test belief", "competence")
            graph1.add_belief(belief)

            # org-2 should not have the belief
            assert belief["belief_id"] not in graph2.beliefs


class TestInvalidation:
    """Test cache invalidation."""

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_invalidate_removes_from_cache(self):
        """invalidate should remove org from cache."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            await manager.get_graph("org-1")
            assert "org-1" in manager.cached_orgs

            manager.invalidate("org-1")

            assert "org-1" not in manager.cached_orgs

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_clear_empties_cache(self):
        """clear should remove all orgs from cache."""
        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            mock_load.return_value = BeliefGraph()

            await manager.get_graph("org-1")
            await manager.get_graph("org-2")

            manager.clear()

            assert manager.cache_size == 0
            assert manager.cached_orgs == []


class TestDatabaseLoading:
    """Test loading from database."""

    def test_load_empty_org(self):
        """Loading org with no beliefs should return empty graph."""
        import asyncio

        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        async def run():
            with patch(
                "src.graphs.belief_graph_manager.load_beliefs_for_org", new_callable=AsyncMock
            ) as mock_load:
                mock_load.return_value = []
                return await manager._load_graph_from_db("org-1")

        graph = asyncio.run(run())
        assert len(graph.beliefs) == 0

    def test_load_with_beliefs(self):
        """Loading org with beliefs should populate graph."""
        import asyncio

        from src.graphs.belief_graph_manager import BeliefGraphManager
        from src.state.schema import create_belief

        manager = BeliefGraphManager()
        test_belief = create_belief("Test", "competence")

        async def run():
            with patch(
                "src.graphs.belief_graph_manager.load_beliefs_for_org", new_callable=AsyncMock
            ) as mock_load:
                mock_load.return_value = [test_belief]
                return await manager._load_graph_from_db("org-1")

        graph = asyncio.run(run())
        assert test_belief["belief_id"] in graph.beliefs

    def test_load_with_support_relationships(self):
        """Loading should rebuild support relationships."""
        import asyncio

        from src.graphs.belief_graph_manager import BeliefGraphManager
        from src.state.schema import create_belief

        manager = BeliefGraphManager()

        # Create beliefs with relationship
        foundation = create_belief("Foundation", "moral")
        derived = create_belief("Derived", "competence")
        derived["supported_by"] = [foundation["belief_id"]]
        derived["support_weights"] = {foundation["belief_id"]: 0.8}

        async def run():
            with patch(
                "src.graphs.belief_graph_manager.load_beliefs_for_org", new_callable=AsyncMock
            ) as mock_load:
                mock_load.return_value = [foundation, derived]
                return await manager._load_graph_from_db("org-1")

        graph = asyncio.run(run())
        assert graph.G.has_edge(foundation["belief_id"], derived["belief_id"])

    def test_load_handles_db_error(self):
        """Should return empty graph on DB error."""
        import asyncio

        from src.graphs.belief_graph_manager import BeliefGraphManager

        manager = BeliefGraphManager()

        async def run():
            with patch(
                "src.graphs.belief_graph_manager.load_beliefs_for_org", new_callable=AsyncMock
            ) as mock_load:
                mock_load.side_effect = Exception("DB connection failed")
                return await manager._load_graph_from_db("org-1")

        graph = asyncio.run(run())
        assert len(graph.beliefs) == 0


class TestSaving:
    """Test saving beliefs to database."""

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_save_belief(self):
        """save_belief should call persistence layer."""
        from src.graphs.belief_graph_manager import BeliefGraphManager
        from src.state.schema import create_belief

        manager = BeliefGraphManager()
        belief = create_belief("Test", "competence")

        with patch(
            "src.graphs.belief_graph_manager.save_belief", new_callable=AsyncMock
        ) as mock_save:
            await manager.save_belief("org-1", belief)

            mock_save.assert_called_once_with("org-1", belief)

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_save_all_beliefs(self):
        """save_all_beliefs should save all beliefs in graph."""
        from src.graphs.belief_graph_manager import BeliefGraphManager
        from src.state.schema import create_belief

        manager = BeliefGraphManager()

        with patch.object(manager, "_load_graph_from_db", new_callable=AsyncMock) as mock_load:
            from src.graphs.belief_graph import BeliefGraph

            graph = BeliefGraph()
            belief1 = create_belief("B1", "competence")
            belief2 = create_belief("B2", "technical")
            graph.add_belief(belief1)
            graph.add_belief(belief2)
            mock_load.return_value = graph

            await manager.get_graph("org-1")

            with patch(
                "src.graphs.belief_graph_manager.save_beliefs_batch", new_callable=AsyncMock
            ) as mock_save:
                await manager.save_all_beliefs("org-1")

                mock_save.assert_called_once()
                saved_beliefs = mock_save.call_args[0][1]
                assert len(saved_beliefs) == 2


class TestSingleton:
    """Test singleton manager."""

    def test_get_belief_graph_manager_singleton(self):
        """get_belief_graph_manager should return same instance."""
        from src.graphs.belief_graph_manager import (
            get_belief_graph_manager,
            reset_belief_graph_manager,
        )

        reset_belief_graph_manager()

        manager1 = get_belief_graph_manager()
        manager2 = get_belief_graph_manager()

        assert manager1 is manager2

    def test_reset_belief_graph_manager(self):
        """reset should clear the singleton."""
        from src.graphs.belief_graph_manager import (
            get_belief_graph_manager,
            reset_belief_graph_manager,
        )

        manager1 = get_belief_graph_manager()
        reset_belief_graph_manager()
        manager2 = get_belief_graph_manager()

        assert manager1 is not manager2


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_get_org_belief_graph(self):
        """get_org_belief_graph should use manager."""
        from src.graphs.belief_graph_manager import get_belief_graph_manager, get_org_belief_graph

        manager = get_belief_graph_manager()

        with patch.object(manager, "get_graph", new_callable=AsyncMock) as mock_get:
            from src.graphs.belief_graph import BeliefGraph

            mock_get.return_value = BeliefGraph()

            await get_org_belief_graph("org-1")

            mock_get.assert_called_once_with("org-1")

    @pytestmark_async
    @pytest.mark.asyncio
    async def test_save_org_belief(self):
        """save_org_belief should use manager."""
        from src.graphs.belief_graph_manager import get_belief_graph_manager, save_org_belief
        from src.state.schema import create_belief

        manager = get_belief_graph_manager()
        belief = create_belief("Test", "competence")

        with patch.object(manager, "save_belief", new_callable=AsyncMock) as mock_save:
            await save_org_belief("org-1", belief)

            mock_save.assert_called_once_with("org-1", belief)
