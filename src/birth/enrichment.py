"""
Apollo API Integration
=======================

Fetches person and company data from Apollo.io for birth enrichment.

Apollo provides:
- Person: name, title, seniority, department, email
- Company: name, industry, employee_count, location
- Rapport hooks: timezone, interests, background
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

# Load .env
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"


@dataclass
class PersonData:
    """Person data from Apollo"""

    id: str = ""
    email: str = ""
    name: str = ""
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    seniority: str = ""  # owner, founder, c_suite, vp, director, manager, senior, entry
    department: str = ""  # finance, operations, engineering, etc.
    linkedin_url: str = ""
    phone: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    timezone: str = ""


@dataclass
class CompanyData:
    """Company data from Apollo"""

    id: str = ""
    name: str = ""
    domain: str = ""
    industry: str = ""
    sub_industry: str = ""
    employee_count: int = 0
    employee_range: str = ""  # 1-10, 11-50, 51-200, etc.
    annual_revenue: int = 0
    revenue_range: str = ""
    founded_year: int = 0
    city: str = ""
    state: str = ""
    country: str = ""
    description: str = ""
    linkedin_url: str = ""
    website: str = ""
    technologies: list = field(default_factory=list)
    keywords: list = field(default_factory=list)


@dataclass
class ApolloEnrichment:
    """Combined enrichment result"""

    person: PersonData
    company: CompanyData
    rapport_hooks: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


async def enrich_from_apollo(email: str) -> Optional[ApolloEnrichment]:
    """
    Fetch person and company data from Apollo API.

    Args:
        email: Email address to look up

    Returns:
        ApolloEnrichment with person, company, and rapport_hooks
        None if lookup fails or no data found
    """
    if not APOLLO_API_KEY:
        print("Warning: APOLLO_API_KEY not set, skipping enrichment")
        return None

    async with httpx.AsyncClient() as client:
        try:
            # Apollo People Enrichment API
            response = await client.post(
                f"{APOLLO_BASE_URL}/people/match",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "X-Api-Key": APOLLO_API_KEY,
                },
                json={
                    "email": email,
                    "reveal_personal_emails": False,
                    "reveal_phone_number": False,
                },
            )

            if response.status_code != 200:
                print(f"Apollo API error: {response.status_code} - {response.text}")
                return None

            data = response.json()

            if not data.get("person"):
                print(f"No Apollo data found for {email}")
                return None

            person_data = data["person"]
            org_data = person_data.get("organization", {}) or {}

            # Extract person
            person = PersonData(
                id=person_data.get("id", ""),
                email=email,
                name=person_data.get("name", ""),
                first_name=person_data.get("first_name", ""),
                last_name=person_data.get("last_name", ""),
                title=person_data.get("title", ""),
                seniority=person_data.get("seniority", ""),
                department=person_data.get("departments", [""])[0]
                if person_data.get("departments")
                else "",
                linkedin_url=person_data.get("linkedin_url", ""),
                phone=person_data.get("phone_numbers", [{}])[0].get("sanitized_number", "")
                if person_data.get("phone_numbers")
                else "",
                city=person_data.get("city", ""),
                state=person_data.get("state", ""),
                country=person_data.get("country", ""),
                timezone=person_data.get("time_zone", ""),
            )

            # Extract company
            company = CompanyData(
                id=org_data.get("id", ""),
                name=org_data.get("name", ""),
                domain=org_data.get("primary_domain", ""),
                industry=org_data.get("industry", ""),
                sub_industry=org_data.get("sub_industry", ""),
                employee_count=org_data.get("estimated_num_employees", 0) or 0,
                employee_range=org_data.get("employee_count", ""),
                annual_revenue=org_data.get("annual_revenue", 0) or 0,
                revenue_range=org_data.get("annual_revenue_printed", ""),
                founded_year=org_data.get("founded_year", 0) or 0,
                city=org_data.get("city", ""),
                state=org_data.get("state", ""),
                country=org_data.get("country", ""),
                description=org_data.get("short_description", ""),
                linkedin_url=org_data.get("linkedin_url", ""),
                website=org_data.get("website_url", ""),
                technologies=org_data.get("technologies", []) or [],
                keywords=org_data.get("keywords", []) or [],
            )

            # Build rapport hooks
            rapport_hooks = {
                "location": f"{person.city}, {person.state}" if person.city else None,
                "timezone": person.timezone,
                "company_size": company.employee_range,
                "industry": company.industry,
                "technologies": company.technologies[:5] if company.technologies else [],
            }
            # Remove None values
            rapport_hooks = {k: v for k, v in rapport_hooks.items() if v}

            return ApolloEnrichment(
                person=person,
                company=company,
                rapport_hooks=rapport_hooks,
                raw_response=data,
            )

        except Exception as e:
            print(f"Apollo enrichment error: {e}")
            return None


def map_industry_to_knowledge_pack(industry: str) -> list[str]:
    """
    Map Apollo industry to knowledge pack names.

    Args:
        industry: Apollo industry string

    Returns:
        List of knowledge pack names to load
    """
    # Normalize industry
    industry_lower = (industry or "").lower()

    # Industry mappings
    mappings = {
        # Financial services
        "financial services": ["gaap", "financial_services"],
        "banking": ["gaap", "banking"],
        "investment management": ["gaap", "investment_management", "sec"],
        "venture capital": ["gaap", "investment_management"],
        "private equity": ["gaap", "investment_management"],
        "insurance": ["gaap", "insurance"],
        # Real estate
        "real estate": ["gaap", "real_estate"],
        "commercial real estate": ["gaap", "real_estate", "lease_accounting"],
        "property management": ["gaap", "real_estate", "property_management"],
        # Technology
        "computer software": ["gaap", "saas", "asc_606"],
        "information technology": ["gaap", "saas"],
        "internet": ["gaap", "saas", "asc_606"],
        # Professional services
        "accounting": ["gaap", "professional_services"],
        "legal services": ["gaap", "professional_services"],
        "management consulting": ["gaap", "professional_services"],
        # Manufacturing
        "manufacturing": ["gaap", "manufacturing", "inventory"],
        "industrial": ["gaap", "manufacturing"],
        # Healthcare
        "hospital & health care": ["gaap", "healthcare"],
        "medical practice": ["gaap", "healthcare"],
        "pharmaceuticals": ["gaap", "healthcare", "r_and_d"],
        # Retail
        "retail": ["gaap", "retail", "inventory"],
        "consumer goods": ["gaap", "retail"],
        # Nonprofit
        "nonprofit": ["gaap", "nonprofit"],
        "philanthropy": ["gaap", "nonprofit"],
    }

    # Find matching packs
    for key, packs in mappings.items():
        if key in industry_lower or industry_lower in key:
            return packs

    # Default
    return ["gaap"]


def infer_authority_from_role(title: str, seniority: str) -> float:
    """
    Infer authority level from title and seniority.

    Args:
        title: Job title
        seniority: Apollo seniority level

    Returns:
        Authority score 0.0-1.0
    """
    title_lower = (title or "").lower()

    # Direct title matches
    if any(x in title_lower for x in ["ceo", "chief executive"]):
        return 1.0
    if any(x in title_lower for x in ["cfo", "chief financial"]):
        return 0.95
    if any(x in title_lower for x in ["coo", "chief operating"]):
        return 0.9
    if "controller" in title_lower:
        return 0.8
    if "vp" in title_lower or "vice president" in title_lower:
        return 0.75
    if "director" in title_lower:
        return 0.7
    if "manager" in title_lower:
        return 0.6
    if "senior" in title_lower:
        return 0.5
    if "analyst" in title_lower:
        return 0.4
    if "specialist" in title_lower:
        return 0.35
    if "coordinator" in title_lower:
        return 0.3

    # Fall back to seniority
    seniority_map = {
        "owner": 1.0,
        "founder": 1.0,
        "c_suite": 0.95,
        "partner": 0.85,
        "vp": 0.75,
        "director": 0.7,
        "manager": 0.6,
        "senior": 0.5,
        "entry": 0.3,
    }

    return seniority_map.get(seniority, 0.4)


def determine_org_size(employee_count: int) -> str:
    """
    Determine org size category from employee count.

    Args:
        employee_count: Number of employees

    Returns:
        Size category: smb, mid_market, enterprise
    """
    if employee_count < 50:
        return "smb"
    elif employee_count < 500:
        return "mid_market"
    else:
        return "enterprise"
