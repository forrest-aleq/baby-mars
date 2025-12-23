# Baby MARS: Production Cognitive Architecture
## Claude + LangGraph Implementation of Aleq Research

**Version:** 0.1.0
**Status:** Development Blueprint
**Target:** 4-Week Build

---

## Executive Summary

Baby MARS is a production-ready implementation of the Aleq cognitive research using off-the-shelf components:

| MARS Component | Baby MARS Implementation |
|----------------|--------------------------|
| TAMI (trained LLM) | Claude API with domain Skills |
| Neo4j Cognitive Graph | NetworkX + Postgres JSON |
| LangGraph Orchestration | LangGraph 1.0 (unchanged) |
| Stargate Connectors | MCP Servers |
| Planner-Translator-Driver | Claude + MCP + PTC |
| Birth System | Claude Skill + Apollo API |

**What we're proving:** The 20 research papers work in production. The cognitive loop produces better outcomes than stateless prompting.

---

## Part I: State Architecture

### 1.1 The Three-Column Working Memory

LangGraph state schema implementing Paper #8 (Three-Column Working Memory):

```python
from typing import TypedDict, Annotated, Literal, Optional
from datetime import datetime, timedelta
from operator import add
import json

# ============================================================
# COLUMN 1: ACTIVE TASKS (3-4 slots)
# ============================================================

class TaskState(TypedDict):
    status: Literal["planning", "executing", "blocked", "awaiting_input", "complete"]
    current_step: Optional[str]
    blocking_reason: Optional[str]
    progress: float  # 0.0-1.0

class ActiveTask(TypedDict):
    task_id: str
    description: str
    state: TaskState
    dependencies: list[str]
    history: list[dict]  # TaskEvents
    started_at: str  # ISO datetime
    estimated_duration_minutes: Optional[int]
    priority: float  # 0.0-1.0
    difficulty_level: int  # 1-5

# ============================================================
# COLUMN 2: NOTES (acknowledged queue with TTL)
# ============================================================

class Note(TypedDict):
    note_id: str
    content: str
    created_at: str  # ISO datetime
    ttl_hours: int
    priority: float
    source: Literal["user", "system", "inferred"]
    context: dict  # Relevant context when noted

# ============================================================
# COLUMN 3: OBJECTS (ambient context)
# ============================================================

class PersonObject(TypedDict):
    person_id: str
    name: str
    role: str
    authority: float  # 0.0-1.0 (Paper #17)
    interaction_strength: float
    context_relevance: float
    relationship_value: float  # 0.6*authority + 0.2*interaction + 0.2*context
    preferences: list[str]
    last_interaction: str

class EntityObject(TypedDict):
    entity_id: str
    name: str
    entity_type: str
    salience: float
    properties: dict

class TemporalContext(TypedDict):
    current_time: str
    is_month_end: bool
    is_quarter_end: bool
    is_year_end: bool
    days_until_deadline: Optional[int]
    urgency_multiplier: float  # 1.0 normal, 1.5 elevated, 2.0 critical

class Objects(TypedDict):
    people: list[PersonObject]
    entities: list[EntityObject]
    beliefs: list[dict]  # BeliefState objects
    knowledge: list[dict]  # Relevant workflows/rules
    goals: list[dict]  # Active goals
    temporal: TemporalContext


# ============================================================
# BELIEF SYSTEM (Papers #1, #4, #9, #10, #11, #12)
# ============================================================

class BeliefState(TypedDict):
    """Context-conditional belief with hierarchical support"""
    belief_id: str
    statement: str
    category: Literal["ethical", "relational", "procedural", "contextual", "aesthetic"]

    # Core strength (Paper #1)
    strength: float  # 0.0-1.0

    # Context conditioning (Paper #4)
    context_key: str  # e.g., "ClientA|month-end|>10K"
    context_states: dict[str, dict]  # context_key -> {strength, last_updated, success_count, failure_count}

    # Hierarchy (Paper #11)
    supports: list[str]  # belief_ids this belief supports
    supported_by: list[str]  # belief_ids that support this belief
    support_weights: dict[str, float]  # belief_id -> weight

    # Temporal (Paper #12)
    last_updated: str
    success_count: int
    failure_count: int
    is_end_memory_influenced: bool
    peak_intensity: float

    # Category thresholds (Paper #10 - A.C.R.E.)
    invalidation_threshold: float  # 0.95 for ethical, 0.60 for aesthetic

    # Moral asymmetry (Paper #9)
    is_distrusted: bool  # Permanent circuit breaker
    moral_violation_count: int

# Learning rate multipliers (Paper #9)
CATEGORY_MULTIPLIERS = {
    "ethical": {"success": 3.0, "failure": 10.0},
    "relational": {"success": 2.0, "failure": 5.0},
    "procedural": {"success": 1.0, "failure": 2.0},
    "contextual": {"success": 1.0, "failure": 1.5},
    "aesthetic": {"success": 1.0, "failure": 1.0},
}

# Invalidation thresholds (Paper #10)
INVALIDATION_THRESHOLDS = {
    "ethical": 0.95,
    "relational": 0.90,
    "procedural": 0.75,
    "contextual": 0.70,
    "aesthetic": 0.60,
}


# ============================================================
# MEMORY SYSTEM (Papers #12, #13)
# ============================================================

class Memory(TypedDict):
    memory_id: str
    description: str
    timestamp: str
    outcome: Literal["success", "failure", "neutral", "validation", "correction"]
    emotional_intensity: float  # 0.0-1.0 (Paper #12)
    is_end_memory: bool  # Paper #12 - peak-end rule
    related_beliefs: list[str]
    related_persons: list[str]
    context_key: str
    difficulty_level: int


# ============================================================
# SOCIAL GRAPH (Paper #17)
# ============================================================

class PersonRelationship(TypedDict):
    """Person-to-person relationship for authority and conflict resolution"""
    source_person_id: str
    target_person_id: str
    authority_differential: float  # How much source outranks target
    domain: str  # Where this authority applies
    interaction_count: int
    last_preemption: Optional[str]  # When source overrode target's guidance


# ============================================================
# MAIN STATE OBJECT
# ============================================================

def task_reducer(existing: list[ActiveTask], new: list[ActiveTask]) -> list[ActiveTask]:
    """Keep max 4 active tasks, priority-based replacement"""
    combined = existing + new
    combined.sort(key=lambda t: t.get("priority", 0), reverse=True)
    return combined[:4]

def note_reducer(existing: list[Note], new: list[Note]) -> list[Note]:
    """Merge notes, expire TTL-exceeded ones"""
    from datetime import datetime, timedelta
    now = datetime.now()
    combined = existing + new
    valid = []
    for note in combined:
        created = datetime.fromisoformat(note["created_at"])
        ttl = timedelta(hours=note["ttl_hours"])
        if now - created < ttl:
            valid.append(note)
    return valid

class BabyMARSState(TypedDict):
    """Complete cognitive state for Baby MARS"""

    # Identity
    thread_id: str
    org_id: str
    user_id: str

    # Three-Column Working Memory (Paper #8)
    active_tasks: Annotated[list[ActiveTask], task_reducer]
    notes: Annotated[list[Note], note_reducer]
    objects: Objects

    # Conversation
    messages: Annotated[list, add]  # LangGraph message format
    current_turn: int

    # Cognitive Loop State
    current_context_key: str
    activated_beliefs: list[BeliefState]
    appraisal: Optional[dict]
    selected_action: Optional[dict]

    # Autonomy (Paper #1)
    supervision_mode: Literal["guidance_seeking", "action_proposal", "autonomous"]
    belief_strength_for_action: float

    # Goal State
    active_goals: list[dict]
    goal_conflict_detected: bool

    # Social Context (Paper #17)
    current_person: Optional[PersonObject]
    authority_context: dict

    # Validation (Paper #3)
    validation_results: list[dict]
    retry_count: int
    max_retries: int

    # Event Log (Paper #7 - immutable audit)
    events: Annotated[list[dict], add]
```

---

## Part II: Graph Persistence Layer

### 2.1 NetworkX for Belief Hierarchy

The belief DAG requires graph traversal for cascading updates (Paper #11). We use NetworkX in-memory, serialized to Postgres:

```python
import networkx as nx
import json
from typing import Optional

class BeliefGraph:
    """
    NetworkX-backed belief hierarchy with cascading updates.
    Serializes to Postgres JSON for persistence.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self.beliefs: dict[str, BeliefState] = {}

    def add_belief(self, belief: BeliefState):
        """Add belief node to graph"""
        self.beliefs[belief["belief_id"]] = belief
        self.G.add_node(
            belief["belief_id"],
            category=belief["category"],
            strength=belief["strength"]
        )

    def add_support_relationship(
        self,
        supporter_id: str,
        supported_id: str,
        weight: float
    ):
        """Add SUPPORTS edge (Paper #11)"""
        self.G.add_edge(
            supporter_id,
            supported_id,
            weight=weight,
            rel_type="SUPPORTS"
        )

    def cascade_strength_update(self, belief_id: str, new_strength: float):
        """
        Update belief strength and cascade to all supported beliefs.
        Paper #11: Hierarchical Beliefs with Cascading Strength Updates
        """
        old_strength = self.beliefs[belief_id]["strength"]
        self.beliefs[belief_id]["strength"] = new_strength
        self.G.nodes[belief_id]["strength"] = new_strength

        # Find all beliefs this one supports
        for _, supported_id, data in self.G.out_edges(belief_id, data=True):
            if data.get("rel_type") == "SUPPORTS":
                weight = data.get("weight", 1.0)
                supported_belief = self.beliefs[supported_id]

                # Compute new effective strength
                # effective = intrinsic + Σ(support_contribution)
                # contribution = source_strength × weight × (1 - intrinsic)
                intrinsic = supported_belief["strength"]
                old_contribution = old_strength * weight * (1 - intrinsic)
                new_contribution = new_strength * weight * (1 - intrinsic)

                delta = new_contribution - old_contribution
                new_effective = min(1.0, max(0.0, intrinsic + delta))

                # Recursive cascade
                self.cascade_strength_update(supported_id, new_effective)

    def resolve_belief_for_context(
        self,
        belief_id: str,
        context_key: str
    ) -> Optional[dict]:
        """
        Paper #4: Context-Conditional Beliefs
        Backoff from specific to general context.
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None

        context_states = belief.get("context_states", {})

        # Try exact match first
        if context_key in context_states:
            return context_states[context_key]

        # Build backoff ladder
        parts = context_key.split("|")
        for i in range(len(parts) - 1, 0, -1):
            generalized = "|".join(parts[:i] + ["*"] * (len(parts) - i))
            if generalized in context_states:
                return context_states[generalized]

        # Global default
        global_key = "|".join(["*"] * len(parts))
        return context_states.get(global_key)

    def get_autonomy_level(self, belief_id: str, context_key: str) -> str:
        """
        Paper #1: Competence-Based Autonomy
        Map belief strength to supervision mode.
        """
        context_state = self.resolve_belief_for_context(belief_id, context_key)

        if not context_state:
            return "guidance_seeking"

        strength = context_state.get("strength", 0.0)

        if strength < 0.4:
            return "guidance_seeking"
        elif strength < 0.7:
            return "action_proposal"
        else:
            return "autonomous"

    def update_belief_from_outcome(
        self,
        belief_id: str,
        context_key: str,
        outcome: str,
        difficulty_level: int,
        is_end_memory: bool = False,
        emotional_intensity: float = 0.5
    ) -> dict:
        """
        Update belief strength from outcome.
        Implements Papers #1, #9, #12
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return {"error": "Belief not found"}

        category = belief["category"]
        context_states = belief.get("context_states", {})

        # Get or create context state
        if context_key not in context_states:
            context_states[context_key] = {
                "strength": 0.5,  # Start uncertain
                "last_updated": datetime.now().isoformat(),
                "success_count": 0,
                "failure_count": 0,
                "last_outcome": None
            }

        state = context_states[context_key]
        old_strength = state["strength"]

        # Outcome signal
        outcome_signals = {
            "success": 1.0,
            "validation": 1.0,
            "neutral": 0.0,
            "failure": -1.0,
            "correction": -1.0
        }
        signal = outcome_signals.get(outcome, 0.0)

        # Category multiplier (Paper #9: Moral Asymmetry)
        multipliers = CATEGORY_MULTIPLIERS[category]
        if signal > 0:
            category_mult = multipliers["success"]
        else:
            category_mult = multipliers["failure"]

        # Peak-End multiplier (Paper #12)
        peak_end_mult = 1.0
        if is_end_memory or emotional_intensity > 0.7:
            peak_end_mult = 3.0

        # Difficulty weight (harder tasks = stronger signal)
        difficulty_weights = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.5, 5: 2.0}
        difficulty_mult = difficulty_weights.get(difficulty_level, 1.0)

        # EMA update
        alpha = 0.15  # Learning rate
        total_signal = signal * category_mult * peak_end_mult * difficulty_mult
        new_strength = max(0.0, min(1.0,
            old_strength + alpha * total_signal
        ))

        # Update state
        state["strength"] = new_strength
        state["last_updated"] = datetime.now().isoformat()
        state["last_outcome"] = outcome

        if signal > 0:
            state["success_count"] = state.get("success_count", 0) + 1
        elif signal < 0:
            state["failure_count"] = state.get("failure_count", 0) + 1

        # Check for moral violation circuit breaker (Paper #9)
        if category == "ethical" and signal < 0:
            belief["moral_violation_count"] = belief.get("moral_violation_count", 0) + 1
            if belief["moral_violation_count"] >= 2:  # Two strikes
                belief["is_distrusted"] = True

        # Cascade to supported beliefs
        self.cascade_strength_update(belief_id, new_strength)

        # Create immutable event (Paper #7)
        event = {
            "event_type": "belief_strength_update",
            "belief_id": belief_id,
            "context_key": context_key,
            "old_strength": old_strength,
            "new_strength": new_strength,
            "outcome": outcome,
            "difficulty_level": difficulty_level,
            "category_multiplier": category_mult,
            "peak_end_multiplier": peak_end_mult,
            "timestamp": datetime.now().isoformat()
        }

        return event

    def serialize(self) -> str:
        """Serialize to JSON for Postgres storage"""
        return json.dumps({
            "nodes": dict(self.G.nodes(data=True)),
            "edges": list(self.G.edges(data=True)),
            "beliefs": self.beliefs
        })

    @classmethod
    def deserialize(cls, json_str: str) -> "BeliefGraph":
        """Restore from Postgres JSON"""
        data = json.loads(json_str)
        graph = cls()

        for node_id, attrs in data["nodes"].items():
            graph.G.add_node(node_id, **attrs)

        for source, target, attrs in data["edges"]:
            graph.G.add_edge(source, target, **attrs)

        graph.beliefs = data["beliefs"]
        return graph
```

### 2.2 Social Graph for Authority

```python
class SocialGraph:
    """
    Paper #17: Social Awareness and Relationship Dynamics
    Tracks person authority, relationships, and conflict resolution.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self.persons: dict[str, PersonObject] = {}

    def add_person(self, person: PersonObject):
        """Add person to social graph"""
        self.persons[person["person_id"]] = person
        self.G.add_node(
            person["person_id"],
            authority=person["authority"],
            role=person["role"]
        )

    def compute_relationship_value(self, person_id: str) -> float:
        """
        Paper #17: relationship_value = 0.6*authority + 0.2*interaction + 0.2*context
        """
        person = self.persons.get(person_id)
        if not person:
            return 0.5

        return (
            0.6 * person.get("authority", 0.5) +
            0.2 * person.get("interaction_strength", 0.5) +
            0.2 * person.get("context_relevance", 0.5)
        )

    def record_preemption(
        self,
        preemptor_id: str,
        preempted_id: str,
        domain: str
    ):
        """
        Paper #17: Authority learning through preemption.
        When high-authority person overrides, their authority strengthens.
        """
        # Strengthen preemptor authority
        if preemptor_id in self.persons:
            current = self.persons[preemptor_id]["authority"]
            self.persons[preemptor_id]["authority"] = min(1.0, current + 0.1)

        # Add/update relationship edge
        self.G.add_edge(
            preemptor_id,
            preempted_id,
            last_preemption=datetime.now().isoformat(),
            domain=domain,
            preemption_count=self.G.edges.get(
                (preemptor_id, preempted_id), {}
            ).get("preemption_count", 0) + 1
        )

    def resolve_conflict(
        self,
        person_a_id: str,
        person_b_id: str,
        guidance_a: str,
        guidance_b: str
    ) -> dict:
        """
        Paper #17: Conflict resolution via authority-weighted triage.
        - If authority difference > 0.3: Auto-defer to higher
        - If <= 0.3: Escalate to human
        """
        auth_a = self.persons.get(person_a_id, {}).get("authority", 0.5)
        auth_b = self.persons.get(person_b_id, {}).get("authority", 0.5)

        diff = abs(auth_a - auth_b)

        if diff > 0.3:
            winner_id = person_a_id if auth_a > auth_b else person_b_id
            winner_guidance = guidance_a if auth_a > auth_b else guidance_b
            return {
                "resolution": "auto_defer",
                "winner": winner_id,
                "guidance": winner_guidance,
                "authority_differential": diff
            }
        else:
            return {
                "resolution": "escalate",
                "reason": "comparable_authority",
                "person_a": {"id": person_a_id, "authority": auth_a, "guidance": guidance_a},
                "person_b": {"id": person_b_id, "authority": auth_b, "guidance": guidance_b}
            }
```

---

## Part III: The Cognitive Loop (LangGraph)

### 3.1 Graph Structure

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

def create_baby_mars_graph():
    """
    The Cognitive Loop from first principles:
    1. Trigger → 2. Cognitive Activation → 3. Appraisal →
    4. Action Selection → 5. Execution → 6. Verification → 7. Feedback
    """

    builder = StateGraph(BabyMARSState)

    # ============================================================
    # NODE 1: COGNITIVE ACTIVATION
    # Retrieve beliefs, memories, objects from graph
    # ============================================================
    builder.add_node("cognitive_activation", cognitive_activation_node)

    # ============================================================
    # NODE 2: APPRAISAL
    # Analyze situation against activated beliefs
    # Detect goal conflicts, expectancy violations, face threats
    # ============================================================
    builder.add_node("appraisal", appraisal_node)

    # ============================================================
    # NODE 3: DIALECTICAL RESOLUTION (conditional)
    # Paper: Goal conflict hijacking
    # ============================================================
    builder.add_node("dialectical_resolution", dialectical_resolution_node)

    # ============================================================
    # NODE 4: ACTION SELECTION
    # Choose action based on goals, beliefs, autonomy level
    # ============================================================
    builder.add_node("action_selection", action_selection_node)

    # ============================================================
    # NODE 5: EXECUTION
    # Execute via MCP servers (Planner-Translator-Driver)
    # ============================================================
    builder.add_node("execution", execution_node)

    # ============================================================
    # NODE 6: VERIFICATION
    # Paper #3: Self-Correcting Validation
    # ============================================================
    builder.add_node("verification", verification_node)

    # ============================================================
    # NODE 7: FEEDBACK
    # Update beliefs, create memories, cascade changes
    # ============================================================
    builder.add_node("feedback", feedback_node)

    # ============================================================
    # NODE 8: RESPONSE GENERATION
    # Generate final response based on supervision mode
    # ============================================================
    builder.add_node("response_generation", response_generation_node)

    # ============================================================
    # EDGES
    # ============================================================

    # Entry
    builder.add_edge(START, "cognitive_activation")

    # After activation: check for goal conflicts
    builder.add_conditional_edges(
        "cognitive_activation",
        route_after_activation,
        {
            "dialectical_resolution": "dialectical_resolution",
            "appraisal": "appraisal"
        }
    )

    # After dialectical resolution, continue to appraisal
    builder.add_edge("dialectical_resolution", "appraisal")

    # After appraisal, select action
    builder.add_edge("appraisal", "action_selection")

    # After action selection: check supervision mode
    builder.add_conditional_edges(
        "action_selection",
        route_after_action_selection,
        {
            "guidance_seeking": "response_generation",  # Ask for help
            "action_proposal": "response_generation",    # Propose and wait
            "execution": "execution"                      # Execute autonomously
        }
    )

    # After execution, verify
    builder.add_edge("execution", "verification")

    # After verification: retry or proceed
    builder.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "retry": "execution",      # Paper #3: self-correction
            "feedback": "feedback",
            "escalate": "response_generation"
        }
    )

    # After feedback, generate response
    builder.add_edge("feedback", "response_generation")

    # Exit
    builder.add_edge("response_generation", END)

    return builder.compile(
        checkpointer=PostgresSaver.from_conn_string(POSTGRES_URL)
    )


# ============================================================
# ROUTING FUNCTIONS
# ============================================================

def route_after_activation(state: BabyMARSState) -> str:
    """Check for goal conflicts"""
    if state.get("goal_conflict_detected", False):
        return "dialectical_resolution"
    return "appraisal"

def route_after_action_selection(state: BabyMARSState) -> str:
    """Route based on autonomy level (Paper #1)"""
    mode = state.get("supervision_mode", "guidance_seeking")

    if mode == "guidance_seeking":
        return "guidance_seeking"
    elif mode == "action_proposal":
        return "action_proposal"
    else:
        return "execution"

def route_after_verification(state: BabyMARSState) -> str:
    """Route based on validation results (Paper #3)"""
    results = state.get("validation_results", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # Check for failures
    failures = [r for r in results if r.get("passed") == False]

    if not failures:
        return "feedback"  # All passed

    if retry_count < max_retries:
        # Check if fixable
        fixable = all(f.get("severity", 1.0) < 0.7 for f in failures)
        if fixable:
            return "retry"

    return "escalate"  # Give up, ask human
```

### 3.2 Node Implementations

```python
from anthropic import Anthropic
import json

client = Anthropic()

# ============================================================
# NODE: COGNITIVE ACTIVATION
# ============================================================

async def cognitive_activation_node(state: BabyMARSState) -> dict:
    """
    Load cognitive context from graphs.
    Implements the "fetch_active_subgraph" pattern.
    """

    # Get graphs from persistent storage
    belief_graph = await load_belief_graph(state["org_id"])
    social_graph = await load_social_graph(state["org_id"])

    # Extract context from last message
    last_message = state["messages"][-1] if state["messages"] else None
    context_key = extract_context_key(last_message)

    # Activate relevant beliefs
    activated_beliefs = []
    for belief_id, belief in belief_graph.beliefs.items():
        context_state = belief_graph.resolve_belief_for_context(
            belief_id, context_key
        )
        if context_state and context_state.get("strength", 0) > 0.3:
            activated_beliefs.append({
                **belief,
                "resolved_strength": context_state["strength"]
            })

    # Sort by strength
    activated_beliefs.sort(
        key=lambda b: b["resolved_strength"],
        reverse=True
    )

    # Load salient people (Paper #17)
    people = []
    for person_id, person in social_graph.persons.items():
        rv = social_graph.compute_relationship_value(person_id)
        if rv > 0.4:  # Salience threshold
            people.append({**person, "relationship_value": rv})

    # Build objects column (Paper #8)
    objects = {
        "people": people[:10],  # Top 10 by relationship value
        "entities": [],  # TODO: extract from context
        "beliefs": activated_beliefs[:20],  # Top 20 beliefs
        "knowledge": [],  # TODO: relevant workflows
        "goals": state.get("active_goals", []),
        "temporal": build_temporal_context()
    }

    # Check for goal conflicts
    goal_conflict = detect_goal_conflict(state.get("active_goals", []))

    return {
        "current_context_key": context_key,
        "activated_beliefs": activated_beliefs,
        "objects": objects,
        "goal_conflict_detected": goal_conflict is not None
    }


# ============================================================
# NODE: APPRAISAL
# ============================================================

async def appraisal_node(state: BabyMARSState) -> dict:
    """
    Analyze situation against activated beliefs.
    Use Claude to perform rich appraisal.
    """

    # Build appraisal prompt
    prompt = build_appraisal_prompt(
        messages=state["messages"],
        beliefs=state["activated_beliefs"],
        objects=state["objects"],
        goals=state.get("active_goals", [])
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=APPRAISAL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse structured appraisal
    appraisal = parse_appraisal_response(response.content[0].text)

    return {"appraisal": appraisal}


APPRAISAL_SYSTEM_PROMPT = """You are the appraisal system for an AI cognitive agent.

Given the current context, activated beliefs, and user message, analyze:

1. EXPECTANCY ANALYSIS
   - What did the agent expect based on beliefs?
   - Does the current situation match expectations?
   - If not, what is the violation type (positive/negative)?

2. FACE THREAT ANALYSIS
   - Is there a threat to user's positive face (need for approval)?
   - Is there a threat to user's negative face (need for autonomy)?
   - Severity: low/medium/high

3. GOAL ALIGNMENT
   - Which active goals are relevant?
   - Does the request advance or conflict with goals?

4. ATTRIBUTION
   - What beliefs influenced this analysis?
   - Confidence in attribution?

5. RECOMMENDED ACTION TYPE
   - guidance_needed: Agent lacks confidence
   - propose_and_confirm: Agent has moderate confidence
   - execute_directly: Agent has high confidence

Respond in JSON format.
"""


# ============================================================
# NODE: ACTION SELECTION
# ============================================================

async def action_selection_node(state: BabyMARSState) -> dict:
    """
    Select action based on appraisal and beliefs.
    Determine autonomy level (Paper #1).
    """

    appraisal = state.get("appraisal", {})
    beliefs = state.get("activated_beliefs", [])

    # Find most relevant belief for this action
    action_type = appraisal.get("recommended_action_type", "guidance_needed")
    relevant_beliefs = appraisal.get("attributed_beliefs", [])

    # Compute aggregate belief strength
    if relevant_beliefs:
        avg_strength = sum(
            b["resolved_strength"] for b in beliefs
            if b["belief_id"] in relevant_beliefs
        ) / len(relevant_beliefs)
    else:
        avg_strength = 0.3  # Low default

    # Determine supervision mode (Paper #1)
    if avg_strength < 0.4:
        supervision_mode = "guidance_seeking"
    elif avg_strength < 0.7:
        supervision_mode = "action_proposal"
    else:
        supervision_mode = "autonomous"

    # Override if high-stakes (Paper #10: category thresholds)
    if appraisal.get("involves_ethical_beliefs"):
        supervision_mode = "action_proposal"  # Always confirm ethical

    # Build action plan
    action = {
        "action_type": action_type,
        "work_units": [],  # PTD work units
        "requires_tools": [],
        "estimated_difficulty": appraisal.get("difficulty", 3),
    }

    # Use Claude to generate work units (Planner role in PTD)
    if supervision_mode != "guidance_seeking":
        work_units = await generate_work_units(
            state["messages"],
            state["objects"],
            appraisal
        )
        action["work_units"] = work_units

    return {
        "selected_action": action,
        "supervision_mode": supervision_mode,
        "belief_strength_for_action": avg_strength
    }


# ============================================================
# NODE: EXECUTION
# ============================================================

async def execution_node(state: BabyMARSState) -> dict:
    """
    Execute action via MCP servers.
    This is the Driver layer in PTD architecture.
    """

    action = state.get("selected_action", {})
    work_units = action.get("work_units", [])

    results = []

    for unit in work_units:
        # Route to appropriate MCP server (Translator layer)
        tool_name = unit.get("tool")

        try:
            # Claude with MCP integration
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                tools=get_mcp_tools(),  # Load from MCP servers
                messages=[{
                    "role": "user",
                    "content": f"Execute this work unit: {json.dumps(unit)}"
                }]
            )

            # Extract tool results
            result = extract_tool_results(response)
            results.append({
                "unit_id": unit.get("unit_id"),
                "status": "success",
                "result": result
            })

        except Exception as e:
            results.append({
                "unit_id": unit.get("unit_id"),
                "status": "error",
                "error": str(e)
            })

    return {
        "execution_results": results
    }


# ============================================================
# NODE: VERIFICATION
# ============================================================

async def verification_node(state: BabyMARSState) -> dict:
    """
    Paper #3: Self-Correcting Validation
    Run validators on execution results.
    """

    results = state.get("execution_results", [])
    action = state.get("selected_action", {})

    validation_results = []

    for result in results:
        # Run domain-specific validators
        validators = get_validators_for_action(action)

        for validator in validators:
            outcome = validator.validate(result)
            validation_results.append({
                "validator": validator.name,
                "passed": outcome.passed,
                "severity": outcome.severity if not outcome.passed else 0,
                "message": outcome.message,
                "fix_hint": outcome.fix_hint
            })

    # Increment retry counter if needed
    failures = [v for v in validation_results if not v["passed"]]
    retry_count = state.get("retry_count", 0)

    if failures:
        retry_count += 1

    return {
        "validation_results": validation_results,
        "retry_count": retry_count
    }


# ============================================================
# NODE: FEEDBACK
# ============================================================

async def feedback_node(state: BabyMARSState) -> dict:
    """
    Update beliefs and create memories based on outcome.
    Papers #1, #9, #11, #12
    """

    belief_graph = await load_belief_graph(state["org_id"])

    # Determine overall outcome
    validation_results = state.get("validation_results", [])
    all_passed = all(v["passed"] for v in validation_results)

    outcome = "success" if all_passed else "failure"

    # Get attributed beliefs from appraisal
    appraisal = state.get("appraisal", {})
    attributed_beliefs = appraisal.get("attributed_beliefs", [])

    # Update each attributed belief
    events = []
    for belief_id in attributed_beliefs:
        if belief_id in belief_graph.beliefs:
            event = belief_graph.update_belief_from_outcome(
                belief_id=belief_id,
                context_key=state["current_context_key"],
                outcome=outcome,
                difficulty_level=state["selected_action"].get("estimated_difficulty", 3),
                is_end_memory=False,  # TODO: detect end of conversation
                emotional_intensity=0.5  # TODO: analyze from interaction
            )
            events.append(event)

    # Create memory
    memory = {
        "memory_id": generate_id(),
        "description": summarize_interaction(state),
        "timestamp": datetime.now().isoformat(),
        "outcome": outcome,
        "emotional_intensity": 0.5,
        "is_end_memory": False,
        "related_beliefs": attributed_beliefs,
        "context_key": state["current_context_key"],
        "difficulty_level": state["selected_action"].get("estimated_difficulty", 3)
    }

    # Save updated graph
    await save_belief_graph(state["org_id"], belief_graph)
    await save_memory(state["org_id"], memory)

    return {
        "events": events
    }


# ============================================================
# NODE: RESPONSE GENERATION
# ============================================================

async def response_generation_node(state: BabyMARSState) -> dict:
    """
    Generate final response based on supervision mode.
    """

    mode = state.get("supervision_mode", "guidance_seeking")
    action = state.get("selected_action", {})
    results = state.get("execution_results", [])

    if mode == "guidance_seeking":
        # Ask for guidance
        response = generate_guidance_request(state)

    elif mode == "action_proposal":
        # Propose action and ask for confirmation
        response = generate_action_proposal(action, state)

    else:
        # Report autonomous execution results
        response = generate_execution_report(results, state)

    return {
        "messages": [{"role": "assistant", "content": response}]
    }
```

---

## Part IV: Birth System (Paper #15)

```python
async def birth_user(email: str, org_id: str) -> dict:
    """
    Paper #15: Birth System - Cold Start Without Belief Inheritance
    Create initial beliefs from external data in <90 seconds.
    """

    # ============================================================
    # PILLAR 1: SOCIAL CONTEXT ENRICHMENT
    # ============================================================

    # Call Apollo API for firmographic data
    apollo_data = await enrich_from_apollo(email)

    identity = {
        "person": {
            "name": apollo_data.get("name"),
            "title": apollo_data.get("title"),
            "seniority": apollo_data.get("seniority"),
            "department": apollo_data.get("department")
        },
        "company": {
            "name": apollo_data.get("company_name"),
            "industry": apollo_data.get("industry"),
            "size": apollo_data.get("employee_count"),
            "location": apollo_data.get("location")
        }
    }

    # Infer initial authority from role
    authority = infer_authority_from_role(identity["person"]["title"])

    # ============================================================
    # PILLAR 2: DOMAIN KNOWLEDGE INJECTION
    # ============================================================

    # Select knowledge packs based on industry
    industry = identity["company"]["industry"]
    knowledge_packs = select_knowledge_packs(industry)

    # Load GAAP, SEC, industry-specific rules
    knowledge = []
    for pack in knowledge_packs:
        knowledge.extend(load_knowledge_pack(pack))

    # ============================================================
    # PILLAR 3: EXPERIENTIAL PRIMING
    # ============================================================

    # Load distilled scenarios for similar roles
    role = identity["person"]["title"]
    scenarios = load_scenarios_for_role(role, industry)

    # ============================================================
    # SYNTHESIZE INITIAL BELIEFS
    # ============================================================

    # Use Claude to generate initial beliefs
    prompt = f"""
    Generate initial beliefs for a new AI agent user.

    USER PROFILE:
    {json.dumps(identity, indent=2)}

    KNOWLEDGE PACKS LOADED:
    {[p["name"] for p in knowledge_packs]}

    EXAMPLE SCENARIOS:
    {json.dumps(scenarios[:3], indent=2)}

    Generate 10-15 initial beliefs with:
    - statement: Natural language belief
    - category: ethical/relational/procedural/contextual/aesthetic
    - initial_strength: 0.4-0.6 (appropriately uncertain)
    - rationale: Why this belief is reasonable given the profile

    Focus on:
    1. Role-appropriate procedural beliefs
    2. Industry-specific contextual beliefs
    3. Communication style preferences

    Respond in JSON format.
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    initial_beliefs = parse_beliefs_from_response(response.content[0].text)

    # ============================================================
    # CREATE GRAPHS
    # ============================================================

    # Initialize belief graph
    belief_graph = BeliefGraph()
    for belief in initial_beliefs:
        belief_state = {
            "belief_id": generate_id(),
            "statement": belief["statement"],
            "category": belief["category"],
            "strength": belief["initial_strength"],
            "context_key": "*|*|*",  # Global default
            "context_states": {
                "*|*|*": {
                    "strength": belief["initial_strength"],
                    "last_updated": datetime.now().isoformat(),
                    "success_count": 0,
                    "failure_count": 0
                }
            },
            "supports": [],
            "supported_by": [],
            "support_weights": {},
            "last_updated": datetime.now().isoformat(),
            "success_count": 0,
            "failure_count": 0,
            "is_end_memory_influenced": False,
            "peak_intensity": 0.0,
            "invalidation_threshold": INVALIDATION_THRESHOLDS[belief["category"]],
            "is_distrusted": False,
            "moral_violation_count": 0
        }
        belief_graph.add_belief(belief_state)

    # Initialize social graph with user as primary person
    social_graph = SocialGraph()
    user_person = {
        "person_id": generate_id(),
        "name": identity["person"]["name"],
        "role": identity["person"]["title"],
        "authority": authority,
        "interaction_strength": 1.0,  # Self
        "context_relevance": 1.0,
        "relationship_value": 1.0,
        "preferences": [],
        "last_interaction": datetime.now().isoformat()
    }
    social_graph.add_person(user_person)

    # Save to Postgres
    await save_belief_graph(org_id, belief_graph)
    await save_social_graph(org_id, social_graph)

    return {
        "user_id": user_person["person_id"],
        "initial_beliefs": len(initial_beliefs),
        "knowledge_packs": [p["name"] for p in knowledge_packs],
        "birth_time_seconds": elapsed_time
    }
```

---

## Part V: File Structure

```
baby_mars/
├── README.md
├── ARCHITECTURE.md (this file)
├── pyproject.toml
│
├── src/
│   ├── __init__.py
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── schema.py          # BabyMARSState definition
│   │   ├── reducers.py        # Custom reducers for state
│   │   └── working_memory.py  # Three-column helpers
│   │
│   ├── graphs/
│   │   ├── __init__.py
│   │   ├── belief_graph.py    # NetworkX belief DAG
│   │   ├── social_graph.py    # NetworkX social graph
│   │   └── persistence.py     # Postgres JSON serialization
│   │
│   ├── cognitive_loop/
│   │   ├── __init__.py
│   │   ├── graph.py           # LangGraph definition
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── cognitive_activation.py
│   │   │   ├── appraisal.py
│   │   │   ├── dialectical_resolution.py
│   │   │   ├── action_selection.py
│   │   │   ├── execution.py
│   │   │   ├── verification.py
│   │   │   ├── feedback.py
│   │   │   └── response_generation.py
│   │   └── routing.py         # Conditional edge functions
│   │
│   ├── birth/
│   │   ├── __init__.py
│   │   ├── birth_system.py    # Main birth orchestration
│   │   ├── enrichment.py      # Apollo API integration
│   │   ├── knowledge_packs.py # Domain knowledge loading
│   │   └── scenarios.py       # Experiential priming
│   │
│   ├── belief_system/
│   │   ├── __init__.py
│   │   ├── strength_update.py # EMA formula, multipliers
│   │   ├── context_resolution.py # Backoff algorithm
│   │   ├── cascading.py       # Hierarchical propagation
│   │   └── acre.py            # Category-specific invalidation
│   │
│   ├── autonomy/
│   │   ├── __init__.py
│   │   ├── competence.py      # Belief strength → supervision
│   │   ├── difficulty.py      # Task difficulty rating
│   │   └── thresholds.py      # Autonomy thresholds
│   │
│   ├── social/
│   │   ├── __init__.py
│   │   ├── authority.py       # Authority computation
│   │   ├── conflict.py        # Conflict resolution
│   │   └── relationships.py   # Relationship value
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── episodic.py        # Memory creation
│   │   ├── peak_end.py        # Peak-end rule
│   │   └── decay.py           # Interference-based decay
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── validators.py      # Domain validators
│   │   └── self_correction.py # Retry logic
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── work_units.py      # PTD work unit generation
│   │   └── mcp_client.py      # MCP server integration
│   │
│   └── skills/
│       ├── __init__.py
│       ├── accounting.md      # Claude skill for accounting
│       ├── appraisal.md       # Claude skill for appraisal
│       └── work_units.md      # Claude skill for PTD
│
├── tests/
│   ├── __init__.py
│   ├── test_belief_graph.py
│   ├── test_social_graph.py
│   ├── test_cognitive_loop.py
│   ├── test_birth_system.py
│   └── scenarios/
│       └── bluebook_scenarios.py  # Your persona stories
│
└── scripts/
    ├── migrate_db.py
    └── run_scenario.py
```

---

## Part VI: Implementation Timeline

### Week 1: Core State + Graphs
- [ ] `state/schema.py` - Complete BabyMARSState
- [ ] `graphs/belief_graph.py` - NetworkX with cascading
- [ ] `graphs/social_graph.py` - Authority computation
- [ ] `graphs/persistence.py` - Postgres JSON
- [ ] Tests for graphs

### Week 2: Cognitive Loop
- [ ] `cognitive_loop/graph.py` - LangGraph structure
- [ ] `cognitive_loop/nodes/*.py` - All 8 nodes
- [ ] `cognitive_loop/routing.py` - Conditional edges
- [ ] Claude prompts for appraisal/action selection
- [ ] Tests for loop

### Week 3: Belief System + Memory
- [ ] `belief_system/*.py` - All belief mechanics
- [ ] `memory/*.py` - Memory creation + decay
- [ ] `autonomy/*.py` - Competence-based routing
- [ ] `validation/*.py` - Self-correction
- [ ] Tests for belief updates

### Week 4: Birth + Integration
- [ ] `birth/*.py` - Full birth system
- [ ] `execution/*.py` - MCP integration
- [ ] `skills/*.md` - Claude skills
- [ ] End-to-end scenario tests
- [ ] Bluebook persona validation

---

## Part VII: What This Proves

When Baby MARS runs successfully against your persona scenarios:

1. **Cognitive Loop Works** — Trigger → Activation → Appraisal → Action → Feedback produces measurably better outcomes than stateless prompting

2. **Belief System Works** — Context-conditional beliefs with hierarchical cascading maintain consistency across interactions

3. **Autonomy Works** — Belief strength correctly gates supervision (guidance-seeking → proposal → autonomous)

4. **Social Awareness Works** — Authority-based conflict resolution reduces escalations

5. **Birth System Works** — External data → initial beliefs → faster time-to-competence

6. **Self-Correction Works** — Validation + retry reduces errors before human escalation

7. **Your Research Is Production-Ready** — All 20 papers (minus LTL training) implement on off-the-shelf infrastructure

---

## Part VIII: Migration Path to MARS

When TAMI is ready, the swap is surgical:

```python
# Before (Baby MARS)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    ...
)

# After (MARS)
response = tami_client.inference(
    model="tami-medium-2025",
    ...
)
```

Everything else stays the same:
- LangGraph orchestration: unchanged
- Belief graph: unchanged
- Social graph: unchanged
- State schema: unchanged
- Validation: unchanged

Baby MARS is MARS with a rented brain.
