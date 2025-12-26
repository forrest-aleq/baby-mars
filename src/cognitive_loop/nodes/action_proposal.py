"""
Action Proposal Node (HITL Interrupt)
======================================

Handles human-in-the-loop approval for actions.
Uses LangGraph's interrupt() to pause execution until human responds.

Flow:
1. Generate human-readable summary of proposed action
2. Call interrupt() - graph pauses here
3. On resume, check response:
   - approve: Continue to execution
   - reject: Go to guidance_seeking mode
"""

from typing import Any, Literal

from langgraph.types import interrupt

from ...claude_singleton import get_claude_client
from ...observability import get_logger
from ...state.schema import BabyMARSState, SelectedAction

logger = get_logger(__name__)

# ============================================================
# HUMAN-READABLE SUMMARY GENERATION
# ============================================================


def _format_work_units(action: SelectedAction) -> str:
    """Format work units as bullet points for display."""
    work_units = action.get("work_units", [])
    descriptions = []
    for wu in work_units:
        tool = wu.get("tool", "unknown")
        verb = wu.get("verb", "unknown")
        entities = wu.get("entities", {})
        desc = f"• {verb.replace('_', ' ').title()} via {tool}"
        if entities:
            entity_str = ", ".join(f"{k}: {v}" for k, v in entities.items())
            desc += f" ({entity_str})"
        descriptions.append(desc)
    return "\n".join(descriptions) if descriptions else "• (No specific actions defined)"


def _get_original_request(state: BabyMARSState) -> str:
    """Extract the most recent user message (truncated to 200 chars)."""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            return str(content)[:200]
    return ""


async def generate_action_summary(state: BabyMARSState, action: SelectedAction) -> str:
    """Generate a human-readable summary of the proposed action for approval."""
    client = get_claude_client()
    work_units_text = _format_work_units(action)
    original_request = _get_original_request(state)

    prompt = f"""Generate a brief, professional summary of this proposed action for human approval.

Original request: {original_request}

Proposed actions:
{work_units_text}

Action type: {action.get("action_type", "unknown")}
Estimated difficulty: {action.get("estimated_difficulty", 3)}/5

Write 2-4 bullet points explaining what will happen if approved.
Be specific about amounts, accounts, and entities involved.
End with a brief reason why approval is needed (e.g., amount threshold, sensitive data, etc.)

Keep it under 150 words. Be professional but conversational."""

    try:
        return await client.complete(messages=[{"role": "user", "content": prompt}])
    except Exception:
        return f"""I'd like to perform the following action:

{work_units_text}

This requires your approval before I can proceed.

[Approve] to continue, or [Reject] to cancel and discuss alternatives."""


# ============================================================
# INTERRUPT PAYLOAD
# ============================================================


def build_interrupt_payload(
    state: BabyMARSState, action: SelectedAction, summary: str
) -> dict[str, Any]:
    """
    Build the payload that will be sent to the frontend
    when the graph pauses for approval.
    """
    return {
        "type": "action_proposal",
        "summary": summary,
        "action_type": action.get("action_type", "unknown"),
        "work_unit_count": len(action.get("work_units", [])),
        "estimated_difficulty": action.get("estimated_difficulty", 3),
        "requires_tools": action.get("requires_tools", []),
        "thread_id": state.get("thread_id"),
        "options": ["approve", "reject"],
    }


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict[str, Any]:
    """
    Action Proposal Node

    Generates a human-readable summary and pauses for approval.

    On interrupt response:
    - "approve": Sets flag to continue to execution
    - "reject": Changes supervision_mode to guidance_seeking
    """

    action = state.get("selected_action")

    if not action:
        # No action to propose - skip to guidance
        return {"supervision_mode": "guidance_seeking", "approval_status": "no_action"}

    # Generate human-readable summary
    summary = await generate_action_summary(state, action)

    # Build interrupt payload
    payload = build_interrupt_payload(state, action, summary)

    # PAUSE HERE - wait for human response
    # The graph will resume when the frontend calls with an interrupt response
    human_response = interrupt(payload)

    # Process the response
    choice = (
        human_response.get("choice", "reject") if isinstance(human_response, dict) else "reject"
    )

    if choice == "approve":
        # Continue to execution
        return {
            "approval_status": "approved",
            "approval_summary": summary,
            # Keep supervision_mode as action_proposal so routing knows we're approved
        }
    else:
        # Rejected - go to guidance seeking
        return {
            "supervision_mode": "guidance_seeking",
            "approval_status": "rejected",
            "approval_summary": summary,
            # Clear the selected action since it was rejected
            "selected_action": None,
        }


# ============================================================
# ROUTING HELPER
# ============================================================


def route_after_proposal(state: BabyMARSState) -> Literal["execution", "response_generation"]:
    """
    Route based on approval status.
    Called after action_proposal node resumes.
    """
    approval_status = state.get("approval_status", "")

    if approval_status == "approved":
        return "execution"
    else:
        return "response_generation"
