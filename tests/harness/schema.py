"""
Test Case Schema
=================

Pydantic models for scenario test specifications.
Each persona has a YAML file with test cases defining expected behavior.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ExpectedWorkUnit(BaseModel):
    """Expected work unit in output."""
    tool: str = Field(..., description="Tool category (erp, bank, email, etc.)")
    verb: str = Field(..., description="Action verb (create_record, send, etc.)")
    min_count: int = Field(default=1, description="Minimum times this should appear")
    max_count: Optional[int] = Field(default=None, description="Maximum times (None = unlimited)")
    entities: Optional[dict] = Field(default=None, description="Expected entity values")


class ValidationRule(BaseModel):
    """Validation rule for test assertions."""
    type: str = Field(..., description="Validation type: work_unit_count, supervision_mode, no_ethical_flags, escalation, capability_used")
    expected: Optional[str] = Field(default=None, description="Expected value for comparison")
    min: Optional[int] = Field(default=None, description="Minimum value for counts")
    max: Optional[int] = Field(default=None, description="Maximum value for counts")
    capability: Optional[str] = Field(default=None, description="Capability key for capability_used validation")


class ExpectedOutput(BaseModel):
    """Expected output for a test case."""
    supervision_mode: str = Field(
        default="autonomous",
        description="Expected supervision mode: autonomous, action_proposal, guidance_seeking"
    )
    work_units: list[ExpectedWorkUnit] = Field(
        default_factory=list,
        description="Expected work units to be generated"
    )
    capabilities_used: list[str] = Field(
        default_factory=list,
        description="Expected Stargate capability keys"
    )
    should_escalate: bool = Field(
        default=False,
        description="Whether the agent should escalate to human"
    )
    should_flag_exceptions: bool = Field(
        default=False,
        description="Whether the agent should flag exceptions"
    )
    ethical_concerns: bool = Field(
        default=False,
        description="Whether the request has ethical concerns"
    )


class TestCase(BaseModel):
    """A single test case for a persona."""
    id: str = Field(..., description="Unique test case ID")
    description: str = Field(..., description="What this test verifies")
    input: str = Field(..., description="User input to send to the agent")
    expected: ExpectedOutput = Field(..., description="Expected agent behavior")
    validation: list[ValidationRule] = Field(
        default_factory=list,
        description="Additional validation rules"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for filtering (e.g., 'critical', 'edge_case')"
    )
    skip: bool = Field(default=False, description="Skip this test")
    skip_reason: Optional[str] = Field(default=None, description="Why the test is skipped")


class PersonaMetadata(BaseModel):
    """Metadata extracted from scenario markdown."""
    difficulty: int = Field(default=3, description="Task difficulty 1-5")
    workflow_steps: int = Field(default=0, description="Number of workflow steps")
    decision_points: int = Field(default=0, description="Number of decision points")
    automation_susceptibility: int = Field(default=3, description="How automatable 1-5")

    def model_post_init(self, __context):
        """Clamp values to valid ranges."""
        object.__setattr__(self, 'difficulty', max(1, min(5, self.difficulty)))
        object.__setattr__(self, 'automation_susceptibility', max(1, min(5, self.automation_susceptibility)))


class PersonaSpec(BaseModel):
    """Complete test specification for a persona."""
    persona: dict = Field(..., description="Persona info: name, role, company, industry")
    metadata: PersonaMetadata = Field(default_factory=PersonaMetadata)
    test_cases: list[TestCase] = Field(default_factory=list)
    source_file: Optional[str] = Field(default=None, description="Source markdown file path")

    @property
    def name(self) -> str:
        return self.persona.get("name", "Unknown")

    @property
    def company(self) -> str:
        return self.persona.get("company", "Unknown")

    @property
    def role(self) -> str:
        return self.persona.get("role", "Unknown")

    def active_test_cases(self) -> list[TestCase]:
        """Return non-skipped test cases."""
        return [tc for tc in self.test_cases if not tc.skip]


class ScoreBreakdown(BaseModel):
    """Breakdown of scores by dimension."""
    understanding: float = Field(default=0.0, description="Appraisal accuracy (20%)")
    action_correctness: float = Field(default=0.0, description="Work unit accuracy (30%)")
    autonomy_calibration: float = Field(default=0.0, description="Supervision mode match (20%)")
    completeness: float = Field(default=0.0, description="All expected units generated (20%)")
    error_handling: float = Field(default=0.0, description="Escalation accuracy (10%)")

    def weighted_total(self) -> float:
        """Calculate weighted total score."""
        return (
            self.understanding * 0.20 +
            self.action_correctness * 0.30 +
            self.autonomy_calibration * 0.20 +
            self.completeness * 0.20 +
            self.error_handling * 0.10
        )


class TestCaseResult(BaseModel):
    """Result of running a single test case."""
    test_case_id: str
    passed: bool
    score: float = Field(ge=0.0, le=100.0)
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    actual_supervision_mode: Optional[str] = None
    actual_work_units: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class PersonaResult(BaseModel):
    """Result of running all tests for a persona."""
    persona_name: str
    company: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    score: float = Field(ge=0.0, le=100.0)
    test_results: list[TestCaseResult] = Field(default_factory=list)
    execution_time_ms: float = 0.0

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests * 100


class CompanyResult(BaseModel):
    """Aggregated results for a company."""
    company: str
    total_personas: int
    total_tests: int
    passed_tests: int
    score: float = Field(ge=0.0, le=100.0)
    persona_results: list[PersonaResult] = Field(default_factory=list)


class HarnessReport(BaseModel):
    """Complete test harness report."""
    overall_score: float = Field(ge=0.0, le=100.0)
    pass_threshold: float = Field(default=96.0)
    passed: bool = False
    total_personas: int = 0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    company_results: list[CompanyResult] = Field(default_factory=list)
    top_failures: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
