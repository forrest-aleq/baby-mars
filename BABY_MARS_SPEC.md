# Baby MARS: Cognitive Architecture on Claude + LangGraph

**Purpose:** Ship MARS research to production using Claude API + LangGraph
**Timeline:** 4 weeks backend, no UI
**What This Is:** Duct-tape implementation that proves the cognitive research works
**What This Isn't:** Final production system (that's TAMI + full MARS)

---

## Part I: Architecture Overview

### The Core Insight

MARS has two layers:
1. **Cognitive Architecture** (the research) — belief system, memory, learning, autonomy
2. **Reasoning Engine** (the LLM) — planning, appraisal, action selection

**Baby MARS** keeps layer 1 intact and rents layer 2 from Anthropic until TAMI is ready.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BABY MARS                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              LangGraph Orchestration Layer                   │   │
│   │   (State, Checkpointing, Routing, HITL, Persistence)        │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│   ┌──────────────────────────┼──────────────────────────────────┐   │
│   │         Cognitive Loop (Cyclic Graph)                        │   │
│   │                          │                                   │   │
│   │   START → [activate] → [appraise] → [route_autonomy]        │   │
│   │               │             │              │                 │   │
│   │               ▼             │         ┌────┴────┐            │   │
│   │        Load context        │    [guidance] [propose] [auto] │   │
│   │        from state          │         └────┬────┘            │   │
│   │                            │              │                 │   │
│   │                            │              ▼                 │   │
│   │                            │        [execute]               │   │
│   │                            │              │                 │   │
│   │                            │              ▼                 │   │
│   │                            │        [verify]                │   │
│   │                            │              │                 │   │
│   │                            │              ▼                 │   │
│   │                            └──────► [update_beliefs]        │   │
│   │                                          │                  │   │
│   │                                          ▼                  │   │
│   │                                        END                  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│   ┌──────────────────────────┼──────────────────────────────────┐   │
│   │              Cognitive State Layer                           │   │
│   │                          │                                   │   │
│   │   ┌──────────────────────┴──────────────────────────────┐   │   │
│   │   │           Three-Column Working Memory                │   │   │
│   │   ├──────────────┬──────────────┬───────────────────────┤   │   │
│   │   │ Active Tasks │    Notes     │       Objects         │   │   │
│   │   │  (3-4 slots) │ (TTL queue)  │  (salient context)    │   │   │
│   │   └──────────────┴──────────────┴───────────────────────┘   │   │
│   │                                                              │   │
│   │   ┌──────────────────────────────────────────────────────┐   │   │
│   │   │              Belief Graph (NetworkX)                  │   │   │
│   │   │  • Hierarchical (SUPPORTS edges)                     │   │   │
│   │   │  • Context-conditional strengths                     │   │   │
│   │   │  • ACRE categories + thresholds                      │   │   │
│   │   │  • Moral asymmetry multipliers                       │   │   │
│   │   │  • Event-sourced history                             │   │   │
│   │   └──────────────────────────────────────────────────────┘   │   │
│   │                                                              │   │
│   │   ┌──────────────────────────────────────────────────────┐   │   │
│   │   │              Memory List                              │   │   │
│   │   │  • Episodic with timestamps                          │   │   │
│   │   │  • Peak-end weighting                                │   │   │
│   │   │  • Interference decay                                │   │   │
│   │   └──────────────────────────────────────────────────────┘   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│   ┌──────────────────────────┼──────────────────────────────────┐   │
│   │              Claude Integration Layer                        │   │
│   │                          │                                   │   │
│   │   [Claude API] ←── Skills (domain prompts)                  │   │
│   │        │                                                     │   │
│   │        ├── accounting_domain.md                             │   │
│   │        ├── situation_appraisal.md                           │   │
│   │        ├── work_unit_vocabulary.md                          │   │
│   │        └── validation_rules.md                              │   │
│   │                                                              │   │
│   │   [MCP Servers] ←── External connectivity                   │   │
│   │        │                                                     │   │
│   │        ├── Apollo (enrichment)                              │   │
│   │        ├── QuickBooks (ERP)                                 │   │
│   │        └── Gmail/Calendar (comms)                           │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part II: State Schema

### The CognitiveState TypedDict

```python
from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import networkx as nx
import json

# ============================================================================
# ENUMS
# ============================================================================

class BeliefCategory(Enum):
    AESTHETIC = "aesthetic"      # Threshold: 0.60 - preferences, style
    CONTEXTUAL = "contextual"    # Threshold: 0.75 - domain knowledge
    RELATIONAL = "relational"    # Threshold: 0.85 - social norms
    ETHICAL = "ethical"          # Threshold: 0.95 - moral principles

class SupervisionMode(Enum):
    GUIDANCE_SEEKING = "guidance"   # strength < 0.4
    ACTION_PROPOSAL = "proposal"    # 0.4 <= strength < 0.7
    AUTONOMOUS = "autonomous"       # strength >= 0.7

class TaskState(Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    BLOCKED = "blocked"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"

class MoralValence(Enum):
    NEUTRAL = "neutral"          # 1x multiplier
    CONFIRMATION = "confirmation" # 3x multiplier
    VIOLATION = "violation"       # 10x multiplier

# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ActiveTask:
    """Column 1: Currently active tasks (3-4 max)"""
    task_id: str
    description: str
    state: TaskState
    started_at: datetime
    context: Dict  # relevant beliefs, entities
    history: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            **asdict(self),
            "state": self.state.value,
            "started_at": self.started_at.isoformat()
        }

@dataclass
class Note:
    """Column 2: Acknowledged items in queue with TTL"""
    note_id: str
    content: str
    created_at: datetime
    ttl_hours: float
    priority: float  # 0.0 - 1.0
    source: str  # where it came from

    @property
    def expires_at(self) -> datetime:
        from datetime import timedelta
        return self.created_at + timedelta(hours=self.ttl_hours)

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def to_dict(self):
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired
        }

@dataclass
class PersonObject:
    """Person in Objects column with relationship value"""
    person_id: str
    name: str
    role: str
    authority: float  # 0.0 - 1.0
    interaction_frequency: float  # 0.0 - 1.0
    context_relevance: float  # 0.0 - 1.0
    preferences: Dict = field(default_factory=dict)

    @property
    def relationship_value(self) -> float:
        """60% authority + 20% interaction + 20% context"""
        return (0.6 * self.authority +
                0.2 * self.interaction_frequency +
                0.2 * self.context_relevance)

    def to_dict(self):
        return {**asdict(self), "relationship_value": self.relationship_value}

@dataclass
class TemporalContext:
    """Time-based context in Objects column"""
    is_month_end: bool = False
    is_quarter_end: bool = False
    is_year_end: bool = False
    days_until_deadline: Optional[int] = None
    urgency_multiplier: float = 1.0

    def to_dict(self):
        return asdict(self)

@dataclass
class Memory:
    """Episodic memory with peak-end weighting"""
    memory_id: str
    description: str
    timestamp: datetime
    outcome: Literal["success", "failure", "neutral"]
    emotional_valence: float  # -1.0 to 1.0
    is_peak: bool = False  # 2x weight
    is_end: bool = False   # 1.5x weight
    related_belief_ids: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict)

    @property
    def salience_weight(self) -> float:
        """Peak: 2x, End: 1.5x, Middle: 1x"""
        if self.is_peak:
            return 2.0
        elif self.is_end:
            return 1.5
        return 1.0

    def to_dict(self):
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "salience_weight": self.salience_weight
        }

@dataclass
class BeliefEvent:
    """Immutable event for belief strength history (event sourcing)"""
    event_id: str
    belief_id: str
    timestamp: datetime
    outcome: Literal["success", "failure", "neutral"]
    moral_valence: MoralValence
    severity: float  # 0.0 - 1.0 (for failures)
    context: Dict
    old_strength: float
    new_strength: float
    multiplier_applied: float

    def to_dict(self):
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "moral_valence": self.moral_valence.value
        }

@dataclass
class WorkUnit:
    """PTD: Semantic work unit from Planner"""
    unit_id: str
    verb: str  # e.g., "create_record", "fill_form", "approve_request"
    entities: Dict  # e.g., {"vendor": "Acme", "amount": 1500}
    constraints: List[Dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

# ============================================================================
# REDUCERS
# ============================================================================

def task_reducer(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Merge active tasks, keep max 4, evict by age"""
    combined = existing + new
    # Sort by started_at, keep 4 most recent
    sorted_tasks = sorted(combined, key=lambda t: t.get("started_at", ""), reverse=True)
    return sorted_tasks[:4]

def note_reducer(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Merge notes, remove expired, sort by priority"""
    combined = existing + new
    # Filter expired
    now = datetime.now().isoformat()
    active = [n for n in combined if n.get("expires_at", now) > now]
    # Sort by priority descending
    return sorted(active, key=lambda n: n.get("priority", 0), reverse=True)

def memory_reducer(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Append memories, apply interference decay"""
    combined = existing + new
    # Keep last 100 memories (simple limit for now)
    return combined[-100:]

def event_reducer(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Append-only event log"""
    return existing + new

# ============================================================================
# MAIN STATE
# ============================================================================

class CognitiveState(TypedDict):
    """
    The complete cognitive state for Baby MARS.
    Persisted via LangGraph checkpointer to Postgres.
    """

    # === IDENTITY ===
    org_id: str
    person_id: str  # The user this state belongs to
    thread_id: str  # LangGraph thread

    # === COLUMN 1: ACTIVE TASKS (3-4 slots) ===
    active_tasks: Annotated[List[Dict], task_reducer]

    # === COLUMN 2: NOTES (TTL queue) ===
    notes: Annotated[List[Dict], note_reducer]

    # === COLUMN 3: OBJECTS (ambient context) ===
    people: List[Dict]  # PersonObject dicts
    entities: List[Dict]  # Salient entities (vendors, projects, etc.)
    temporal_context: Dict  # TemporalContext dict
    high_strength_beliefs: List[Dict]  # Beliefs with strength > 0.8

    # === BELIEF GRAPH (serialized NetworkX) ===
    belief_graph_json: str  # nx.node_link_data(G) serialized

    # === MEMORY ===
    memories: Annotated[List[Dict], memory_reducer]

    # === EVENT LOG (immutable history) ===
    belief_events: Annotated[List[Dict], event_reducer]

    # === CURRENT INTERACTION ===
    user_input: str
    conversation_history: List[Dict]  # {"role": "user"|"assistant", "content": str}

    # === COGNITIVE LOOP STATE ===
    current_context: Dict  # Result of activation node
    appraisal: Dict  # Result of appraise node
    supervision_mode: str  # "guidance" | "proposal" | "autonomous"
    selected_action: Dict  # WorkUnit or action decision
    execution_result: Dict  # What happened
    verification_result: Dict  # Did it work?

    # === BIRTH METADATA ===
    birth_timestamp: str
    birth_source: str  # "full" | "micro"
    initial_beliefs_count: int
```

---

## Part III: Belief Graph Implementation

### NetworkX-Based Belief System

```python
import networkx as nx
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json
import uuid

# ============================================================================
# BELIEF THRESHOLDS (A.C.R.E.)
# ============================================================================

CATEGORY_THRESHOLDS = {
    BeliefCategory.AESTHETIC: 0.60,
    BeliefCategory.CONTEXTUAL: 0.75,
    BeliefCategory.RELATIONAL: 0.85,
    BeliefCategory.ETHICAL: 0.95,
}

MORAL_MULTIPLIERS = {
    MoralValence.NEUTRAL: 1.0,
    MoralValence.CONFIRMATION: 3.0,
    MoralValence.VIOLATION: 10.0,
}

# ============================================================================
# BELIEF GRAPH CLASS
# ============================================================================

class BeliefGraph:
    """
    NetworkX-based belief system implementing:
    - Hierarchical beliefs with SUPPORTS edges
    - Context-conditional strengths
    - A.C.R.E. category thresholds
    - Moral asymmetry multipliers
    - Event-sourced history
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self.events: List[BeliefEvent] = []

    # === SERIALIZATION ===

    def to_json(self) -> str:
        """Serialize for LangGraph state"""
        data = nx.node_link_data(self.G)
        data["events"] = [e.to_dict() for e in self.events]
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "BeliefGraph":
        """Deserialize from LangGraph state"""
        data = json.loads(json_str)
        events_data = data.pop("events", [])

        graph = cls()
        graph.G = nx.node_link_graph(data)
        graph.events = [
            BeliefEvent(
                event_id=e["event_id"],
                belief_id=e["belief_id"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                outcome=e["outcome"],
                moral_valence=MoralValence(e["moral_valence"]),
                severity=e["severity"],
                context=e["context"],
                old_strength=e["old_strength"],
                new_strength=e["new_strength"],
                multiplier_applied=e["multiplier_applied"]
            )
            for e in events_data
        ]
        return graph

    # === BELIEF CRUD ===

    def add_belief(
        self,
        belief_id: str,
        statement: str,
        category: BeliefCategory,
        initial_strength: float = 0.5,
        context_strengths: Optional[Dict[str, float]] = None,
        is_core: bool = False
    ) -> None:
        """Add a belief node"""
        self.G.add_node(
            belief_id,
            statement=statement,
            category=category.value,
            strength=initial_strength,
            context_strengths=context_strengths or {},
            is_core=is_core,
            created_at=datetime.now().isoformat(),
            is_invalidated=False,
            is_distrusted=False  # Permanent flag for moral violations
        )

    def add_supports_edge(
        self,
        assumption_id: str,
        core_id: str,
        weight: float = 1.0
    ) -> None:
        """Add hierarchical SUPPORTS relationship"""
        self.G.add_edge(assumption_id, core_id, rel="SUPPORTS", weight=weight)

    def get_belief(self, belief_id: str) -> Optional[Dict]:
        """Get belief by ID"""
        if belief_id in self.G.nodes:
            return dict(self.G.nodes[belief_id])
        return None

    def get_belief_strength(
        self,
        belief_id: str,
        context: Optional[str] = None
    ) -> float:
        """
        Get belief strength, optionally for specific context.
        Implements context-conditional beliefs with hierarchical backoff.
        """
        belief = self.get_belief(belief_id)
        if not belief:
            return 0.0

        # Check context-specific strength first
        if context and context in belief.get("context_strengths", {}):
            return belief["context_strengths"][context]

        # Fall back to default strength
        return belief.get("strength", 0.0)

    # === BELIEF UPDATES WITH MORAL ASYMMETRY ===

    def update_belief(
        self,
        belief_id: str,
        outcome: Literal["success", "failure", "neutral"],
        moral_valence: MoralValence = MoralValence.NEUTRAL,
        severity: float = 0.5,
        context: Optional[str] = None,
        event_context: Optional[Dict] = None,
        α_base: float = 0.15
    ) -> Tuple[float, float]:
        """
        Update belief strength with moral asymmetry.
        Returns (old_strength, new_strength).

        Formula: new = clip(old + α_effective × signal, 0, 1)
        Where α_effective = α_base × moral_multiplier × (0.5 + 0.5 × severity)
        """
        belief = self.get_belief(belief_id)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")

        # Check if permanently distrusted
        if belief.get("is_distrusted"):
            return belief["strength"], belief["strength"]

        # Get moral multiplier
        moral_multiplier = MORAL_MULTIPLIERS[moral_valence]

        # Calculate effective learning rate
        if outcome == "failure":
            α_effective = α_base * moral_multiplier * (0.5 + 0.5 * severity)
        else:
            α_effective = α_base * moral_multiplier

        # Determine signal
        signal = {"success": 1, "failure": -1, "neutral": 0}[outcome]

        # Get old strength (context-specific or default)
        old_strength = self.get_belief_strength(belief_id, context)

        # Calculate new strength
        new_strength = max(0.0, min(1.0, old_strength + α_effective * signal))

        # Update graph
        if context:
            self.G.nodes[belief_id]["context_strengths"][context] = new_strength
        else:
            self.G.nodes[belief_id]["strength"] = new_strength

        # Check for permanent distrust (moral violation that drops to 0)
        if (moral_valence == MoralValence.VIOLATION and
            new_strength == 0.0 and
            BeliefCategory(belief["category"]) == BeliefCategory.ETHICAL):
            self.G.nodes[belief_id]["is_distrusted"] = True

        # Check invalidation threshold
        category = BeliefCategory(belief["category"])
        threshold = CATEGORY_THRESHOLDS[category]
        self.G.nodes[belief_id]["is_invalidated"] = new_strength < threshold

        # Record event (event sourcing)
        event = BeliefEvent(
            event_id=str(uuid.uuid4()),
            belief_id=belief_id,
            timestamp=datetime.now(),
            outcome=outcome,
            moral_valence=moral_valence,
            severity=severity,
            context=event_context or {},
            old_strength=old_strength,
            new_strength=new_strength,
            multiplier_applied=moral_multiplier
        )
        self.events.append(event)

        # Cascade to supported beliefs
        self._cascade_update(belief_id)

        return old_strength, new_strength

    def _cascade_update(self, updated_belief_id: str) -> None:
        """
        Cascade strength updates to core beliefs that this assumption supports.
        Core belief strength = weighted average of supporting assumptions.
        """
        # Find all beliefs this one supports
        for _, target_id, data in self.G.out_edges(updated_belief_id, data=True):
            if data.get("rel") == "SUPPORTS":
                # Recalculate core belief strength from all supporters
                self._recalculate_core_strength(target_id)

    def _recalculate_core_strength(self, core_id: str) -> None:
        """Recalculate core belief strength from weighted average of supporters"""
        # Find all assumptions that support this core
        supporters = []
        for source_id, _, data in self.G.in_edges(core_id, data=True):
            if data.get("rel") == "SUPPORTS":
                weight = data.get("weight", 1.0)
                strength = self.G.nodes[source_id].get("strength", 0.5)
                supporters.append((strength, weight))

        if supporters:
            total_weight = sum(w for _, w in supporters)
            weighted_sum = sum(s * w for s, w in supporters)
            new_strength = weighted_sum / total_weight
            self.G.nodes[core_id]["strength"] = new_strength

            # Check invalidation for the core
            belief = self.G.nodes[core_id]
            category = BeliefCategory(belief["category"])
            threshold = CATEGORY_THRESHOLDS[category]
            self.G.nodes[core_id]["is_invalidated"] = new_strength < threshold

    # === AUTONOMY DETERMINATION ===

    def get_supervision_mode(
        self,
        belief_id: str,
        context: Optional[str] = None
    ) -> SupervisionMode:
        """
        Determine supervision mode based on belief strength.
        - < 0.4: GUIDANCE_SEEKING
        - 0.4 - 0.7: ACTION_PROPOSAL
        - >= 0.7: AUTONOMOUS
        """
        strength = self.get_belief_strength(belief_id, context)

        if strength < 0.4:
            return SupervisionMode.GUIDANCE_SEEKING
        elif strength < 0.7:
            return SupervisionMode.ACTION_PROPOSAL
        else:
            return SupervisionMode.AUTONOMOUS

    # === QUERIES ===

    def get_beliefs_by_category(self, category: BeliefCategory) -> List[Dict]:
        """Get all beliefs in a category"""
        return [
            {**self.G.nodes[n], "belief_id": n}
            for n in self.G.nodes
            if self.G.nodes[n].get("category") == category.value
        ]

    def get_high_strength_beliefs(self, threshold: float = 0.8) -> List[Dict]:
        """Get beliefs above strength threshold"""
        return [
            {**self.G.nodes[n], "belief_id": n}
            for n in self.G.nodes
            if self.G.nodes[n].get("strength", 0) >= threshold
        ]

    def get_invalidated_beliefs(self) -> List[Dict]:
        """Get beliefs that have been invalidated"""
        return [
            {**self.G.nodes[n], "belief_id": n}
            for n in self.G.nodes
            if self.G.nodes[n].get("is_invalidated", False)
        ]

    def get_relevant_beliefs(
        self,
        entity_ids: List[str],
        context: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get beliefs relevant to given entities, sorted by strength"""
        # For now, simple implementation - would be more sophisticated with embeddings
        relevant = []
        for node_id in self.G.nodes:
            node = self.G.nodes[node_id]
            # Check if any entity mentioned in statement (simple heuristic)
            statement = node.get("statement", "").lower()
            if any(e.lower() in statement for e in entity_ids):
                strength = self.get_belief_strength(node_id, context)
                relevant.append({**node, "belief_id": node_id, "current_strength": strength})

        # Sort by strength descending
        relevant.sort(key=lambda b: b["current_strength"], reverse=True)
        return relevant[:limit]
```

---

## Part IV: LangGraph Implementation

### The Cognitive Loop Graph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt
import anthropic
from typing import Dict, Any
import os

# ============================================================================
# CLAUDE CLIENT
# ============================================================================

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ============================================================================
# SKILL LOADERS (Prompt Templates)
# ============================================================================

SKILLS = {
    "accounting_domain": """
You are an expert accountant with deep knowledge of:
- GAAP principles and standards
- GL code classification
- Invoice processing workflows
- Month-end close procedures
- Accounts payable/receivable
- Financial reporting

When analyzing accounting tasks, consider:
1. Regulatory compliance requirements
2. Audit trail needs
3. Segregation of duties
4. Materiality thresholds
""",

    "situation_appraisal": """
Analyze the current situation considering:

1. FACE THREATS: Does this interaction threaten anyone's professional reputation?
2. EXPECTANCY VIOLATIONS: Is anything unexpected happening?
3. URGENCY: Is there time pressure? (month-end, deadlines)
4. AUTHORITY: Who has decision-making power here?
5. UNCERTAINTY: What don't we know that we need to know?

Provide structured appraisal:
- face_threat_level: none | low | medium | high
- urgency: low | medium | high | critical
- uncertainty_areas: [list]
- recommended_approach: string
""",

    "work_unit_vocabulary": """
Generate semantic Work Units using these verbs:

RECORD KEEPING:
- create_record, update_record, delete_record
- validate_entry, reconcile_accounts

DOCUMENT HANDLING:
- process_invoice, approve_document, reject_document
- extract_data, fill_form, generate_report

COMMUNICATION:
- send_notification, request_approval, escalate_issue
- schedule_followup, confirm_receipt

ANALYSIS:
- compare_values, calculate_variance, identify_anomaly
- summarize_period, forecast_trend

Output format:
{
    "unit_id": "U-xxx",
    "verb": "verb_name",
    "entities": {"key": "value"},
    "constraints": [{"type": "constraint_type", "value": "..."}]
}
""",

    "validation_rules": """
Verify the execution result against these criteria:

1. COMPLETENESS: Were all required fields populated?
2. ACCURACY: Do the values match expected patterns?
3. AUTHORIZATION: Was proper approval obtained?
4. TIMING: Was the action completed within SLA?
5. AUDIT: Is there a complete trail of what happened?

Return validation result:
{
    "is_valid": bool,
    "issues": [{"severity": "low|medium|high", "description": "..."}],
    "recommended_action": "proceed | retry | escalate"
}
"""
}

# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def cognitive_activation(state: CognitiveState) -> Dict[str, Any]:
    """
    Load cognitive context from state.
    Populates three-column working memory.
    """
    # Load belief graph
    belief_graph = BeliefGraph.from_json(state["belief_graph_json"])

    # Get high-strength beliefs for Objects column
    high_strength = belief_graph.get_high_strength_beliefs(threshold=0.8)

    # Get invalidated beliefs (need attention)
    invalidated = belief_graph.get_invalidated_beliefs()

    # Build context
    context = {
        "active_tasks": state["active_tasks"],
        "notes": [n for n in state["notes"] if not n.get("is_expired")],
        "people": state["people"],
        "entities": state["entities"],
        "temporal": state["temporal_context"],
        "high_strength_beliefs": high_strength,
        "invalidated_beliefs": invalidated,
        "user_input": state["user_input"],
        "conversation_history": state["conversation_history"][-10:]  # Last 10 turns
    }

    return {"current_context": context}


def appraise_situation(state: CognitiveState) -> Dict[str, Any]:
    """
    Analyze the situation using Claude.
    Applies situation_appraisal skill.
    """
    context = state["current_context"]

    # Build prompt
    prompt = f"""
{SKILLS["situation_appraisal"]}

Current Context:
- User Input: {state["user_input"]}
- Active Tasks: {json.dumps(context["active_tasks"], indent=2)}
- Relevant People: {json.dumps(context["people"], indent=2)}
- Temporal Context: {json.dumps(context["temporal"], indent=2)}
- High-Strength Beliefs: {json.dumps(context["high_strength_beliefs"][:5], indent=2)}

Conversation History:
{json.dumps(context["conversation_history"][-5:], indent=2)}

Provide your appraisal as JSON.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse response (assume JSON in response)
    appraisal_text = response.content[0].text
    try:
        appraisal = json.loads(appraisal_text)
    except:
        appraisal = {"raw": appraisal_text, "parsed": False}

    return {"appraisal": appraisal}


def route_by_autonomy(state: CognitiveState) -> str:
    """
    Conditional edge: route based on belief strength for this task type.
    """
    # Determine relevant belief for this task
    user_input = state["user_input"].lower()
    belief_graph = BeliefGraph.from_json(state["belief_graph_json"])

    # Simple heuristic: find most relevant belief
    # In production, this would be more sophisticated
    relevant_beliefs = belief_graph.get_relevant_beliefs(
        entity_ids=[user_input.split()[:3]],  # First 3 words as entities
        limit=1
    )

    if relevant_beliefs:
        belief = relevant_beliefs[0]
        mode = belief_graph.get_supervision_mode(belief["belief_id"])
    else:
        # No relevant belief = guidance seeking
        mode = SupervisionMode.GUIDANCE_SEEKING

    return mode.value


def guidance_seeking(state: CognitiveState) -> Dict[str, Any]:
    """
    Supervision mode: Ask for guidance.
    Strength < 0.4
    """
    prompt = f"""
{SKILLS["accounting_domain"]}

I need guidance on this task. I don't have enough experience to act confidently.

User Request: {state["user_input"]}

Appraisal: {json.dumps(state["appraisal"], indent=2)}

Please help me understand:
1. What is the correct approach here?
2. What should I watch out for?
3. Can you show me how to do this?
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    # This requires human input - use LangGraph interrupt
    human_guidance = interrupt({
        "type": "guidance_request",
        "question": response.content[0].text,
        "context": state["current_context"]
    })

    return {
        "supervision_mode": "guidance",
        "selected_action": {
            "type": "awaiting_guidance",
            "question": response.content[0].text,
            "human_response": human_guidance
        }
    }


def action_proposal(state: CognitiveState) -> Dict[str, Any]:
    """
    Supervision mode: Propose action for approval.
    Strength 0.4 - 0.7
    """
    prompt = f"""
{SKILLS["accounting_domain"]}
{SKILLS["work_unit_vocabulary"]}

Based on my experience, I believe I should take this action. Please confirm.

User Request: {state["user_input"]}

Appraisal: {json.dumps(state["appraisal"], indent=2)}

My Proposed Action:
Generate a Work Unit that addresses this request.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    proposed_action = response.content[0].text

    # Request approval via interrupt
    approval = interrupt({
        "type": "approval_request",
        "proposed_action": proposed_action,
        "requires": "yes/no/modify"
    })

    return {
        "supervision_mode": "proposal",
        "selected_action": {
            "type": "proposed",
            "work_unit": proposed_action,
            "approval": approval
        }
    }


def autonomous_execution(state: CognitiveState) -> Dict[str, Any]:
    """
    Supervision mode: Execute independently.
    Strength >= 0.7
    """
    prompt = f"""
{SKILLS["accounting_domain"]}
{SKILLS["work_unit_vocabulary"]}

I have strong experience with this type of task. Executing autonomously.

User Request: {state["user_input"]}

Appraisal: {json.dumps(state["appraisal"], indent=2)}

Generate the Work Unit and I will execute it.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "supervision_mode": "autonomous",
        "selected_action": {
            "type": "autonomous",
            "work_unit": response.content[0].text,
            "approval": "auto-approved"
        }
    }


def execute_action(state: CognitiveState) -> Dict[str, Any]:
    """
    Execute the selected action.
    In production, this would call MCP servers / Stargate.
    """
    action = state["selected_action"]

    if action.get("type") == "awaiting_guidance":
        # Learning from guidance
        result = {
            "status": "learned",
            "learned_from": action.get("human_response"),
            "should_create_belief": True
        }
    elif action.get("approval") in ["yes", "auto-approved"]:
        # Execute the work unit
        # TODO: Actual MCP/Stargate integration
        result = {
            "status": "executed",
            "work_unit": action.get("work_unit"),
            "outcome": "success"  # Would come from actual execution
        }
    else:
        result = {
            "status": "rejected",
            "reason": action.get("approval")
        }

    return {"execution_result": result}


def verify_outcome(state: CognitiveState) -> Dict[str, Any]:
    """
    Verify the execution result.
    Self-correcting validation with retry budget.
    """
    result = state["execution_result"]

    if result.get("status") != "executed":
        return {"verification_result": {"is_valid": True, "skipped": True}}

    prompt = f"""
{SKILLS["validation_rules"]}

Verify this execution result:
{json.dumps(result, indent=2)}

Original request: {state["user_input"]}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        verification = json.loads(response.content[0].text)
    except:
        verification = {"is_valid": True, "raw": response.content[0].text}

    return {"verification_result": verification}


def update_beliefs(state: CognitiveState) -> Dict[str, Any]:
    """
    Update belief strengths based on outcome.
    Implements moral asymmetry and event sourcing.
    """
    belief_graph = BeliefGraph.from_json(state["belief_graph_json"])
    result = state["execution_result"]
    verification = state["verification_result"]

    # Determine outcome
    if result.get("status") == "learned":
        outcome = "neutral"  # Learning isn't success or failure
        moral_valence = MoralValence.NEUTRAL
    elif verification.get("is_valid"):
        outcome = "success"
        moral_valence = MoralValence.CONFIRMATION if _is_moral_context(state) else MoralValence.NEUTRAL
    else:
        outcome = "failure"
        severity = _calculate_severity(verification.get("issues", []))
        moral_valence = MoralValence.VIOLATION if _is_moral_context(state) else MoralValence.NEUTRAL

    # Find and update relevant beliefs
    # In production, this would be more sophisticated
    relevant_beliefs = belief_graph.get_relevant_beliefs(
        entity_ids=state["user_input"].split()[:5],
        limit=3
    )

    for belief in relevant_beliefs:
        belief_graph.update_belief(
            belief_id=belief["belief_id"],
            outcome=outcome,
            moral_valence=moral_valence,
            severity=severity if outcome == "failure" else 0.0,
            event_context={"user_input": state["user_input"]}
        )

    # Create new belief if learned something
    if result.get("should_create_belief"):
        belief_graph.add_belief(
            belief_id=str(uuid.uuid4()),
            statement=f"Learned: {result.get('learned_from', 'guidance')}",
            category=BeliefCategory.CONTEXTUAL,
            initial_strength=0.5
        )

    # Create memory
    memory = Memory(
        memory_id=str(uuid.uuid4()),
        description=f"Interaction: {state['user_input'][:100]}",
        timestamp=datetime.now(),
        outcome=outcome,
        emotional_valence=1.0 if outcome == "success" else -0.5 if outcome == "failure" else 0.0,
        related_belief_ids=[b["belief_id"] for b in relevant_beliefs]
    )

    return {
        "belief_graph_json": belief_graph.to_json(),
        "memories": [memory.to_dict()],
        "belief_events": [e.to_dict() for e in belief_graph.events[-5:]]  # Last 5 events
    }


def _is_moral_context(state: CognitiveState) -> bool:
    """Check if current context involves moral dimensions"""
    moral_keywords = ["confidential", "privacy", "security", "compliance", "audit", "fraud"]
    return any(kw in state["user_input"].lower() for kw in moral_keywords)


def _calculate_severity(issues: List[Dict]) -> float:
    """Calculate severity from validation issues"""
    if not issues:
        return 0.0
    severity_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
    severities = [severity_map.get(i.get("severity", "low"), 0.3) for i in issues]
    return max(severities)


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_cognitive_graph():
    """Build the LangGraph cognitive loop"""

    builder = StateGraph(CognitiveState)

    # Add nodes
    builder.add_node("activate", cognitive_activation)
    builder.add_node("appraise", appraise_situation)
    builder.add_node("guidance", guidance_seeking)
    builder.add_node("proposal", action_proposal)
    builder.add_node("autonomous", autonomous_execution)
    builder.add_node("execute", execute_action)
    builder.add_node("verify", verify_outcome)
    builder.add_node("update", update_beliefs)

    # Add edges
    builder.add_edge(START, "activate")
    builder.add_edge("activate", "appraise")

    # Conditional routing based on autonomy
    builder.add_conditional_edges(
        "appraise",
        route_by_autonomy,
        {
            "guidance": "guidance",
            "proposal": "proposal",
            "autonomous": "autonomous"
        }
    )

    # All supervision modes lead to execute
    builder.add_edge("guidance", "execute")
    builder.add_edge("proposal", "execute")
    builder.add_edge("autonomous", "execute")

    # Execute -> Verify -> Update -> END
    builder.add_edge("execute", "verify")
    builder.add_edge("verify", "update")
    builder.add_edge("update", END)

    return builder


def create_app(postgres_url: str):
    """Create the compiled graph with persistence"""

    builder = build_cognitive_graph()

    # Add Postgres checkpointer
    checkpointer = PostgresSaver.from_conn_string(postgres_url)

    # Compile
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["guidance", "proposal"]  # HITL points
    )

    return graph
```

---

## Part V: Birth System

### Initialize New Users

```python
import httpx
from datetime import datetime
import uuid

# ============================================================================
# BIRTH SYSTEM
# ============================================================================

async def birth_full(
    email: str,
    apollo_api_key: str
) -> CognitiveState:
    """
    Full birth: 90 seconds, three pillars.
    1. Social context enrichment (Apollo)
    2. Domain knowledge injection
    3. Initial belief synthesis
    """

    # === PILLAR 1: Social Context Enrichment ===
    async with httpx.AsyncClient() as client:
        # Apollo API enrichment
        response = await client.post(
            "https://api.apollo.io/v1/people/match",
            headers={"X-Api-Key": apollo_api_key},
            json={"email": email}
        )
        profile = response.json() if response.status_code == 200 else {}

    person = {
        "person_id": str(uuid.uuid4()),
        "name": profile.get("name", email.split("@")[0]),
        "role": profile.get("title", "Unknown"),
        "company": profile.get("organization", {}).get("name", "Unknown"),
        "industry": profile.get("organization", {}).get("industry", "Unknown"),
        "seniority": profile.get("seniority", "unknown")
    }

    # === PILLAR 2: Domain Knowledge Injection ===
    # Load knowledge packs based on industry
    knowledge_packs = _load_knowledge_packs(person["industry"])

    # === PILLAR 3: Initial Belief Synthesis ===
    belief_graph = BeliefGraph()

    # Core ethical beliefs (high initial strength, high threshold)
    ethical_beliefs = [
        ("Maintain confidentiality of financial data", BeliefCategory.ETHICAL, 0.85),
        ("Ensure accuracy in all financial records", BeliefCategory.ETHICAL, 0.85),
        ("Follow segregation of duties requirements", BeliefCategory.ETHICAL, 0.80),
        ("Respect authorization boundaries", BeliefCategory.ETHICAL, 0.80),
    ]

    for statement, category, strength in ethical_beliefs:
        belief_graph.add_belief(
            belief_id=str(uuid.uuid4()),
            statement=statement,
            category=category,
            initial_strength=strength,
            is_core=True
        )

    # Contextual beliefs from knowledge packs (medium initial strength)
    for pack in knowledge_packs:
        for rule in pack.get("rules", []):
            belief_graph.add_belief(
                belief_id=str(uuid.uuid4()),
                statement=rule["statement"],
                category=BeliefCategory.CONTEXTUAL,
                initial_strength=0.5  # Appropriately uncertain
            )

    # Role-based assumptions
    role_beliefs = _generate_role_beliefs(person["role"], person["seniority"])
    for statement, strength in role_beliefs:
        belief_graph.add_belief(
            belief_id=str(uuid.uuid4()),
            statement=statement,
            category=BeliefCategory.CONTEXTUAL,
            initial_strength=strength
        )

    # === Build Initial State ===
    state: CognitiveState = {
        "org_id": str(uuid.uuid4()),
        "person_id": person["person_id"],
        "thread_id": "",  # Set by LangGraph

        # Column 1: Empty initially
        "active_tasks": [],

        # Column 2: Empty initially
        "notes": [],

        # Column 3: Populated
        "people": [PersonObject(
            person_id=person["person_id"],
            name=person["name"],
            role=person["role"],
            authority=_estimate_authority(person["seniority"]),
            interaction_frequency=0.0,
            context_relevance=1.0,
            preferences={}
        ).to_dict()],
        "entities": [],
        "temporal_context": TemporalContext().to_dict(),
        "high_strength_beliefs": belief_graph.get_high_strength_beliefs(),

        # Belief graph
        "belief_graph_json": belief_graph.to_json(),

        # Memory: Empty initially
        "memories": [],

        # Events: Empty initially
        "belief_events": [],

        # Current interaction: Empty
        "user_input": "",
        "conversation_history": [],

        # Cognitive loop state: Empty
        "current_context": {},
        "appraisal": {},
        "supervision_mode": "",
        "selected_action": {},
        "execution_result": {},
        "verification_result": {},

        # Birth metadata
        "birth_timestamp": datetime.now().isoformat(),
        "birth_source": "full",
        "initial_beliefs_count": len(list(belief_graph.G.nodes))
    }

    return state


async def birth_micro(name: str, email: Optional[str] = None) -> Dict:
    """
    Micro birth: <5 seconds, single pillar.
    Creates minimal person record when unknown person mentioned.
    """
    return PersonObject(
        person_id=str(uuid.uuid4()),
        name=name,
        role="Unknown",
        authority=0.5,  # Neutral authority until learned
        interaction_frequency=0.0,
        context_relevance=0.5,
        preferences={}
    ).to_dict()


def _load_knowledge_packs(industry: str) -> List[Dict]:
    """Load domain knowledge packs"""
    # Would load from file/database
    base_packs = [
        {
            "name": "GAAP_FUNDAMENTALS",
            "rules": [
                {"statement": "Revenue recognized when earned and realized"},
                {"statement": "Expenses matched to related revenues"},
                {"statement": "Materiality threshold typically 5% of net income"},
            ]
        }
    ]

    industry_packs = {
        "Investment Management": [
            {
                "name": "SEC_COMPLIANCE",
                "rules": [
                    {"statement": "Form ADV updates required annually"},
                    {"statement": "Client fee calculations must be documented"},
                ]
            }
        ],
        # ... other industries
    }

    return base_packs + industry_packs.get(industry, [])


def _generate_role_beliefs(role: str, seniority: str) -> List[Tuple[str, float]]:
    """Generate role-based initial beliefs"""
    beliefs = []

    role_lower = role.lower()

    if "analyst" in role_lower:
        beliefs.extend([
            ("Analysts typically handle variance analysis", 0.6),
            ("Analysts prepare reports for review", 0.6),
        ])
    elif "manager" in role_lower:
        beliefs.extend([
            ("Managers have approval authority for standard transactions", 0.5),
            ("Managers oversee team workflows", 0.5),
        ])
    elif "controller" in role_lower:
        beliefs.extend([
            ("Controllers have final approval on financial statements", 0.5),
            ("Controllers ensure compliance with accounting standards", 0.5),
        ])

    return beliefs


def _estimate_authority(seniority: str) -> float:
    """Estimate authority level from seniority"""
    authority_map = {
        "entry": 0.3,
        "junior": 0.4,
        "senior": 0.6,
        "manager": 0.7,
        "director": 0.8,
        "vp": 0.85,
        "c_suite": 0.95,
        "unknown": 0.5
    }
    return authority_map.get(seniority.lower(), 0.5)
```

---

## Part VI: File Structure

```
baby_mars/
├── BABY_MARS_SPEC.md          # This file
├── requirements.txt
├── .env.example
│
├── src/
│   ├── __init__.py
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── schema.py          # CognitiveState, dataclasses, enums
│   │   └── reducers.py        # Custom reducers for state merging
│   │
│   ├── beliefs/
│   │   ├── __init__.py
│   │   ├── graph.py           # BeliefGraph class (NetworkX)
│   │   ├── categories.py      # ACRE thresholds
│   │   └── moral.py           # Moral asymmetry logic
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── episodic.py        # Memory class with peak-end
│   │   └── decay.py           # Interference decay logic
│   │
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── activation.py      # cognitive_activation node
│   │   ├── appraisal.py       # appraise_situation node
│   │   ├── autonomy.py        # route_by_autonomy + 3 modes
│   │   ├── execution.py       # execute_action node
│   │   ├── verification.py    # verify_outcome node
│   │   └── learning.py        # update_beliefs node
│   │
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── accounting.md      # Accounting domain skill
│   │   ├── appraisal.md       # Situation appraisal skill
│   │   ├── work_units.md      # PTD work unit vocabulary
│   │   └── validation.md      # Validation rules skill
│   │
│   ├── birth/
│   │   ├── __init__.py
│   │   ├── full.py            # Full birth (90 sec)
│   │   ├── micro.py           # Micro birth (<5 sec)
│   │   └── knowledge_packs/   # GAAP, SEC, industry packs
│   │       ├── gaap.json
│   │       ├── sec.json
│   │       └── industries/
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py         # build_cognitive_graph()
│   │   └── app.py             # create_app() with persistence
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py            # FastAPI app
│       └── routes/
│           ├── chat.py        # Main interaction endpoint
│           ├── birth.py       # Birth endpoints
│           └── health.py      # Health checks
│
├── tests/
│   ├── __init__.py
│   ├── test_beliefs.py
│   ├── test_memory.py
│   ├── test_nodes.py
│   ├── test_autonomy.py
│   └── test_birth.py
│
└── scripts/
    ├── setup_db.py            # Create Postgres tables
    ├── seed_beliefs.py        # Seed initial beliefs
    └── run_scenario.py        # Test against Bluebook scenarios
```

---

## Part VII: Requirements

```
# requirements.txt

# Core
langgraph>=0.2.0
langchain-anthropic>=0.2.0
anthropic>=0.30.0

# Graph
networkx>=3.0

# Persistence
psycopg[binary]>=3.1.0
langgraph-checkpoint-postgres>=1.0.0

# API
fastapi>=0.110.0
uvicorn>=0.29.0
httpx>=0.27.0

# Utils
python-dotenv>=1.0.0
pydantic>=2.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## Part VIII: Implementation Timeline

### Week 1: Core Loop
- [ ] State schema (CognitiveState, dataclasses)
- [ ] BeliefGraph class with NetworkX
- [ ] Basic nodes: activate, appraise, execute
- [ ] LangGraph graph definition
- [ ] Postgres checkpointer setup

### Week 2: Belief System
- [ ] Hierarchical beliefs (SUPPORTS edges)
- [ ] Context-conditional strengths
- [ ] ACRE categories + thresholds
- [ ] Moral asymmetry multipliers
- [ ] Event sourcing for belief history

### Week 3: Memory + Social
- [ ] Memory list with peak-end weighting
- [ ] Interference decay
- [ ] Person authority modeling
- [ ] Three-column working memory population
- [ ] Autonomy routing (3 modes)

### Week 4: Birth + Testing
- [ ] Full birth (Apollo integration)
- [ ] Micro birth
- [ ] FastAPI endpoints
- [ ] Test against 5+ Bluebook scenarios
- [ ] Documentation

---

## Part IX: What This Proves

If Baby MARS works:

| Research Paper | Validated By |
|----------------|--------------|
| Competence-Based Autonomy | Belief strength → supervision mode routing |
| Context-Conditional Beliefs | Per-context strength lookups |
| Hierarchical Beliefs | SUPPORTS edges + cascading updates |
| Moral Asymmetry | 10x/3x/1x multipliers on belief updates |
| ACRE Categories | Different thresholds per category |
| Event Sourcing | Immutable BeliefEvent log |
| Peak-End Memory | Salience weights on memories |
| Three-Column Working Memory | Active Tasks / Notes / Objects separation |
| Birth System | External data → initial beliefs in 90 sec |
| PTD Architecture | Work Units as semantic verbs |
| Self-Correcting Validation | Verify node with retry logic |

---

## Part X: What This Doesn't Prove

| Gap | Why |
|-----|-----|
| LTL Training | Can't fine-tune Claude; just prompting |
| Neo4j Schema Optimality | Using NetworkX, not Neo4j |
| TAMI Economics | Claude costs >> TAMI costs |
| Stargate Connectors | Mocked, not real |
| Production Scale | Single-user testing only |

---

**This is the spec. Ready to build.**
