"""
Belief Packs (Industry-Specific)
================================

BELIEFS are uncertain claims WITH strength (0.0-1.0).
These are what the learning loop updates.

This is DIFFERENT from knowledge.py which has FACTS (certain, no strength).

Examples of the distinction:
- KNOWLEDGE: "ASC 606 governs revenue recognition" (fact, certain)
- BELIEF: "This client follows ASC 606 correctly" (claim, strength 0.7)

- KNOWLEDGE: "Month-end close is a period-end process" (fact, certain)
- BELIEF: "This org's close takes 5 days" (claim, strength 0.6)
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..graphs.belief_graph import BeliefGraph


def seed_industry_beliefs(graph: "BeliefGraph", industry: str, org_id: str) -> None:
    """
    Seed beliefs about how this org likely operates based on industry.

    These are UNCERTAIN claims with strength. The learning loop
    will adjust these based on experience.
    """
    packs = _get_industry_packs(industry)

    for pack in packs:
        _seed_pack_beliefs(graph, pack, org_id)


def _get_industry_packs(industry: str) -> list[str]:
    """Map industry to relevant belief packs."""
    industry_lower = (industry or "").lower()

    packs = []

    if any(x in industry_lower for x in ["software", "technology", "saas", "cloud"]):
        packs.extend(["saas_beliefs", "recurring_revenue_beliefs"])

    if any(x in industry_lower for x in ["investment", "asset management", "hedge", "fund"]):
        packs.extend(["investment_beliefs", "regulatory_beliefs"])

    if any(x in industry_lower for x in ["real estate", "property", "reit"]):
        packs.extend(["real_estate_beliefs", "lease_beliefs"])

    if any(x in industry_lower for x in ["manufacturing", "industrial"]):
        packs.extend(["manufacturing_beliefs"])

    # Everyone gets general accounting beliefs
    packs.append("general_accounting_beliefs")

    return packs


def _seed_pack_beliefs(graph: "BeliefGraph", pack: str, org_id: str) -> None:
    """Seed beliefs from a specific pack."""
    beliefs = BELIEF_PACKS.get(pack, [])

    for belief_id, statement, category, strength in beliefs:
        graph.add_belief(
            {
                "belief_id": f"{org_id}_{belief_id}",
                "category": category,
                "statement": statement,
                "scope": f"org:{org_id}|*|*",
                "strength": strength,
                "immutable": False,
                "invalidatable": True,
                "tags": [category, "industry_belief", pack],
            }
        )


# ============================================================
# BELIEF PACKS
# Uncertain claims about how orgs in this industry TYPICALLY operate.
# These will be updated by the learning loop based on experience.
# ============================================================

BELIEF_PACKS = {
    # SaaS-specific beliefs (uncertain claims about SaaS orgs)
    "saas_beliefs": [
        # Competence beliefs about processes
        (
            "saas_revenue_correct",
            "Revenue recognition follows proper ASC 606 allocation",
            "competence",
            0.7,
        ),
        (
            "saas_deferred_accurate",
            "Deferred revenue is accurately tracked and released",
            "competence",
            0.7,
        ),
        ("saas_metrics_reliable", "ARR/MRR metrics are accurately calculated", "competence", 0.65),
        # Technical beliefs about systems
        (
            "saas_billing_integrated",
            "Billing system is properly integrated with GL",
            "technical",
            0.6,
        ),
    ],
    "recurring_revenue_beliefs": [
        ("rr_churn_tracked", "Customer churn is actively monitored", "competence", 0.6),
        ("rr_cohort_analysis", "Cohort analysis is used for forecasting", "competence", 0.5),
    ],
    # Investment management beliefs
    "investment_beliefs": [
        ("inv_nav_accurate", "NAV calculations are accurate and timely", "competence", 0.7),
        (
            "inv_custody_reconciled",
            "Custody accounts reconcile without material breaks",
            "competence",
            0.7,
        ),
        (
            "inv_valuations_fair",
            "Investment valuations follow fair value hierarchy",
            "competence",
            0.65,
        ),
    ],
    "regulatory_beliefs": [
        ("reg_filings_timely", "Regulatory filings are submitted on time", "competence", 0.7),
        (
            "reg_compliance_monitored",
            "Compliance requirements are actively monitored",
            "competence",
            0.65,
        ),
    ],
    # Real estate beliefs
    "real_estate_beliefs": [
        ("re_cam_accurate", "CAM reconciliations are accurate", "competence", 0.65),
        (
            "re_depreciation_correct",
            "Depreciation schedules are properly maintained",
            "competence",
            0.7,
        ),
        ("re_lease_compliant", "Lease accounting follows ASC 842", "competence", 0.6),
    ],
    "lease_beliefs": [
        ("lease_rou_tracked", "Right-of-use assets are properly tracked", "competence", 0.6),
        (
            "lease_liability_accurate",
            "Lease liabilities are accurately measured",
            "competence",
            0.6,
        ),
    ],
    # Manufacturing beliefs
    "manufacturing_beliefs": [
        ("mfg_inventory_accurate", "Inventory counts are accurate", "competence", 0.65),
        ("mfg_costing_reliable", "Product costing is reliable", "competence", 0.6),
        ("mfg_variance_analyzed", "Cost variances are analyzed timely", "competence", 0.55),
    ],
    # General accounting beliefs (everyone gets these)
    "general_accounting_beliefs": [
        # Process beliefs
        ("close_timely", "Month-end close completes within standard timeframe", "competence", 0.6),
        ("recon_complete", "Account reconciliations are complete", "competence", 0.65),
        ("je_documented", "Journal entries have proper documentation", "competence", 0.7),
        # Control beliefs
        ("controls_effective", "Internal controls are operating effectively", "competence", 0.6),
        ("segregation_proper", "Duties are properly segregated", "competence", 0.55),
        # Accuracy beliefs
        ("tb_balanced", "Trial balance is balanced", "competence", 0.8),
        (
            "interco_eliminated",
            "Intercompany transactions are properly eliminated",
            "competence",
            0.6,
        ),
    ],
}


def seed_authority_beliefs(
    graph: "BeliefGraph", title: str, authority: float, person_id: str
) -> None:
    """
    Seed beliefs about this person's capabilities and authority.

    These are BELIEFS about what this person can handle, not facts.
    The learning loop will adjust based on observed competence.
    """
    if authority >= 0.8:
        # Executive-level beliefs
        beliefs = [
            ("handles_strategic", "This person handles strategic financial decisions well", 0.7),
            ("board_capable", "This person can prepare board-level materials", 0.65),
            ("risk_aware", "This person identifies material risks", 0.7),
        ]
    elif authority >= 0.5:
        # Manager-level beliefs
        beliefs = [
            ("team_capable", "This person manages team workflows effectively", 0.6),
            ("approval_appropriate", "This person makes appropriate approval decisions", 0.65),
            ("process_knowledgeable", "This person understands processes well", 0.7),
        ]
    else:
        # Analyst-level beliefs
        beliefs = [
            ("detail_oriented", "This person is detail-oriented", 0.7),
            ("escalates_well", "This person escalates appropriately", 0.6),
            ("follows_procedures", "This person follows established procedures", 0.7),
        ]

    for belief_id, statement, strength in beliefs:
        graph.add_belief(
            {
                "belief_id": f"{person_id}_{belief_id}",
                "category": "competence",
                "statement": statement,
                "scope": f"person:{person_id}|*|*",
                "strength": strength,
                "immutable": False,
                "invalidatable": True,
                "tags": ["competence", "authority", "person"],
            }
        )


def seed_preference_beliefs(
    graph: "BeliefGraph", person_id: str, apollo_data: Optional[dict[str, Any]] = None
) -> None:
    """
    Seed beliefs about person's preferences.

    These start with low strength - we're uncertain until we learn.
    """
    # Default preference beliefs (low strength - we'll learn)
    beliefs = [
        ("prefers_concise", "This person prefers concise communication", 0.5),
        ("prefers_detail", "This person wants detailed explanations", 0.5),
        ("prefers_proactive", "This person appreciates proactive suggestions", 0.5),
    ]

    # Adjust based on seniority from Apollo
    if apollo_data and "person" in apollo_data:
        seniority = apollo_data["person"].get("seniority", "").lower()
        if seniority in ["c_suite", "vp", "director"]:
            # Executives typically prefer concise
            beliefs = [
                ("prefers_concise", "This person prefers concise communication", 0.65),
                ("prefers_detail", "This person wants detailed explanations", 0.35),
                ("prefers_proactive", "This person appreciates proactive suggestions", 0.6),
            ]

    for belief_id, statement, strength in beliefs:
        graph.add_belief(
            {
                "belief_id": f"{person_id}_{belief_id}",
                "category": "preference",
                "statement": statement,
                "scope": f"person:{person_id}|*|*",
                "strength": strength,
                "immutable": False,
                "invalidatable": True,
                "tags": ["preference", "communication", "person"],
            }
        )


def infer_goals_from_role(title: str, authority: float) -> list[dict[str, Any]]:
    """
    Infer standing goals from role and authority.

    Goals have priority (0.0-1.0), not strength.
    Goals are not beliefs - they're what we're trying to accomplish.
    """
    title_lower = (title or "").lower()

    if authority >= 0.8 or any(x in title_lower for x in ["ceo", "cfo", "coo", "chief"]):
        return [
            {
                "goal_id": "strategic_oversight",
                "description": "Maintain strategic financial oversight",
                "priority": 0.95,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "stakeholder_reporting",
                "description": "Ensure accurate stakeholder reporting",
                "priority": 0.9,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "risk_management",
                "description": "Identify and mitigate financial risks",
                "priority": 0.85,
                "type": "standing",
                "state": "active",
            },
        ]

    if any(x in title_lower for x in ["controller", "director"]):
        return [
            {
                "goal_id": "accurate_records",
                "description": "Maintain accurate financial records",
                "priority": 0.95,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "timely_close",
                "description": "Complete period-end close on schedule",
                "priority": 0.85,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "compliance",
                "description": "Ensure regulatory compliance",
                "priority": 0.9,
                "type": "standing",
                "state": "active",
            },
        ]

    if "manager" in title_lower:
        return [
            {
                "goal_id": "team_efficiency",
                "description": "Optimize team workflows",
                "priority": 0.85,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "process_accuracy",
                "description": "Ensure process accuracy",
                "priority": 0.9,
                "type": "standing",
                "state": "active",
            },
            {
                "goal_id": "timely_processing",
                "description": "Process work items timely",
                "priority": 0.85,
                "type": "standing",
                "state": "active",
            },
        ]

    # Default for analysts and specialists
    return [
        {
            "goal_id": "task_accuracy",
            "description": "Complete tasks accurately",
            "priority": 0.9,
            "type": "standing",
            "state": "active",
        },
        {
            "goal_id": "timely_completion",
            "description": "Meet deadlines",
            "priority": 0.85,
            "type": "standing",
            "state": "active",
        },
    ]
