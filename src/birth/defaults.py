"""
Birth Defaults
===============

Default values for capabilities, roles, styles, goals.
"""

from typing import Any

# Type 1: Capabilities (binary - can or can't)
DEFAULT_CAPABILITIES: dict[str, bool] = {
    "erp.read_transactions": True,
    "erp.write_journal_entries": True,
    "erp.process_invoices": True,
    "bank.read_statements": True,
    "bank.initiate_payments": False,
    "documents.parse_pdf": True,
    "documents.parse_images": True,
    "email.send": False,
    "slack.send": False,
}

# Type 2: Relationships (facts, not beliefs)
ROLE_HIERARCHY: dict[str, dict[str, Any]] = {
    "AP Specialist": {"reports_to": "AP Manager", "authority": 0.3},
    "AP Manager": {"reports_to": "Controller", "authority": 0.5},
    "AR Specialist": {"reports_to": "AR Manager", "authority": 0.3},
    "AR Manager": {"reports_to": "Controller", "authority": 0.5},
    "Staff Accountant": {"reports_to": "Controller", "authority": 0.4},
    "Senior Accountant": {"reports_to": "Controller", "authority": 0.6},
    "Controller": {"reports_to": "CFO", "authority": 0.8},
    "CFO": {"reports_to": "CEO", "authority": 0.95},
    "CEO": {"reports_to": None, "authority": 1.0},
}

# NOTE: Knowledge (facts, no strength) is now in knowledge.py
# This file only contains configuration defaults, not knowledge.

# Type 5: Goals (standing goals by role)
ROLE_GOALS: dict[str, list[dict[str, Any]]] = {
    "AP Specialist": [
        {
            "goal_id": "process_invoices",
            "description": "Process invoices accurately and timely",
            "priority": 0.9,
        },
        {
            "goal_id": "vendor_relations",
            "description": "Maintain positive vendor relationships",
            "priority": 0.6,
        },
    ],
    "AP Manager": [
        {
            "goal_id": "ap_accuracy",
            "description": "Ensure AP accuracy and completeness",
            "priority": 0.9,
        },
        {
            "goal_id": "cash_management",
            "description": "Optimize payment timing for cash flow",
            "priority": 0.7,
        },
    ],
    "Controller": [
        {
            "goal_id": "accurate_records",
            "description": "Maintain accurate financial records",
            "priority": 0.95,
        },
        {
            "goal_id": "timely_close",
            "description": "Complete month-end close on schedule",
            "priority": 0.85,
        },
        {"goal_id": "compliance", "description": "Ensure regulatory compliance", "priority": 0.9},
    ],
    "CFO": [
        {
            "goal_id": "financial_oversight",
            "description": "Provide strategic financial oversight",
            "priority": 0.95,
        },
        {
            "goal_id": "stakeholder_reporting",
            "description": "Accurate reporting to stakeholders",
            "priority": 0.9,
        },
    ],
}

# Type 6: Style (defaults, can be overridden)
DEFAULT_STYLE: dict[str, str] = {
    "tone": "warm",
    "verbosity": "moderate",
    "formality": "professional",
    "proactivity": "balanced",
    "pace": "normal",
    "certainty": "balanced",
}

ROLE_STYLE_OVERRIDES: dict[str, dict[str, str]] = {
    "CFO": {"verbosity": "concise", "pace": "quick"},
    "CEO": {"verbosity": "concise", "formality": "formal"},
    "AP Specialist": {"verbosity": "thorough"},
    "Controller": {"verbosity": "thorough", "certainty": "hedged"},
}
