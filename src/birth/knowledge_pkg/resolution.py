"""
Knowledge Resolution
=====================

Functions for resolving and converting knowledge facts.
"""

from .model import KnowledgeFact


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
    by_topic: dict[str, list[KnowledgeFact]] = {}

    for fact in all_facts:
        if not fact.matches_scope(org_id, person_id):
            continue

        topic = fact.tags[0] if fact.tags else fact.category
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(fact)

    scope_priority = {"person": 0, "org": 1, "industry": 2, "global": 3}

    resolved = []
    seen_ids = set()

    for topic, facts in by_topic.items():
        facts.sort(key=lambda f: scope_priority.get(f.scope, 99))

        for fact in facts:
            if fact.fact_id not in seen_ids:
                resolved.append(fact)
                seen_ids.add(fact.fact_id)

    return resolved


def knowledge_to_context_string(
    facts: list[KnowledgeFact], max_facts: int = 15
) -> str:
    """
    Convert knowledge facts to a context string for the cognitive loop.

    This is injected into prompts as factual context.
    """
    if not facts:
        return ""

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
