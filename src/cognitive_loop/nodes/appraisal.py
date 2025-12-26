"""
Appraisal Node
===============

Analyzes the current situation against activated beliefs.
Uses Claude to perform rich cognitive appraisal.

Implements the appraisal phase of the cognitive loop:
- Face threat analysis
- Expectancy violation detection
- Goal alignment assessment
- Uncertainty identification
"""

from typing import Any, cast

from ...analytics import get_belief_analytics
from ...claude_models import AppraisalOutput
from ...claude_singleton import get_claude_client
from ...observability import get_logger
from ...state.schema import (
    AppraisalResult,
    BabyMARSState,
)

logger = get_logger(__name__)


def _track_autonomy_decision(
    state: BabyMARSState,
    mode: str,
    belief_strength: float,
    belief_count: int,
    difficulty: int,
) -> None:
    """Track autonomy decision in PostHog analytics."""
    org_id = state.get("org_id", "default")
    person = state.get("person", {})
    person_id = person.get("id", "unknown") if isinstance(person, dict) else "unknown"
    analytics = get_belief_analytics()
    analytics.autonomy_mode_determined(
        org_id=org_id,
        person_id=person_id,
        mode=mode,
        aggregate_strength=belief_strength,
        belief_count=belief_count,
        difficulty=difficulty,
    )


# ============================================================
# CONTEXT BUILDING
# ============================================================


def _format_beliefs_context(beliefs: list[Any]) -> str:
    """Format activated beliefs prioritizing competence over identity."""
    if not beliefs:
        return ""
    competence = [b for b in beliefs if b.get("category") in ("competence", "technical")]
    other = [b for b in beliefs if b.get("category") not in ("competence", "technical", "identity")]
    identity = [b for b in beliefs if b.get("category") == "identity"]
    prioritized = competence[:6] + other[:2] + identity[:2]

    lines = []
    for b in prioritized:
        strength = b.get("resolved_strength", b.get("strength", 0))
        lines.append(
            f"- [{b['belief_id']}] {b['statement']} (category={b['category']}, strength={strength:.2f})"
        )
    return "<activated_beliefs>\n" + "\n".join(lines) + "\n</activated_beliefs>"


def _format_people_context(people: list[Any]) -> str:
    """Format people context for appraisal."""
    if not people:
        return ""
    lines = []
    for p in people[:5]:
        lines.append(
            f"- {p['name']} ({p['role']}) - authority={p.get('authority', 0):.2f}, relationship_value={p.get('relationship_value', 0):.2f}"
        )
    return "<people_context>\n" + "\n".join(lines) + "\n</people_context>"


def _format_temporal_context(temporal: Any) -> str:
    """Format temporal context for appraisal."""
    if not temporal:
        return ""
    return f"""<temporal_context>
- Current time: {temporal.get("current_time", "unknown")}
- Month-end: {temporal.get("is_month_end", False)}
- Quarter-end: {temporal.get("is_quarter_end", False)}
- Year-end: {temporal.get("is_year_end", False)}
- Urgency multiplier: {temporal.get("urgency_multiplier", 1.0)}
</temporal_context>"""


def build_appraisal_context(state: BabyMARSState) -> str:
    """Build context string for Claude appraisal."""
    parts = []

    # Current message
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<current_request>\n{content}\n</current_request>")

    parts.append(f"<context_key>{state.get('current_context_key', '*|*|*')}</context_key>")

    beliefs_ctx = _format_beliefs_context(state.get("activated_beliefs", []))
    if beliefs_ctx:
        parts.append(beliefs_ctx)

    goals = state.get("active_goals", [])
    if goals:
        goal_strs = [f"- [{g.get('goal_id', 'unknown')}] {g.get('description', '')}" for g in goals]
        parts.append("<active_goals>\n" + "\n".join(goal_strs) + "\n</active_goals>")

    objects = state.get("objects", {})
    people_ctx = _format_people_context(objects.get("people", []))
    if people_ctx:
        parts.append(people_ctx)

    temporal_ctx = _format_temporal_context(objects.get("temporal", {}))
    if temporal_ctx:
        parts.append(temporal_ctx)

    return "\n\n".join(parts)


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


def _build_appraisal_prompt(context: str) -> str:
    """Build the appraisal prompt for Claude."""
    return f"""Perform cognitive appraisal of this situation.

{context}

Analyze the request and provide a structured appraisal including:
- Face threat level (how much does this threaten the user's professional identity?)
- Expectancy violation (is this request surprising in any way?)
- Goal alignment (how does this align with active goals?)
- Urgency level
- Areas of uncertainty
- Recommended approach (seek_guidance, propose_action, or execute)
- Which beliefs are most relevant
- Difficulty assessment (1-5)
- Whether ethical beliefs are involved

Return your appraisal in the structured format."""


def _convert_to_appraisal_result(appraisal: AppraisalOutput) -> AppraisalResult:
    """Convert AppraisalOutput to AppraisalResult format."""
    return {
        "expectancy_violation": {"type": appraisal.expectancy_violation, "description": None}
        if appraisal.expectancy_violation
        else None,
        "face_threat": {
            "level": appraisal.face_threat_level,
            "mitigation_needed": appraisal.face_threat_level > 0.3,
        }
        if appraisal.face_threat_level > 0
        else None,
        "goal_alignment": appraisal.goal_alignment,
        "attributed_beliefs": appraisal.relevant_belief_ids,
        "recommended_action_type": _map_approach(appraisal.recommended_approach),  # type: ignore[typeddict-item]
        "difficulty": appraisal.difficulty_assessment,
        "involves_ethical_beliefs": appraisal.involves_ethical_beliefs,
    }


def _fallback_appraisal_result() -> dict[str, Any]:
    """Return fallback result when appraisal fails."""
    return {
        "appraisal": {
            "expectancy_violation": None,
            "face_threat": None,
            "goal_alignment": {},
            "attributed_beliefs": [],
            "recommended_action_type": "guidance_needed",
            "difficulty": 3,
            "involves_ethical_beliefs": False,
        },
        "supervision_mode": "guidance_seeking",
        "belief_strength_for_action": 0.3,
    }


async def process(state: BabyMARSState) -> dict[str, Any]:
    """Appraisal Node: analyze situation against beliefs and determine autonomy."""
    try:
        client = get_claude_client()
        context = build_appraisal_context(state)
        messages = [{"role": "user", "content": _build_appraisal_prompt(context)}]

        appraisal = await client.complete_structured(
            messages=messages,
            response_model=AppraisalOutput,
            skills=["situation_appraisal", "accounting_domain"],
        )

        result = _convert_to_appraisal_result(appraisal)
        activated_beliefs = state.get("activated_beliefs", [])
        belief_strength = _compute_aggregate_strength(
            appraisal.relevant_belief_ids, cast(list[dict[str, Any]], activated_beliefs)
        )
        supervision_mode = _determine_supervision_mode(appraisal, state, belief_strength)

        _track_autonomy_decision(
            state,
            supervision_mode,
            belief_strength,
            len(appraisal.relevant_belief_ids),
            appraisal.difficulty_assessment,
        )

        return {
            "appraisal": result,
            "supervision_mode": supervision_mode,
            "belief_strength_for_action": belief_strength,
        }
    except Exception as e:
        logger.error(f"Appraisal error: {e}")
        return _fallback_appraisal_result()


def _map_approach(approach: str) -> str:
    """Map appraisal approach to action type"""
    mapping = {
        "seek_guidance": "guidance_needed",
        "propose_action": "propose_and_confirm",
        "execute": "execute_directly",
    }
    return mapping.get(approach, "guidance_needed")


def _determine_supervision_mode(
    appraisal: AppraisalOutput, state: BabyMARSState, belief_strength: float
) -> str:
    """
    Determine supervision mode primarily from belief strength (Paper #1).

    Paper #1: Competence-Based Autonomy
    - belief_strength < 0.4: guidance_seeking
    - belief_strength 0.4-0.7: action_proposal
    - belief_strength >= 0.7: autonomous

    Exceptions that force lower autonomy:
    - Difficulty 5: always guidance_seeking
    - Difficulty 4: cap at action_proposal
    - Low belief strength always wins
    """
    from ...state.schema import AUTONOMY_THRESHOLDS

    # Very high difficulty forces guidance_seeking
    if appraisal.difficulty_assessment >= 5:
        return "guidance_seeking"

    # Compute mode from belief strength (Paper #1)
    if belief_strength < AUTONOMY_THRESHOLDS["guidance_seeking"]:
        mode = "guidance_seeking"
    elif belief_strength < AUTONOMY_THRESHOLDS["action_proposal"]:
        mode = "action_proposal"
    else:
        mode = "autonomous"

    # High difficulty (4) caps at action_proposal
    if appraisal.difficulty_assessment >= 4 and mode == "autonomous":
        mode = "action_proposal"

    return mode


def _compute_aggregate_strength(belief_ids: list[str], beliefs: list[dict[str, Any]]) -> float:
    """
    Compute average strength of relevant competence beliefs.

    Paper #1: Autonomy is based on COMPETENCE beliefs, not identity.
    Identity beliefs are immutable constraints, not capability indicators.
    """
    if not belief_ids:
        return 0.3  # Default low

    belief_map = {b["belief_id"]: b for b in beliefs}
    competence_strengths = []
    other_strengths = []

    for bid in belief_ids:
        if bid in belief_map:
            b = belief_map[bid]
            strength = b.get("resolved_strength", b.get("strength", 0.5))
            category = b.get("category", "competence")

            # Identity beliefs are constraints, not competence indicators
            if category == "identity":
                continue

            # Competence and technical beliefs drive autonomy
            if category in ("competence", "technical"):
                competence_strengths.append(strength)
            else:
                other_strengths.append(strength)

    # Prefer competence/technical beliefs
    if competence_strengths:
        return float(sum(competence_strengths) / len(competence_strengths))

    # Fall back to other beliefs (moral, preference) if no competence beliefs
    if other_strengths:
        return float(sum(other_strengths) / len(other_strengths))

    return 0.3  # Default low when no relevant beliefs
