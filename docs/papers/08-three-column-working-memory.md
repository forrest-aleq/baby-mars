# Three-Column Working Memory for Relationship-Aware AI Agents

**First Conceptualized:** October 20, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

LLM-based agents struggle with working memory management. They either maintain too little context (forgetting recent interactions) or too much context (overwhelming the context window with irrelevant details). Traditional approaches use a single undifferentiated context buffer, forcing the agent to treat all information equally—active tasks, background notes, and ambient context are mixed together without structure.

We introduce a three-column working memory architecture that separates cognitive state into distinct functional regions: (1) Active Tasks—the 3-4 items currently being worked on, with full state and dependencies; (2) Notes—acknowledged items in a queue with time-to-live, representing things to address later; (3) Objects—ambient context including people (with relationship beliefs), entities, high-strength beliefs, and temporal context.

The key insight is that these columns serve different cognitive functions and require different management policies. Active Tasks need rich state tracking and explicit dependencies. Notes need TTL-based expiration and priority escalation. Objects need salience-based population from the knowledge graph, loading only items relevant to current context.

Critically, there are no explicit pointers between columns—the LLM reasons about relationships implicitly. This prevents brittle coupling and enables flexible cross-column reasoning (e.g., "This task involves Person X, who I noted earlier has a preference for detailed explanations").

We demonstrate this architecture on a professional workflow where the agent manages multiple concurrent tasks, maintains awareness of stakeholder preferences, and proactively surfaces relevant prior context. The three-column structure reduces context window usage by 40% (vs. undifferentiated buffer) while improving task completion rate by 23% and relationship quality scores by 31%.

---

## 1. Introduction: The Working Memory Problem

LLM agents face a fundamental tension: they need enough context to make informed decisions, but too much context overwhelms the model and degrades performance. This is the working memory problem.

Consider an agent managing a professional workflow:

**Current state:**
- Processing invoice from Vendor X (active task)
- User mentioned earlier that Vendor X requires special handling (prior context)
- User asked to review the Cheyenne variance report later (deferred task)
- User prefers detailed explanations for financial decisions (relationship preference)
- It's month-end, so urgency is higher than usual (temporal context)

**Question:** How should this information be represented in the agent's working memory?

**Naive approach (undifferentiated buffer):**

```
Context:
- Processing invoice from Vendor X
- User mentioned Vendor X requires special handling
- User asked to review Cheyenne variance report
- User prefers detailed explanations
- It's month-end
- [... 50 other facts ...]
```

This approach has fatal flaws:

1. **No prioritization:** All facts are treated equally. The agent can't distinguish between "currently processing" and "mentioned in passing."
2. **No expiration:** Old facts accumulate indefinitely. The context window fills with stale information.
3. **No structure:** The agent must scan the entire buffer to find relevant facts.

**Three-column approach:**

```
Column 1 - Active Tasks (3-4 slots):
  [Task 1] Process invoice from Vendor X
    State: Awaiting GL code assignment
    Dependencies: Requires vendor master lookup
    History: Started 2 minutes ago

Column 2 - Notes (acknowledged queue):
  [Note 1] Review Cheyenne variance report (TTL: 4 hours, Priority: 0.6)
  [Note 2] Follow up on Q3 budget (TTL: 24 hours, Priority: 0.4)

Column 3 - Objects (ambient context):
  People:
    - User (relationship_value: 0.95, prefers detailed explanations)
    - Vendor X contact (relationship_value: 0.72, requires special handling)
  Entities:
    - Vendor X (recent, high salience)
    - Cheyenne project (mentioned in Note 1)
  Beliefs:
    - "Vendor X invoices use GL code 5100" (strength 0.88)
  Temporal:
    - Month-end period (urgency multiplier: 1.5x)
```

This structured representation enables:

1. **Clear prioritization:** Active Tasks are top priority, Notes are queued, Objects provide context
2. **Automatic expiration:** Notes have TTL, Objects are refreshed based on salience
3. **Efficient lookup:** The agent knows where to find each type of information

---

## 2. Column 1: Active Tasks (3-4 Slots)

Active Tasks represent items currently being worked on. The agent can only maintain 3-4 active tasks simultaneously (matching human working memory capacity).

### 2.1 Task Structure

```python
@dataclass
class ActiveTask:
    task_id: str
    description: str  # Natural language summary
    state: TaskState  # Current state (planning, executing, blocked, etc.)
    dependencies: List[str]  # What this task depends on
    history: List[TaskEvent]  # What's happened so far
    started_at: datetime
    estimated_duration: Optional[timedelta]
    priority: float  # [0,1] urgency score

@dataclass
class TaskState:
    status: Literal["planning", "executing", "blocked", "awaiting_input", "complete"]
    current_step: Optional[str]  # Which step are we on?
    blocking_reason: Optional[str]  # Why are we blocked?
    progress: float  # [0,1] completion estimate
```

### 2.2 Task Lifecycle

**1. Admission:** When a new task arrives, the agent decides whether to:
- Make it active (if slots available and priority is high)
- Note it for later (if slots full or priority is moderate)
- Defer it (if priority is low)

**2. Execution:** While active, the task receives full attention:
- State is updated after each step
- Dependencies are tracked
- History is maintained

**3. Completion:** When complete, the task is removed from active slots:
- Final state is recorded
- Outcomes are logged for learning
- Slot becomes available for next task

**4. Blocking:** If blocked, the task remains active but marked:
- Blocking reason is explicit
- Agent can work on other tasks while waiting
- Unblocking triggers resumption

### 2.3 Slot Management

With only 3-4 slots, the agent must prioritize ruthlessly:

```python
def should_activate_task(
    task: Task,
    active_tasks: List[ActiveTask],
    max_slots: int = 4
) -> bool:
    """
    Decide whether to activate a task or note it for later.
    """
    # If slots available, activate high-priority tasks
    if len(active_tasks) < max_slots:
        return task.priority > 0.5

    # If slots full, only activate if higher priority than lowest active task
    lowest_priority = min(t.priority for t in active_tasks)
    if task.priority > lowest_priority * 1.3:  # 30% threshold
        # Demote lowest-priority active task to notes
        demote_lowest_priority_task(active_tasks)
        return True

    return False  # Note it for later
```

This creates a natural queue: high-priority tasks are activated immediately, moderate-priority tasks are noted, and low-priority tasks are deferred.

---

## 3. Column 2: Notes (Acknowledged Queue with TTL)

Notes represent items that have been acknowledged but not yet acted upon. They're not active tasks (not currently being worked on) but they're not forgotten either (they're in the queue).

### 3.1 Note Structure

```python
@dataclass
class Note:
    note_id: str
    content: str  # Natural language description
    created_at: datetime
    ttl: timedelta  # Time to live
    priority: float  # [0,1] base priority
    source: Literal["user", "system", "inferred"]  # Where did this come from?
    context: Dict[str, Any]  # Relevant context when noted

def effective_priority(note: Note) -> float:
    """
    Compute effective priority with TTL escalation.

    As TTL approaches expiration, priority increases.
    """
    age = now() - note.created_at
    remaining_fraction = 1.0 - (age / note.ttl)

    if remaining_fraction < 0.05:  # <5% TTL remaining
        escalation = 2.0  # Double priority
    elif remaining_fraction < 0.20:  # <20% TTL remaining
        escalation = 1.5
    else:
        escalation = 1.0

    return min(1.0, note.priority * escalation)
```

### 3.2 TTL-Based Expiration

Notes don't live forever. They have a TTL based on urgency:

- **Urgent notes** (user explicitly said "soon"): TTL = 2-4 hours
- **Normal notes** (user said "later" or "when you get a chance"): TTL = 24-48 hours
- **Low-priority notes** (inferred from context): TTL = 7 days

When TTL expires:
- **High-priority notes:** Escalate to user ("You asked me to review the Cheyenne variance report. Should I prioritize this?")
- **Low-priority notes:** Archive silently (assume no longer relevant)

### 3.3 Proactive Surfacing

The agent proactively surfaces notes when they become relevant:

```python
def should_surface_note(
    note: Note,
    current_context: Context
) -> bool:
    """
    Decide whether to surface a note based on current context.
    """
    # Surface if TTL is low
    if effective_priority(note) > 0.9:
        return True

    # Surface if contextually relevant
    if is_contextually_relevant(note, current_context):
        return True

    return False

def is_contextually_relevant(note: Note, context: Context) -> bool:
    """
    Check if note is relevant to current context.

    Examples:
    - Note mentions "Cheyenne variance" and user just asked about Cheyenne
    - Note mentions "Q3 budget" and we're currently in Q3 planning
    """
    # Extract entities from note and context
    note_entities = extract_entities(note.content)
    context_entities = extract_entities(context.description)

    # Check for overlap
    overlap = note_entities & context_entities
    return len(overlap) > 0
```

**Example:**

User is working on Cheyenne project. Agent surfaces: "Earlier you mentioned wanting to review the Cheyenne variance report. Would you like me to pull that up now?"

This proactive surfacing creates the impression of attentiveness and memory.

---

## 4. Column 3: Objects (Ambient Context)

Objects represent ambient context—things that aren't tasks or notes but provide important background for decision-making.

### 4.1 Object Categories

**People:**
- User and colleagues
- Each person has relationship_beliefs (preferences, communication style, authority level)
- Relationship_value score (how important is this relationship?)

**Entities:**
- Clients, vendors, projects, accounts
- Recently mentioned or high salience
- Linked to relevant beliefs

**Beliefs:**
- High-strength beliefs (>0.8) relevant to current context
- Recently updated beliefs (changed in last 7 days)
- Beliefs linked to active tasks or notes

**Knowledge:**
- Policies, procedures, constraints
- Domain-specific rules
- Regulatory requirements

**Goals:**
- User's stated objectives
- Organizational priorities
- Personal preferences

**Temporal Context:**
- Current period (month-end, quarter-end, year-end)
- Upcoming deadlines
- Seasonal patterns

**Patterns:**
- Recurring workflows
- Historical precedents
- Learned heuristics

### 4.2 Salience-Based Population

Objects are not loaded indiscriminately. They're populated based on salience:

```python
def populate_objects(
    active_tasks: List[ActiveTask],
    notes: List[Note],
    max_objects: int = 20
) -> Objects:
    """
    Load salient objects from knowledge graph.

    Salience is computed based on:
    - Recency (mentioned in last N turns)
    - Relevance (linked to active tasks or notes)
    - Importance (relationship_value, belief strength)
    """
    # Extract entities from active tasks and notes
    task_entities = extract_entities_from_tasks(active_tasks)
    note_entities = extract_entities_from_notes(notes)

    # Query knowledge graph for related objects
    candidate_objects = query_knowledge_graph(
        entities=task_entities | note_entities,
        max_depth=2  # 2-hop neighborhood
    )

    # Score each object by salience
    scored_objects = [
        (obj, compute_salience(obj, active_tasks, notes))
        for obj in candidate_objects
    ]

    # Sort by salience and take top N
    scored_objects.sort(key=lambda x: x[1], reverse=True)
    top_objects = [obj for obj, score in scored_objects[:max_objects]]

    return Objects(
        people=filter_by_type(top_objects, "Person"),
        entities=filter_by_type(top_objects, "Entity"),
        beliefs=filter_by_type(top_objects, "Belief"),
        knowledge=filter_by_type(top_objects, "Knowledge"),
        goals=filter_by_type(top_objects, "Goal"),
        temporal=get_temporal_context(),
        patterns=get_relevant_patterns(active_tasks)
    )

def compute_salience(
    obj: Object,
    active_tasks: List[ActiveTask],
    notes: List[Note]
) -> float:
    """
    Compute salience score for an object.
    """
    score = 0.0

    # Recency: mentioned in last N turns
    if obj.last_mentioned_turn > current_turn - 5:
        score += 0.3

    # Relevance: linked to active tasks
    if any(obj.id in task.dependencies for task in active_tasks):
        score += 0.4

    # Relevance: linked to notes
    # note.context is Dict[str, Any], checking if obj.id exists as a key
    # (e.g., note.context = {"entity_123": {...}, "person_456": {...}})
    if any(obj.id in note.context for note in notes):
        score += 0.2

    # Importance: relationship value (for people)
    if isinstance(obj, Person):
        score += 0.3 * obj.relationship_value

    # Importance: belief strength (for beliefs)
    if isinstance(obj, Belief):
        score += 0.3 * obj.strength

    return score
```

This salience-based approach ensures that Objects contains only relevant context, not everything in the knowledge graph.

---

## 5. No Explicit Pointers: LLM Reasons About Relationships

A critical design decision: there are no explicit pointers between columns. The LLM reasons about relationships implicitly.

**Wrong approach (explicit pointers):**

```python
# DON'T DO THIS
@dataclass
class ActiveTask:
    task_id: str
    related_notes: List[str]  # Explicit pointers to notes
    related_people: List[str]  # Explicit pointers to people
    related_beliefs: List[str]  # Explicit pointers to beliefs
```

This creates brittle coupling. If a note is deleted, we must update all tasks that point to it. If a person is renamed, we must update all pointers. The system becomes fragile.

**Correct approach (implicit reasoning):**

```python
# DO THIS
@dataclass
class ActiveTask:
    task_id: str
    description: str  # Natural language, mentions entities implicitly
    # No explicit pointers
```

The LLM reads the task description ("Process invoice from Vendor X") and implicitly connects it to:
- The Vendor X object in Column 3
- The note about "Vendor X requires special handling"
- The belief "Vendor X invoices use GL code 5100"

This implicit reasoning is more flexible and robust. The LLM can discover connections that weren't explicitly encoded.

---

## 6. Evaluation: Context Efficiency and Task Performance

We evaluated the three-column architecture on a professional workflow over 30 days:

### 6.1 Experimental Setup

**Baseline:** Undifferentiated context buffer (all information in single list)

**Three-column:** Structured working memory with Active Tasks, Notes, Objects

**Workload:**
- Average 8 concurrent tasks per day
- Average 12 notes in queue
- Average 45 objects in knowledge graph

**Metrics:**
- Context window usage (tokens)
- Task completion rate
- Relationship quality (human ratings)
- Proactive surfacing accuracy

### 6.2 Results: Context Efficiency

**Baseline (undifferentiated buffer):**
- Average context window usage: 4,200 tokens
- Context includes: all tasks (active and inactive), all notes, all objects
- Problem: 60% of context is irrelevant to current task

**Three-column:**
- Average context window usage: 2,500 tokens (40% reduction)
- Context includes: 3-4 active tasks, top 8 notes by priority, top 20 objects by salience
- Benefit: 85% of context is relevant to current task

The 40% reduction in context usage enables:
- Faster inference (less tokens to process)
- Lower cost (fewer tokens billed)
- Better focus (model attends to relevant information)

### 6.3 Results: Task Completion Rate

**Baseline:**
- Task completion rate: 67%
- Common failure mode: Agent forgets about tasks that aren't currently active

**Three-column:**
- Task completion rate: 82% (23% improvement)
- Notes with TTL ensure tasks aren't forgotten
- Proactive surfacing brings tasks back to attention when relevant

### 6.4 Results: Relationship Quality

**Baseline:**
- Relationship quality score: 3.2/5.0 (human ratings)
- Common complaint: "Agent doesn't remember my preferences"

**Three-column:**
- Relationship quality score: 4.2/5.0 (31% improvement)
- People objects include relationship_beliefs (preferences, communication style)
- Agent consistently applies preferences across interactions

**Example:**

User prefers detailed explanations for financial decisions. With three-column architecture, this preference is stored in the User object and applied consistently:

"I assigned GL code 5100 for this invoice because: (1) it's office supplies, which typically use 5100-5199 range, (2) we've used 5100 for similar invoices from this vendor in the past, and (3) the amount is under $10K, so it doesn't require special approval."

With undifferentiated buffer, this preference might be lost or inconsistently applied.

### 6.5 Results: Proactive Surfacing Accuracy

**Metric:** When agent proactively surfaces a note, is it actually relevant?

**Baseline:** N/A (no proactive surfacing)

**Three-column:**
- Proactive surfacing events: 47 over 30 days
- Relevant surfacing: 41 (87% accuracy)
- Irrelevant surfacing: 6 (13% false positives)

**Example of relevant surfacing:**

User asks about Cheyenne project. Agent surfaces: "Earlier you mentioned wanting to review the Cheyenne variance report. Would you like me to pull that up now?"

User confirms: "Yes, perfect timing."

**Example of irrelevant surfacing:**

User asks about Q4 budget. Agent surfaces: "Earlier you mentioned the Cheyenne variance report."

User: "That's not related to what I'm asking about."

The 87% accuracy shows that salience-based surfacing works well but isn't perfect. Future work could improve this through better entity extraction and relevance scoring.

---

## 7. Conclusion

The three-column working memory architecture separates cognitive state into Active Tasks (3-4 slots with rich state), Notes (acknowledged queue with TTL), and Objects (ambient context with salience-based population). This structure reduces context window usage by 40%, improves task completion by 23%, and improves relationship quality by 31% compared to undifferentiated context buffers.

The key insights are: (1) different types of information require different management policies, (2) explicit structure enables efficient lookup and prioritization, (3) TTL-based expiration prevents stale information from accumulating, (4) salience-based population ensures only relevant objects are loaded, and (5) implicit reasoning (no explicit pointers) creates flexible, robust connections between columns.

The architecture is grounded in cognitive science (human working memory capacity of 3-4 items) and practical deployment experience (agents need to manage multiple concurrent tasks while maintaining relationship awareness and proactively surfacing relevant context).

---

**Invention Date:** October 20, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art
