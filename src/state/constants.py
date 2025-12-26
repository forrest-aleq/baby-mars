"""
State Constants
================

Constants from research papers affecting state structure.
"""

# Paper #9: Moral Asymmetry Multipliers
# MARS taxonomy: moral, competence, technical, preference, identity
CATEGORY_MULTIPLIERS = {
    "moral": {"success": 3.0, "failure": 10.0},  # Trust violations = massive impact
    "competence": {"success": 1.0, "failure": 2.0},  # How to do things
    "technical": {"success": 1.0, "failure": 1.5},  # Domain-specific facts
    "preference": {"success": 1.0, "failure": 1.0},  # Style choices
    "identity": {"success": 0.0, "failure": 0.0},  # IMMUTABLE - A.C.R.E. firewall
}

# Paper #10: Category-Specific Invalidation Thresholds (A.C.R.E.)
INVALIDATION_THRESHOLDS = {
    "moral": 0.95,  # Very hard to invalidate moral beliefs
    "competence": 0.75,  # Moderate threshold
    "technical": 0.70,  # Technical facts can be updated
    "preference": 0.60,  # Preferences are flexible
    "identity": 1.0,  # NEVER invalidate - immutable
}

# Paper #1: Autonomy Thresholds
AUTONOMY_THRESHOLDS = {
    "guidance_seeking": 0.4,  # Below this
    "action_proposal": 0.7,  # Between 0.4 and this
    "autonomous": 1.0,  # Above 0.7
}

# Paper #16: Difficulty Weights
DIFFICULTY_WEIGHTS = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.5, 5: 2.0}

# Paper #12: Peak-End Multiplier
PEAK_END_MULTIPLIER = 3.0
PEAK_INTENSITY_THRESHOLD = 0.7

# Learning rate for EMA updates
LEARNING_RATE = 0.15

# HITL Approval Timeout (seconds)
# Default 5 minutes - after this, pending approvals expire
APPROVAL_TIMEOUT_SECONDS = 300
