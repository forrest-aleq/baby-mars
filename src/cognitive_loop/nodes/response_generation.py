"""
Response Generation Node
=========================

Generates the final response to the user.
Adapts tone and content based on supervision mode and outcome.

Uses response_generation skill for proper formatting
and professional communication patterns.
"""

from ...claude_client import ResponseOutput, get_claude_client
from ...state.schema import (
    BabyMARSState,
)

# ============================================================
# CONTEXT BUILDING
# ============================================================


def build_response_context(state: BabyMARSState) -> str:
    """Build context for response generation"""
    parts = []

    # Original request
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<original_request>\n{content}\n</original_request>")

    # Supervision mode
    supervision_mode = state.get("supervision_mode", "guidance_seeking")
    parts.append(f"<supervision_mode>{supervision_mode}</supervision_mode>")

    # Appraisal summary
    appraisal = state.get("appraisal")
    if appraisal:
        parts.append(f"""<appraisal>
  Difficulty: {appraisal.get('difficulty', 'unknown')}
  Recommended action: {appraisal.get('recommended_action_type', 'unknown')}
  Face threat: {appraisal.get('face_threat', {}).get('level', 0) if appraisal.get('face_threat') else 'none'}
</appraisal>""")

    # Selected action (if any)
    selected_action = state.get("selected_action")
    if selected_action:
        work_units = selected_action.get("work_units", [])
        wu_summary = []
        for wu in work_units[:5]:
            wu_summary.append(f"- {wu.get('tool', '?')}.{wu.get('verb', '?')}")
        parts.append(f"""<selected_action>
  Type: {selected_action.get('action_type', 'unknown')}
  Work units:
{chr(10).join(wu_summary)}
</selected_action>""")

    # Execution results (if any)
    execution_results = state.get("execution_results", [])
    if execution_results:
        result_summary = []
        for r in execution_results:
            status = "✓" if r.get("success", False) else "✗"
            result_summary.append(
                f"- {status} {r.get('tool', '?')}.{r.get('verb', '?')}: {r.get('message', '')}"
            )
        parts.append(f"""<execution_results>
{chr(10).join(result_summary)}
</execution_results>""")

    # Outcome summary
    outcome = state.get("execution_outcome")
    if outcome:
        parts.append(f"""<outcome>
  Type: {outcome.get('outcome_type', 'unknown')}
  Success rate: {outcome.get('success_rate', 0):.0%}
  Failures: {', '.join(outcome.get('failures', [])[:3]) or 'none'}
</outcome>""")

    # Validation results
    validation_results = state.get("validation_results", [])
    if validation_results:
        failures = [r for r in validation_results if not r.get("passed", True)]
        if failures:
            failure_msgs = [f.get("message", "") for f in failures[:3]]
            parts.append(f"""<validation_issues>
{chr(10).join('- ' + m for m in failure_msgs)}
</validation_issues>""")

    # People context (for tone adjustment)
    objects = state.get("objects", {})
    people = objects.get("people", [])
    if people:
        primary = people[0]
        parts.append(f"""<communication_context>
  Primary person: {primary.get('name', 'unknown')} ({primary.get('role', 'unknown')})
  Authority level: {primary.get('authority', 0):.2f}
  Relationship value: {primary.get('relationship_value', 0):.2f}
</communication_context>""")

    # Relevant beliefs for tone
    beliefs = state.get("activated_beliefs", [])
    style_beliefs = [b for b in beliefs if b.get("category") == "style"][:3]
    if style_beliefs:
        style_strs = [f"- {b['statement']}" for b in style_beliefs]
        parts.append(f"""<style_beliefs>
{chr(10).join(style_strs)}
</style_beliefs>""")

    return "\n\n".join(parts)


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


async def process(state: BabyMARSState) -> dict:
    """
    Response Generation Node

    Generates the final response:
    1. Determine response type from supervision mode
    2. Build context from state
    3. Generate response via Claude
    4. Format appropriately
    """

    client = get_claude_client()

    supervision_mode = state.get("supervision_mode", "guidance_seeking")
    context = build_response_context(state)
    template = get_response_template(supervision_mode)

    # Build messages
    messages = [
        {
            "role": "user",
            "content": f"""Generate a response to the user based on this context.

{template}

{context}

Generate a professional, helpful response that:
1. Addresses the user's original request
2. Uses appropriate tone for the relationship
3. Is clear and concise
4. Follows the supervision mode guidelines

Return your response in the structured format.""",
        }
    ]

    try:
        # Call Claude for response generation
        response = await client.complete_structured(
            messages=messages,
            response_model=ResponseOutput,
            skills=["response_generation", "accounting_domain"],
        )

        # Build final response
        final_response = _format_response(response, supervision_mode)

        # Add to messages
        new_message = {"role": "assistant", "content": final_response}

        return {
            "messages": state.get("messages", []) + [new_message],
            "final_response": final_response,
        }

    except Exception as e:
        # Fallback response on error
        print(f"Response generation error: {e}")

        fallback = _generate_fallback_response(state, supervision_mode)

        return {
            "messages": state.get("messages", []) + [{"role": "assistant", "content": fallback}],
            "final_response": fallback,
        }


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
        action = state.get("selected_action", {})
        action_type = action.get("action_type", "action")
        return f"I've prepared to {action_type}. Would you like me to proceed with this?"

    else:  # autonomous
        outcome = state.get("execution_outcome", {})
        if outcome.get("outcome_type") == "success":
            return "I've completed the requested action. Let me know if you need anything else."
        else:
            failures = outcome.get("failures", [])
            if failures:
                return f"I encountered an issue: {failures[0]}. How would you like me to proceed?"
            return "I've processed your request. Please let me know if you need any adjustments."
