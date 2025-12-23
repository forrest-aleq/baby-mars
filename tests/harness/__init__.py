"""
Baby MARS Scenario Test Harness
================================

Tests 41 personas across 4 companies with a 96% pass threshold.

Usage:
    python -m tests.harness.runner --all
    python -m tests.harness.runner --persona angela_park
    python -m tests.harness.runner --company storagecorner
"""

from .runner import HarnessRunner
from .schema import (
    ExpectedOutput,
    PersonaResult,
    PersonaSpec,
    TestCase,
    TestCaseResult,
    ValidationRule,
)
from .scorer import Scorer

__all__ = [
    "TestCase",
    "PersonaSpec",
    "ExpectedOutput",
    "ValidationRule",
    "TestCaseResult",
    "PersonaResult",
    "Scorer",
    "HarnessRunner",
]
