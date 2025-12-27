"""
PostHog Analytics Client
========================

Deep belief system analytics for Baby MARS.
Tracks belief lifecycle, autonomy decisions, and learning patterns.
"""

import os
import types
from typing import Optional

try:
    import posthog

    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False
    # Create a dummy module for type checking when posthog isn't installed
    posthog = types.ModuleType("posthog")

from ..observability import get_logger

logger = get_logger(__name__)

# Initialize PostHog on import if configured
_initialized = False


def _ensure_initialized() -> bool:
    """Initialize PostHog if API key is configured."""
    global _initialized
    if _initialized:
        return POSTHOG_AVAILABLE

    if not POSTHOG_AVAILABLE:
        logger.debug("PostHog not available - install with 'pip install posthog'")
        return False

    api_key = os.getenv("POSTHOG_API_KEY")
    if not api_key:
        logger.debug("PostHog not configured - set POSTHOG_API_KEY to enable analytics")
        return False

    posthog.project_api_key = api_key
    posthog.host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
    _initialized = True
    logger.info("PostHog analytics initialized", host=posthog.host)
    return True


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _strength_bucket(strength: float) -> str:
    """Bucket strength for histogram analysis."""
    if strength < 0.2:
        return "very_low"
    if strength < 0.4:
        return "low"
    if strength < 0.6:
        return "medium"
    if strength < 0.8:
        return "high"
    return "very_high"


def _magnitude_bucket(delta: float) -> str:
    """Bucket change magnitude."""
    if delta < 0.01:
        return "negligible"
    if delta < 0.05:
        return "small"
    if delta < 0.10:
        return "medium"
    if delta < 0.20:
        return "large"
    return "massive"


def _distance_to_threshold(strength: float) -> float:
    """Distance to nearest autonomy threshold (0.4 or 0.7)."""
    return min(abs(strength - 0.4), abs(strength - 0.7))


def _mode_rank(mode: str) -> int:
    """Rank autonomy modes for comparison."""
    return {"guidance_seeking": 0, "action_proposal": 1, "autonomous": 2}.get(mode, -1)


# ============================================================
# BELIEF ANALYTICS
# ============================================================


class BeliefAnalytics:
    """Analytics for belief system tracking."""

    @staticmethod
    def belief_created(
        org_id: str,
        belief_id: str,
        category: str,
        strength: float,
        context_key: str,
    ) -> None:
        """Track new belief creation."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="belief_created",
            properties={
                "belief_id": belief_id,
                "category": category,
                "strength": strength,
                "context_key": context_key,
                "context_bucket": context_key.split("|")[0] if context_key else "*",
                "strength_bucket": _strength_bucket(strength),
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def belief_updated(
        org_id: str,
        belief_id: str,
        category: str,
        old_strength: float,
        new_strength: float,
        outcome: str,
        multiplier: float,
        context_key: str,
        is_cascade: bool = False,
    ) -> None:
        """Track belief strength change - the core learning event."""
        if not _ensure_initialized():
            return

        delta = new_strength - old_strength
        posthog.capture(
            distinct_id=org_id,
            event="belief_updated",
            properties={
                "belief_id": belief_id,
                "category": category,
                "old_strength": old_strength,
                "new_strength": new_strength,
                "delta": delta,
                "delta_abs": abs(delta),
                "outcome": outcome,
                "multiplier": multiplier,
                "context_key": context_key,
                "is_cascade": is_cascade,
                # Computed properties for analysis
                "strength_bucket": _strength_bucket(new_strength),
                "direction": "increase" if delta > 0 else "decrease",
                "magnitude": _magnitude_bucket(abs(delta)),
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def belief_invalidation_blocked(
        org_id: str,
        belief_id: str,
        category: str,
        current_strength: float,
        proposed_strength: float,
        threshold: float,
    ) -> None:
        """Track when A.C.R.E. blocks belief invalidation."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="belief_invalidation_blocked",
            properties={
                "belief_id": belief_id,
                "category": category,
                "current_strength": current_strength,
                "proposed_strength": proposed_strength,
                "threshold": threshold,
                "blocked_delta": current_strength - proposed_strength,
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def moral_violation_detected(
        org_id: str,
        belief_id: str,
        violation_count: int,
        is_distrusted: bool,
    ) -> None:
        """Track moral circuit breaker activation."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="moral_violation_detected",
            properties={
                "belief_id": belief_id,
                "violation_count": violation_count,
                "is_distrusted": is_distrusted,
                "circuit_breaker_triggered": violation_count >= 2,
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def autonomy_mode_determined(
        org_id: str,
        person_id: str,
        mode: str,
        aggregate_strength: float,
        belief_count: int,
        difficulty: int,
    ) -> None:
        """Track autonomy decision - guidance_seeking vs action_proposal vs autonomous."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="autonomy_mode_determined",
            properties={
                "person_id": person_id,
                "mode": mode,
                "aggregate_strength": aggregate_strength,
                "belief_count": belief_count,
                "difficulty": difficulty,
                # Threshold proximity (instability indicator)
                "distance_to_threshold": _distance_to_threshold(aggregate_strength),
                "near_threshold": abs(_distance_to_threshold(aggregate_strength)) < 0.05,
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def autonomy_threshold_crossed(
        org_id: str,
        person_id: str,
        old_mode: str,
        new_mode: str,
        trigger_belief_id: str,
    ) -> None:
        """Track when autonomy mode changes (significant event)."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="autonomy_threshold_crossed",
            properties={
                "person_id": person_id,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "trigger_belief_id": trigger_belief_id,
                "direction": (
                    "promoted" if _mode_rank(new_mode) > _mode_rank(old_mode) else "demoted"
                ),
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def cascade_update_triggered(
        org_id: str,
        source_belief_id: str,
        affected_count: int,
        max_depth: int,
    ) -> None:
        """Track hierarchical belief propagation."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="cascade_update_triggered",
            properties={
                "source_belief_id": source_belief_id,
                "affected_count": affected_count,
                "max_depth": max_depth,
                "is_large_cascade": affected_count > 10,
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def peak_end_multiplier_applied(
        org_id: str,
        belief_id: str,
        emotional_intensity: float,
        is_end_memory: bool,
    ) -> None:
        """Track when peak-end rule amplifies learning."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="peak_end_multiplier_applied",
            properties={
                "belief_id": belief_id,
                "emotional_intensity": emotional_intensity,
                "is_end_memory": is_end_memory,
                "trigger_reason": "end_memory" if is_end_memory else "high_intensity",
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def context_resolution_performed(
        org_id: str,
        belief_id: str,
        requested_context: str,
        resolved_context: str,
        backoff_levels: int,
    ) -> None:
        """Track context-conditional belief resolution."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="context_resolution_performed",
            properties={
                "belief_id": belief_id,
                "requested_context": requested_context,
                "resolved_context": resolved_context,
                "backoff_levels": backoff_levels,
                "used_global_default": resolved_context == "*|*|*",
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def cognitive_loop_completed(
        org_id: str,
        person_id: str,
        duration_ms: float,
        node_count: int,
        claude_calls: int,
        tokens_total: int,
        outcome: str,
    ) -> None:
        """Track full cognitive loop execution."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="cognitive_loop_completed",
            properties={
                "person_id": person_id,
                "duration_ms": duration_ms,
                "node_count": node_count,
                "claude_calls": claude_calls,
                "tokens_total": tokens_total,
                "outcome": outcome,
            },
            groups={"organization": org_id},
        )

    @staticmethod
    def personality_gate_triggered(
        org_id: str,
        violation_type: str,
        retry_count: int,
        was_blocked: bool,
    ) -> None:
        """Track personality gate enforcement."""
        if not _ensure_initialized():
            return

        posthog.capture(
            distinct_id=org_id,
            event="personality_gate_triggered",
            properties={
                "violation_type": violation_type,
                "retry_count": retry_count,
                "was_blocked": was_blocked,
                "required_regeneration": retry_count > 0,
            },
            groups={"organization": org_id},
        )


# ============================================================
# LLM ANALYTICS
# ============================================================


class LLMAnalytics:
    """Analytics for Claude API usage."""

    @staticmethod
    def claude_call(
        org_id: str,
        node_name: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        success: bool,
        error_type: Optional[str] = None,
    ) -> None:
        """Track Claude API call for cost/latency analysis."""
        if not _ensure_initialized():
            return

        # Cost calculation (approximate, Dec 2025 pricing)
        cost_per_1k_in = 0.015 if "opus" in model else 0.003
        cost_per_1k_out = 0.075 if "opus" in model else 0.015
        cost_usd = (tokens_in * cost_per_1k_in + tokens_out * cost_per_1k_out) / 1000

        posthog.capture(
            distinct_id=org_id,
            event="claude_api_call",
            properties={
                "node_name": node_name,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tokens_total": tokens_in + tokens_out,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "success": success,
                "error_type": error_type,
            },
            groups={"organization": org_id},
        )


# ============================================================
# SINGLETON ACCESS
# ============================================================

_analytics: Optional[BeliefAnalytics] = None
_llm_analytics: Optional[LLMAnalytics] = None


def get_belief_analytics() -> BeliefAnalytics:
    """Get the global belief analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = BeliefAnalytics()
    return _analytics


def get_llm_analytics() -> LLMAnalytics:
    """Get the global LLM analytics instance."""
    global _llm_analytics
    if _llm_analytics is None:
        _llm_analytics = LLMAnalytics()
    return _llm_analytics
