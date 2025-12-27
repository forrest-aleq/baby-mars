"""
Scheduler Module
================

SYSTEM_PULSE - Aleq's proactive coworker brain.

Provides:
- Time awareness (Aleq always knows what time/day it is)
- Proactive triggers (morning check-in, follow-ups, deadlines)
- Background scheduler that invokes cognitive loop

This enables Aleq to be a proactive 25-year-old coworker,
not just a reactive chatbot.
"""

from .pulse_scheduler import PulseScheduler, get_pulse_scheduler
from .time_awareness import build_temporal_context, get_time_of_day

__all__ = [
    "build_temporal_context",
    "get_time_of_day",
    "PulseScheduler",
    "get_pulse_scheduler",
]
