"""
Knowledge System
=================

Certain facts with NO strength. Knowledge is not uncertain.

MARS distinguishes:
- Knowledge: "ASC 606 governs revenue recognition" (fact, no strength)
- Belief: "This client follows ASC 606 correctly" (claim, strength 0.7)

Knowledge is:
- Scoped: global → industry → org → person (narrower wins)
- Changed via REPLACE (delete + insert), not learning
- Used as CONTEXT in cognitive loop, not for autonomy decisions

The learning loop NEVER touches knowledge. Only beliefs learn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional


@dataclass
class KnowledgeFact:
    """
    A certain fact. No strength because it's not uncertain.

    Examples:
    - "Debits must equal credits" (global, accounting)
    - "ASC 606 governs revenue recognition" (global, regulatory)
    - "Company fiscal year ends December 31" (org, temporal)
    - "User timezone is America/New_York" (person, context)
    """

    fact_id: str
    statement: str
    scope: Literal["global", "industry", "org", "person"]
    scope_id: Optional[str] = None  # org_id or person_id if scoped
    category: str = "general"  # accounting, regulatory, process, entity, temporal
    source: str = "system"  # system, apollo, user, inferred
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def matches_scope(self, org_id: Optional[str], person_id: Optional[str]) -> bool:
        """Check if this fact applies to the given scope."""
        if self.scope == "global":
            return True
        if self.scope == "industry":
            return True  # Industry facts apply to matching industries
        if self.scope == "org":
            return self.scope_id == org_id
        if self.scope == "person":
            return self.scope_id == person_id
        return False


# ============================================================
# GLOBAL KNOWLEDGE (Accounting Fundamentals)
# These are FACTS, not beliefs. No strength, no learning.
# ============================================================

GLOBAL_KNOWLEDGE_FACTS = [
    # Accounting fundamentals
    KnowledgeFact(
        fact_id="global_double_entry",
        statement="Every journal entry must have balanced debits and credits",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "fundamental"],
    ),
    KnowledgeFact(
        fact_id="global_fiscal_periods",
        statement="Fiscal year consists of 12 monthly accounting periods",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "temporal"],
    ),
    KnowledgeFact(
        fact_id="global_accrual_basis",
        statement="GAAP requires accrual basis accounting for most entities",
        scope="global",
        category="regulatory",
        source="system",
        tags=["gaap", "fundamental"],
    ),
    KnowledgeFact(
        fact_id="global_materiality",
        statement="Materiality thresholds determine disclosure requirements",
        scope="global",
        category="accounting",
        source="system",
        tags=["gaap", "audit"],
    ),
    KnowledgeFact(
        fact_id="global_internal_controls",
        statement="Internal controls are required to prevent fraud and errors",
        scope="global",
        category="regulatory",
        source="system",
        tags=["sox", "controls"],
    ),
    KnowledgeFact(
        fact_id="global_audit_trail",
        statement="All transactions require supporting documentation",
        scope="global",
        category="accounting",
        source="system",
        tags=["audit", "compliance"],
    ),
]


# ============================================================
# INDUSTRY KNOWLEDGE PACKS
# Facts specific to industries. Still no strength.
# ============================================================

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

    if any(x in industry_lower for x in ["investment", "asset management", "hedge", "fund"]):
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


def create_org_knowledge(
    org_id: str,
    org_name: str,
    industry: str,
    size: str,
    apollo_data: Optional[dict] = None,
) -> list[KnowledgeFact]:
    """
    Create org-specific knowledge from Apollo and inference.

    These are FACTS about this specific org, not beliefs.
    """
    facts = []

    # Basic org facts
    facts.append(
        KnowledgeFact(
            fact_id=f"{org_id}_name",
            statement=f"Organization name is {org_name}",
            scope="org",
            scope_id=org_id,
            category="entity",
            source="apollo",
            tags=["identity"],
        )
    )

    facts.append(
        KnowledgeFact(
            fact_id=f"{org_id}_industry",
            statement=f"Organization operates in {industry} industry",
            scope="org",
            scope_id=org_id,
            category="entity",
            source="apollo",
            tags=["industry"],
        )
    )

    facts.append(
        KnowledgeFact(
            fact_id=f"{org_id}_size",
            statement=f"Organization is {size} size ({_size_description(size)})",
            scope="org",
            scope_id=org_id,
            category="entity",
            source="apollo",
            tags=["size"],
        )
    )

    # Extract additional facts from Apollo company data
    if apollo_data and "company" in apollo_data:
        company = apollo_data["company"]

        if company.get("keywords"):
            keywords = ", ".join(company["keywords"][:5])
            facts.append(
                KnowledgeFact(
                    fact_id=f"{org_id}_focus",
                    statement=f"Organization focus areas: {keywords}",
                    scope="org",
                    scope_id=org_id,
                    category="entity",
                    source="apollo",
                    tags=["focus", "keywords"],
                )
            )

    return facts


def create_person_knowledge(
    person_id: str,
    org_id: str,
    name: str,
    email: str,
    role: str,
    apollo_data: Optional[dict] = None,
) -> list[KnowledgeFact]:
    """
    Create person-specific knowledge from Apollo.

    These are FACTS about this person, not beliefs about them.
    """
    facts = []

    facts.append(
        KnowledgeFact(
            fact_id=f"{person_id}_identity",
            statement=f"User is {name}, {role}",
            scope="person",
            scope_id=person_id,
            category="entity",
            source="apollo",
            tags=["identity"],
        )
    )

    facts.append(
        KnowledgeFact(
            fact_id=f"{person_id}_email",
            statement=f"User email is {email}",
            scope="person",
            scope_id=person_id,
            category="entity",
            source="apollo",
            tags=["contact"],
        )
    )

    # Extract from Apollo person data
    if apollo_data and "person" in apollo_data:
        person = apollo_data["person"]

        if person.get("timezone"):
            facts.append(
                KnowledgeFact(
                    fact_id=f"{person_id}_timezone",
                    statement=f"User timezone is {person['timezone']}",
                    scope="person",
                    scope_id=person_id,
                    category="temporal",
                    source="apollo",
                    tags=["timezone", "context"],
                )
            )

        if person.get("location"):
            facts.append(
                KnowledgeFact(
                    fact_id=f"{person_id}_location",
                    statement=f"User is located in {person['location']}",
                    scope="person",
                    scope_id=person_id,
                    category="entity",
                    source="apollo",
                    tags=["location", "context"],
                )
            )

        if person.get("seniority"):
            facts.append(
                KnowledgeFact(
                    fact_id=f"{person_id}_seniority",
                    statement=f"User seniority level is {person['seniority']}",
                    scope="person",
                    scope_id=person_id,
                    category="entity",
                    source="apollo",
                    tags=["seniority", "role"],
                )
            )

    # Rapport hooks as knowledge (facts for personalization)
    if apollo_data and "rapport_hooks" in apollo_data:
        hooks = apollo_data["rapport_hooks"]
        if hooks:
            # Handle both list and other iterables
            if isinstance(hooks, list):
                hooks_text = ", ".join(hooks[:3])
            else:
                hooks_text = str(hooks)
            facts.append(
                KnowledgeFact(
                    fact_id=f"{person_id}_rapport",
                    statement=f"Rapport context: {hooks_text}",
                    scope="person",
                    scope_id=person_id,
                    category="context",
                    source="apollo",
                    tags=["rapport", "personalization"],
                )
            )

    return facts


def _size_description(size: str) -> str:
    """Human-readable size description."""
    return {
        "startup": "under 50 employees",
        "smb": "50-200 employees",
        "mid_market": "200-1000 employees",
        "enterprise": "1000+ employees",
    }.get(size, size)


# ============================================================
# KNOWLEDGE RESOLUTION
# Narrower scope wins, no strength-based resolution.
# ============================================================


def resolve_knowledge(
    all_facts: list[KnowledgeFact],
    org_id: str,
    person_id: str,
) -> list[KnowledgeFact]:
    """
    Resolve knowledge by scope. Narrower scope wins.

    Unlike beliefs, there's no strength-based resolution.
    If a person-scoped fact exists, it overrides org-scoped on same topic.

    Returns: Deduplicated facts with narrowest scope winning.
    """
    # Group by fact category/topic
    by_topic: dict[str, list[KnowledgeFact]] = {}

    for fact in all_facts:
        if not fact.matches_scope(org_id, person_id):
            continue

        # Use first tag as topic key, or category
        topic = fact.tags[0] if fact.tags else fact.category
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(fact)

    # For each topic, keep all facts (knowledge can have multiple facts per topic)
    # But prefer narrower scopes
    scope_priority = {"person": 0, "org": 1, "industry": 2, "global": 3}

    resolved = []
    seen_ids = set()

    for topic, facts in by_topic.items():
        # Sort by scope priority (narrower first)
        facts.sort(key=lambda f: scope_priority.get(f.scope, 99))

        for fact in facts:
            if fact.fact_id not in seen_ids:
                resolved.append(fact)
                seen_ids.add(fact.fact_id)

    return resolved


def knowledge_to_context_string(facts: list[KnowledgeFact], max_facts: int = 15) -> str:
    """
    Convert knowledge facts to a context string for the cognitive loop.

    This is injected into prompts as factual context.
    """
    if not facts:
        return ""

    # Prioritize by scope (person > org > industry > global)
    scope_priority = {"person": 0, "org": 1, "industry": 2, "global": 3}
    sorted_facts = sorted(facts, key=lambda f: scope_priority.get(f.scope, 99))

    lines = ["KNOWN FACTS (certain, no uncertainty):"]
    for fact in sorted_facts[:max_facts]:
        lines.append(f"- {fact.statement}")

    return "\n".join(lines)


def facts_to_dicts(facts: list[KnowledgeFact]) -> list[dict]:
    """Convert KnowledgeFact objects to dicts for state storage."""
    return [
        {
            "fact_id": f.fact_id,
            "statement": f.statement,
            "scope": f.scope,
            "scope_id": f.scope_id,
            "category": f.category,
            "source": f.source,
            "tags": f.tags,
        }
        for f in facts
    ]


def dicts_to_facts(dicts: list[dict]) -> list[KnowledgeFact]:
    """Convert dicts back to KnowledgeFact objects."""
    return [
        KnowledgeFact(
            fact_id=d["fact_id"],
            statement=d["statement"],
            scope=d["scope"],
            scope_id=d.get("scope_id"),
            category=d.get("category", "general"),
            source=d.get("source", "system"),
            tags=d.get("tags", []),
        )
        for d in dicts
    ]
