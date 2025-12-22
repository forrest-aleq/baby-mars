"""
Baby MARS Scenario Test Harness
================================

Tests 41 personas across 4 companies with a 96% pass threshold.

Usage:
    python -m tests.harness.runner --all
    python -m tests.harness.runner --persona angela_park
    python -m tests.harness.runner --company storagecorner
"""

from .schema import TestCase, PersonaSpec, ExpectedOutput, ValidationRule, TestCaseResult, PersonaResult
from .scorer import Scorer
from .runner import HarnessRunner

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
