"""
Scenario-Based Integration Tests
=================================

pytest integration for the scenario test harness.
Runs persona tests through the Baby MARS cognitive loop.

Usage:
    pytest tests/test_scenarios.py -v
    pytest tests/test_scenarios.py -k "storagecorner" -v
    pytest tests/test_scenarios.py --run-scenarios
"""

import pytest
import asyncio
from pathlib import Path

from tests.harness import HarnessRunner
from tests.harness.schema import PersonaSpec, HarnessReport
from tests.harness.runner import RunConfig


# Skip by default - use --run-scenarios to enable
pytestmark = pytest.mark.skipif(
    "not config.getoption('--run-scenarios')",
    reason="Scenario tests require --run-scenarios flag"
)


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-scenarios",
        action="store_true",
        default=False,
        help="Run scenario-based integration tests (uses real Claude API)"
    )
    parser.addoption(
        "--threshold",
        type=float,
        default=96.0,
        help="Pass threshold for scenario tests (default: 96%%)"
    )


@pytest.fixture
def runner_config(request) -> RunConfig:
    """Get runner configuration from pytest options."""
    threshold = request.config.getoption("--threshold")
    return RunConfig(
        pass_threshold=threshold,
        verbose=True,
    )


@pytest.fixture
def harness_runner(runner_config) -> HarnessRunner:
    """Create harness runner instance."""
    return HarnessRunner(runner_config)


class TestScenarioHarness:
    """Scenario test harness integration tests."""

    @pytest.mark.asyncio
    async def test_list_personas(self, harness_runner: HarnessRunner):
        """Verify personas can be listed."""
        personas = harness_runner.list_personas()
        # May be empty if not extracted yet
        assert isinstance(personas, list)

    @pytest.mark.asyncio
    async def test_run_all_scenarios(self, harness_runner: HarnessRunner):
        """Run all scenarios and verify pass threshold."""
        personas = harness_runner.list_personas()

        if not personas:
            pytest.skip("No persona specs found. Run extractor first.")

        report = await harness_runner.run_all()

        assert isinstance(report, HarnessReport)
        assert report.overall_score >= 0.0
        assert report.overall_score <= 100.0

        # Check pass threshold
        if not report.passed:
            failures = [
                f"{f['persona']}/{f['test_case']}: {f['score']:.1f}%"
                for f in report.top_failures[:5]
            ]
            pytest.fail(
                f"Readiness score {report.overall_score:.1f}% below threshold "
                f"{report.pass_threshold}%.\nTop failures:\n" +
                "\n".join(failures)
            )


class TestStorageCorner:
    """StorageCorner persona tests."""

    @pytest.mark.asyncio
    async def test_storagecorner_personas(self, harness_runner: HarnessRunner):
        """Test all StorageCorner personas."""
        result = await harness_runner.run_company("storagecorner")

        assert result.score >= harness_runner.config.pass_threshold, (
            f"StorageCorner score {result.score:.1f}% below threshold"
        )


class TestClose:
    """Close company persona tests."""

    @pytest.mark.asyncio
    async def test_close_personas(self, harness_runner: HarnessRunner):
        """Test all Close personas."""
        result = await harness_runner.run_company("close")

        assert result.score >= harness_runner.config.pass_threshold, (
            f"Close score {result.score:.1f}% below threshold"
        )


class TestGGHC:
    """GGHC persona tests."""

    @pytest.mark.asyncio
    async def test_gghc_personas(self, harness_runner: HarnessRunner):
        """Test all GGHC personas."""
        result = await harness_runner.run_company("gghc")

        assert result.score >= harness_runner.config.pass_threshold, (
            f"GGHC score {result.score:.1f}% below threshold"
        )


class TestDockwa:
    """Dockwa persona tests."""

    @pytest.mark.asyncio
    async def test_dockwa_personas(self, harness_runner: HarnessRunner):
        """Test all Dockwa personas."""
        result = await harness_runner.run_company("dockwa")

        assert result.score >= harness_runner.config.pass_threshold, (
            f"Dockwa score {result.score:.1f}% below threshold"
        )
