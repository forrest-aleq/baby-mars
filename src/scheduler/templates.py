"""
Natural Language Templates
==========================

Message templates that make Aleq sound like a 25-year-old finance coworker,
not a robotic notification system.

Templates are calibrated by:
- Time of day (morning = fresh, afternoon = focused, evening = wrapping up)
- Day of week (Monday = ramping up, Friday = wrapping up)
- Urgency (month-end = more direct, normal = casual)
"""

import random
from typing import Any, Optional

from ..observability import get_logger

logger = get_logger(__name__)


# ============================================================
# MORNING CHECK-IN TEMPLATES
# ============================================================

MORNING_GREETINGS = {
    "monday": [
        "Happy Monday! Here's what's on the plate this week:",
        "Morning! New week, fresh start. Here's what we've got:",
        "Hey, hope you had a good weekend! Let's dive in:",
    ],
    "friday": [
        "Happy Friday! Let's knock out the week strong:",
        "TGIF! Here's what we need to wrap up:",
        "Almost there! Quick Friday rundown:",
    ],
    "default": [
        "Good morning! Here's what's on the plate today:",
        "Morning! Quick rundown for today:",
        "Hey, good morning! Here's what we've got:",
    ],
}

MORNING_PRIORITY_INTROS = [
    "Top priorities today:",
    "Main things to tackle:",
    "Here's what needs attention:",
]

MORNING_FOLLOW_UP_INTROS = [
    "Also, a few things that have been sitting:",
    "Quick heads up on some aging items:",
    "Don't forget about:",
]

MORNING_DEADLINE_INTROS = [
    "And FYI, {deadline} is coming up in {days} days.",
    "Just a heads up - {deadline} is {days} days out.",
    "Keeping an eye on: {deadline} ({days} days away).",
]


def format_morning_message(
    day_of_week: str,
    priorities: list[dict[str, Any]],
    follow_ups: list[dict[str, Any]],
    upcoming_deadline: Optional[tuple[str, int]] = None,
) -> str:
    """
    Format a morning check-in message.

    Args:
        day_of_week: Current day ("Monday", "Friday", etc.)
        priorities: List of priority items
        follow_ups: List of aging follow-up items
        upcoming_deadline: Optional (deadline_name, days_until) tuple

    Returns:
        Natural language morning message
    """
    parts = []

    # Greeting based on day
    day_key = day_of_week.lower() if day_of_week.lower() in MORNING_GREETINGS else "default"
    greeting = random.choice(MORNING_GREETINGS[day_key])
    parts.append(greeting)

    # Priorities
    if priorities:
        parts.append("")
        parts.append(random.choice(MORNING_PRIORITY_INTROS))
        for i, item in enumerate(priorities[:5], 1):
            parts.append(f"  {i}. {item.get('summary', item.get('content', 'Item'))}")

    # Follow-ups
    if follow_ups:
        parts.append("")
        parts.append(random.choice(MORNING_FOLLOW_UP_INTROS))
        for item in follow_ups[:3]:
            content = item.get("content", "")[:60]
            parts.append(f"  • {content}")

    # Upcoming deadline
    if upcoming_deadline:
        deadline_name, days = upcoming_deadline
        parts.append("")
        template = random.choice(MORNING_DEADLINE_INTROS)
        parts.append(template.format(deadline=deadline_name, days=days))

    return "\n".join(parts)


# ============================================================
# END OF DAY TEMPLATES
# ============================================================

EOD_GREETINGS = [
    "Quick end-of-day recap:",
    "Wrapping up for the day. Here's where we're at:",
    "Day's almost done! Quick summary:",
]

EOD_COMPLETED_INTROS = [
    "Got through today:",
    "Knocked out:",
    "Completed:",
]

EOD_ROLLOVER_INTROS = [
    "Rolling over to tomorrow:",
    "Still on the list for tomorrow:",
    "Carrying forward:",
]

EOD_TOMORROW_PREVIEW = [
    "Tomorrow looks pretty clear - I'll check in again in the morning.",
    "Should be a smooth day tomorrow. See you in the AM!",
    "Tomorrow's looking manageable. Talk soon!",
]

EOD_TOMORROW_BUSY = [
    "Tomorrow's got a few things lined up. I'll have the rundown in the morning.",
    "Heads up, tomorrow's got some items. More details in the AM.",
]


def format_eod_message(
    completed: list[dict[str, Any]],
    rollover: list[dict[str, Any]],
    tomorrow_count: int = 0,
) -> str:
    """
    Format an end-of-day summary message.

    Args:
        completed: List of items completed today
        rollover: List of items rolling to tomorrow
        tomorrow_count: Number of items expected tomorrow

    Returns:
        Natural language EOD message
    """
    parts = []

    parts.append(random.choice(EOD_GREETINGS))

    # Completed items
    if completed:
        parts.append("")
        parts.append(random.choice(EOD_COMPLETED_INTROS))
        for item in completed[:5]:
            summary = item.get("summary", item.get("content", "Item"))
            parts.append(f"  ✓ {summary}")
    else:
        parts.append("")
        parts.append("Quiet day - no major items completed.")

    # Rollover items
    if rollover:
        parts.append("")
        parts.append(random.choice(EOD_ROLLOVER_INTROS))
        for item in rollover[:3]:
            summary = item.get("summary", item.get("content", "Item"))
            parts.append(f"  • {summary}")

    # Tomorrow preview
    parts.append("")
    if tomorrow_count > 3:
        parts.append(random.choice(EOD_TOMORROW_BUSY))
    else:
        parts.append(random.choice(EOD_TOMORROW_PREVIEW))

    return "\n".join(parts)


# ============================================================
# DEADLINE REMINDER TEMPLATES
# ============================================================

DEADLINE_URGENT = {
    1: [
        "Hey, {deadline} is TOMORROW. Want me to do a final check on open items?",
        "Quick heads up - {deadline} is tomorrow! Here's what's still open:",
        "Tomorrow's {deadline}. Making sure we're buttoned up?",
    ],
    3: [
        "{deadline} is 3 days out. Here's the status on open items:",
        "Quick check-in: {deadline} is this {day}. Where are we at?",
        "3 days to {deadline}. Let's make sure we're on track:",
    ],
    7: [
        "Week out from {deadline}. Here's the lay of the land:",
        "{deadline} is coming up next week. Quick status check:",
        "One week to {deadline}. Time to start wrapping things up:",
    ],
}

DEADLINE_STATUS_GOOD = [
    "Looking good - no major blockers I can see.",
    "We're in good shape. Let me know if you need anything.",
    "On track from what I can tell. Holler if you need a hand.",
]

DEADLINE_STATUS_ISSUES = [
    "A few things to keep an eye on:",
    "Some items that might need attention:",
    "Couple of potential blockers:",
]


def format_deadline_message(
    deadline_name: str,
    days_until: int,
    open_items: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    day_of_week: str = "",
) -> str:
    """
    Format a deadline reminder message.

    Args:
        deadline_name: Name of deadline (e.g., "month-end")
        days_until: Days remaining
        open_items: List of open items
        blockers: List of potential blockers
        day_of_week: Day the deadline falls on

    Returns:
        Natural language deadline message
    """
    parts = []

    # Get appropriate urgency templates
    urgency_key = min(days_until, 7)
    if urgency_key not in DEADLINE_URGENT:
        urgency_key = 7

    template = random.choice(DEADLINE_URGENT[urgency_key])
    parts.append(template.format(deadline=deadline_name, day=day_of_week))

    # Open items
    if open_items:
        parts.append("")
        parts.append(f"Open items ({len(open_items)}):")
        for item in open_items[:5]:
            summary = item.get("summary", item.get("content", "Item"))
            parts.append(f"  • {summary}")

    # Status assessment
    parts.append("")
    if blockers:
        parts.append(random.choice(DEADLINE_STATUS_ISSUES))
        for blocker in blockers[:3]:
            parts.append(f"  ⚠ {blocker.get('summary', 'Issue')}")
    else:
        parts.append(random.choice(DEADLINE_STATUS_GOOD))

    return "\n".join(parts)


# ============================================================
# FOLLOW-UP REMINDER TEMPLATES
# ============================================================

FOLLOW_UP_SINGLE = [
    "Hey, quick reminder about '{item}' - been sitting for a bit.",
    "Just checking in on '{item}'. Want me to handle this?",
    "Heads up, '{item}' is getting close to expiring.",
]

FOLLOW_UP_MULTIPLE = [
    "A few items that have been sitting and need attention:",
    "Quick heads up on some aging follow-ups:",
    "Some items that are getting close to their deadlines:",
]

FOLLOW_UP_OFFER = [
    "Want me to take a crack at any of these?",
    "Let me know if you want me to handle any of these.",
    "Happy to tackle these if you give the go-ahead.",
]


def format_follow_up_message(
    items: list[dict[str, Any]],
) -> str:
    """
    Format a follow-up reminder message.

    Args:
        items: List of expiring items with content and ttl_remaining

    Returns:
        Natural language follow-up message
    """
    if not items:
        return "All caught up on follow-ups!"

    parts = []

    if len(items) == 1:
        item = items[0]
        content = item.get("content", "the item")[:50]
        template = random.choice(FOLLOW_UP_SINGLE)
        parts.append(template.format(item=content))
    else:
        parts.append(random.choice(FOLLOW_UP_MULTIPLE))
        parts.append("")
        for item in items[:5]:
            content = item.get("content", "Item")[:40]
            pct = int(item.get("ttl_remaining", 0.25) * 100)
            parts.append(f"  • {content} ({pct}% time left)")

    parts.append("")
    parts.append(random.choice(FOLLOW_UP_OFFER))

    return "\n".join(parts)


# ============================================================
# LOCKBOX SUMMARY TEMPLATES
# ============================================================

LOCKBOX_INTRO = [
    "Just finished processing the lockbox. Here's the summary:",
    "Lockbox run complete! Quick recap:",
    "Got through the lockbox. Here's what came in:",
]

LOCKBOX_EXCEPTIONS = [
    "A few items couldn't be auto-matched:",
    "Some items need manual review:",
    "These need a human eye:",
]


def format_lockbox_message(
    payment_count: int,
    total_amount: float,
    matched: int,
    exceptions: list[dict[str, Any]],
) -> str:
    """
    Format a lockbox processing summary.

    Args:
        payment_count: Total payments processed
        total_amount: Total dollar amount
        matched: Number auto-matched
        exceptions: Items needing manual review

    Returns:
        Natural language lockbox summary
    """
    parts = []

    parts.append(random.choice(LOCKBOX_INTRO))
    parts.append("")
    parts.append(f"  • {payment_count} payments totaling ${total_amount:,.2f}")
    parts.append(f"  • {matched} auto-matched")

    if exceptions:
        parts.append("")
        parts.append(random.choice(LOCKBOX_EXCEPTIONS))
        for exc in exceptions[:5]:
            amount = exc.get("amount", 0)
            reason = exc.get("reason", "needs review")
            parts.append(f"  • ${amount:,.2f} - {reason}")

    if not exceptions:
        parts.append("")
        parts.append("Everything matched up. Nice clean run!")

    return "\n".join(parts)
