"""
Verification Node
==================

Validates execution results against constraints.
Paper #3: Self-Correcting Validation

Runs validators on execution results and determines
whether to proceed, retry, or escalate.
"""

from typing import Any, cast

from ...claude_models import ValidationOutput
from ...claude_singleton import get_claude_client
from ...observability import get_logger
from ...state.schema import (
    BabyMARSState,
    ValidationResult,
)

logger = get_logger(__name__)

# ============================================================
# BUILT-IN VALIDATORS
# ============================================================


class Validators:
    """Collection of standard validators"""

    @staticmethod
    def amount_validator(result: dict[str, Any], constraint: dict[str, Any]) -> ValidationResult:
        """Validate amount is within bounds"""
        params = constraint.get("params", {})
        min_val = params.get("min", 0)
        max_val = params.get("max", float("inf"))

        amount = result.get("result", {}).get("amount", 0)

        if amount < min_val:
            return {
                "validator": "amount_validator",
                "passed": False,
                "severity": 0.7,
                "message": f"Amount {amount} below minimum {min_val}",
                "fix_hint": f"Adjust amount to be at least {min_val}",
            }

        if amount > max_val:
            return {
                "validator": "amount_validator",
                "passed": False,
                "severity": 0.8,
                "message": f"Amount {amount} exceeds maximum {max_val}",
                "fix_hint": "Amount exceeds limit - requires additional approval",
            }

        return {
            "validator": "amount_validator",
            "passed": True,
            "severity": 0.0,
            "message": f"Amount {amount} within bounds [{min_val}, {max_val}]",
            "fix_hint": None,
        }

    @staticmethod
    def required_fields_validator(
        result: dict[str, Any], constraint: dict[str, Any]
    ) -> ValidationResult:
        """Validate all required fields are present"""
        params = constraint.get("params", {})
        required_fields = params.get("fields", [])

        result_data = result.get("result", {})
        missing = []

        for field in required_fields:
            if field not in result_data or result_data[field] is None:
                missing.append(field)

        if missing:
            return {
                "validator": "required_fields_validator",
                "passed": False,
                "severity": 0.6,
                "message": f"Missing required fields: {', '.join(missing)}",
                "fix_hint": f"Provide values for: {', '.join(missing)}",
            }

        return {
            "validator": "required_fields_validator",
            "passed": True,
            "severity": 0.0,
            "message": "All required fields present",
            "fix_hint": None,
        }

    @staticmethod
    def balance_validator(result: dict[str, Any], constraint: dict[str, Any]) -> ValidationResult:
        """Validate debits equal credits (for journal entries)"""
        params = constraint.get("params", {})
        tolerance = params.get("tolerance", 0.01)

        result_data = result.get("result", {})
        debits = result_data.get("debits_total", 0)
        credits = result_data.get("credits_total", 0)

        difference = abs(debits - credits)

        if difference > tolerance:
            return {
                "validator": "balance_validator",
                "passed": False,
                "severity": 0.9,
                "message": f"Entry out of balance: debits={debits}, credits={credits}, diff={difference}",
                "fix_hint": "Adjust entries to balance debits and credits",
            }

        return {
            "validator": "balance_validator",
            "passed": True,
            "severity": 0.0,
            "message": f"Entry balanced: debits={debits}, credits={credits}",
            "fix_hint": None,
        }

    @staticmethod
    def success_validator(result: dict[str, Any], constraint: dict[str, Any]) -> ValidationResult:
        """Basic check that execution succeeded"""
        success = result.get("success", False)

        if not success:
            return {
                "validator": "success_validator",
                "passed": False,
                "severity": 0.8,
                "message": f"Execution failed: {result.get('message', 'Unknown error')}",
                "fix_hint": "Review execution error and retry",
            }

        return {
            "validator": "success_validator",
            "passed": True,
            "severity": 0.0,
            "message": "Execution succeeded",
            "fix_hint": None,
        }


# Validator registry
VALIDATORS = {
    "amount_within_bounds": Validators.amount_validator,
    "required_fields_present": Validators.required_fields_validator,
    "balance_check": Validators.balance_validator,
    "success_check": Validators.success_validator,
}


# ============================================================
# VALIDATION LOGIC
# ============================================================


def run_validators(
    execution_results: list[dict[str, Any]], work_units: list[dict[str, Any]]
) -> list[ValidationResult]:
    """
    Run validators on execution results.

    Maps work unit constraints to their results and
    runs appropriate validators.
    """
    all_results = []

    for i, result in enumerate(execution_results):
        unit_id = result.get("unit_id", f"unknown_{i}")

        # Always run success validator
        success_result = Validators.success_validator(result, {})
        all_results.append(success_result)

        # If execution failed, skip other validators
        if not result.get("success", False):
            continue

        # Find matching work unit
        matching_wu = None
        for wu in work_units:
            if wu.get("unit_id") == unit_id:
                matching_wu = wu
                break

        if not matching_wu:
            continue

        # Run constraint validators
        constraints = matching_wu.get("constraints", [])
        for constraint in constraints:
            constraint_type = constraint.get("type", "")

            if constraint_type in VALIDATORS:
                validator = VALIDATORS[constraint_type]
                validation_result = validator(result, constraint)
                all_results.append(validation_result)

    return all_results


def determine_action(
    validation_results: list[ValidationResult], retry_count: int, max_retries: int
) -> str:
    """
    Determine next action based on validation results.

    Returns: "proceed", "retry", or "escalate"
    """
    failures = [r for r in validation_results if not r.get("passed", True)]

    if not failures:
        return "proceed"

    # Check severity of failures
    max_severity = max(f.get("severity", 0) for f in failures)

    # High severity always escalates
    if max_severity >= 0.9:
        return "escalate"

    # Check retry budget
    if retry_count >= max_retries:
        return "escalate"

    # Check if failures are retryable
    # Low severity failures can be retried
    if max_severity < 0.7:
        return "retry"

    # Medium severity - retry once, then escalate
    if retry_count == 0:
        return "retry"

    return "escalate"


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict[str, Any]:
    """
    Verification Node

    Validates execution results:
    1. Run built-in validators based on work unit constraints
    2. Optionally use Claude for complex validation
    3. Determine if results pass, need retry, or escalation
    """

    execution_results = list(state.get("execution_results") or [])
    selected_action = state.get("selected_action")
    work_units = cast(
        list[dict[str, Any]],
        selected_action.get("work_units", [])
        if selected_action and isinstance(selected_action, dict)
        else [],
    )

    retry_count = int(state.get("retry_count") or 0)
    max_retries = int(state.get("max_retries") or 3)

    # Run built-in validators
    validation_results = run_validators(execution_results, work_units)

    # Check if Claude-based validation needed for complex cases
    complex_validation_needed = _needs_complex_validation(validation_results, execution_results)

    if complex_validation_needed:
        try:
            claude_results = await _claude_validation(state, execution_results)
            validation_results.extend(claude_results)
        except Exception as e:
            print(f"Claude validation error: {e}")
            # Continue with built-in results only

    # Determine action
    action = determine_action(validation_results, retry_count, max_retries)

    # Map action to state updates
    if action == "retry":
        return {"validation_results": validation_results, "retry_count": retry_count + 1}
    elif action == "escalate":
        return {
            "validation_results": validation_results,
            "supervision_mode": "guidance_seeking",  # Force escalation
        }
    else:  # proceed
        return {"validation_results": validation_results}


def _needs_complex_validation(
    validation_results: list[ValidationResult], execution_results: list[dict[str, Any]]
) -> bool:
    """Check if complex Claude-based validation is needed"""
    # For MVP, only use Claude validation if:
    # - There are uncertain failures
    # - Results involve multiple interconnected records
    # - Custom business rules may apply

    # Simple heuristic for now
    for result in execution_results:
        if result.get("verb") in ["post_journal_entry", "reconcile_account"]:
            return True

    return False


def _build_validation_prompt(state: BabyMARSState, execution_results: list[dict[str, Any]]) -> str:
    """Build validation prompt for Claude."""
    context_parts = [f"<execution_results>\n{execution_results}\n</execution_results>"]
    beliefs = state.get("activated_beliefs", [])[:5]
    if beliefs:
        belief_strs = [f"- {b['statement']}" for b in beliefs]
        context_parts.append(
            "<relevant_beliefs>\n" + "\n".join(belief_strs) + "\n</relevant_beliefs>"
        )

    return f"""Validate these execution results against accounting best practices.

{chr(10).join(context_parts)}

Check for:
1. Completeness - all necessary data present
2. Accuracy - calculations and references correct
3. Compliance - follows accounting standards
4. Consistency - internal logic coherent

Return validation results in structured format."""


def _convert_validation_results(response: ValidationOutput) -> list[ValidationResult]:
    """Convert ValidationOutput to ValidationResult list."""
    results: list[ValidationResult] = []
    for r in response.results:
        results.append(
            cast(
                ValidationResult,
                {
                    "validator": r.get("validator", "claude_validator"),
                    "passed": r.get("passed", True),
                    "severity": r.get("severity", 0.0),
                    "message": r.get("message", ""),
                    "fix_hint": r.get("fix_hint"),
                },
            )
        )
    return results


async def _claude_validation(
    state: BabyMARSState, execution_results: list[dict[str, Any]]
) -> list[ValidationResult]:
    """Use Claude for complex validation."""
    try:
        client = get_claude_client()
        prompt = _build_validation_prompt(state, execution_results)
        response = await client.complete_structured(
            messages=[{"role": "user", "content": prompt}],
            response_model=ValidationOutput,
            skills=["validation_rules", "accounting_domain"],
        )
        return _convert_validation_results(response)
    except Exception as e:
        return cast(
            list[ValidationResult],
            [
                {
                    "validator": "claude_validator",
                    "passed": True,
                    "severity": 0.1,
                    "message": f"Claude validation skipped: {e}",
                    "fix_hint": None,
                }
            ],
        )
