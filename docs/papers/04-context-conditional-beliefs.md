# Context-Conditional Belief Surfaces for Situated AI Competence

**First Conceptualized:** June 8, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

Traditional belief systems represent agent knowledge as scalar averages: "I'm 75% confident that action X works." This averaging destroys situational expertise. An agent might be 95% confident that action X works for Client A during month-end but only 40% confident it works for Client B during mid-month. Averaging these to 67.5% makes the agent equally uncertain everywhere—it has lost the knowledge that it's expert in one context and novice in another.

We introduce context-conditional beliefs, a hierarchical representation where beliefs are indexed by explicit context keys (e.g., client|period|amount) and resolved through a backoff mechanism borrowed from natural language processing. When the agent encounters a situation, it searches for the most specific matching belief. If no exact match exists, it backs off to progressively more general contexts until a match is found or the global default is reached.

This preserves situational expertise while preventing overfitting. The agent maintains separate beliefs for "Client A | month-end | large amounts" and "Client B | mid-month | small amounts," each with independent strength and temporal state. Statistical admission criteria prevent creating contexts for insufficient data (avoiding overfitting to noise), while pruning mechanisms remove contexts that no longer provide predictive value.

The critical implementation insight—discovered during production deployment—is that each context must maintain independent temporal state. Sharing temporal state across contexts creates "global state contamination" where updates in one context corrupt beliefs in unrelated contexts. This bug pattern is subtle but catastrophic: the agent appears to learn correctly in isolation but exhibits bizarre cross-contamination in production.

We demonstrate the framework on a financial workflow where context-conditional beliefs achieve 89% prediction accuracy (vs. 67% for scalar beliefs) and reduce clarification requests by 43%. The framework is psychologically grounded in situated cognition theory and technically grounded in hierarchical backoff from computational linguistics.

---

## 1. Introduction: The Expertise-Destroying Average

Consider an accounting agent that processes invoices. Over time, it learns:

- For Client A during month-end with amounts > $10K: Use GL code 5100 (95% confidence, based on 200 successful executions)
- For Client B during mid-month with amounts < $1K: Use GL code 5200 (92% confidence, based on 150 successful executions)

Now suppose we represent this as a scalar belief: "Use GL code 5100 for office supplies." What's the confidence? If we average: (95% + 92%) / 2 = 93.5%. But this is wrong. The agent isn't 93.5% confident globally—it's 95% confident in context A and 92% confident in context B. More importantly, if we encounter a new context (Client C, year-end, $5K), the agent has no basis for confidence. It might guess 93.5% by averaging, but that's not grounded in experience.

The problem is that scalar beliefs flatten context into a single number. They answer "How confident am I on average?" when the right question is "How confident am I in this specific situation?"

This averaging destroys expertise in two ways:

**1. False confidence in unfamiliar contexts**: The agent appears confident (93.5%) even in situations it has never encountered. This leads to silent failures—the agent acts autonomously in contexts where it should seek guidance.

**2. False uncertainty in familiar contexts**: If the agent has one high-confidence context (95%) and many low-confidence contexts (40%), the average might be 60%, causing the agent to seek guidance even in the high-confidence context where it's actually expert.

The solution is context-conditional beliefs: represent beliefs not as scalars but as functions from context to confidence. The agent doesn't have a single belief "Use GL code 5100 (93.5%)"—it has a belief surface with different confidence levels for different contexts.

---

## 2. Hierarchical Context Representation

A context is a structured key with multiple dimensions:

```
context = client | period | amount_range | category | ...
```

For example:

- `ClientA | month-end | >10K | office-supplies`
- `ClientB | mid-month | <1K | travel`
- `ClientA | month-end | * | *` (wildcard for amount and category)

The hierarchy is defined by specificity: more dimensions = more specific. The most specific context is a fully-qualified key with all dimensions specified. The least specific context is the global default with all dimensions wildcarded.

A belief is then a mapping from context to (strength, temporal_state):

```python
@dataclass
class ContextualBelief:
    statement: str  # e.g., "Use GL code 5100"
    contexts: Dict[ContextKey, BeliefState]

@dataclass
class BeliefState:
    strength: float  # [0,1] confidence based on experience
    last_updated: datetime
    success_count: int
    failure_count: int
    last_outcome: Literal["success", "failure", "neutral"]
    # CRITICAL: Each context has independent temporal state
```

The key insight is that each context maintains independent state. If we update the belief for `ClientA | month-end | >10K`, we don't touch the state for `ClientB | mid-month | <1K`. This prevents cross-contamination.

---

## 3. Backoff Resolution: Finding the Best Match

When the agent encounters a situation, it needs to find the most specific matching belief. The backoff algorithm is:

> **Note**: The pseudocode below presents a simplified backoff algorithm for conceptual clarity. The production implementation (`src/neo4j_layer/belief_contexts.py:220-242`) uses a more sophisticated **combinatorial subset matching** approach: instead of sequentially dropping dimensions right-to-left, it evaluates **all possible N-facet combinations** at each backoff level (e.g., for 3 facets `{A, B, C}`, it tries `ABC → {AB, AC, BC} → {A, B, C} → base`). This provides better context matching by exploring all subset paths, not just linear dimensional reduction. The simplified version here aids understanding of the core concept without implementation complexity.

```python
def resolve_belief(
    belief: ContextualBelief,
    current_context: ContextKey
) -> Optional[BeliefState]:
    """
    Find the most specific matching belief state.

    Backoff order:
    1. Exact match (all dimensions match)
    2. Drop least important dimension, try again
    3. Continue until match found or global default reached
    """
    # Try exact match first
    if current_context in belief.contexts:
        return belief.contexts[current_context]

    # Build backoff ladder (most specific to least specific)
    backoff_ladder = build_backoff_ladder(current_context)

    for candidate_context in backoff_ladder:
        if candidate_context in belief.contexts:
            return belief.contexts[candidate_context]

    # No match found, return None (agent should seek guidance)
    return None


def build_backoff_ladder(context: ContextKey) -> List[ContextKey]:
    """
    Generate progressively more general contexts.

    Example for context "ClientA | month-end | >10K | office-supplies":
    1. ClientA | month-end | >10K | office-supplies (exact)
    2. ClientA | month-end | >10K | * (drop category)
    3. ClientA | month-end | * | * (drop amount)
    4. ClientA | * | * | * (drop period)
    5. * | * | * | * (global default)
    """
    dimensions = context.split("|")
    ladder = []

    # Start with exact match
    ladder.append(context)

    # Drop dimensions one at a time (right to left, least to most important)
    for i in range(len(dimensions) - 1, 0, -1):
        generalized = dimensions[:i] + ["*"] * (len(dimensions) - i)
        ladder.append("|".join(generalized))

    # Add global default
    ladder.append("|".join(["*"] * len(dimensions)))

    return ladder
```

This backoff mechanism has several important properties:

**1. Specificity preference**: The agent always uses the most specific available knowledge. If it has experience with the exact context, it uses that. Only if no specific match exists does it fall back to more general knowledge.

**2. Graceful degradation**: If the agent has no experience with the current context, it backs off to increasingly general contexts until it finds a match. This prevents "I've never seen this exact situation before, so I have no idea what to do."

**3. Explicit uncertainty**: If no match is found even after backing off to the global default, the agent returns None, signaling that it should seek guidance. This prevents false confidence.

**4. Logarithmic search**: With proper indexing (e.g., trie structure), backoff resolution is O(log n) in the number of contexts, making it efficient even with thousands of contexts.

---

## 4. Statistical Admission: Preventing Overfitting

A naive implementation would create a new context for every unique situation encountered. This leads to overfitting: the agent creates a context for "ClientA | month-end | $10,342.17 | office-supplies | Tuesday | rainy-weather" based on a single observation. This context has 100% confidence (1 success, 0 failures) but is meaningless—it's fitting noise, not signal.

Statistical admission criteria prevent this by requiring sufficient evidence before creating a new context:

```python
def should_create_context(
    child_state: BeliefState,
    min_observations: int = 5,
    parent_state: Optional[BeliefState] = None
) -> bool:
    """
    Decide whether to create a new context or use parent.

    Args:
        child_state: Proposed child context's belief state with observations
        min_observations: Minimum observations required for context creation
        parent_state: Parent context's belief state (None if creating global default)

    Criteria:
    1. Sufficient observations (≥ min_observations)
    2. Predictive improvement over parent (if parent exists)
    """
    # Helper to compute accuracy with divide-by-zero guard
    def compute_accuracy(context_state: BeliefState) -> float:
        total = context_state.success_count + context_state.failure_count
        if total == 0:
            return 0.0  # No observations yet
        return context_state.success_count / total

    # Need minimum observations
    total_observations = child_state.success_count + child_state.failure_count
    if total_observations < min_observations:
        return False

    # If no parent, create (this is the global default)
    if parent_state is None:
        return True

    # Check if child context provides predictive improvement
    child_accuracy = compute_accuracy(child_state)
    parent_accuracy = compute_accuracy(parent_state)

    # Require meaningful improvement (e.g., 10% absolute gain)
    improvement_threshold = 0.10
    if child_accuracy - parent_accuracy < improvement_threshold:
        return False  # Not worth the complexity

    return True
```

This creates a natural hierarchy where contexts are only created when they provide predictive value. If "ClientA | month-end | >10K" has 90% accuracy and "ClientA | month-end | >10K | office-supplies" also has 90% accuracy, we don't create the more specific context—it's not adding information.

---

## 5. The Global State Contamination Bug

During production deployment, we discovered a subtle but catastrophic bug: sharing temporal state across contexts. The bug manifested as:

**Symptom**: Agent would learn correctly in one context (e.g., ClientA | month-end), then suddenly become uncertain in an unrelated context (e.g., ClientB | mid-month) even though nothing had changed in that context.

**Root cause**: Shared temporal state. The initial implementation stored `last_updated` and `last_outcome` globally per belief, not per context. When the agent updated the belief for ClientA, it set `last_updated = now` and `last_outcome = success`. This global state then affected belief strength calculations for ClientB, even though ClientB hadn't been touched.

**Example**:

```python
# BUGGY IMPLEMENTATION (DO NOT USE)
@dataclass
class BuggyBelief:
    statement: str
    contexts: Dict[ContextKey, float]  # Just strength, no temporal state
    last_updated: datetime  # GLOBAL - WRONG!
    last_outcome: str  # GLOBAL - WRONG!

# Agent processes ClientA invoice successfully
belief.contexts["ClientA|month-end"] = 0.95
belief.last_updated = now()
belief.last_outcome = "success"

# Later, agent evaluates ClientB context
# Belief strength calculation uses global last_updated and last_outcome
# This makes ClientB appear recently successful even though it wasn't touched
# Result: False confidence in ClientB context
```

**Fix**: Each context must maintain independent temporal state:

```python
# CORRECT IMPLEMENTATION
@dataclass
class CorrectBelief:
    statement: str
    contexts: Dict[ContextKey, BeliefState]  # Each context has full state

@dataclass
class BeliefState:
    strength: float
    last_updated: datetime  # INDEPENDENT per context
    last_outcome: str  # INDEPENDENT per context
    success_count: int
    failure_count: int
```

This bug is a general pattern: **any system with context-conditional state must maintain independent temporal state per context**. Sharing temporal state creates hidden coupling that causes bizarre cross-contamination.

---

## 6. Belief Update with Context Isolation

When the agent executes an action and receives feedback, it updates the belief for the specific context:

```python
def update_belief(
    belief: ContextualBelief,
    context: ContextKey,
    outcome: Literal["success", "failure"],
    learning_rate: float = 0.15
) -> None:
    """
    Update belief strength for specific context.

    CRITICAL: Only update the specific context, not parent or child contexts.
    """
    # Get or create belief state for this context
    if context not in belief.contexts:
        # Check admission criteria
        if not should_create_context(context, ...):
            # Use parent context instead
            context = find_parent_context(context)

    state = belief.contexts[context]

    # Update counts
    if outcome == "success":
        state.success_count += 1
        signal = +1
    else:
        state.failure_count += 1
        signal = -1

    # Update strength (bounded EMA)
    state.strength = clip(
        state.strength + learning_rate * signal,
        0.0, 1.0
    )

    # Update temporal state (INDEPENDENT per context)
    state.last_updated = now()
    state.last_outcome = outcome

    # CRITICAL: Do NOT update other contexts
    # Each context evolves independently based on its own experience
```

The isolation principle is critical: updates to one context do not affect other contexts. If the agent succeeds at ClientA | month-end, that doesn't change its confidence in ClientB | mid-month. Each context accumulates its own evidence independently.

This might seem to prevent transfer learning (if the agent learns something about ClientA, shouldn't it transfer to similar ClientB?). Transfer learning is handled separately through belief inheritance and similarity-based initialization, not through shared temporal state.

---

## 7. Pruning: Removing Obsolete Contexts

Over time, contexts can become obsolete:

- **Merged into parent**: If a specific context's accuracy converges to its parent's accuracy, it's no longer providing value and can be pruned.
- **Insufficient data**: If a context was created but never accumulated enough observations, it should be pruned.
- **Stale**: If a context hasn't been used in months, it might be obsolete (e.g., a client that no longer exists).

Pruning criteria:

```python
def should_prune_context(
    context: ContextKey,
    state: BeliefState,
    parent_state: Optional[BeliefState],
    staleness_threshold_days: int = 90
) -> bool:
    """
    Decide whether to prune a context.
    """
    # Prune if stale
    if (now() - state.last_updated).days > staleness_threshold_days:
        return True

    # Prune if insufficient data
    total_observations = state.success_count + state.failure_count
    if total_observations < 5:
        return True

    # Prune if no improvement over parent
    if parent_state is not None:
        parent_total = parent_state.success_count + parent_state.failure_count

        # Guard against divide-by-zero
        if parent_total == 0:
            return False  # Can't compare to parent with no observations

        child_accuracy = state.success_count / total_observations
        parent_accuracy = parent_state.success_count / parent_total

        if abs(child_accuracy - parent_accuracy) < 0.05:
            return True  # Not providing meaningful improvement

    return False
```

Pruning keeps the belief graph lean and prevents it from growing unbounded. In production, we prune contexts quarterly, removing ~15% of contexts that have become obsolete.

---

## 8. Evaluation: Financial Workflow Case Study

We evaluated context-conditional beliefs on a 10-step financial workflow over 90 days:

### 8.1 Experimental Setup

**Contexts**: 4 dimensions (client, period, amount_range, category)

- 12 clients
- 3 periods (month-end, mid-month, quarter-end)
- 4 amount ranges (<$1K, $1K-$10K, $10K-$100K, >$100K)
- 8 categories (office supplies, travel, consulting, etc.)

**Theoretical context space**: 12 × 3 × 4 × 8 = 1,152 possible contexts

**Actual contexts created**: 287 (statistical admission prevented overfitting)

**Baseline**: Scalar beliefs (single global confidence per belief, no context conditioning)

### 8.2 Results: Prediction Accuracy

**Prediction task**: Given a context, predict the correct GL code.

**Scalar beliefs**:

- Accuracy: 67%
- Clarification rate: 41% (agent uncertain, asks for guidance)
- Silent error rate: 18% (agent confident but wrong)

**Context-conditional beliefs**:

- Accuracy: 89%
- Clarification rate: 23% (43% reduction)
- Silent error rate: 7% (61% reduction)

The improvement comes from two sources:

1. **Better confidence calibration**: The agent is confident when it should be (in familiar contexts) and uncertain when it should be (in novel contexts). Scalar beliefs are poorly calibrated—they're either over-confident (averaging high-confidence contexts with low-confidence contexts) or under-confident (averaging low-confidence contexts with high-confidence contexts).
2. **Situational expertise**: The agent learns that GL code 5100 works for ClientA | month-end but GL code 5200 works for ClientB | mid-month. Scalar beliefs can't represent this—they force a single global answer.

### 8.3 Context Distribution

**Most specific contexts** (4 dimensions specified):

- 43 contexts created
- Average observations per context: 47
- Average accuracy: 94%

**Moderately specific contexts** (2-3 dimensions):

- 198 contexts created
- Average observations per context: 23
- Average accuracy: 87%

**General contexts** (1 dimension):

- 46 contexts created
- Average observations per context: 112
- Average accuracy: 79%

This distribution shows the backoff mechanism working correctly. Most contexts are moderately specific (2-3 dimensions), providing a balance between specificity and generalization. Very specific contexts (4 dimensions) have high accuracy but require more observations to create. General contexts (1 dimension) have lower accuracy but serve as reliable fallbacks.

### 8.4 Backoff Frequency

**Exact match**: 67% of queries (agent has experience with exact context)
**1-level backoff**: 21% (drop 1 dimension)
**2-level backoff**: 9% (drop 2 dimensions)
**3+ level backoff**: 3% (drop 3+ dimensions, rare)

This shows that the agent builds specific knowledge quickly. After 90 days, it has exact-match experience for 67% of situations encountered. For the remaining 33%, it successfully backs off to more general knowledge.

---

## 9. Psychological Grounding: Situated Cognition

Context-conditional beliefs operationalize situated cognition theory (Clancey, 1997; Suchman, 1987), which argues that knowledge is not abstract and context-free but situated in specific contexts of use.

Traditional AI assumes knowledge is universal: "If X then Y" applies everywhere. Situated cognition argues that knowledge is contextual: "If X in context C then Y" might not apply in context D.

Example from human expertise: A doctor knows that symptom X indicates disease Y in adult patients but disease Z in pediatric patients. The knowledge "X → Y" is not universal—it's situated in the context "adult patient." Averaging across contexts ("X → Y with 60% confidence, X → Z with 40% confidence") destroys the doctor's expertise. The doctor isn't 60% confident globally—they're 95% confident in adults and 95% confident in children, with different diagnoses.

Context-conditional beliefs capture this situated nature of expertise. The agent doesn't learn "Use GL code 5100 (75% confidence)"—it learns "Use GL code 5100 for ClientA during month-end (95% confidence) and GL code 5200 for ClientB during mid-month (92% confidence)."

---

## 10. Relationship to Hierarchical Backoff in NLP

The backoff mechanism is borrowed from statistical language modeling (Katz, 1987). In NLP, backoff smoothing addresses data sparsity: if you've never seen the trigram "the quick brown," you back off to the bigram "quick brown," then to the unigram "brown."

The same principle applies to beliefs. If the agent has never seen the exact context "ClientA | month-end | $15K | office-supplies," it backs off to "ClientA | month-end | $15K," then to "ClientA | month-end," then to "ClientA," then to the global default.

However, our application differs from NLP in two ways:

**1. Statistical admission**: NLP backoff creates all possible n-grams and backs off when counts are zero. We use statistical admission to avoid creating contexts with insufficient data. This prevents overfitting and keeps the context space manageable.

**2. Independent temporal state**: NLP backoff only tracks counts (how many times did we see this n-gram?). We track full temporal state (when did we last see this context? what was the outcome?). This enables time-based decay and recency weighting.

---

## 11. Conclusion

Context-conditional beliefs preserve situational expertise by representing beliefs as functions from context to confidence rather than scalar averages. Hierarchical backoff resolution finds the most specific matching belief, gracefully degrading to more general knowledge when exact matches don't exist. Statistical admission prevents overfitting by requiring sufficient evidence before creating new contexts. Independent temporal state per context prevents global state contamination.

The framework achieves 89% prediction accuracy (vs. 67% for scalar beliefs) and reduces clarification requests by 43% on a financial workflow. It's psychologically grounded in situated cognition theory and technically grounded in hierarchical backoff from computational linguistics.

The critical implementation insight—independent temporal state per context—prevents a subtle but catastrophic bug where updates in one context corrupt beliefs in unrelated contexts. This is a general pattern: any system with context-conditional state must maintain independent temporal state per context.

---

**Invention Date:** June 8, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art
