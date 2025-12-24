"""
Belief Graph Manager
=====================

Manages per-org belief graphs with LRU caching.
Loads from Postgres on cache miss, saves after updates.

Architecture:
- In-memory dict with LRU eviction for 10-100 concurrent orgs
- Load beliefs from DB on cache miss
- Save to DB after every belief update (durability over performance)
"""

import asyncio
from collections import OrderedDict
from typing import Any, Optional, cast

from ..persistence.beliefs import (
    load_beliefs_for_org,
    save_belief,
    save_beliefs_batch,
)
from .belief_graph import BeliefGraph


class BeliefGraphManager:
    """
    LRU cache for per-org belief graphs.

    Usage:
        manager = get_belief_graph_manager()
        graph = await manager.get_graph("org_123")
        # Use graph...
        await manager.save_belief("org_123", updated_belief)
    """

    def __init__(self, max_size: int = 100):
        """
        Args:
            max_size: Maximum number of org graphs to keep in memory.
                      When exceeded, least recently used is evicted.
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, BeliefGraph] = OrderedDict()
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, org_id: str) -> asyncio.Lock:
        """Get or create a lock for an org (for thread-safe loading)"""
        if org_id not in self._locks:
            self._locks[org_id] = asyncio.Lock()
        return self._locks[org_id]

    async def get_graph(self, org_id: str) -> BeliefGraph:
        """
        Get belief graph for an org.
        Loads from database on cache miss.
        """
        # Check cache first
        if org_id in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(org_id)
            return self._cache[org_id]

        # Cache miss - load from DB with lock
        async with self._get_lock(org_id):
            # Double-check after acquiring lock
            if org_id in self._cache:
                self._cache.move_to_end(org_id)
                return self._cache[org_id]

            # Load from database
            graph = await self._load_graph_from_db(org_id)

            # Add to cache
            self._cache[org_id] = graph
            self._cache.move_to_end(org_id)

            # Evict if over capacity
            while len(self._cache) > self.max_size:
                # Remove least recently used (first item)
                evicted_org, _ = self._cache.popitem(last=False)
                # Clean up lock
                if evicted_org in self._locks:
                    del self._locks[evicted_org]

            return graph

    async def _load_graph_from_db(self, org_id: str) -> BeliefGraph:
        """Load all beliefs for an org and build graph"""
        graph = BeliefGraph()

        try:
            beliefs = await load_beliefs_for_org(org_id)

            for belief in beliefs:
                graph.add_belief(belief)

            # Rebuild support relationships from the stored data
            for belief in beliefs:
                for supporter_id in belief.get("supported_by", []):
                    if supporter_id in graph.beliefs:
                        weight = belief.get("support_weights", {}).get(supporter_id, 0.8)
                        try:
                            graph.add_support_relationship(
                                supporter_id, belief["belief_id"], weight
                            )
                        except ValueError:
                            # Relationship may already exist
                            pass

        except Exception as e:
            # If DB fails, return empty graph (will be populated by birth)
            print(f"Warning: Failed to load beliefs for org {org_id}: {e}")

        return graph

    async def save_belief(self, org_id: str, belief: dict[str, Any]) -> None:
        """
        Save a belief to the database.
        Called after every belief update for durability.
        """
        await save_belief(org_id, belief)

    async def save_all_beliefs(self, org_id: str) -> None:
        """Save all beliefs for an org (e.g., after birth)"""
        if org_id not in self._cache:
            return

        graph = self._cache[org_id]
        beliefs = list(graph.beliefs.values())

        if beliefs:
            await save_beliefs_batch(org_id, cast(list[dict[str, Any]], beliefs))

    def invalidate(self, org_id: str) -> None:
        """Remove an org from cache (e.g., on logout or error)"""
        if org_id in self._cache:
            del self._cache[org_id]
        if org_id in self._locks:
            del self._locks[org_id]

    def clear(self) -> None:
        """Clear entire cache (e.g., on shutdown)"""
        self._cache.clear()
        self._locks.clear()

    @property
    def cache_size(self) -> int:
        """Current number of orgs in cache"""
        return len(self._cache)

    @property
    def cached_orgs(self) -> list[str]:
        """List of org_ids currently in cache"""
        return list(self._cache.keys())


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_manager: Optional[BeliefGraphManager] = None


def get_belief_graph_manager() -> BeliefGraphManager:
    """Get the singleton belief graph manager"""
    global _manager
    if _manager is None:
        _manager = BeliefGraphManager(max_size=100)
    return _manager


def reset_belief_graph_manager() -> None:
    """Reset the manager (for testing)"""
    global _manager
    if _manager is not None:
        _manager.clear()
    _manager = None


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


async def get_org_belief_graph(org_id: str) -> BeliefGraph:
    """
    Get belief graph for an org.
    Main entry point for node code.
    """
    manager = get_belief_graph_manager()
    return await manager.get_graph(org_id)


async def save_org_belief(org_id: str, belief: dict[str, Any]) -> None:
    """
    Save a belief after update.
    Called from feedback node.
    """
    manager = get_belief_graph_manager()
    await manager.save_belief(org_id, belief)


async def save_all_org_beliefs(org_id: str) -> None:
    """
    Save all beliefs for an org.
    Called after birth to persist initial beliefs.
    """
    manager = get_belief_graph_manager()
    await manager.save_all_beliefs(org_id)


async def save_modified_beliefs(org_id: str, belief_graph: "BeliefGraph") -> int:
    """
    Save all beliefs modified since last clear.
    Called from feedback node after cascade updates.
    Returns number of beliefs saved.
    """
    modified_ids = belief_graph.get_modified_belief_ids()
    if not modified_ids:
        return 0

    beliefs_to_save = []
    for belief_id in modified_ids:
        belief = belief_graph.get_belief(belief_id)
        if belief:
            beliefs_to_save.append(cast(dict[str, Any], belief))

    if beliefs_to_save:
        await save_beliefs_batch(org_id, beliefs_to_save)

    belief_graph.clear_modified_beliefs()
    return len(beliefs_to_save)
