"""
Baby MARS Birth System
=======================

In-memory initialization of the 6 types:
1. Capabilities - What Aleq CAN do (binary)
2. Relationships - Org structure facts
3. Knowledge - Certain facts (no strength)
4. Beliefs - Uncertain claims (has strength)
5. Goals - What to accomplish (has priority)
6. Style - How to behave (configuration)

This is the Baby MARS version - no Neo4j, no Apollo API.
Just sensible defaults based on role and org type.
"""

from typing import Optional, Literal
from datetime import datetime
import uuid

from ..state.schema import (
    BabyMARSState,
    PersonObject,
    Note,
    ActiveTask,
)
from ..graphs.belief_graph import get_belief_graph, reset_belief_graph


# ============================================================
# TYPE DEFINITIONS (The 6 Things)
# ============================================================

# Type 1: Capabilities (binary - can or can't)
DEFAULT_CAPABILITIES = {
    "erp.read_transactions": True,
    "erp.write_journal_entries": True,
    "erp.process_invoices": True,
    "bank.read_statements": True,
    "bank.initiate_payments": False,  # Requires explicit enable
    "documents.parse_pdf": True,
    "documents.parse_images": True,
    "email.send": False,  # Requires explicit enable
    "slack.send": False,  # Requires explicit enable
}

# Type 2: Relationships (facts, not beliefs)
ROLE_HIERARCHY = {
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

# Type 3: Knowledge (certain facts by scope)
GLOBAL_KNOWLEDGE = [
    "Debits must equal credits in every journal entry",
    "Fiscal year typically has 12 monthly periods",
    "GAAP requires revenue recognition when earned",
    "Materiality thresholds guide audit focus",
    "Internal controls prevent fraud and errors",
]

INDUSTRY_KNOWLEDGE = {
    "investment_management": [
        "NAV calculated daily for mutual funds",
        "SEC Form ADV required annually",
        "Custody accounts reconcile T+1",
        "Performance fees follow high-water mark",
    ],
    "real_estate": [
        "Depreciation uses straight-line or MACRS",
        "CAM reconciliation required annually",
        "Lease accounting follows ASC 842",
        "Property taxes accrue monthly",
    ],
    "saas": [
        "Revenue recognition follows ASC 606",
        "Deferred revenue for prepaid subscriptions",
        "CAC and LTV are key metrics",
        "ARR/MRR tracking essential",
    ],
    "manufacturing": [
        "Inventory uses FIFO, LIFO, or weighted average",
        "Cost of goods sold includes direct materials/labor",
        "WIP tracking required for job costing",
        "Standard costing enables variance analysis",
    ],
    "professional_services": [
        "Revenue recognized as services performed",
        "Utilization rate drives profitability",
        "WIP for unbilled time",
        "Realization rate measures billing efficiency",
    ],
}

# Type 5: Goals (standing goals by role)
ROLE_GOALS = {
    "AP Specialist": [
        {"goal_id": "process_invoices", "description": "Process invoices accurately and timely", "priority": 0.9},
        {"goal_id": "vendor_relations", "description": "Maintain positive vendor relationships", "priority": 0.6},
    ],
    "AP Manager": [
        {"goal_id": "ap_accuracy", "description": "Ensure AP accuracy and completeness", "priority": 0.9},
        {"goal_id": "cash_management", "description": "Optimize payment timing for cash flow", "priority": 0.7},
    ],
    "Controller": [
        {"goal_id": "accurate_records", "description": "Maintain accurate financial records", "priority": 0.95},
        {"goal_id": "timely_close", "description": "Complete month-end close on schedule", "priority": 0.85},
        {"goal_id": "compliance", "description": "Ensure regulatory compliance", "priority": 0.9},
    ],
    "CFO": [
        {"goal_id": "financial_oversight", "description": "Provide strategic financial oversight", "priority": 0.95},
        {"goal_id": "stakeholder_reporting", "description": "Accurate reporting to stakeholders", "priority": 0.9},
    ],
}

# Type 6: Style (defaults, can be overridden)
DEFAULT_STYLE = {
    "tone": "warm",
    "verbosity": "moderate",
    "formality": "professional",
    "proactivity": "balanced",
    "pace": "normal",
    "certainty": "balanced",
}

ROLE_STYLE_OVERRIDES = {
    "CFO": {"verbosity": "concise", "pace": "quick"},
    "CEO": {"verbosity": "concise", "formality": "formal"},
    "AP Specialist": {"verbosity": "thorough"},
    "Controller": {"verbosity": "thorough", "certainty": "hedged"},
}


# ============================================================
# IMMUTABLE BELIEFS (Identity - NEVER change)
# MARS taxonomy: identity beliefs have multiplier 0.0 (cannot be updated)
# ============================================================

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


# ============================================================
# BIRTH MODES (Based on salience)
# ============================================================

def calculate_salience(
    role: str,
    org_size: str = "mid_market",
    is_decision_maker: bool = False
) -> float:
    """
    Calculate salience score to determine birth mode.
    
    salience = (future_interaction × 0.4) + (incentive_value × 0.4) + (deviation × 0.2)
    """
    # Future interaction probability by role
    future_interaction = {
        "CFO": 0.9,
        "Controller": 0.85,
        "AP Manager": 0.7,
        "AR Manager": 0.7,
        "Senior Accountant": 0.6,
        "Staff Accountant": 0.5,
        "AP Specialist": 0.4,
        "AR Specialist": 0.4,
    }.get(role, 0.5)
    
    # Incentive value by org size
    incentive_value = {
        "enterprise": 0.9,
        "mid_market": 0.7,
        "smb": 0.4,
    }.get(org_size, 0.5)
    
    # Deviation (how different from typical)
    deviation = 0.3 if is_decision_maker else 0.1
    
    salience = (future_interaction * 0.4) + (incentive_value * 0.4) + (deviation * 0.2)
    return round(salience, 2)


def determine_birth_mode(salience: float) -> Literal["full", "standard", "micro"]:
    """
    Determine birth mode based on salience.
    
    - FULL (≥0.7): 20-25 beliefs, all pillars, LLM synthesis
    - STANDARD (0.4-0.7): 10-15 beliefs, key pillars
    - MICRO (<0.4): 5-8 beliefs, no LLM, rule-based only
    """
    if salience >= 0.7:
        return "full"
    elif salience >= 0.4:
        return "standard"
    else:
        return "micro"


# ============================================================
# BELIEF SEEDING BY SCOPE
# ============================================================

def seed_global_beliefs(graph) -> None:
    """Seed global accounting beliefs (scope: *|*|*) using MARS taxonomy"""
    global_beliefs = [
        # MORAL: Core ethical requirements
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
        # COMPETENCE: How to do things correctly
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


def seed_industry_beliefs(graph, industry: str) -> None:
    """Seed industry-specific beliefs using MARS taxonomy (technical category)"""
    # Industry beliefs are TECHNICAL - domain-specific facts
    industry_belief_templates = {
        "investment_management": [
            ("industry_nav_daily", "NAV should be calculated and verified daily", 0.8),
            ("industry_custody_recon", "Custody accounts reconcile within T+1", 0.75),
        ],
        "real_estate": [
            ("industry_cam_recon", "CAM reconciliation required annually for tenants", 0.8),
            ("industry_depreciation", "Property depreciation follows consistent method", 0.85),
        ],
        "saas": [
            ("industry_deferred_rev", "Prepaid subscriptions recorded as deferred revenue", 0.85),
            ("industry_arr_tracking", "ARR/MRR tracked and reconciled monthly", 0.75),
        ],
        "manufacturing": [
            ("industry_inventory_method", "Inventory valued using consistent cost method", 0.85),
            ("industry_cogs_components", "COGS includes all direct costs", 0.8),
        ],
        "professional_services": [
            ("industry_wip_tracking", "Unbilled time tracked as WIP", 0.8),
            ("industry_utilization", "Utilization rates monitored for profitability", 0.7),
        ],
    }

    templates = industry_belief_templates.get(industry, [])
    for belief_id, statement, strength in templates:
        graph.add_belief({
            "belief_id": belief_id,
            "category": "technical",  # MARS taxonomy: domain-specific facts
            "statement": statement,
            "scope": f"industry:{industry}|*|*",
            "strength": strength,
            "immutable": False,
            "invalidatable": True,
            "tags": ["technical", "industry", industry],
        })


def seed_role_beliefs(graph, role: str, person_id: str) -> None:
    """Seed role-specific beliefs for a person using MARS taxonomy (competence)"""
    # Role beliefs are COMPETENCE - how to do things in this role
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
            "category": "competence",  # MARS taxonomy: how to do things
            "statement": statement,
            "scope": f"person:{person_id}|*|*",
            "strength": strength,
            "immutable": False,
            "invalidatable": True,
            "tags": ["competence", "role", role.lower().replace(" ", "_")],
        })


# ============================================================
# MAIN BIRTH FUNCTION
# ============================================================

def birth_person(
    person_id: str,
    name: str,
    email: str,
    role: str,
    org_id: str,
    org_name: str,
    industry: str = "general",
    org_size: str = "mid_market",
    capabilities_override: Optional[dict] = None,
) -> dict:
    """
    Birth a new person into Baby MARS.
    
    Returns a BirthResult with everything needed to initialize state.
    
    This is the Baby MARS equivalent of the 9-step Neo4j birth flow,
    but entirely in-memory.
    """
    
    # Step 1: Calculate salience and birth mode
    salience = calculate_salience(role, org_size)
    birth_mode = determine_birth_mode(salience)
    
    # Step 2: Get capabilities
    capabilities = {**DEFAULT_CAPABILITIES}
    if capabilities_override:
        capabilities.update(capabilities_override)
    
    # Step 3: Build relationships
    role_info = ROLE_HIERARCHY.get(role, {"reports_to": None, "authority": 0.5})
    relationships = {
        "reports_to": role_info["reports_to"],
        "authority": role_info["authority"],
        "org_id": org_id,
    }
    
    # Step 4: Gather knowledge
    knowledge = list(GLOBAL_KNOWLEDGE)
    if industry in INDUSTRY_KNOWLEDGE:
        knowledge.extend(INDUSTRY_KNOWLEDGE[industry])
    
    # Step 5: Seed beliefs into graph
    graph = get_belief_graph()
    
    # Always seed immutables first
    for belief in IMMUTABLE_BELIEFS:
        graph.add_belief(belief)
    
    # Seed by mode
    seed_global_beliefs(graph)
    
    if birth_mode in ("full", "standard"):
        seed_industry_beliefs(graph, industry)
    
    if birth_mode == "full":
        seed_role_beliefs(graph, role, person_id)
    
    # Step 6: Create standing goals
    goals = ROLE_GOALS.get(role, [
        {"goal_id": "default_accuracy", "description": "Maintain accurate records", "priority": 0.8}
    ])
    
    # Step 7: Resolve style
    style = {**DEFAULT_STYLE}
    if role in ROLE_STYLE_OVERRIDES:
        style.update(ROLE_STYLE_OVERRIDES[role])
    
    # Step 8: Build person object
    person: PersonObject = {
        "id": person_id,
        "name": name,
        "role": role,
        "authority": role_info["authority"],
        "relationship_value": 0.5,  # Neutral start
        "interaction_count": 0,
        "last_interaction": None,
        "expertise_areas": [],
        "communication_preferences": style,
    }
    
    # Return birth result
    return {
        "birth_mode": birth_mode,
        "salience": salience,
        "person": person,
        "org": {
            "org_id": org_id,
            "org_name": org_name,
            "industry": industry,
            "size": org_size,
        },
        "capabilities": capabilities,
        "relationships": relationships,
        "knowledge": knowledge,
        "goals": goals,
        "style": style,
        "belief_count": len(graph.beliefs),
        "immutable_count": len([b for b in graph.beliefs.values() if b.get("immutable")]),
    }


def create_initial_state(birth_result: dict, user_message: str) -> BabyMARSState:
    """
    Create initial BabyMARSState from birth result.
    
    This is what gets passed to the cognitive loop.
    """
    person = birth_result["person"]
    org = birth_result["org"]
    
    return {
        # Identity
        "thread_id": f"thread_{uuid.uuid4().hex[:12]}",
        "org_id": org["org_id"],
        
        # Messages
        "messages": [{"role": "user", "content": user_message}],
        
        # Three-Column Working Memory
        "active_tasks": [],
        "notes": [],
        "objects": {
            "people": [person],
            "entities": [],
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "is_month_end": False,
                "is_quarter_end": False,
                "is_year_end": False,
                "urgency_multiplier": 1.0,
            },
        },
        
        # Cognitive state (populated by mount)
        "current_context_key": "*|*|*",
        "activated_beliefs": [],
        "active_goals": [
            {
                "goal_id": g["goal_id"],
                "description": g["description"],
                "priority": g["priority"],
                "status": "active",
                "resources": [],
                "conflicts_with": [],
            }
            for g in birth_result["goals"]
        ],
        
        # Capabilities (for action selection)
        "capabilities": birth_result["capabilities"],
        
        # Knowledge (for context)
        "knowledge": birth_result["knowledge"],
        
        # Style (for response generation)
        "style": birth_result["style"],
        
        # Runtime state
        "supervision_mode": "guidance_seeking",
        "belief_strength_for_action": 0.0,
        "goal_conflict_detected": False,
        "retry_count": 0,
        "max_retries": 3,
        
        # Results (populated during loop)
        "appraisal": None,
        "selected_action": None,
        "execution_results": [],
        "validation_results": [],
        "memories": [],
        "feedback_events": [],
    }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def quick_birth(
    name: str,
    role: str = "Controller",
    industry: str = "general",
    message: str = "Hello, I need help with something."
) -> BabyMARSState:
    """
    Quick birth for testing - creates person and initial state in one call.
    """
    # Reset belief graph for clean start
    reset_belief_graph()
    
    person_id = f"person_{uuid.uuid4().hex[:8]}"
    org_id = f"org_{uuid.uuid4().hex[:8]}"
    
    birth_result = birth_person(
        person_id=person_id,
        name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        role=role,
        org_id=org_id,
        org_name="Test Organization",
        industry=industry,
    )
    
    return create_initial_state(birth_result, message)
