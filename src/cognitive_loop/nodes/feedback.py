"""
Feedback Node
==============

Updates beliefs based on execution outcomes.
Implements learning from experience (Papers #3, #7, #9, #12).

Key responsibilities:
1. Update belief strengths based on outcomes
2. Create memories from significant events
3. Log feedback for future learning
4. Handle peak-end memory weighting
"""

import uuid
from datetime import datetime
from typing import Any, Optional, cast

from ...analytics import get_belief_analytics
from ...graphs.belief_graph_manager import get_org_belief_graph, save_modified_beliefs
from ...observability import get_logger
from ...state.schema import (
    BabyMARSState,
    BeliefState,
    FeedbackEvent,
    Memory,
)

logger = get_logger(__name__)


def _track_belief_update(
    org_id: str,
    belief_id: str,
    belief: BeliefState,
    old_strength: float,
    new_strength: float,
    outcome: str,
    multiplier: float,
    context_key: str,
) -> None:
    """Track belief update in PostHog analytics."""
    analytics = get_belief_analytics()
    analytics.belief_updated(
        org_id=org_id,
        belief_id=belief_id,
        category=belief.get("category", "unknown"),
        old_strength=old_strength,
        new_strength=new_strength,
        outcome=outcome,
        multiplier=multiplier,
        context_key=context_key,
        is_cascade=False,
    )


# ============================================================
# OUTCOME ANALYSIS
# ============================================================


def _compute_success_rate(
    execution_results: list[dict[str, Any]], validation_results: list[dict[str, Any]]
) -> float:
    """Compute combined success rate from execution and validation results."""
    exec_successes = sum(1 for r in execution_results if r.get("success", False))
    exec_total = len(execution_results)
    val_successes = sum(1 for r in validation_results if r.get("passed", True))
    val_total = len(validation_results) if validation_results else 1
    exec_rate = exec_successes / exec_total if exec_total > 0 else 0
    val_rate = val_successes / val_total if val_total > 0 else 1
    return (exec_rate + val_rate) / 2


def _find_peak_event(validation_results: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Find the most significant validation event (Paper #12 peak-end rule)."""
    peak_event, peak_severity = None, 0
    for r in validation_results:
        severity = r.get("severity", 0)
        if severity > peak_severity:
            peak_severity = severity
            peak_event = {
                "type": "validation_failure" if not r.get("passed") else "validation_success",
                "message": r.get("message", ""),
                "severity": severity,
            }
    return peak_event


def _collect_failures(
    execution_results: list[dict[str, Any]], validation_results: list[dict[str, Any]]
) -> list[str]:
    """Collect failure messages from execution and validation results."""
    failures = [
        r.get("message", "Execution failed")
        for r in execution_results
        if not r.get("success", False)
    ]
    failures += [
        r.get("message", "Validation failed")
        for r in validation_results
        if not r.get("passed", True)
    ]
    return failures


def analyze_outcome(
    execution_results: list[dict[str, Any]], validation_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Analyze execution and validation results to determine outcome."""
    if not execution_results:
        return {
            "outcome_type": "failure",
            "success_rate": 0.0,
            "peak_event": None,
            "failures": ["No execution results"],
        }

    success_rate = _compute_success_rate(execution_results, validation_results)
    outcome_type = (
        "success"
        if success_rate >= 0.9
        else ("partial_success" if success_rate >= 0.5 else "failure")
    )

    return {
        "outcome_type": outcome_type,
        "success_rate": success_rate,
        "peak_event": _find_peak_event(validation_results),
        "failures": _collect_failures(execution_results, validation_results),
    }


# ============================================================
# BELIEF UPDATE LOGIC
# ============================================================


def _outcome_to_signal(outcome_type: str) -> str:
    """Map outcome type to signal for belief update."""
    if outcome_type == "success":
        return "success"
    elif outcome_type == "partial_success":
        return "neutral"
    return "failure"


async def update_beliefs_from_outcome(
    state: BabyMARSState, outcome: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Update beliefs based on outcome (Papers #7, #9, #11).
    Persists all modified beliefs including cascaded updates.
    """
    org_id = state.get("org_id", "default")
    belief_graph = await get_org_belief_graph(org_id)
    appraisal: dict[str, Any] = cast(dict[str, Any], state.get("appraisal") or {})
    attributed_beliefs = appraisal.get("attributed_beliefs", [])
    context_key = state.get("current_context_key", "*|*|*")
    outcome_signal = _outcome_to_signal(outcome.get("outcome_type", "failure"))
    difficulty = appraisal.get("difficulty", 3)

    updates = []
    for belief_id in attributed_beliefs:
        update = await _update_single_belief(
            org_id, belief_graph, belief_id, context_key, outcome_signal, difficulty
        )
        if update:
            updates.append(update)

    # Persist ALL modified beliefs (including cascaded ones) in a single batch
    saved_count = await save_modified_beliefs(org_id, belief_graph)
    if saved_count > len(updates):
        logger.info(f"Saved {saved_count} beliefs ({saved_count - len(updates)} cascaded)")

    return updates


async def _update_single_belief(
    org_id: str,
    belief_graph: Any,
    belief_id: str,
    context_key: str,
    outcome_signal: str,
    difficulty: int,
) -> Optional[dict[str, Any]]:
    """Update a single belief and track in analytics."""
    try:
        event = belief_graph.update_belief_from_outcome(
            belief_id=belief_id,
            context_key=context_key,
            outcome=outcome_signal,
            difficulty_level=difficulty,
            is_end_memory=False,
            emotional_intensity=0.5,
        )
        if not event:
            return None

        old_strength = event.get("old_strength", 0)
        new_strength = event.get("new_strength", 0)

        # Track in PostHog
        updated_belief = belief_graph.get_belief(belief_id)
        if updated_belief:
            _track_belief_update(
                org_id,
                belief_id,
                updated_belief,
                old_strength,
                new_strength,
                outcome_signal,
                event.get("category_multiplier", 1.0),
                context_key,
            )

        return {
            "belief_id": belief_id,
            "old_strength": old_strength,
            "new_strength": new_strength,
            "outcome": outcome_signal,
        }
    except Exception as e:
        print(f"Error updating belief {belief_id}: {e}")
        return None


# ============================================================
# MEMORY CREATION
# ============================================================


def _classify_memory(outcome: dict[str, Any]) -> Optional[tuple[str, float]]:
    """Classify outcome for memory creation. Returns (type, weight) or None if not memorable."""
    outcome_type = outcome.get("outcome_type", "")
    if outcome_type == "success":
        if outcome.get("success_rate", 0) < 0.95:
            return None
        return ("procedural", 0.3)
    elif outcome_type == "failure":
        return ("episodic", 0.6)
    elif outcome.get("peak_event"):
        return ("episodic", 0.4)
    return None


def _extract_request_content(state: BabyMARSState) -> str:
    """Extract the most recent user request from state messages."""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            return str(content)[:200]
    return ""


def create_memory_from_outcome(state: BabyMARSState, outcome: dict[str, Any]) -> Optional[Memory]:
    """Create memory from significant outcomes (Papers #12, #14)."""
    classification = _classify_memory(outcome)
    if not classification:
        return None

    memory_type, emotional_weight = classification
    action: dict[str, Any] = state.get("selected_action") or {}  # type: ignore[assignment]
    appraisal_data: dict[str, Any] = cast(dict[str, Any], state.get("appraisal") or {})

    return cast(
        Memory,
        {
            "memory_id": f"mem_{uuid.uuid4().hex[:12]}",
            "type": memory_type,
            "content": {
                "request": _extract_request_content(state),
                "action": f"{action.get('action_type', 'unknown')} with {len(action.get('work_units', []))} work units",
                "outcome": outcome.get("outcome_type", ""),
                "failures": outcome.get("failures", [])[:3],
                "peak_event": outcome.get("peak_event"),
            },
            "created_at": datetime.now().isoformat(),
            "emotional_weight": emotional_weight,
            "decay_rate": 0.01 if memory_type == "procedural" else 0.05,
            "associations": appraisal_data.get("attributed_beliefs", []),
        },
    )


# ============================================================
# FEEDBACK EVENT LOGGING
# ============================================================


def create_feedback_event(
    state: BabyMARSState, outcome: dict[str, Any], belief_updates: list[dict[str, Any]]
) -> FeedbackEvent:
    """Create a feedback event for logging"""

    return cast(
        FeedbackEvent,
        {
            "event_id": f"fb_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now().isoformat(),
            "trigger": "execution_outcome",
            "outcome_type": outcome.get("outcome_type", "unknown"),
            "belief_updates": belief_updates,
            "context_key": state.get("current_context_key", "*|*|*"),
            "supervision_mode": state.get("supervision_mode") or "unknown",
        },
    )


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict[str, Any]:
    """
    Feedback Node

    Updates system based on execution outcome:
    1. Analyze outcome (success/failure)
    2. Update attributed beliefs
    3. Create memories for significant events
    4. Log feedback event
    """

    execution_results = state.get("execution_results", [])
    validation_results = state.get("validation_results", [])

    # Skip feedback if no execution occurred
    if not execution_results:
        return {}

    # Analyze outcome
    outcome = analyze_outcome(
        execution_results,
        cast(list[dict[str, Any]], validation_results),
    )

    # Update beliefs
    belief_updates = await update_beliefs_from_outcome(state, outcome)

    # Create memory if significant
    memory = create_memory_from_outcome(state, outcome)

    # Create feedback event
    feedback_event = create_feedback_event(state, outcome, belief_updates)

    # Build state updates
    feedback_events: list[Any] = cast(list[Any], state.get("feedback_events") or [])
    updates: dict[str, Any] = {"feedback_events": feedback_events + [feedback_event]}

    if memory:
        memories: list[Any] = cast(list[Any], state.get("memories") or [])
        updates["memories"] = memories + [memory]

    # Store outcome for response generation
    updates["execution_outcome"] = outcome

    return updates
