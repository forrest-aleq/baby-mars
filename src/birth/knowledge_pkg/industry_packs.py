"""
Industry Knowledge Packs
=========================

Facts specific to industries. Still no strength.
"""

from .model import KnowledgeFact

INDUSTRY_KNOWLEDGE_PACKS = {
    "saas": [
        KnowledgeFact(
            fact_id="saas_asc_606",
            statement="ASC 606 governs SaaS revenue recognition with 5-step model",
            scope="industry",
            category="regulatory",
            tags=["asc_606", "revenue"],
        ),
        KnowledgeFact(
            fact_id="saas_deferred_revenue",
            statement="Prepaid subscriptions are recorded as deferred revenue liability",
            scope="industry",
            category="accounting",
            tags=["revenue", "liability"],
        ),
        KnowledgeFact(
            fact_id="saas_arr_definition",
            statement="ARR is annualized value of recurring subscription contracts",
            scope="industry",
            category="accounting",
            tags=["metrics", "revenue"],
        ),
        KnowledgeFact(
            fact_id="saas_mrr_definition",
            statement="MRR is monthly recurring revenue from active subscriptions",
            scope="industry",
            category="accounting",
            tags=["metrics", "revenue"],
        ),
        KnowledgeFact(
            fact_id="saas_cac_ltv",
            statement="CAC (customer acquisition cost) and LTV (lifetime value) are key unit economics",
            scope="industry",
            category="accounting",
            tags=["metrics", "unit_economics"],
        ),
    ],
    "investment_management": [
        KnowledgeFact(
            fact_id="inv_nav_requirement",
            statement="Net Asset Value (NAV) must be calculated daily for open-end funds",
            scope="industry",
            category="regulatory",
            tags=["sec", "valuation"],
        ),
        KnowledgeFact(
            fact_id="inv_custody_rule",
            statement="SEC Custody Rule requires qualified custodian for client assets",
            scope="industry",
            category="regulatory",
            tags=["sec", "custody"],
        ),
        KnowledgeFact(
            fact_id="inv_form_adv",
            statement="SEC Form ADV must be filed annually and updated for material changes",
            scope="industry",
            category="regulatory",
            tags=["sec", "compliance"],
        ),
        KnowledgeFact(
            fact_id="inv_mark_to_market",
            statement="Investment securities are marked to market at fair value",
            scope="industry",
            category="accounting",
            tags=["valuation", "gaap"],
        ),
    ],
    "real_estate": [
        KnowledgeFact(
            fact_id="re_asc_842",
            statement="ASC 842 requires lessees to recognize lease liabilities and ROU assets",
            scope="industry",
            category="regulatory",
            tags=["asc_842", "leases"],
        ),
        KnowledgeFact(
            fact_id="re_depreciation",
            statement="Real property depreciated over 27.5 years (residential) or 39 years (commercial)",
            scope="industry",
            category="accounting",
            tags=["depreciation", "tax"],
        ),
        KnowledgeFact(
            fact_id="re_cam_reconciliation",
            statement="Common Area Maintenance (CAM) charges require annual reconciliation",
            scope="industry",
            category="accounting",
            tags=["leases", "reconciliation"],
        ),
        KnowledgeFact(
            fact_id="re_property_tax",
            statement="Property taxes accrue monthly based on assessed value",
            scope="industry",
            category="accounting",
            tags=["taxes", "accrual"],
        ),
    ],
    "financial_services": [
        KnowledgeFact(
            fact_id="fs_regulatory_capital",
            statement="Basel III requires minimum capital ratios for banking institutions",
            scope="industry",
            category="regulatory",
            tags=["basel", "capital"],
        ),
        KnowledgeFact(
            fact_id="fs_liquidity_coverage",
            statement="Liquidity Coverage Ratio (LCR) must exceed 100% of 30-day outflows",
            scope="industry",
            category="regulatory",
            tags=["basel", "liquidity"],
        ),
        KnowledgeFact(
            fact_id="fs_fair_value",
            statement="ASC 820 establishes fair value hierarchy for financial instruments",
            scope="industry",
            category="regulatory",
            tags=["asc_820", "valuation"],
        ),
    ],
    "manufacturing": [
        KnowledgeFact(
            fact_id="mfg_inventory_methods",
            statement="Inventory costing uses FIFO, LIFO, or weighted average method",
            scope="industry",
            category="accounting",
            tags=["inventory", "costing"],
        ),
        KnowledgeFact(
            fact_id="mfg_cogs",
            statement="Cost of goods sold includes direct materials, labor, and overhead",
            scope="industry",
            category="accounting",
            tags=["cogs", "costing"],
        ),
        KnowledgeFact(
            fact_id="mfg_wip",
            statement="Work-in-progress inventory tracked for job costing and variance analysis",
            scope="industry",
            category="accounting",
            tags=["inventory", "wip"],
        ),
    ],
    "professional_services": [
        KnowledgeFact(
            fact_id="ps_revenue_recognition",
            statement="Revenue recognized as services are performed over time",
            scope="industry",
            category="accounting",
            tags=["revenue", "asc_606"],
        ),
        KnowledgeFact(
            fact_id="ps_wip_unbilled",
            statement="Work-in-progress represents unbilled time and expenses",
            scope="industry",
            category="accounting",
            tags=["wip", "billing"],
        ),
        KnowledgeFact(
            fact_id="ps_utilization",
            statement="Utilization rate measures billable hours vs available hours",
            scope="industry",
            category="accounting",
            tags=["metrics", "profitability"],
        ),
    ],
}


def get_industry_from_apollo(apollo_industry: str) -> list[str]:
    """Map Apollo industry string to knowledge pack keys."""
    industry_lower = (apollo_industry or "").lower()

    packs = []

    if any(x in industry_lower for x in ["software", "technology", "saas", "cloud"]):
        packs.append("saas")

    if any(
        x in industry_lower for x in ["investment", "asset management", "hedge", "fund"]
    ):
        packs.append("investment_management")

    if any(x in industry_lower for x in ["real estate", "property", "reit"]):
        packs.append("real_estate")

    if any(x in industry_lower for x in ["bank", "financial services", "insurance"]):
        packs.append("financial_services")

    if any(x in industry_lower for x in ["manufacturing", "industrial"]):
        packs.append("manufacturing")

    if any(x in industry_lower for x in ["consulting", "legal", "professional"]):
        packs.append("professional_services")

    return packs


def load_industry_knowledge(industry: str) -> list[KnowledgeFact]:
    """Load knowledge facts for an industry."""
    packs = get_industry_from_apollo(industry)
    facts = []

    for pack in packs:
        pack_facts = INDUSTRY_KNOWLEDGE_PACKS.get(pack, [])
        facts.extend(pack_facts)

    return facts
