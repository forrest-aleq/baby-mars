"""
Action Selection Node
======================

Selects action based on appraisal and beliefs.
Determines autonomy level per Paper #1.

Key responsibilities:
1. Determine if we have sufficient belief strength to act
2. Select appropriate action based on appraisal
3. Build work units for execution (if autonomous)
4. Route to appropriate next step based on supervision mode
"""

from typing import Any, Optional

from ...claude_client import ActionSelectionOutput, get_claude_client
from ...observability import get_logger
from ...state.schema import (
    AUTONOMY_THRESHOLDS,
    BabyMARSState,
    SelectedAction,
    WorkUnit,
)

logger = get_logger(__name__)

# ============================================================
# ACTION PLANNING
# ============================================================


def build_action_context(state: BabyMARSState) -> str:
    """Build context for action selection"""
    parts = []

    # Current request
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<request>\n{content}\n</request>")

    # Appraisal results
    appraisal = state.get("appraisal")
    if appraisal:
        parts.append(f"""<appraisal>
  Recommended action type: {appraisal.get("recommended_action_type", "unknown")}
  Difficulty: {appraisal.get("difficulty", 3)}
  Involves ethical beliefs: {appraisal.get("involves_ethical_beliefs", False)}
  Attributed beliefs: {", ".join(appraisal.get("attributed_beliefs", []))}
</appraisal>""")

    # Supervision mode and belief strength
    parts.append(f"""<autonomy>
  Supervision mode: {state.get("supervision_mode", "guidance_seeking")}
  Belief strength for action: {state.get("belief_strength_for_action", 0):.2f}
</autonomy>""")

    # Relevant beliefs for context
    beliefs = state.get("activated_beliefs", [])
    if beliefs:
        belief_strs = []
        for b in beliefs[:8]:
            strength = b.get("resolved_strength", b.get("strength", 0))
            belief_strs.append(
                f"- {b['statement']} (strength={strength:.2f}, category={b['category']})"
            )
        parts.append("<relevant_beliefs>\n" + "\n".join(belief_strs) + "\n</relevant_beliefs>")

    # Active tasks (to avoid duplication)
    tasks = state.get("active_tasks", [])
    if tasks:
        task_strs = []
        for t in tasks:
            task_strs.append(f"- {t['description']} (status={t['state']['status']})")
        parts.append("<active_tasks>\n" + "\n".join(task_strs) + "\n</active_tasks>")

    return "\n\n".join(parts)


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict[str, Any]:
    """
    Action Selection Node

    Determines appropriate action based on:
    1. Appraisal results
    2. Belief strength (autonomy level)
    3. Available tools and capabilities
    4. Current supervision mode

    Returns:
    - selected_action: The action to take (or None for guidance)
    - supervision_mode: May be updated based on action requirements
    """

    supervision_mode = state.get("supervision_mode", "guidance_seeking")
    belief_strength = state.get("belief_strength_for_action", 0.0)
    appraisal = state.get("appraisal")

    # For guidance_seeking mode, don't select an action
    if supervision_mode == "guidance_seeking":
        return {"selected_action": None, "supervision_mode": "guidance_seeking"}

    client = get_claude_client()

    # Build context
    context = build_action_context(state)

    # Build messages
    messages = [
        {
            "role": "user",
            "content": f"""Based on the appraisal, select an appropriate action.

{context}

If the supervision mode is "action_proposal", design an action that you will propose for confirmation.
If the supervision mode is "autonomous", design an action you can execute directly.

Create work units using the semantic vocabulary:
- tool: Which system (erp, bank, documents, email, workflow)
- verb: Semantic action (create_record, process_invoice, send_notification, etc.)
- entities: What to operate on
- slots: Parameters
- constraints: Verification requirements

Return your action selection in the structured format.""",
        }
    ]

    try:
        # Call Claude for action selection
        selection = await client.complete_structured(
            messages=messages,
            response_model=ActionSelectionOutput,
            skills=["work_unit_vocabulary", "accounting_domain"],
        )

        # Check if human approval required (override to action_proposal)
        if selection.requires_human_approval:
            supervision_mode = "action_proposal"

        # Build selected action
        work_units: list[WorkUnit] = []
        for wu in selection.work_units:
            work_units.append(
                {
                    "unit_id": wu.get("unit_id", f"wu_{len(work_units)}"),
                    "tool": wu.get("tool", "workflow"),
                    "verb": wu.get("verb", "query_records"),
                    "entities": wu.get("entities", {}),
                    "slots": wu.get("slots", {}),
                    "constraints": wu.get("constraints", []),
                }
            )

        selected_action: SelectedAction = {
            "action_type": selection.action_type,
            "work_units": work_units,
            "requires_tools": selection.tool_requirements,
            "estimated_difficulty": selection.estimated_difficulty,
        }

        return {
            "selected_action": selected_action,
            "supervision_mode": supervision_mode,
            "belief_strength_for_action": selection.confidence,
        }

    except Exception as e:
        # On error, fall back to guidance seeking
        print(f"Action selection error: {e}")
        return {"selected_action": None, "supervision_mode": "guidance_seeking"}


# ============================================================
# AUTONOMY HELPERS
# ============================================================


def compute_autonomy_level(belief_strength: float, appraisal: Optional[dict[str, Any]]) -> str:
    """
    Compute autonomy level from belief strength.
    Paper #1: Competence-Based Autonomy
    """
    # Check for overrides from appraisal
    if appraisal:
        if appraisal.get("involves_ethical_beliefs", False):
            return "guidance_seeking"

        difficulty = appraisal.get("difficulty", 3)
        if difficulty >= 5:
            return "guidance_seeking"
        elif difficulty >= 4 and belief_strength < 0.8:
            return "action_proposal"

    # Standard threshold mapping
    if belief_strength < AUTONOMY_THRESHOLDS["guidance_seeking"]:
        return "guidance_seeking"
    elif belief_strength < AUTONOMY_THRESHOLDS["action_proposal"]:
        return "action_proposal"
    else:
        return "autonomous"
