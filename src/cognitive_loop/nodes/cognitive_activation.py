"""
Cognitive Activation Node
==========================

Loads cognitive context from graphs.
Implements the "fetch_active_subgraph" pattern.

This is the first step in the cognitive loop - it retrieves
relevant beliefs, memories, and social context for the current
interaction.
"""

from datetime import datetime
from typing import Any

from ...state.schema import (
    BabyMARSState,
    Objects,
    TemporalContext,
    PersonObject,
)
from ...graphs.belief_graph import BeliefGraph
from ...graphs.belief_graph_manager import get_org_belief_graph
from ...graphs.social_graph import SocialGraph


# ============================================================
# GRAPH LOADING
# ============================================================

# Social graphs still use simple in-memory cache (less critical than beliefs)
_social_graphs: dict[str, SocialGraph] = {}


async def load_belief_graph(org_id: str) -> BeliefGraph:
    """Load belief graph for organization (uses LRU-cached manager)"""
    return await get_org_belief_graph(org_id)


async def load_social_graph(org_id: str) -> SocialGraph:
    """Load social graph for organization"""
    if org_id not in _social_graphs:
        from ...graphs.social_graph import SocialGraph
        _social_graphs[org_id] = SocialGraph()
    return _social_graphs[org_id]


# ============================================================
# CONTEXT EXTRACTION
# ============================================================

def extract_context_key(message: dict) -> str:
    """
    Extract context key from message.
    
    Format: "client|period|amount_range"
    
    In production, this would use NER and classification
    to extract structured context from the message.
    """
    # Default context
    context_parts = ["*", "*", "*"]
    
    if not message:
        return "|".join(context_parts)
        
    content = message.get("content", "")
    if isinstance(content, list):
        content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    
    # Simple keyword extraction (replace with real NER)
    content_lower = content.lower()
    
    # Client detection
    if "client" in content_lower:
        # Extract client name (naive)
        context_parts[0] = "client_mentioned"
        
    # Period detection
    if "month-end" in content_lower or "month end" in content_lower:
        context_parts[1] = "month-end"
    elif "quarter" in content_lower:
        context_parts[1] = "quarter-end"
    elif "year-end" in content_lower or "year end" in content_lower:
        context_parts[1] = "year-end"
        
    # Amount detection
    if "$" in content or "million" in content_lower:
        context_parts[2] = ">10K"  # Simplified
        
    return "|".join(context_parts)


def build_temporal_context() -> TemporalContext:
    """Build temporal context for current time"""
    now = datetime.now()
    
    # Check for period boundaries
    is_month_end = now.day >= 25
    is_quarter_end = is_month_end and now.month in [3, 6, 9, 12]
    is_year_end = is_quarter_end and now.month == 12
    
    # Calculate urgency
    urgency = 1.0
    if is_year_end:
        urgency = 2.0
    elif is_quarter_end:
        urgency = 1.75
    elif is_month_end:
        urgency = 1.5
        
    return {
        "current_time": now.isoformat(),
        "is_month_end": is_month_end,
        "is_quarter_end": is_quarter_end,
        "is_year_end": is_year_end,
        "days_until_deadline": None,
        "urgency_multiplier": urgency
    }


def detect_goal_conflict(goals: list[dict]) -> dict | None:
    """
    Detect conflicts between active goals.
    
    Returns conflict details if found, None otherwise.
    """
    if len(goals) < 2:
        return None
        
    # Check for explicit conflicts (marked in goal metadata)
    for i, goal_a in enumerate(goals):
        for goal_b in goals[i+1:]:
            conflicts_with = goal_a.get("conflicts_with", [])
            if goal_b.get("goal_id") in conflicts_with:
                return {
                    "type": "explicit_conflict",
                    "goal_a": goal_a,
                    "goal_b": goal_b
                }
                
    # Check for resource conflicts (same resource, different objectives)
    resources_used = {}
    for goal in goals:
        for resource in goal.get("resources", []):
            if resource in resources_used:
                return {
                    "type": "resource_conflict",
                    "resource": resource,
                    "goal_a": resources_used[resource],
                    "goal_b": goal
                }
            resources_used[resource] = goal
            
    return None


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================

async def process(state: BabyMARSState) -> dict:
    """
    Cognitive Activation Node
    
    Loads cognitive context from graphs:
    1. Extract context key from message
    2. Activate relevant beliefs
    3. Load salient people
    4. Build Objects column
    5. Detect goal conflicts
    
    Returns state updates.
    """
    
    org_id = state.get("org_id", "default")
    
    # Load graphs
    belief_graph = await load_belief_graph(org_id)
    social_graph = await load_social_graph(org_id)
    
    # Extract context from last message
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    context_key = extract_context_key(last_message)
    
    # Activate relevant beliefs
    activated_beliefs = belief_graph.get_activated_beliefs(
        context_key=context_key,
        min_strength=0.3,
        limit=20
    )
    
    # Load salient people
    people = []
    for person_id, person in social_graph.persons.items():
        rv = social_graph.compute_relationship_value(person_id)
        if rv > 0.4:  # Salience threshold
            people.append({
                **person,
                "relationship_value": rv
            })
    
    # Sort by relationship value
    people.sort(key=lambda p: p.get("relationship_value", 0), reverse=True)
    
    # Build Objects column (Paper #8)
    objects: Objects = {
        "people": people[:10],  # Top 10
        "entities": [],  # TODO: extract from context
        "beliefs": activated_beliefs[:20],
        "knowledge": [],  # TODO: relevant workflows
        "goals": state.get("active_goals", []),
        "temporal": build_temporal_context()
    }
    
    # Detect goal conflicts
    goal_conflict = detect_goal_conflict(state.get("active_goals", []))
    
    # Return state updates
    return {
        "current_context_key": context_key,
        "activated_beliefs": activated_beliefs,
        "objects": objects,
        "goal_conflict_detected": goal_conflict is not None,
        "current_turn": state.get("current_turn", 0) + 1
    }
