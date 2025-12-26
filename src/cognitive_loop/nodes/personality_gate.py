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

from typing import Any, Optional, cast

from ...claude_singleton import get_claude_client
from ...graphs.belief_graph import get_belief_graph
from ...observability import get_logger
from ...state.schema import BabyMARSState

logger = get_logger(__name__)

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


def _build_violation_check_prompt(response: str, immutable_beliefs: list[dict[str, Any]]) -> str:
    """Build prompt for Claude violation check."""
    belief_statements = "\n".join([f"- {b['statement']}" for b in immutable_beliefs])
    return f"""Check if this response violates any of these personality constraints:

CONSTRAINTS (must NEVER be violated):
{belief_statements}

RESPONSE TO CHECK:
{response}

Does this response violate any constraint? Answer in this format:
- If NO violation: "CLEAN"
- If violation: "VIOLATION: [belief that was violated] - [brief explanation]"

Be strict. Even subtle violations count."""


def _parse_violation_result(result: str, response: str) -> Optional[dict[str, Any]]:
    """Parse Claude's violation check result."""
    if result.strip().upper().startswith("CLEAN"):
        return None
    if "VIOLATION" in result.upper():
        return {"detected": True, "explanation": result}
    # Ambiguous - fall back to pattern check
    logger.warning(f"Ambiguous gate result from Claude: {result[:100]}...")
    pattern_violation = quick_violation_check(response)
    if pattern_violation:
        return {
            "detected": True,
            "explanation": f"Pattern match on {pattern_violation} (Claude response ambiguous)",
        }
    return None


async def claude_violation_check(
    response: str, immutable_beliefs: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Use Claude to check for subtle violations. Returns violation details or None if clean."""
    try:
        client = get_claude_client()
        prompt = _build_violation_check_prompt(response, immutable_beliefs)
        result = await client.complete(
            messages=[{"role": "user", "content": prompt}], temperature=0.0
        )
        return _parse_violation_result(result, response)
    except Exception as e:
        logger.error(f"Gate check error: {e}, response_preview={response[:100]}...")
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


async def generate_boundary_response(original_request: str, violation: dict[str, Any]) -> str:
    """
    Generate a response that maintains boundaries while being helpful.
    """
    client = get_claude_client()

    messages = [
        {
            "role": "user",
            "content": f"""The user asked: "{original_request}"

My initial response would have violated this principle: {violation.get("explanation", "professional boundaries")}

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


def _get_original_request(state: BabyMARSState) -> str:
    """Extract original user request from state."""
    messages = state.get("messages", [])
    if not messages:
        return ""
    content = messages[0].get("content", "")
    if isinstance(content, list):
        content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return str(content)


def _build_violation_result(
    state: BabyMARSState, new_response: str, gate_retries: int, fallback: bool = False
) -> dict[str, Any]:
    """Build result dict for violation case."""
    updated_messages = state.get("messages", [])[:-1]
    updated_messages.append({"role": "assistant", "content": new_response})
    result: dict[str, Any] = {
        "messages": updated_messages,
        "final_response": new_response,
        "gate_violation_detected": True,
    }
    if fallback:
        result["gate_fallback_used"] = True
    else:
        result["gate_retries"] = gate_retries + 1
    return result


async def process(state: BabyMARSState) -> dict[str, Any]:
    """Personality Gate: validate response against immutable beliefs."""
    final_response = str(state.get("final_response") or "")
    if not final_response:
        return {}

    graph = get_belief_graph()
    immutable_beliefs = cast(
        list[dict[str, Any]], [b for b in graph.beliefs.values() if b.get("immutable", False)]
    )

    gate_retries_val = state.get("gate_retries")
    gate_retries = int(gate_retries_val) if isinstance(gate_retries_val, (int, float, str)) else 0

    # Step 1: Quick pattern check
    quick_violation = quick_violation_check(final_response)
    if quick_violation:
        if gate_retries < 2:
            new_response = await generate_boundary_response(
                _get_original_request(state), {"explanation": f"Violated: {quick_violation}"}
            )
            return _build_violation_result(state, new_response, gate_retries)
        return _build_violation_result(state, BOUNDARY_RESPONSE, gate_retries, fallback=True)

    # Step 2: Claude check for subtle violations (first pass only)
    if gate_retries == 0 and immutable_beliefs:
        claude_violation = await claude_violation_check(final_response, immutable_beliefs)
        if claude_violation:
            new_response = await generate_boundary_response(
                _get_original_request(state), claude_violation
            )
            return _build_violation_result(state, new_response, gate_retries)

    return {"gate_violation_detected": False}
