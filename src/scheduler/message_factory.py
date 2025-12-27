"""
Message Factory
================

Creates synthetic state for proactive cognitive loop invocations.
When triggers fire, this factory builds the state that flows through
the cognitive loop as if a user had sent a message.
"""

from datetime import datetime
from typing import Any, Optional, cast
from zoneinfo import ZoneInfo

from ..observability import get_logger
from ..state.factory import create_initial_state
from .time_awareness import build_temporal_context
from .triggers import ScheduledTrigger

logger = get_logger(__name__)


def create_trigger_state(
    trigger: ScheduledTrigger,
    event_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Create state for cognitive loop invocation from a trigger.

    This creates a "synthetic" state as if a user had sent a message,
    but marked as system-initiated for proper handling.

    Args:
        trigger: The trigger that fired
        event_data: Optional data from event triggers

    Returns:
        BabyMARSState-compatible dict for cognitive loop
    """
    org_id = trigger["org_id"]
    user_id = trigger.get("user_id")

    # Get org timezone (would come from org settings in production)
    org_timezone = _get_org_timezone(org_id)

    # Create base state
    thread_id = (
        f"pulse_{trigger['trigger_id']}_{datetime.now(ZoneInfo('UTC')).strftime('%Y%m%d_%H%M%S')}"
    )

    state = create_initial_state(
        thread_id=thread_id,
        org_id=org_id,
        user_id=user_id or "system",
        org_timezone=org_timezone,
    )

    # Fresh temporal context
    state["objects"]["temporal"] = build_temporal_context(org_timezone)

    # Add trigger metadata
    state["trigger_context"] = {
        "trigger_id": trigger["trigger_id"],
        "trigger_type": trigger["trigger_type"],
        "action": trigger["action"],
        "action_context": trigger.get("action_context", {}),
        "is_proactive": True,
        "event_data": event_data,
    }

    # Create synthetic message based on trigger type
    synthetic_message = _create_synthetic_message(trigger, event_data)
    state["messages"] = [
        {
            "role": "system",
            "content": synthetic_message,
            "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
            "is_synthetic": True,
        }
    ]

    logger.debug(f"Created trigger state for {trigger['trigger_id']}: {trigger['action']}")
    return cast(dict[str, Any], state)


def _create_synthetic_message(
    trigger: ScheduledTrigger,
    event_data: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a synthetic message that will guide cognitive loop.

    This message acts as the "prompt" for the proactive action.
    """
    action = trigger["action"]
    config = trigger["config"]

    if action == "morning_check":
        return _morning_check_prompt(trigger)
    elif action == "end_of_day_summary":
        return _end_of_day_prompt(trigger)
    elif action == "deadline_reminder":
        return _deadline_reminder_prompt(trigger, config)
    elif action == "follow_up_reminder":
        return _follow_up_prompt(trigger)
    elif action == "weekly_reconciliation":
        return _weekly_recon_prompt(trigger)
    elif action == "month_end_prep":
        return _month_end_prompt(trigger)
    elif action == "lockbox_summary":
        return _lockbox_summary_prompt(trigger, event_data)
    else:
        # Generic prompt for custom actions
        return f"[SYSTEM_PULSE] Execute proactive action: {action}"


def _morning_check_prompt(trigger: ScheduledTrigger) -> str:
    """Morning check-in prompt."""
    return """[SYSTEM_PULSE: MORNING_CHECK]
It's morning. Time to check in with the user proactively.

Review pending tasks and notes for this org. Compose a friendly morning
message that:
1. Greets appropriately for the day of week
2. Highlights top priorities for today
3. Mentions any aging follow-ups that need attention
4. Notes any upcoming deadlines (month-end, quarter-end)

Sound like a helpful 25-year-old coworker, not a robot.
Be casual but professional. Keep it concise."""


def _end_of_day_prompt(trigger: ScheduledTrigger) -> str:
    """End of day summary prompt."""
    return """[SYSTEM_PULSE: END_OF_DAY_SUMMARY]
It's late afternoon. Time for a quick end-of-day check.

Review what happened today and compose a brief summary:
1. Tasks completed today
2. Items that rolled over (if any)
3. Quick heads up for tomorrow
4. Any pending items that need human decision

Keep it brief and friendly. Don't be preachy."""


def _deadline_reminder_prompt(
    trigger: ScheduledTrigger,
    config: dict[str, Any],
) -> str:
    """Deadline reminder prompt."""
    deadline_type = config.get("deadline_type", "month_end")
    days = config.get("current_days_until", "soon")

    deadline_names = {
        "month_end": "month-end close",
        "quarter_end": "quarter-end",
        "year_end": "year-end",
        "custom": "the deadline",
    }
    deadline_name = deadline_names.get(deadline_type, "the deadline")

    return f"""[SYSTEM_PULSE: DEADLINE_REMINDER]
{deadline_name.title()} is coming up ({days} days away).

Check for any items that need attention before the deadline:
1. Open reconciliation items
2. Pending approvals
3. Documents or invoices that need processing

Compose a helpful reminder that's appropriately urgent based on how
close the deadline is. Closer = more direct, further = more casual."""


def _follow_up_prompt(trigger: ScheduledTrigger) -> str:
    """Follow-up reminder prompt."""
    return """[SYSTEM_PULSE: FOLLOW_UP_REMINDER]
Some follow-up items are aging and need attention.

Check expiring notes and compose a reminder:
1. List the items that are close to expiring
2. Prioritize by urgency and importance
3. Offer to help handle them if within autonomy

Sound helpful, not nagging. Like a coworker who noticed something
slipping through the cracks."""


def _weekly_recon_prompt(trigger: ScheduledTrigger) -> str:
    """Weekly reconciliation prompt."""
    return """[SYSTEM_PULSE: WEEKLY_RECONCILIATION]
Time for the weekly reconciliation check.

Review the org's reconciliation status:
1. Bank reconciliation status
2. Outstanding items from last week
3. New items that need matching

Compose a helpful summary. If reconciliation is clear, keep it short.
If there are issues, highlight them with suggested next steps."""


def _month_end_prompt(trigger: ScheduledTrigger) -> str:
    """Month-end prep prompt."""
    return """[SYSTEM_PULSE: MONTH_END_PREP]
Month-end close is approaching. Time to prep.

Check month-end readiness:
1. Outstanding reconciliation items
2. Pending invoices or payments
3. Accruals or adjustments needed
4. Any blockers for close

Be appropriately urgent. Month-end is serious business."""


def _lockbox_summary_prompt(
    trigger: ScheduledTrigger,
    event_data: Optional[dict[str, Any]] = None,
) -> str:
    """Lockbox processing summary prompt."""
    if event_data:
        count = event_data.get("payment_count", "several")
        total = event_data.get("total_amount", "the payments")
        return f"""[SYSTEM_PULSE: LOCKBOX_SUMMARY]
Lockbox processing just completed: {count} payments totaling {total}.

Compose a brief summary:
1. What was processed
2. Any items that couldn't be auto-matched
3. Next steps if any

Keep it informative but concise."""
    else:
        return """[SYSTEM_PULSE: LOCKBOX_SUMMARY]
Lockbox processing completed.

Summarize results and any items needing attention."""


# ============================================================
# FIRST IMPRESSION / BIRTH MESSAGE
# ============================================================


def create_birth_state(
    org_id: str,
    person_name: str,
    person_role: str,
    industry: str,
    org_timezone: str = "America/Los_Angeles",
) -> dict[str, Any]:
    """
    Create state for Aleq's first impression greeting.

    This is the critical first moment of rapport building.
    Aleq introduces herself in a way that's warm, personal,
    and sets the tone for a peer-to-peer working relationship.

    Args:
        org_id: Organization ID
        person_name: The new person's name
        person_role: Their role (Controller, CFO, etc.)
        industry: Industry for context
        org_timezone: Timezone for time-appropriate greeting

    Returns:
        BabyMARSState-compatible dict for cognitive loop
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    thread_id = f"birth_{org_id}_{datetime.now(ZoneInfo('UTC')).strftime('%Y%m%d_%H%M%S')}"

    state = create_initial_state(
        thread_id=thread_id,
        org_id=org_id,
        user_id="system",
        org_timezone=org_timezone,
    )

    # Fresh temporal context
    state["objects"]["temporal"] = build_temporal_context(org_timezone)

    # Mark this as a birth/first impression context
    state["trigger_context"] = {
        "trigger_type": "birth",
        "action": "first_impression",
        "is_proactive": True,
        "is_first_meeting": True,
        "person_context": {
            "name": person_name,
            "role": person_role,
            "industry": industry,
        },
    }

    # Create the first impression prompt
    temporal_dict: dict[str, Any] = dict(state["objects"]["temporal"])
    synthetic_message = _create_first_impression_prompt(
        person_name, person_role, industry, temporal_dict
    )

    state["messages"] = [
        {
            "role": "system",
            "content": synthetic_message,
            "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
            "is_synthetic": True,
            "is_first_impression": True,
        }
    ]

    logger.info(f"Created birth state for first impression: {person_name} ({person_role})")
    return cast(dict[str, Any], state)


def _create_first_impression_prompt(
    person_name: str,
    person_role: str,
    industry: str,
    temporal: dict[str, Any],
) -> str:
    """
    Create the prompt that guides Aleq's first impression.

    This is psychology-informed: first impressions are formed in seconds
    and are incredibly sticky. We want Aleq to come across as:
    - Warm but not sycophantic
    - Competent but not arrogant
    - Peer-like, not subservient
    - Authentic, not templated
    """
    time_of_day = temporal.get("time_of_day", "day")
    day_of_week = temporal.get("day_of_week", "")
    is_weekend = temporal.get("is_weekend", False)
    is_month_end = temporal.get("is_month_end", False)
    hour = temporal.get("hour", 12)

    # Time-aware context
    time_context = ""
    if is_weekend:
        time_context = (
            "It's the weekend - they might be catching up on work or just getting set up."
        )
    elif hour < 7:
        time_context = (
            "It's very early - they're probably an early bird or dealing with something urgent."
        )
    elif hour >= 20:
        time_context = (
            "It's late in the evening - they might be working late or in a different timezone."
        )
    elif is_month_end:
        time_context = "It's month-end period - they're probably in crunch mode."
    elif day_of_week == "Monday":
        time_context = "It's Monday - they're starting their week."
    elif day_of_week == "Friday":
        time_context = "It's Friday - they might be wrapping up for the week."

    return f"""[SYSTEM_BIRTH: FIRST_IMPRESSION]

You are meeting {person_name} for the very first time. They are a {person_role} in {industry}.
{time_context}

This is YOUR first impression - the moment that shapes your entire working relationship.
Research shows first impressions form in 7 seconds and are incredibly persistent.

CRITICAL PSYCHOLOGY:
- Warmth comes before competence in impression formation
- Peers are trusted more than subordinates or superiors
- Authenticity beats polish
- Shared context creates instant rapport

YOUR GREETING SHOULD:
1. Acknowledge them by name (personalization signals attention)
2. Reference something specific about their context (role, time, situation)
3. Position yourself as a peer, not an assistant ("we'll be working together" not "I'm here to help you")
4. Show a tiny bit of self-awareness/vulnerability ("still learning the specifics of your workflows")
5. Open with an easy, low-pressure invitation ("no pressure to dive in right now")

YOUR GREETING SHOULD NOT:
- Be generic ("Hello! How can I help you today?")
- Be sycophantic ("I'm so excited to work with you!")
- List your capabilities ("I can help with X, Y, Z...")
- Be too long (2-4 sentences max)
- Use exclamation marks excessively

VOICE: 25-year-old finance professional, competent but approachable, casual but not sloppy.

TIME CONTEXT: {time_of_day} on {day_of_week}

Generate a natural, warm first greeting that sets the foundation for a great working relationship."""


def _get_org_timezone(org_id: str) -> str:
    """
    Get timezone for an organization.

    In production, this would query org settings.
    For now, default to America/Los_Angeles.
    """
    # TODO: Query org settings for timezone
    return "America/Los_Angeles"
