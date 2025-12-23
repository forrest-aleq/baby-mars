"""
Baby MARS State Schema
======================

Implementation of the Three-Column Working Memory (Paper #8)
and supporting data structures for the cognitive loop.

All 20 research papers that affect state structure are implemented here.

This module re-exports all types and functions for backwards compatibility.
"""

# Constants
from .constants import (
    AUTONOMY_THRESHOLDS,
    CATEGORY_MULTIPLIERS,
    DIFFICULTY_WEIGHTS,
    INVALIDATION_THRESHOLDS,
    LEARNING_RATE,
    PEAK_END_MULTIPLIER,
    PEAK_INTENSITY_THRESHOLD,
)

# Factory functions
from .factory import (
    compute_relationship_value,
    create_belief,
    create_initial_state,
    create_memory,
    create_person,
    generate_id,
)

# Main state
from .main import BabyMARSState

# Reducers
from .reducers import note_reducer, task_reducer

# All types
from .types import (
    ActiveTask,
    AppraisalResult,
    BeliefState,
    BeliefStrengthEvent,
    ContextState,
    EntityObject,
    FeedbackEvent,
    Memory,
    Note,
    Objects,
    PersonObject,
    PersonRelationship,
    SelectedAction,
    TaskState,
    TemporalContext,
    ValidationResult,
    WorkUnit,
)

__all__ = [
    # Constants
    "CATEGORY_MULTIPLIERS",
    "INVALIDATION_THRESHOLDS",
    "AUTONOMY_THRESHOLDS",
    "DIFFICULTY_WEIGHTS",
    "PEAK_END_MULTIPLIER",
    "PEAK_INTENSITY_THRESHOLD",
    "LEARNING_RATE",
    # Types - Column 1
    "TaskState",
    "ActiveTask",
    # Types - Column 2
    "Note",
    # Types - Column 3
    "PersonObject",
    "EntityObject",
    "TemporalContext",
    "Objects",
    # Types - Beliefs
    "ContextState",
    "BeliefState",
    # Types - Memory
    "Memory",
    # Types - Social
    "PersonRelationship",
    # Types - Appraisal
    "AppraisalResult",
    # Types - Actions
    "WorkUnit",
    "SelectedAction",
    # Types - Validation
    "ValidationResult",
    # Types - Events
    "BeliefStrengthEvent",
    "FeedbackEvent",
    # Main state
    "BabyMARSState",
    # Reducers
    "task_reducer",
    "note_reducer",
    # Factory functions
    "generate_id",
    "create_initial_state",
    "create_belief",
    "create_memory",
    "compute_relationship_value",
    "create_person",
]
