"""
Social Graph Implementation
============================

NetworkX-backed social graph for authority and relationship tracking.
Implements Paper #17: Social Awareness and Relationship Dynamics.
"""

import json
from datetime import datetime
from typing import Any, Optional

import networkx as nx

from ..state.schema import PersonObject, create_person


class SocialGraph:
    """
    Social graph for tracking authority and relationships.

    Paper #17: Social Awareness and Relationship Dynamics

    Key features:
    - Relationship value computation (0.6*authority + 0.2*interaction + 0.2*context)
    - Authority learning through preemption
    - Conflict resolution via authority-weighted triage
    """

    def __init__(self) -> None:
        self.G: nx.DiGraph[str] = nx.DiGraph()
        self.persons: dict[str, PersonObject] = {}

    # ============================================================
    # PERSON MANAGEMENT
    # ============================================================

    def add_person(self, person: PersonObject) -> None:
        """Add person to social graph"""
        self.persons[person["person_id"]] = person
        self.G.add_node(
            person["person_id"],
            authority=person["authority"],
            role=person["role"],
            name=person["name"],
        )

    def get_person(self, person_id: str) -> Optional[PersonObject]:
        """Get person by ID"""
        return self.persons.get(person_id)

    def find_person_by_name(self, name: str) -> Optional[PersonObject]:
        """Find person by name (case-insensitive)"""
        name_lower = name.lower()
        for person in self.persons.values():
            if person["name"].lower() == name_lower:
                return person
        return None

    def create_and_add_person(self, name: str, role: str, authority: float = 0.5) -> PersonObject:
        """Create and add a new person"""
        person = create_person(name, role, authority)
        self.add_person(person)
        return person

    # ============================================================
    # RELATIONSHIP VALUE
    # Paper #17
    # ============================================================

    def compute_relationship_value(self, person_id: str) -> float:
        """
        Compute relationship value.

        Paper #17: relationship_value = 0.6*authority + 0.2*interaction + 0.2*context
        """
        person = self.persons.get(person_id)
        if not person:
            return 0.5  # Default

        return (
            0.6 * person.get("authority", 0.5)
            + 0.2 * person.get("interaction_strength", 0.5)
            + 0.2 * person.get("context_relevance", 0.5)
        )

    def update_interaction_strength(
        self, person_id: str, positive: bool = True, weight: float = 0.1
    ) -> None:
        """Update interaction strength after an interaction"""
        person = self.persons.get(person_id)
        if not person:
            return

        current = person.get("interaction_strength", 0.5)

        if positive:
            new_strength = min(1.0, current + weight)
        else:
            new_strength = max(0.0, current - weight)

        person["interaction_strength"] = new_strength
        person["last_interaction"] = datetime.now().isoformat()

        # Recompute relationship value
        person["relationship_value"] = self.compute_relationship_value(person_id)

    # ============================================================
    # AUTHORITY LEARNING
    # Paper #17
    # ============================================================

    def record_preemption(
        self, preemptor_id: str, preempted_id: str, domain: str = "general"
    ) -> None:
        """
        Record authority preemption event.

        Paper #17: Authority learning through preemption.
        When high-authority person overrides, their authority strengthens.
        """
        # Strengthen preemptor authority
        if preemptor_id in self.persons:
            current = self.persons[preemptor_id]["authority"]
            self.persons[preemptor_id]["authority"] = min(1.0, current + 0.1)

            # Update node
            self.G.nodes[preemptor_id]["authority"] = self.persons[preemptor_id]["authority"]

        # Add/update relationship edge
        edge_data = self.G.edges.get((preemptor_id, preempted_id), {})
        preemption_count = edge_data.get("preemption_count", 0) + 1

        self.G.add_edge(
            preemptor_id,
            preempted_id,
            last_preemption=datetime.now().isoformat(),
            domain=domain,
            preemption_count=preemption_count,
            rel_type="HAS_AUTHORITY_OVER",
        )

    def infer_authority_from_role(self, role: str) -> float:
        """
        Infer initial authority from role title.

        Based on Paper #17 heuristics.
        """
        role_lower = role.lower()

        # C-level
        if any(x in role_lower for x in ["ceo", "cfo", "coo", "cto", "chief"]):
            return 0.9

        # VP level
        if any(x in role_lower for x in ["vp", "vice president", "svp", "evp"]):
            return 0.8

        # Director level
        if "director" in role_lower:
            return 0.7

        # Manager level
        if "manager" in role_lower or "lead" in role_lower:
            return 0.6

        # Senior level
        if "senior" in role_lower or "sr." in role_lower:
            return 0.55

        # Staff/Individual contributor
        if any(x in role_lower for x in ["analyst", "specialist", "coordinator"]):
            return 0.5

        # Junior
        if any(x in role_lower for x in ["junior", "jr.", "associate", "assistant"]):
            return 0.4

        # Intern
        if "intern" in role_lower:
            return 0.3

        return 0.5  # Default

    # ============================================================
    # CONFLICT RESOLUTION
    # Paper #17
    # ============================================================

    def resolve_conflict(
        self, person_a_id: str, person_b_id: str, guidance_a: str, guidance_b: str
    ) -> dict[str, Any]:
        """
        Resolve conflict between two people's guidance.

        Paper #17: Conflict resolution via authority-weighted triage.
        - If authority difference > 0.3: Auto-defer to higher
        - If <= 0.3: Escalate to human
        """
        person_a = self.persons.get(person_a_id)
        person_b = self.persons.get(person_b_id)
        auth_a: float = person_a.get("authority", 0.5) if person_a else 0.5
        auth_b: float = person_b.get("authority", 0.5) if person_b else 0.5

        diff = abs(auth_a - auth_b)

        if diff > 0.3:
            # Clear authority winner - auto-resolve
            winner_id = person_a_id if auth_a > auth_b else person_b_id
            winner_guidance = guidance_a if auth_a > auth_b else guidance_b
            loser_id = person_b_id if auth_a > auth_b else person_a_id

            return {
                "resolution": "auto_defer",
                "winner": winner_id,
                "guidance": winner_guidance,
                "authority_differential": diff,
                "reason": f"Authority differential {diff:.2f} exceeds 0.3 threshold",
            }
        else:
            # Comparable authority - escalate
            name_a = person_a.get("name", "Unknown") if person_a else "Unknown"
            name_b = person_b.get("name", "Unknown") if person_b else "Unknown"
            return {
                "resolution": "escalate",
                "reason": "comparable_authority",
                "authority_differential": diff,
                "person_a": {
                    "id": person_a_id,
                    "authority": auth_a,
                    "guidance": guidance_a,
                    "name": name_a,
                },
                "person_b": {
                    "id": person_b_id,
                    "authority": auth_b,
                    "guidance": guidance_b,
                    "name": name_b,
                },
            }

    # ============================================================
    # PRIORITY CALCULATION
    # Paper #17
    # ============================================================

    def calculate_priority(self, base_urgency: float, person_id: str) -> float:
        """
        Calculate priority incorporating relationship value.

        Paper #17: priority = 0.85 * urgency + 0.15 * relationship_value
        """
        relationship_value = self.compute_relationship_value(person_id)
        return 0.85 * base_urgency + 0.15 * relationship_value

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def serialize(self) -> str:
        """Serialize to JSON for Postgres storage"""
        return json.dumps(
            {
                "nodes": {n: dict(d) for n, d in self.G.nodes(data=True)},
                "edges": [(u, v, dict(d)) for u, v, d in self.G.edges(data=True)],
                "persons": self.persons,
            },
            default=str,
        )

    @classmethod
    def deserialize(cls, json_str: str) -> "SocialGraph":
        """Restore from Postgres JSON"""
        data = json.loads(json_str)
        graph = cls()

        for node_id, attrs in data.get("nodes", {}).items():
            graph.G.add_node(node_id, **attrs)

        for source, target, attrs in data.get("edges", []):
            graph.G.add_edge(source, target, **attrs)

        graph.persons = data.get("persons", {})
        return graph

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "nodes": dict(self.G.nodes(data=True)),
            "edges": list(self.G.edges(data=True)),
            "persons": self.persons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SocialGraph":
        """Restore from dictionary"""
        graph = cls()

        for node_id, attrs in data.get("nodes", {}).items():
            graph.G.add_node(node_id, **attrs)

        for source, target, attrs in data.get("edges", []):
            graph.G.add_edge(source, target, **attrs)

        graph.persons = data.get("persons", {})
        return graph
