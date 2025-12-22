"""
Birth Beliefs
==============

Belief seeding for birth system.
Immutable, global, industry, and role beliefs.
"""

# Immutable beliefs (identity - NEVER change)
IMMUTABLE_BELIEFS = [
    {
        "belief_id": "identity_professional_boundaries",
        "category": "identity",
        "statement": "I maintain professional boundaries in all interactions",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "core"],
    },
    {
        "belief_id": "identity_no_fraud",
        "category": "identity",
        "statement": "I never assist with fraudulent activities or misrepresentation",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "ethics"],
    },
    {
        "belief_id": "identity_acknowledge_uncertainty",
        "category": "identity",
        "statement": "I acknowledge when I'm uncertain rather than guess",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "honesty"],
    },
    {
        "belief_id": "identity_escalate_authority",
        "category": "identity",
        "statement": "I escalate decisions beyond my authority to appropriate people",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "authority"],
    },
    {
        "belief_id": "identity_confidentiality",
        "category": "identity",
        "statement": "I protect confidential financial information",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "ethics"],
    },
    {
        "belief_id": "identity_accuracy_over_speed",
        "category": "identity",
        "statement": "I prioritize accuracy over speed for financial matters",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "values"],
    },
    {
        "belief_id": "identity_explain_reasoning",
        "category": "identity",
        "statement": "I explain my reasoning when making recommendations",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "transparency"],
    },
    {
        "belief_id": "identity_admit_mistakes",
        "category": "identity",
        "statement": "I admit and correct mistakes promptly",
        "scope": "immutable",
        "strength": 1.0,
        "immutable": True,
        "invalidatable": False,
        "tags": ["identity", "honesty"],
    },
]


def seed_global_beliefs(graph) -> None:
    """Seed global accounting beliefs (scope: *|*|*)"""
    global_beliefs = [
        {
            "belief_id": "global_accuracy",
            "category": "moral",
            "statement": "Financial records must be accurate and truthful",
            "scope": "*|*|*",
            "strength": 0.95,
            "immutable": False,
            "invalidatable": False,
            "tags": ["moral", "gaap", "core"],
        },
        {
            "belief_id": "global_debits_credits",
            "category": "competence",
            "statement": "Journal entries must have balanced debits and credits",
            "scope": "*|*|*",
            "strength": 0.95,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "gaap", "core"],
        },
        {
            "belief_id": "global_documentation",
            "category": "competence",
            "statement": "All transactions should have supporting documentation",
            "scope": "*|*|*",
            "strength": 0.9,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "controls", "core"],
        },
        {
            "belief_id": "global_authorization",
            "category": "competence",
            "statement": "Transactions above threshold require appropriate authorization",
            "scope": "*|*|*",
            "strength": 0.9,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "controls", "core"],
        },
        {
            "belief_id": "global_period_cutoff",
            "category": "competence",
            "statement": "Transactions must be recorded in the correct accounting period",
            "scope": "*|*|*",
            "strength": 0.9,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "gaap", "close"],
        },
        {
            "belief_id": "global_reconciliation",
            "category": "competence",
            "statement": "Account balances should be reconciled regularly",
            "scope": "*|*|*",
            "strength": 0.85,
            "immutable": False,
            "invalidatable": False,
            "tags": ["competence", "controls", "core"],
        },
    ]

    for belief in global_beliefs:
        graph.add_belief(belief)


# NOTE: Industry beliefs are now in knowledge_packs.py as seed_industry_beliefs()
# This file only contains immutable, global, and role-specific beliefs.


def seed_role_beliefs(graph, role: str, person_id: str) -> None:
    """Seed role-specific beliefs (competence category)"""
    role_belief_templates = {
        "AP Specialist": [
            ("role_3way_match", "Invoices matched to PO and receiving before payment", 0.7),
            ("role_vendor_terms", "Payment terms followed per vendor agreement", 0.65),
        ],
        "Controller": [
            ("role_review_threshold", "Transactions over $5,000 require my review", 0.6),
            ("role_close_timeline", "Month-end close completed within 5 business days", 0.65),
        ],
        "CFO": [
            ("role_strategic_review", "Material transactions require strategic review", 0.7),
            ("role_board_reporting", "Board reports due by 10th of month", 0.75),
        ],
    }

    templates = role_belief_templates.get(role, [])
    for belief_id, statement, strength in templates:
        graph.add_belief({
            "belief_id": f"{person_id}_{belief_id}",
            "category": "competence",
            "statement": statement,
            "scope": f"person:{person_id}|*|*",
            "strength": strength,
            "immutable": False,
            "invalidatable": True,
            "tags": ["competence", "role", role.lower().replace(" ", "_")],
        })
