"""
Mount System Models
====================

Data classes for the mount system.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemporalContext:
    """
    Current temporal situation (computed at mount, not stored).

    This affects:
    - Which context-specific beliefs activate
    - Urgency multipliers for goals
    - Style adjustments (month-end = more deliberate)
    """

    current_time: str
    day_of_week: str
    time_of_day: str  # morning, afternoon, evening
    month_phase: str  # month-start, mid-month, month-end
    quarter_phase: str  # normal, Q-close
    is_month_end: bool
    is_quarter_end: bool
    is_year_end: bool
    fiscal_events: list[str] = field(default_factory=list)


@dataclass
class ActiveSubgraph:
    """
    The mounted state for a person - all 6 things resolved.

    This is what the cognitive loop receives.
    """

    person: dict[str, Any]
    org: dict[str, Any]
    capabilities: dict[str, bool]  # Binary flags
    relationships: dict[str, Any]  # Org structure
    knowledge: list[dict[str, Any]]  # Facts (no strength)
    beliefs: list[dict[str, Any]]  # Claims (with strength)
    goals: list[dict[str, Any]]  # Active goals
    style: dict[str, Any]  # Resolved style
    temporal: TemporalContext  # Current situation
