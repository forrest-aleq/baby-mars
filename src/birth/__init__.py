"""
Baby MARS Birth System
=======================

In-memory initialization of the 6 types for new people/orgs.
"""

from .birth_system import (
    birth_person,
    create_initial_state,
    quick_birth,
    calculate_salience,
    determine_birth_mode,
    IMMUTABLE_BELIEFS,
    DEFAULT_CAPABILITIES,
    ROLE_HIERARCHY,
    ROLE_GOALS,
)

__all__ = [
    "birth_person",
    "create_initial_state", 
    "quick_birth",
    "calculate_salience",
    "determine_birth_mode",
    "IMMUTABLE_BELIEFS",
    "DEFAULT_CAPABILITIES",
    "ROLE_HIERARCHY",
    "ROLE_GOALS",
]
