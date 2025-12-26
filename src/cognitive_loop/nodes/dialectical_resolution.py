"""
Dialectical Resolution Node
============================

Handles goal conflicts through synthesis or prioritization.
Uses Claude to reason about competing goals and find resolution.

Paper #6: Goal Conflict Resolution
"""

from typing import Any

from ...claude_models import DialecticalOutput
from ...claude_singleton import get_claude_client
from ...observability import get_logger
from ...state.schema import BabyMARSState

logger = get_logger(__name__)

# ============================================================
# CONFLICT ANALYSIS
# ============================================================


def build_conflict_context(state: BabyMARSState) -> str:
    """Build context describing the goal conflict"""
    parts = []

    # Current request
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<current_request>\n{content}\n</current_request>")

    # Active goals
    goals = state.get("active_goals", [])
    if goals:
        goal_details = []
        for g in goals:
            goal_details.append(f"""<goal id="{g.get("goal_id", "unknown")}">
  Description: {g.get("description", "")}
  Priority: {g.get("priority", 0.5)}
  Resources: {", ".join(g.get("resources", []))}
  Conflicts with: {", ".join(g.get("conflicts_with", []))}
</goal>""")
        parts.append("<active_goals>\n" + "\n".join(goal_details) + "\n</active_goals>")

    # Objects context for additional information
    objects = state.get("objects", {})

    # Relevant beliefs about goals
    beliefs = state.get("activated_beliefs", [])
    goal_related = [b for b in beliefs if "goal" in b.get("statement", "").lower()]
    if goal_related:
        belief_strs = []
        for b in goal_related[:5]:
            belief_strs.append(f"- {b.get('statement', '')} (strength={b.get('strength', 0):.2f})")
        parts.append("<relevant_beliefs>\n" + "\n".join(belief_strs) + "\n</relevant_beliefs>")

    # People context (for authority in resolution)
    people = objects.get("people", [])
    if people:
        parts.append("<authority_context>")
        for p in people[:3]:
            parts.append(
                f"- {p.get('name', 'unknown')} ({p.get('role', 'unknown')}): authority={p.get('authority', 0):.2f}"
            )
        parts.append("</authority_context>")

    return "\n\n".join(parts)


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


def _build_resolution_prompt(context: str) -> str:
    """Build prompt for goal conflict resolution."""
    return f"""A goal conflict has been detected. Please resolve it.

{context}

Analyze the conflicting goals and determine:
1. Can these goals be synthesized (combined in a way that satisfies both)?
2. If not, which goal should be prioritized and why?
3. How should the deferred goal(s) be handled?
4. Does this require human input to resolve?

Provide your resolution in the structured format."""


def _build_human_input_result(resolution: DialecticalOutput) -> dict[str, Any]:
    """Build result when human input is required."""
    return {
        "supervision_mode": "guidance_seeking",
        "goal_conflict_detected": True,
        "appraisal": {
            "expectancy_violation": {
                "type": "negative",
                "description": f"Goal conflict requiring resolution: {resolution.resolution_reasoning}",
            },
            "face_threat": None,
            "goal_alignment": {},
            "attributed_beliefs": [],
            "recommended_action_type": "guidance_needed",
            "difficulty": 4,
            "involves_ethical_beliefs": False,
        },
    }


def _process_resolution(state: BabyMARSState, resolution: DialecticalOutput) -> dict[str, Any]:
    """Process the resolution and update goals."""
    active_goals = state.get("active_goals", [])
    updated_goals = []
    deferred_notes = []
    current_time = state.get("objects", {}).get("temporal", {}).get("current_time", "")

    for goal in active_goals:
        goal_id = goal.get("goal_id", "")
        if goal_id == resolution.chosen_goal_id:
            updated_goals.append(
                {
                    **goal,
                    "synthesized_with": resolution.deferred_goal_ids
                    if resolution.synthesis
                    else [],
                    "resolution_note": resolution.synthesis if resolution.synthesis else None,
                }
            )
        elif goal_id in resolution.deferred_goal_ids:
            deferred_notes.append(
                {
                    "note_id": f"deferred_{goal_id}",
                    "content": f"Deferred goal: {goal.get('description', '')}. Reason: {resolution.resolution_reasoning}",
                    "created_at": current_time,
                    "ttl_hours": 24,
                    "priority": goal.get("priority", 0.5) * 0.8,
                    "source": "system",
                    "context": {"original_goal": goal},
                }
            )
        else:
            updated_goals.append(goal)

    return {
        "active_goals": updated_goals,
        "notes": state.get("notes", []) + deferred_notes,
        "goal_conflict_detected": False,
    }


async def process(state: BabyMARSState) -> dict[str, Any]:
    """Dialectical Resolution: resolve conflicts between competing goals (Paper #6)."""
    if not state.get("goal_conflict_detected", False):
        return {}

    try:
        client = get_claude_client()
        context = build_conflict_context(state)
        prompt = _build_resolution_prompt(context)

        resolution = await client.complete_structured(
            messages=[{"role": "user", "content": prompt}],
            response_model=DialecticalOutput,
            skills=["accounting_domain"],
        )

        if resolution.requires_human_input:
            return _build_human_input_result(resolution)

        return _process_resolution(state, resolution)
    except Exception as e:
        logger.error(f"Dialectical resolution error: {e}")
        return {"supervision_mode": "guidance_seeking", "goal_conflict_detected": True}
