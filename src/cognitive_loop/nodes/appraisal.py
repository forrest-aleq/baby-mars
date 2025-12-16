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

from typing import Any
from pydantic import BaseModel, Field

from ...state.schema import (
    BabyMARSState,
    AppraisalResult,
)
from ...claude_client import get_claude_client, AppraisalOutput


# ============================================================
# CONTEXT BUILDING
# ============================================================

def build_appraisal_context(state: BabyMARSState) -> str:
    """
    Build context string for Claude appraisal.
    Includes activated beliefs, current context, and conversation history.
    """
    parts = []
    
    # Current message
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"<current_request>\n{content}\n</current_request>")
    
    # Context key
    context_key = state.get("current_context_key", "*|*|*")
    parts.append(f"<context_key>{context_key}</context_key>")
    
    # Activated beliefs
    beliefs = state.get("activated_beliefs", [])
    if beliefs:
        belief_strs = []
        for b in beliefs[:10]:  # Top 10
            strength = b.get("resolved_strength", b.get("strength", 0))
            belief_strs.append(
                f"- [{b['belief_id']}] {b['statement']} "
                f"(category={b['category']}, strength={strength:.2f})"
            )
        parts.append(f"<activated_beliefs>\n" + "\n".join(belief_strs) + "\n</activated_beliefs>")
    
    # Active goals
    goals = state.get("active_goals", [])
    if goals:
        goal_strs = []
        for g in goals:
            goal_strs.append(f"- [{g.get('goal_id', 'unknown')}] {g.get('description', '')}")
        parts.append(f"<active_goals>\n" + "\n".join(goal_strs) + "\n</active_goals>")
    
    # People in context
    objects = state.get("objects", {})
    people = objects.get("people", [])
    if people:
        people_strs = []
        for p in people[:5]:  # Top 5
            people_strs.append(
                f"- {p['name']} ({p['role']}) - "
                f"authority={p.get('authority', 0):.2f}, "
                f"relationship_value={p.get('relationship_value', 0):.2f}"
            )
        parts.append(f"<people_context>\n" + "\n".join(people_strs) + "\n</people_context>")
    
    # Temporal context
    temporal = objects.get("temporal", {})
    if temporal:
        parts.append(f"""<temporal_context>
- Current time: {temporal.get('current_time', 'unknown')}
- Month-end: {temporal.get('is_month_end', False)}
- Quarter-end: {temporal.get('is_quarter_end', False)}
- Year-end: {temporal.get('is_year_end', False)}
- Urgency multiplier: {temporal.get('urgency_multiplier', 1.0)}
</temporal_context>""")
    
    return "\n\n".join(parts)


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================

async def process(state: BabyMARSState) -> dict:
    """
    Appraisal Node
    
    Analyzes the current situation:
    1. Build context from state
    2. Call Claude with appraisal skill
    3. Parse structured response
    4. Return appraisal result
    """
    
    client = get_claude_client()
    
    # Build context for Claude
    context = build_appraisal_context(state)
    
    # Build messages
    messages = [
        {
            "role": "user",
            "content": f"""Perform cognitive appraisal of this situation.

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
        }
    ]
    
    try:
        # Call Claude with structured output
        appraisal = await client.complete_structured(
            messages=messages,
            response_model=AppraisalOutput,
            skills=["situation_appraisal", "accounting_domain"]
        )
        
        # Convert to AppraisalResult format
        result: AppraisalResult = {
            "expectancy_violation": {
                "type": appraisal.expectancy_violation,
                "description": None
            } if appraisal.expectancy_violation else None,
            "face_threat": {
                "level": appraisal.face_threat_level,
                "mitigation_needed": appraisal.face_threat_level > 0.3
            } if appraisal.face_threat_level > 0 else None,
            "goal_alignment": appraisal.goal_alignment,
            "attributed_beliefs": appraisal.relevant_belief_ids,
            "recommended_action_type": _map_approach(appraisal.recommended_approach),
            "difficulty": appraisal.difficulty_assessment,
            "involves_ethical_beliefs": appraisal.involves_ethical_beliefs
        }
        
        # Determine supervision mode based on appraisal
        supervision_mode = _determine_supervision_mode(appraisal, state)
        
        return {
            "appraisal": result,
            "supervision_mode": supervision_mode,
            "belief_strength_for_action": _compute_aggregate_strength(
                appraisal.relevant_belief_ids,
                state.get("activated_beliefs", [])
            )
        }
        
    except Exception as e:
        # Fallback to safe defaults on error
        print(f"Appraisal error: {e}")
        return {
            "appraisal": {
                "expectancy_violation": None,
                "face_threat": None,
                "goal_alignment": {},
                "attributed_beliefs": [],
                "recommended_action_type": "guidance_needed",
                "difficulty": 3,
                "involves_ethical_beliefs": False
            },
            "supervision_mode": "guidance_seeking",
            "belief_strength_for_action": 0.3
        }


def _map_approach(approach: str) -> str:
    """Map appraisal approach to action type"""
    mapping = {
        "seek_guidance": "guidance_needed",
        "propose_action": "propose_and_confirm",
        "execute": "execute_directly"
    }
    return mapping.get(approach, "guidance_needed")


def _determine_supervision_mode(appraisal: AppraisalOutput, state: BabyMARSState) -> str:
    """
    Determine supervision mode based on appraisal.
    
    Factors:
    - Recommended approach from Claude
    - Belief strength
    - Ethical involvement
    - Difficulty level
    """
    # Always seek guidance for ethical matters
    if appraisal.involves_ethical_beliefs:
        return "guidance_seeking"
    
    # High difficulty requires more supervision
    if appraisal.difficulty_assessment >= 4:
        if appraisal.recommended_approach == "execute":
            return "action_proposal"  # Downgrade
        return "guidance_seeking"
    
    # Map approach to mode
    approach_to_mode = {
        "seek_guidance": "guidance_seeking",
        "propose_action": "action_proposal",
        "execute": "autonomous"
    }
    
    return approach_to_mode.get(appraisal.recommended_approach, "guidance_seeking")


def _compute_aggregate_strength(belief_ids: list[str], beliefs: list[dict]) -> float:
    """Compute average strength of relevant beliefs"""
    if not belief_ids:
        return 0.3  # Default low
    
    belief_map = {b["belief_id"]: b for b in beliefs}
    strengths = []
    
    for bid in belief_ids:
        if bid in belief_map:
            b = belief_map[bid]
            strength = b.get("resolved_strength", b.get("strength", 0.5))
            strengths.append(strength)
    
    if not strengths:
        return 0.3
    
    return sum(strengths) / len(strengths)
