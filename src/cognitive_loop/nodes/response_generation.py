"""
Response Generation Node
=========================

Generates the final response to the user.
Adapts tone and content based on supervision mode and outcome.

Uses response_generation skill for proper formatting
and professional communication patterns.
"""

from typing import Any

from ...claude_models import ResponseOutput
from ...claude_singleton import get_claude_client
from ...observability import get_logger
from ...state.schema import (
    BabyMARSState,
)

logger = get_logger(__name__)

# ============================================================
# CONTEXT BUILDING
# ============================================================


def _format_appraisal_context(appraisal: Any) -> str:
    """Format appraisal summary for response context."""
    face_threat = appraisal.get("face_threat")
    face_threat_level = face_threat.get("level", 0) if isinstance(face_threat, dict) else "none"
    return f"""<appraisal>
  Difficulty: {appraisal.get("difficulty", "unknown")}
  Recommended action: {appraisal.get("recommended_action_type", "unknown")}
  Face threat: {face_threat_level}
</appraisal>"""


def _format_action_context(selected_action: Any) -> str:
    """Format selected action for response context."""
    work_units = selected_action.get("work_units", [])
    wu_summary = [f"- {wu.get('tool', '?')}.{wu.get('verb', '?')}" for wu in work_units[:5]]
    return f"""<selected_action>
  Type: {selected_action.get("action_type", "unknown")}
  Work units:
{chr(10).join(wu_summary)}
</selected_action>"""


def _format_execution_context(execution_results: list[dict[str, Any]]) -> str:
    """Format execution results for response context."""
    result_summary = []
    for r in execution_results:
        status = "✓" if r.get("success", False) else "✗"
        result_summary.append(
            f"- {status} {r.get('tool', '?')}.{r.get('verb', '?')}: {r.get('message', '')}"
        )
    return f"<execution_results>\n{chr(10).join(result_summary)}\n</execution_results>"


def _format_outcome_context(outcome: dict[str, Any]) -> str:
    """Format outcome summary for response context."""
    failures = outcome.get("failures", [])
    failure_list = failures[:3] if isinstance(failures, list) else []
    return f"""<outcome>
  Type: {outcome.get("outcome_type", "unknown")}
  Success rate: {float(outcome.get("success_rate", 0)):.0%}
  Failures: {", ".join(failure_list) or "none"}
</outcome>"""


def _format_rapport_context(rapport: dict[str, Any]) -> str:
    """Format rapport context for response generation."""
    parts = [
        f"  Person: {rapport.get('person_name', 'unknown')}",
        f"  Rapport level: {rapport.get('rapport_level', 0):.2f}",
        f"  Familiarity: {rapport.get('familiarity', 0):.2f}",
        f"  Interactions: {rapport.get('interaction_count', 0)}",
        f"  Preferred formality: {rapport.get('preferred_formality', 'casual')}",
        f"  Preferred verbosity: {rapport.get('preferred_verbosity', 'concise')}",
        f"  Humor receptivity: {rapport.get('humor_receptivity', 0.5):.2f}",
    ]
    if inside_refs := rapport.get("inside_references", []):
        parts.append(f"  Inside references: {', '.join(inside_refs[:3])}")
    if moments := rapport.get("memorable_moments", []):
        summaries = []
        for m in moments[:2]:
            if isinstance(m, dict) and m.get("summary"):
                summaries.append(str(m["summary"])[:50])
            elif isinstance(m, str):
                summaries.append(m[:50])
        if summaries:
            parts.append(f"  Recent moments: {'; '.join(summaries)}")
    if rapport.get("is_first_meeting"):
        parts.append("  NOTE: This is a FIRST MEETING - be warm but not presumptuous")
    return f"<rapport_context>\n{chr(10).join(parts)}\n</rapport_context>"


def _format_validation_issues(validation_results: list[Any]) -> str | None:
    """Format validation issues for response context."""
    valid_results = [r for r in validation_results if isinstance(r, dict)]
    failures = [r for r in valid_results if not r.get("passed", True)]
    if not failures:
        return None
    msgs = [f.get("message", "") for f in failures[:3] if isinstance(f, dict)]
    return f"<validation_issues>\n{chr(10).join('- ' + m for m in msgs)}\n</validation_issues>"


def build_response_context(state: BabyMARSState) -> str:
    """Build context for response generation."""
    parts = []
    messages = state.get("messages", [])
    if messages:
        content = messages[-1].get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<original_request>\n{content}\n</original_request>")

    parts.append(
        f"<supervision_mode>{state.get('supervision_mode', 'guidance_seeking')}</supervision_mode>"
    )

    if (appraisal := state.get("appraisal")) and isinstance(appraisal, dict):
        parts.append(_format_appraisal_context(appraisal))
    if (action := state.get("selected_action")) and isinstance(action, dict):
        parts.append(_format_action_context(action))
    exec_results = [r for r in state.get("execution_results", []) if isinstance(r, dict)]
    if exec_results:
        parts.append(_format_execution_context(exec_results))
    if (outcome := state.get("execution_outcome")) and isinstance(outcome, dict):
        parts.append(_format_outcome_context(outcome))
    if issues := _format_validation_issues(state.get("validation_results", [])):
        parts.append(issues)

    if people := state.get("objects", {}).get("people", []):
        p = people[0]
        parts.append(
            f"<communication_context>\n  Primary person: {p.get('name', 'unknown')} ({p.get('role', 'unknown')})\n  Authority: {p.get('authority', 0):.2f}\n</communication_context>"
        )

    if rapport := state.get("rapport_context"):
        parts.append(_format_rapport_context(rapport))
        if style := _get_rapport_style_guidance(rapport):
            parts.append(f"<style_guidance>\n{style}\n</style_guidance>")

    style_beliefs = [
        b for b in state.get("activated_beliefs", []) if str(b.get("category", "")) == "style"
    ][:3]
    if style_beliefs:
        parts.append(
            f"<style_beliefs>\n{chr(10).join('- ' + b['statement'] for b in style_beliefs)}\n</style_beliefs>"
        )

    return "\n\n".join(parts)


def _get_rapport_style_guidance(rapport: dict[str, Any]) -> str:
    """Generate style guidance based on rapport level."""
    rapport_level = rapport.get("rapport_level", 0.3)
    familiarity = rapport.get("familiarity", 0.0)
    humor_receptivity = rapport.get("humor_receptivity", 0.5)
    formality = rapport.get("preferred_formality", "casual")
    verbosity = rapport.get("preferred_verbosity", "concise")

    guidance = []

    # Rapport-based adjustments
    if rapport_level >= 0.7:
        guidance.append("High rapport: Be warm and friendly, can use casual language")
    elif rapport_level >= 0.5:
        guidance.append("Good rapport: Friendly but professional")
    else:
        guidance.append("Building rapport: Be helpful and approachable, earn trust")

    # Familiarity-based adjustments
    if familiarity >= 0.6:
        guidance.append("High familiarity: Can reference past interactions, use shortcuts")
    elif familiarity >= 0.3:
        guidance.append("Moderate familiarity: Some shared context, still building understanding")
    else:
        guidance.append("Low familiarity: Explain context, don't assume shared knowledge")

    # Humor guidance
    if humor_receptivity >= 0.7:
        guidance.append("Humor welcome: Light humor and personality encouraged")
    elif humor_receptivity <= 0.3:
        guidance.append("Keep it professional: Focus on substance, minimize personality")

    # Formality preference
    if formality == "formal":
        guidance.append("Use formal language and complete sentences")
    elif formality == "casual":
        guidance.append("Casual tone is fine, contractions ok")

    # Verbosity preference
    if verbosity == "detailed":
        guidance.append("They prefer thorough explanations")
    elif verbosity == "concise":
        guidance.append("Keep it brief and to the point")

    return "\n".join(f"- {g}" for g in guidance)


# ============================================================
# RESPONSE TEMPLATES
# ============================================================


def get_response_template(supervision_mode: str) -> str:
    """Get response template based on supervision mode"""

    templates = {
        "guidance_seeking": """You are seeking guidance from the user.
Generate a response that:
- Clearly explains what you need clarification on
- Presents specific options if applicable
- Asks focused questions (1-2 max)
- Maintains professional, helpful tone
- Does NOT make assumptions about what to do""",
        "action_proposal": """You are proposing an action for user approval.
Generate a response that:
- Clearly states what action you propose to take
- Explains the reasoning briefly
- Lists key details (amounts, accounts, dates)
- Asks for explicit confirmation before proceeding
- Offers alternatives if relevant""",
        "autonomous": """You have completed an action autonomously.
Generate a response that:
- Confirms what was done
- Provides key details of the result
- Notes any items for user awareness
- Offers next steps if applicable
- Is concise but complete""",
    }

    return templates.get(supervision_mode, templates["guidance_seeking"])


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================


def _build_response_prompt(template: str, context: str) -> str:
    """Build the response generation prompt."""
    return f"""Generate a response to the user based on this context.

{template}

{context}

Generate a professional, helpful response that:
1. Addresses the user's original request
2. Uses appropriate tone for the relationship
3. Is clear and concise
4. Follows the supervision mode guidelines

Return your response in the structured format."""


def _build_result(state: BabyMARSState, final_response: str) -> dict[str, Any]:
    """Build result dict with updated messages and final response."""
    return {
        "messages": state.get("messages", []) + [{"role": "assistant", "content": final_response}],
        "final_response": final_response,
    }


async def process(state: BabyMARSState) -> dict[str, Any]:
    """Response Generation: generate final response based on supervision mode."""
    supervision_mode = state.get("supervision_mode") or "guidance_seeking"

    try:
        client = get_claude_client()
        context = build_response_context(state)
        template = get_response_template(supervision_mode)
        prompt = _build_response_prompt(template, context)

        response = await client.complete_structured(
            messages=[{"role": "user", "content": prompt}],
            response_model=ResponseOutput,
            skills=["response_generation", "accounting_domain"],
        )

        return _build_result(state, _format_response(response, supervision_mode))
    except Exception as e:
        import traceback

        logger.error(f"Response generation error: {e}\n{traceback.format_exc()}")
        return _build_result(state, _generate_fallback_response(state, supervision_mode))


def _format_response(response: ResponseOutput, supervision_mode: str) -> str:
    """Format the response output"""

    parts = []

    # Main content
    parts.append(response.main_content)

    # Add action items if present
    if response.action_items:
        parts.append("")
        for item in response.action_items:
            parts.append(f"• {item}")

    # Add questions if seeking guidance
    if supervision_mode == "guidance_seeking" and response.questions:
        parts.append("")
        for q in response.questions:
            parts.append(f"→ {q}")

    # Add confirmation prompt if proposing action
    if supervision_mode == "action_proposal" and response.confirmation_prompt:
        parts.append("")
        parts.append(response.confirmation_prompt)

    return "\n".join(parts)


def _generate_fallback_response(state: BabyMARSState, supervision_mode: str) -> str:
    """Generate a fallback response when Claude call fails"""

    if supervision_mode == "guidance_seeking":
        return "I'd like to help with this request, but I need some additional information. Could you provide more details about what you're looking to accomplish?"

    elif supervision_mode == "action_proposal":
        action = state.get("selected_action")
        action_type = action.get("action_type", "action") if isinstance(action, dict) else "action"
        return f"I've prepared to {action_type}. Would you like me to proceed with this?"

    else:  # autonomous
        outcome = state.get("execution_outcome")
        if isinstance(outcome, dict):
            if outcome.get("outcome_type") == "success":
                return "I've completed the requested action. Let me know if you need anything else."
            else:
                failures = outcome.get("failures", [])
                if failures and isinstance(failures, list) and len(failures) > 0:
                    return (
                        f"I encountered an issue: {failures[0]}. How would you like me to proceed?"
                    )
        return "I've processed your request. Please let me know if you need any adjustments."
