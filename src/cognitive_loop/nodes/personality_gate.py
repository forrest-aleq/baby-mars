"""
Personality Gate
=================

Final validation before response goes to user.
Checks response against immutable personality beliefs.

If violation detected:
1. Regenerate with boundary-aware prompt
2. Max 2 retries
3. Fail safe with generic boundary response

This ensures Aleq NEVER violates core personality constraints,
regardless of what the cognitive loop produced.
"""

from typing import Optional

from ...claude_client import get_claude_client
from ...graphs.belief_graph import get_belief_graph
from ...state.schema import BabyMARSState

# ============================================================
# IMMUTABLE BELIEF PATTERNS
# ============================================================

# These are the things we check for - mapped to belief IDs
VIOLATION_PATTERNS = {
    "personality_professional_boundaries": [
        "personal relationship",
        "romantic",
        "after hours",
        "outside of work",
        "personal life",
    ],
    "personality_no_fraud": [
        "hide this",
        "don't tell",
        "falsify",
        "misrepresent",
        "cover up",
        "off the books",
        "avoid audit",
    ],
    "personality_acknowledge_uncertainty": [
        # Violation = expressing certainty when should hedge
        # This is checked via Claude, not patterns
    ],
    "personality_escalate_authority": [
        # Violation = agreeing to act beyond authority
        # Checked contextually
    ],
    "personality_confidentiality": [
        "share with",
        "tell them about",
        "disclose",
        "leak",
    ],
}

# Generic boundary response when all retries fail
BOUNDARY_RESPONSE = """I appreciate you reaching out, but I need to maintain professional boundaries in how I can help.

I'm designed to assist with accounting and finance tasks within appropriate limits. If you have questions about invoices, journal entries, reconciliations, or other financial processes, I'm happy to help with those.

Is there something specific in the accounting domain I can assist you with?"""


# ============================================================
# QUICK PATTERN CHECK
# ============================================================


def quick_violation_check(response: str) -> Optional[str]:
    """
    Fast pattern-based check for obvious violations.
    Returns the violated belief_id or None.
    """
    response_lower = response.lower()

    for belief_id, patterns in VIOLATION_PATTERNS.items():
        for pattern in patterns:
            if pattern in response_lower:
                return belief_id

    return None


# ============================================================
# CLAUDE-BASED VALIDATION
# ============================================================


async def claude_violation_check(response: str, immutable_beliefs: list[dict]) -> Optional[dict]:
    """
    Use Claude to check for subtle violations.

    Returns violation details or None if clean.
    """
    client = get_claude_client()

    # Build belief list for prompt
    belief_statements = "\n".join([f"- {b['statement']}" for b in immutable_beliefs])

    messages = [
        {
            "role": "user",
            "content": f"""Check if this response violates any of these personality constraints:

CONSTRAINTS (must NEVER be violated):
{belief_statements}

RESPONSE TO CHECK:
{response}

Does this response violate any constraint? Answer in this format:
- If NO violation: "CLEAN"
- If violation: "VIOLATION: [belief that was violated] - [brief explanation]"

Be strict. Even subtle violations count.""",
        }
    ]

    try:
        result = await client.complete(
            messages=messages,
            temperature=0.0,  # Deterministic for safety checks
        )

        if result.strip().upper().startswith("CLEAN"):
            return None
        elif "VIOLATION" in result.upper():
            return {
                "detected": True,
                "explanation": result,
            }
        else:
            # Ambiguous - fall back to pattern check
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Ambiguous gate result from Claude: {result[:100]}...")

            # Use pattern check as fallback
            pattern_violation = quick_violation_check(response)
            if pattern_violation:
                return {
                    "detected": True,
                    "explanation": f"Pattern match on {pattern_violation} (Claude response ambiguous)",
                }
            return None

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Gate check error: {e}, response_preview={response[:100]}...")

        # On error, fall back to pattern check instead of letting through
        pattern_violation = quick_violation_check(response)
        if pattern_violation:
            return {
                "detected": True,
                "explanation": f"Pattern match on {pattern_violation} (Claude check failed)",
            }
        return None


# ============================================================
# BOUNDARY RESPONSE GENERATION
# ============================================================


async def generate_boundary_response(original_request: str, violation: dict) -> str:
    """
    Generate a response that maintains boundaries while being helpful.
    """
    client = get_claude_client()

    messages = [
        {
            "role": "user",
            "content": f"""The user asked: "{original_request}"

My initial response would have violated this principle: {violation.get('explanation', 'professional boundaries')}

Generate a response that:
1. Politely declines the problematic aspect
2. Maintains warmth and professionalism
3. Redirects to how I CAN help
4. Is brief (2-3 sentences max)

Do NOT explain the violation or be preachy. Just redirect naturally.""",
        }
    ]

    try:
        result = await client.complete(messages=messages, temperature=0.7)
        return result
    except Exception:
        return BOUNDARY_RESPONSE


# ============================================================
# MAIN GATE FUNCTION
# ============================================================


async def process(state: BabyMARSState) -> dict:
    """
    Personality Gate Node

    Validates final response against immutable beliefs.

    Flow:
    1. Quick pattern check
    2. If suspicious, Claude validation
    3. If violation, regenerate (max 2 tries)
    4. If still violating, use boundary response
    """

    final_response = state.get("final_response", "")

    if not final_response:
        return {}  # Nothing to check

    # Get immutable beliefs
    graph = get_belief_graph()
    immutable_beliefs = [b for b in graph.beliefs.values() if b.get("immutable", False)]

    # Track retries
    gate_retries = state.get("gate_retries", 0)
    max_gate_retries = 2

    # Step 1: Quick pattern check
    quick_violation = quick_violation_check(final_response)

    if quick_violation:
        # Definite violation - regenerate
        if gate_retries < max_gate_retries:
            original_request = ""
            messages = state.get("messages", [])
            if messages:
                msg = messages[0]
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                original_request = content

            new_response = await generate_boundary_response(
                original_request, {"explanation": f"Violated: {quick_violation}"}
            )

            # Update messages with new response
            updated_messages = state.get("messages", [])[:-1]  # Remove old response
            updated_messages.append({"role": "assistant", "content": new_response})

            return {
                "messages": updated_messages,
                "final_response": new_response,
                "gate_retries": gate_retries + 1,
                "gate_violation_detected": True,
            }
        else:
            # Max retries - use safe default
            updated_messages = state.get("messages", [])[:-1]
            updated_messages.append({"role": "assistant", "content": BOUNDARY_RESPONSE})

            return {
                "messages": updated_messages,
                "final_response": BOUNDARY_RESPONSE,
                "gate_violation_detected": True,
                "gate_fallback_used": True,
            }

    # Step 2: Claude check for subtle violations (only on first pass)
    if gate_retries == 0 and immutable_beliefs:
        claude_violation = await claude_violation_check(final_response, immutable_beliefs)

        if claude_violation:
            original_request = ""
            messages = state.get("messages", [])
            if messages:
                msg = messages[0]
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                original_request = content

            new_response = await generate_boundary_response(original_request, claude_violation)

            updated_messages = state.get("messages", [])[:-1]
            updated_messages.append({"role": "assistant", "content": new_response})

            return {
                "messages": updated_messages,
                "final_response": new_response,
                "gate_retries": gate_retries + 1,
                "gate_violation_detected": True,
            }

    # No violation - pass through
    return {
        "gate_violation_detected": False,
    }
