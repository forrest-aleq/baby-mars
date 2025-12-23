"""
Knowledge Creation
===================

Functions to create org-specific and person-specific knowledge facts.
"""

from typing import Any, Optional

from .model import KnowledgeFact


def create_org_knowledge(
    org_id: str,
    org_name: str,
    industry: str,
    size: str,
    apollo_data: Optional[dict[str, Any]] = None,
) -> list[KnowledgeFact]:
    """
    Create org-specific knowledge from Apollo and inference.

    These are FACTS about this specific org, not beliefs.
    """
    facts = []

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
    apollo_data: Optional[dict[str, Any]] = None,
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

    if apollo_data and "person" in apollo_data:
        person = apollo_data["person"]
        _add_person_details(facts, person_id, person)

    if apollo_data and "rapport_hooks" in apollo_data:
        _add_rapport_hooks(facts, person_id, apollo_data["rapport_hooks"])

    return facts


def _add_person_details(facts: list[KnowledgeFact], person_id: str, person: dict[str, Any]) -> None:
    """Add person detail facts from Apollo data."""
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


def _add_rapport_hooks(facts: list[KnowledgeFact], person_id: str, hooks: Any) -> None:
    """Add rapport hooks as knowledge facts."""
    if not hooks:
        return

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


def _size_description(size: str) -> str:
    """Human-readable size description."""
    return {
        "startup": "under 50 employees",
        "smb": "50-200 employees",
        "mid_market": "200-1000 employees",
        "enterprise": "1000+ employees",
    }.get(size, size)
