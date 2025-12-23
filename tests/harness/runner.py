"""
Harness Runner
===============

Executes persona test cases through the Baby MARS cognitive loop.
Uses real Claude API and real Stargate for integration tests.
"""

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .extractor import ScenarioExtractor
from .schema import (
    CompanyResult,
    HarnessReport,
    PersonaResult,
    PersonaSpec,
    TestCase,
    TestCaseResult,
)
from .scorer import Scorer


@dataclass
class RunConfig:
    """Configuration for test runs."""

    use_real_api: bool = True  # Use real Claude API
    use_real_stargate: bool = True  # Use real Stargate
    pass_threshold: float = 96.0
    verbose: bool = True
    parallel: bool = False  # Run tests in parallel (costs more)


class HarnessRunner:
    """Runs test cases through the Baby MARS cognitive loop."""

    def __init__(self, config: Optional[RunConfig] = None):
        self.config = config or RunConfig()
        self.scorer = Scorer(pass_threshold=self.config.pass_threshold)
        self.scenarios_dir = Path("tests/scenarios")

    def load_persona_spec(self, yaml_path: Path) -> PersonaSpec:
        """Load a persona spec from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return PersonaSpec(**data)

    def list_personas(self, company: Optional[str] = None) -> list[Path]:
        """List all persona YAML files."""
        if company:
            return list((self.scenarios_dir / company).glob("*.yaml"))
        return list(self.scenarios_dir.glob("**/*.yaml"))

    async def run_test_case(
        self,
        test_case: TestCase,
        persona: PersonaSpec,
    ) -> TestCaseResult:
        """Run a single test case through the cognitive loop."""
        from src.birth import quick_birth
        from src.cognitive_loop.graph import create_graph_in_memory, invoke_cognitive_loop
        from src.graphs.belief_graph import get_belief_graph, reset_belief_graph
        from src.graphs.belief_graph_manager import (
            get_belief_graph_manager,
            reset_belief_graph_manager,
        )

        # Reset both the in-memory graph AND the manager cache
        reset_belief_graph()
        reset_belief_graph_manager()

        start_time = time.time()

        # Birth the agent with persona's role
        state = quick_birth(
            name=persona.name,
            role=persona.role,
            industry=persona.persona.get("industry", "general"),
            message=test_case.input,
        )

        # Add company context
        org_id = persona.company.lower().replace(" ", "_")
        state["org_id"] = org_id

        # CRITICAL: Populate the manager cache with the birthed beliefs
        # quick_birth seeds beliefs into get_belief_graph() but cognitive_activation
        # loads via get_org_belief_graph(org_id) which uses the manager
        manager = get_belief_graph_manager()
        birthed_graph = get_belief_graph()
        manager._cache[org_id] = birthed_graph

        # Run cognitive loop
        loop_graph = create_graph_in_memory()

        try:
            result = await invoke_cognitive_loop(state, loop_graph)
        except Exception as e:
            # Handle errors gracefully
            elapsed_ms = (time.time() - start_time) * 1000
            return TestCaseResult(
                test_case_id=test_case.id,
                passed=False,
                score=0.0,
                errors=[f"Execution error: {str(e)}"],
                execution_time_ms=elapsed_ms,
            )

        elapsed_ms = (time.time() - start_time) * 1000

        # Handle None result
        if result is None:
            return TestCaseResult(
                test_case_id=test_case.id,
                passed=False,
                score=0.0,
                errors=["Cognitive loop returned None"],
                execution_time_ms=elapsed_ms,
            )

        # Extract actual values from result
        actual_supervision_mode = result.get("supervision_mode", "unknown")
        selected_action = result.get("selected_action") or {}
        actual_work_units = selected_action.get("work_units", []) if selected_action else []
        actual_appraisal = result.get("appraisal", {})

        # Check if agent escalated
        did_escalate = actual_supervision_mode == "guidance_seeking" or result.get(
            "gate_violation_detected", False
        )

        # Check if exceptions were flagged
        flagged_exceptions = actual_appraisal.get("has_exceptions", False)

        # Score the result
        test_result = self.scorer.score_test_case(
            test_case=test_case,
            actual_supervision_mode=actual_supervision_mode,
            actual_work_units=actual_work_units,
            actual_appraisal=actual_appraisal,
            did_escalate=did_escalate,
            flagged_exceptions=flagged_exceptions,
        )

        test_result.execution_time_ms = elapsed_ms
        return test_result

    async def run_persona(self, spec: PersonaSpec) -> PersonaResult:
        """Run all test cases for a persona."""
        start_time = time.time()
        test_results = []

        active_tests = spec.active_test_cases()

        if self.config.verbose:
            print(f"\n  Running {len(active_tests)} tests for {spec.name}...")

        for test_case in active_tests:
            if self.config.verbose:
                print(f"    - {test_case.id}: ", end="", flush=True)

            result = await self.run_test_case(test_case, spec)
            test_results.append(result)

            if self.config.verbose:
                status = "PASS" if result.passed else "FAIL"
                print(f"{status} ({result.score:.1f}%)")

        elapsed_ms = (time.time() - start_time) * 1000

        return self.scorer.aggregate_persona_results(
            persona_name=spec.name,
            company=spec.company,
            test_results=test_results,
            execution_time_ms=elapsed_ms,
        )

    async def run_company(self, company: str) -> CompanyResult:
        """Run all personas for a company."""
        persona_files = self.list_personas(company)
        persona_results = []

        if self.config.verbose:
            print(f"\nCompany: {company} ({len(persona_files)} personas)")

        for yaml_path in persona_files:
            try:
                spec = self.load_persona_spec(yaml_path)
                result = await self.run_persona(spec)
                persona_results.append(result)
            except Exception as e:
                if self.config.verbose:
                    print(f"  ERROR loading {yaml_path.name}: {e}")

        return self.scorer.aggregate_company_results(company, persona_results)

    async def run_all(self) -> HarnessReport:
        """Run all personas across all companies."""
        start_time = time.time()

        # Find all companies
        companies = [d.name for d in self.scenarios_dir.iterdir() if d.is_dir()]

        if self.config.verbose:
            print("\nBaby MARS Scenario Test Harness")
            print("================================")
            print(f"Companies: {', '.join(companies)}")
            print(f"Pass threshold: {self.config.pass_threshold}%")
            print(f"Real API: {self.config.use_real_api}")
            print(f"Real Stargate: {self.config.use_real_stargate}")

        company_results = []
        for company in companies:
            result = await self.run_company(company)
            company_results.append(result)

        elapsed_ms = (time.time() - start_time) * 1000

        return self.scorer.generate_report(company_results, elapsed_ms)

    async def run_single_persona(self, persona_name: str) -> PersonaResult:
        """Run tests for a single persona by name."""
        # Find the persona file
        for yaml_path in self.list_personas():
            spec = self.load_persona_spec(yaml_path)
            if spec.name.lower().replace(" ", "_") == persona_name.lower().replace(" ", "_"):
                return await self.run_persona(spec)

        raise ValueError(f"Persona not found: {persona_name}")


def print_report(report: HarnessReport):
    """Print a formatted report."""
    status_emoji = {
        True: "PASS",
        False: "FAIL",
    }

    score_emoji = (
        lambda s: "READY"
        if s >= 96
        else ("PARTIAL" if s >= 70 else ("LIMITED" if s >= 50 else "NOT READY"))
    )

    print(f"\n{'='*60}")
    print("Baby MARS Readiness Report")
    print(f"{'='*60}")
    print(f"\nOverall Score: {report.overall_score:.1f}% {score_emoji(report.overall_score)}")
    print(f"Status: {status_emoji[report.passed]} (threshold: {report.pass_threshold}%)")
    print("\nBy Company:")

    for cr in report.company_results:
        print(
            f"  {cr.company:20} {cr.score:5.1f}% {score_emoji(cr.score)} ({cr.total_personas} personas)"
        )

    if report.top_failures:
        print("\nTop Failures:")
        for f in report.top_failures[:5]:
            print(f"  X {f['persona']}/{f['test_case']} - {f['score']:.1f}%")
            for err in f.get("errors", [])[:1]:
                print(f"      {err}")

    if report.recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

    print(f"\nExecution Time: {report.execution_time_ms/1000:.1f}s")
    print(
        f"Total: {report.total_tests} tests, {report.passed_tests} passed, {report.failed_tests} failed"
    )
    print(f"{'='*60}\n")


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Baby MARS Scenario Test Harness")
    parser.add_argument("--all", action="store_true", help="Run all personas")
    parser.add_argument("--company", help="Run all personas for a company")
    parser.add_argument("--persona", help="Run a single persona")
    parser.add_argument(
        "--threshold", type=float, default=96.0, help="Pass threshold (default: 96)"
    )
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--extract", action="store_true", help="Extract test cases first")
    parser.add_argument("--list", action="store_true", help="List available personas")
    args = parser.parse_args()

    config = RunConfig(
        pass_threshold=args.threshold,
        verbose=not args.quiet,
    )

    runner = HarnessRunner(config)

    # Extract mode - run extractor first
    if args.extract:
        extractor = ScenarioExtractor()
        if args.company:
            specs = extractor.extract_all(company=args.company)
        else:
            specs = extractor.extract_all()
        print(f"Extracted {len(specs)} persona specs")
        return

    # List mode
    if args.list:
        personas = runner.list_personas(args.company)
        print(f"Found {len(personas)} personas:")
        for p in personas:
            print(f"  {p.parent.name}/{p.stem}")
        return

    # Run tests
    if args.persona:
        result = await runner.run_single_persona(args.persona)
        print(
            f"\n{result.persona_name}: {result.score:.1f}% ({result.passed_tests}/{result.total_tests} passed)"
        )

    elif args.company:
        result = await runner.run_company(args.company)
        print(
            f"\n{result.company}: {result.score:.1f}% ({result.passed_tests}/{result.total_tests} passed)"
        )

    elif args.all:
        report = await runner.run_all()
        print_report(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
