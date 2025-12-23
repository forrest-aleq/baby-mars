"""
State Factory Functions
========================

Factory functions for creating state objects with proper defaults.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from .constants import INVALIDATION_THRESHOLDS
from .types import BeliefState, Memory, PersonObject

if TYPE_CHECKING:
    from .main import BabyMARSState


def generate_id() -> str:
    """Generate unique ID (full UUID to avoid collisions)."""
    return str(uuid.uuid4())


def create_initial_state(thread_id: str, org_id: str, user_id: str) -> "BabyMARSState":
    """Create initial state for a new conversation."""
    return {
        "thread_id": thread_id,
        "org_id": org_id,
        "user_id": user_id,
        "active_tasks": [],
        "notes": [],
        "objects": {
            "people": [],
            "entities": [],
            "beliefs": [],
            "knowledge": [],
            "goals": [],
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "is_month_end": False,
                "is_quarter_end": False,
                "is_year_end": False,
                "days_until_deadline": None,
                "urgency_multiplier": 1.0,
            },
        },
        "messages": [],
        "current_turn": 0,
        "current_context_key": "*|*|*",
        "activated_beliefs": [],
        "appraisal": None,
        "selected_action": None,
        "supervision_mode": "guidance_seeking",
        "belief_strength_for_action": 0.0,
        "approval_status": None,
        "approval_summary": None,
        "active_goals": [],
        "goal_conflict_detected": False,
        "current_person": None,
        "authority_context": {},
        "execution_results": [],
        "validation_results": [],
        "retry_count": 0,
        "max_retries": 3,
        "events": [],
    }


def create_belief(
    statement: str,
    category: Literal["moral", "competence", "technical", "preference", "identity"],
    initial_strength: float = 0.5,
    context_key: str = "*|*|*",
) -> BeliefState:
    """Factory function to create a new belief with proper defaults."""
    belief_id = generate_id()
    now = datetime.now().isoformat()

    return {
        "belief_id": belief_id,
        "statement": statement,
        "category": category,
        "strength": initial_strength,
        "context_key": context_key,
        "context_states": {
            context_key: {
                "strength": initial_strength,
                "last_updated": now,
                "success_count": 0,
                "failure_count": 0,
                "last_outcome": None,
            }
        },
        "supports": [],
        "supported_by": [],
        "support_weights": {},
        "last_updated": now,
        "success_count": 0,
        "failure_count": 0,
        "is_end_memory_influenced": False,
        "peak_intensity": 0.0,
        "invalidation_threshold": INVALIDATION_THRESHOLDS[category],
        "is_distrusted": False,
        "moral_violation_count": 0,
    }


def create_memory(
    description: str,
    outcome: Literal["success", "failure", "neutral", "validation", "correction"],
    context_key: str,
    difficulty_level: int = 3,
    emotional_intensity: float = 0.5,
    is_end_memory: bool = False,
    related_beliefs: Optional[list[str]] = None,
    related_persons: Optional[list[str]] = None,
) -> Memory:
    """Factory function to create a new memory."""
    return {
        "memory_id": generate_id(),
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "outcome": outcome,
        "emotional_intensity": emotional_intensity,
        "is_end_memory": is_end_memory,
        "related_beliefs": related_beliefs or [],
        "related_persons": related_persons or [],
        "context_key": context_key,
        "difficulty_level": difficulty_level,
    }


def compute_relationship_value(
    authority: float, interaction_strength: float, context_relevance: float
) -> float:
    """
    Compute relationship value per Paper #17 formula.

    Formula: 0.6 * authority + 0.2 * interaction_strength + 0.2 * context_relevance
    """
    return 0.6 * authority + 0.2 * interaction_strength + 0.2 * context_relevance


def create_person(name: str, role: str, authority: float = 0.5) -> PersonObject:
    """Factory function to create a new person."""
    interaction_strength = 0.5
    context_relevance = 0.5
    return {
        "person_id": generate_id(),
        "name": name,
        "role": role,
        "authority": authority,
        "interaction_strength": interaction_strength,
        "context_relevance": context_relevance,
        "relationship_value": compute_relationship_value(
            authority, interaction_strength, context_relevance
        ),
        "preferences": [],
        "last_interaction": datetime.now().isoformat(),
    }
