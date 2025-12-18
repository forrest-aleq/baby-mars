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

from datetime import datetime
from typing import Optional
import uuid

from ...state.schema import (
    BabyMARSState,
    Memory,
    FeedbackEvent,
)
from ...graphs.belief_graph_manager import get_org_belief_graph, save_org_belief


# ============================================================
# OUTCOME ANALYSIS
# ============================================================

def analyze_outcome(
    execution_results: list[dict],
    validation_results: list[dict]
) -> dict:
    """
    Analyze execution and validation results to determine outcome.
    
    Returns:
        outcome_type: "success", "partial_success", "failure"
        success_rate: 0.0 to 1.0
        peak_event: Most significant event (for peak-end rule)
        failures: List of failure details
    """
    if not execution_results:
        return {
            "outcome_type": "failure",
            "success_rate": 0.0,
            "peak_event": None,
            "failures": ["No execution results"]
        }
    
    # Count successes
    exec_successes = sum(1 for r in execution_results if r.get("success", False))
    exec_total = len(execution_results)
    
    val_successes = sum(1 for r in validation_results if r.get("passed", True))
    val_total = len(validation_results) if validation_results else 1
    
    # Combined success rate
    exec_rate = exec_successes / exec_total if exec_total > 0 else 0
    val_rate = val_successes / val_total if val_total > 0 else 1
    success_rate = (exec_rate + val_rate) / 2
    
    # Determine outcome type
    if success_rate >= 0.9:
        outcome_type = "success"
    elif success_rate >= 0.5:
        outcome_type = "partial_success"
    else:
        outcome_type = "failure"
    
    # Find peak event (most significant)
    peak_event = None
    peak_severity = 0
    
    for r in validation_results:
        severity = r.get("severity", 0)
        if severity > peak_severity:
            peak_severity = severity
            peak_event = {
                "type": "validation_failure" if not r.get("passed") else "validation_success",
                "message": r.get("message", ""),
                "severity": severity
            }
    
    # Collect failures
    failures = []
    for r in execution_results:
        if not r.get("success", False):
            failures.append(r.get("message", "Execution failed"))
    for r in validation_results:
        if not r.get("passed", True):
            failures.append(r.get("message", "Validation failed"))
    
    return {
        "outcome_type": outcome_type,
        "success_rate": success_rate,
        "peak_event": peak_event,
        "failures": failures
    }


# ============================================================
# BELIEF UPDATE LOGIC
# ============================================================

async def update_beliefs_from_outcome(
    state: BabyMARSState,
    outcome: dict
) -> list[dict]:
    """
    Update beliefs based on outcome.

    Paper #7: Moral Asymmetry Event Sourcing
    Paper #9: Moral Asymmetry Multiplier

    - Positive outcomes strengthen beliefs gradually
    - Negative outcomes weaken beliefs more rapidly
    - Ethical beliefs have special protection
    - Beliefs are persisted to DB after each update
    """
    org_id = state.get("org_id", "default")
    belief_graph = await get_org_belief_graph(org_id)

    attributed_beliefs = state.get("appraisal", {}).get("attributed_beliefs", [])
    outcome_type = outcome.get("outcome_type", "failure")
    success_rate = outcome.get("success_rate", 0.0)
    context_key = state.get("current_context_key", "*|*|*")

    updates = []

    for belief_id in attributed_beliefs:
        # Calculate outcome signal
        if outcome_type == "success":
            outcome_signal = "success"
        elif outcome_type == "partial_success":
            outcome_signal = "neutral"
        else:
            outcome_signal = "failure"

        # Get difficulty from appraisal
        difficulty = state.get("appraisal", {}).get("difficulty", 3)

        # Update the belief using the proper method
        try:
            event = belief_graph.update_belief_from_outcome(
                belief_id=belief_id,
                context_key=context_key,
                outcome=outcome_signal,
                difficulty_level=difficulty,
                is_end_memory=False,
                emotional_intensity=0.5
            )

            if event:
                updates.append({
                    "belief_id": belief_id,
                    "old_strength": event.get("old_strength", 0),
                    "new_strength": event.get("new_strength", 0),
                    "outcome": outcome_signal
                })

                # Persist the updated belief to database
                updated_belief = belief_graph.get_belief(belief_id)
                if updated_belief:
                    await save_org_belief(org_id, updated_belief)

        except Exception as e:
            print(f"Error updating belief {belief_id}: {e}")

    return updates


# ============================================================
# MEMORY CREATION
# ============================================================

def create_memory_from_outcome(
    state: BabyMARSState,
    outcome: dict
) -> Optional[Memory]:
    """
    Create a memory from significant outcomes.
    
    Paper #12: Peak-End Rule Memory Weighting
    Paper #14: Cognitive Engrams
    
    Only create memories for:
    - Significant successes
    - Failures (for learning)
    - Events with high emotional/professional impact
    """
    outcome_type = outcome.get("outcome_type", "")
    peak_event = outcome.get("peak_event")
    
    # Determine if memory-worthy
    if outcome_type == "success":
        # Only memorable if it was a significant achievement
        if outcome.get("success_rate", 0) < 0.95:
            return None
        memory_type = "procedural"
        emotional_weight = 0.3
    elif outcome_type == "failure":
        # Failures are always memorable for learning
        memory_type = "episodic"
        emotional_weight = 0.6
    else:
        # Partial success - memorable if notable
        if not peak_event:
            return None
        memory_type = "episodic"
        emotional_weight = 0.4
    
    # Build memory content (find most recent user message)
    messages = state.get("messages", [])
    request_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            request_content = content[:200]  # Truncate
            break
    
    action = state.get("selected_action", {})
    action_summary = f"{action.get('action_type', 'unknown')} with {len(action.get('work_units', []))} work units"
    
    memory: Memory = {
        "memory_id": f"mem_{uuid.uuid4().hex[:12]}",
        "type": memory_type,
        "content": {
            "request": request_content,
            "action": action_summary,
            "outcome": outcome_type,
            "failures": outcome.get("failures", [])[:3],  # Top 3 failures
            "peak_event": peak_event
        },
        "created_at": datetime.now().isoformat(),
        "emotional_weight": emotional_weight,
        "decay_rate": 0.01 if memory_type == "procedural" else 0.05,
        "associations": state.get("appraisal", {}).get("attributed_beliefs", [])
    }
    
    return memory


# ============================================================
# FEEDBACK EVENT LOGGING
# ============================================================

def create_feedback_event(
    state: BabyMARSState,
    outcome: dict,
    belief_updates: list[dict]
) -> FeedbackEvent:
    """Create a feedback event for logging"""
    
    return {
        "event_id": f"fb_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now().isoformat(),
        "trigger": "execution_outcome",
        "outcome_type": outcome.get("outcome_type", "unknown"),
        "belief_updates": belief_updates,
        "context_key": state.get("current_context_key", "*|*|*"),
        "supervision_mode": state.get("supervision_mode", "unknown")
    }


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================

async def process(state: BabyMARSState) -> dict:
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
    outcome = analyze_outcome(execution_results, validation_results)
    
    # Update beliefs
    belief_updates = await update_beliefs_from_outcome(state, outcome)
    
    # Create memory if significant
    memory = create_memory_from_outcome(state, outcome)
    
    # Create feedback event
    feedback_event = create_feedback_event(state, outcome, belief_updates)
    
    # Build state updates
    updates = {
        "feedback_events": state.get("feedback_events", []) + [feedback_event]
    }
    
    if memory:
        updates["memories"] = state.get("memories", []) + [memory]
    
    # Store outcome for response generation
    updates["execution_outcome"] = outcome
    
    return updates
