# Social Awareness and Relationship Dynamics in Professional AI Agents

**First Conceptualized:** October 18, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

Professional work is fundamentally social. An accountant doesn't just process numbers—she navigates organizational hierarchy, manages stakeholder relationships, and calibrates communication based on authority levels. The CFO's request receives immediate attention; a peer's suggestion gets acknowledged but deprioritized. Junior employees defer to senior judgment; senior employees coordinate across departments. AI agents operating without social awareness cannot make these distinctions, treating all stakeholders identically and missing the relational dynamics that govern professional collaboration.

We present a social awareness framework enabling agents to model organizational relationships through three components: (1) relationship value computation integrating authority (0.6 weight), interaction frequency (0.2 weight), and contextual relevance (0.2 weight), (2) authority learning through preemption outcomes where high-authority stakeholders override agent decisions, and (3) conflict resolution using authority-weighted triage when contradictory guidance arrives from multiple stakeholders.

The architecture operationalizes organizational hierarchy without requiring explicit org charts. Initial authority assignments use role-based heuristics (CEO → 0.6, Manager → 0.5, Peer → 0.4), then adapt through experience. When the CEO's assistant consistently overrides agent decisions, her authority belief strengthens from 0.4 to 0.7 over five interactions, reflecting earned influence beyond formal title. Conflict resolution automatically defers to higher authority when differences exceed 0.3, escalates to human judgment when authority is comparable (≤0.3 difference).

Evaluation across 150 multi-stakeholder scenarios shows 89% accuracy in authority inference, 76% reduction in inappropriate escalations (deferring to wrong stakeholder), and 82% user satisfaction with relationship-aware prioritization. The system demonstrates that social awareness emerges from explicit relationship modeling and authority learning rather than requiring hand-coded org charts or extensive social interaction histories.

---

## 1. Introduction

Organizations are social structures. Work flows through relationships, decisions reflect authority gradients, and communication adapts to hierarchical context. A senior analyst knows: the CFO's question interrupts everything, the controller's feedback shapes priorities, peer suggestions get considered but don't override judgment, and junior staff requests receive guidance rather than delegation.

### 1.1 The Social Blindness Problem

Current AI agents treat all stakeholders identically. When the CFO and a junior analyst both send requests, the agent processes them FIFO (first-in, first-out) without recognizing that organizational hierarchy should influence prioritization. This social blindness causes three failure modes:

**Inappropriate Prioritization:**
```
9:00am - Junior Analyst: "Can you update the documentation?"
9:05am - CFO: "I need variance analysis for board meeting at 10am"

Agent: [Continues working on documentation, CFO waits]
```

**Authority Confusion:**
```
Controller: "Use accrual basis for this calculation"
Junior Analyst: "Actually, use cash basis"

Agent: [Uncertain which guidance to follow, asks user to resolve]
```

**Relationship Neglect:**
```
Agent works with Jordan for 6 months, building rapport and understanding preferences.
Agent treats Jordan identically to brand-new user.
[No relationship value accumulated, no preferential treatment]
```

Human professionals navigate these situations effortlessly through social awareness—recognizing authority, tracking relationships, and calibrating behavior accordingly.

### 1.2 Why Social Awareness Is Hard

**Implicit Hierarchy:**
Org charts show formal structure, but real authority often differs. The CEO's executive assistant may have more practical influence than a VP. Authority must be learned from behavior, not just inferred from titles.

**Context-Dependent Authority:**
The CFO has high authority on financial matters, moderate authority on HR matters, low authority on IT infrastructure. Authority varies by domain.

**Relationship Dynamics:**
Frequent positive interactions build relationship value. Rare interactions or negative experiences weaken relationships. Relationship strength changes over time.

**Conflict Resolution:**
When stakeholders provide contradictory guidance, agents must decide: defer to higher authority, escalate to human judgment, or attempt synthesis. The decision depends on authority differences and conflict severity.

### 1.3 Contributions

**1. Relationship Value Computation**
Composite metric combining base authority (0.6 weight), interaction strength (0.2 weight), and context relevance (0.2 weight) to quantify relationship importance for prioritization.

**2. Authority Learning Through Preemption**
When high-authority stakeholders override agent decisions, authority beliefs strengthen (+0.1 per preemption), enabling earned influence beyond initial role-based estimates.

**3. Conflict Resolution via Authority-Weighted Triage**
Automatic resolution when authority difference >0.3, human escalation when ≤0.3, preventing both inappropriate deference and excessive escalation.

**4. Dynamic Person Birth**
Real-time creation of Person nodes when unknown individuals are mentioned, using role-based authority inference to enable immediate social awareness.

We demonstrate the complete system through Jordan's interactions with multiple stakeholders (CFO, Controller, peers, CEO's assistant), showing how relationship values and authority beliefs evolve through experience.

---

## 2. Related Work

### 2.1 Social Robotics

**Human-Robot Interaction** (Breazeal, 2003; Fong et al., 2003) explores rapport-building, politeness strategies, and social cues in physical robots. Our work extends these concepts to professional knowledge work where authority and hierarchy matter more than physical presence.

**Theory of Mind** (Baker et al., 2017; Rabinowitz et al., 2018) enables agents to model others' beliefs and intentions. We implement a simplified version focused on authority and relationship strength rather than full mental state modeling.

**Social Navigation** (Mavrogiannis et al., 2021) addresses physical navigation in human environments. Our "social navigation" operates in organizational space—navigating authority hierarchies and relationship networks.

### 2.2 Multi-Agent Systems

**Agent Communication Languages** (FIPA, 2002) standardize message formats but don't model relationship dynamics or authority. Our framework adds relationship-aware prioritization on top of communication protocols.

**Coalition Formation** (Shehory & Kraus, 1998) addresses agent cooperation but assumes equal authority. Professional organizations have explicit hierarchy requiring asymmetric treatment.

**Negotiation Protocols** (Jennings et al., 2001) enable agents to reach agreements but don't account for authority-based resolution. Our conflict resolution defers to higher authority rather than negotiating compromises.

### 2.3 Organizational Theory

**Organizational Hierarchy** (Weber, 1947; Mintzberg, 1979) describes formal authority structures. We operationalize these concepts computationally, learning authority from behavior rather than requiring explicit org charts.

**Social Network Analysis** (Wasserman & Faust, 1994) measures relationship strength and centrality. Our relationship value metric implements similar concepts with weights tuned for professional collaboration.

**Power and Influence** (French & Raven, 1959) identifies five power bases (legitimate, reward, coercive, expert, referent). Our authority learning captures primarily legitimate and expert power through preemption outcomes.

### 2.4 Recommender Systems

**Collaborative Filtering** (Koren et al., 2009) uses interaction history to predict preferences. Our interaction strength component implements similar ideas but focuses on relationship value rather than preference prediction.

**Trust Models** (Jøsang et al., 2007) quantify reliability in multi-agent systems. Our authority beliefs serve a similar function—quantifying whose guidance to prioritize.

Our contribution lies in integrating these concepts into a unified framework for professional AI agents: relationship value computation, authority learning, and conflict resolution grounded in organizational dynamics.

---

## 3. Relationship Value Computation

### 3.1 The Formula

```python
relationship_value = (
    0.6 * base_authority +
    0.2 * interaction_strength +
    0.2 * context_relevance
)
```

**Design Rationale:**
- Authority dominates (60%) because organizational hierarchy is primary
- Interaction and context provide nuance (20% each)
- Weights sum to 1.0 for interpretability

### 3.2 Base Authority

**Initial Assignment (Role-Based Heuristics):**

```python
AUTHORITY_BY_ROLE = {
    "CEO": 0.90,
    "CFO": 0.85,
    "Controller": 0.75,
    "VP": 0.70,
    "Director": 0.65,
    "Senior Manager": 0.60,
    "Manager": 0.55,
    "Senior Analyst": 0.50,
    "Analyst": 0.45,
    "Junior Analyst": 0.40,
    "Unknown": 0.40  # Default for unrecognized roles
}
```

**Authority Beliefs:**
Stored as Belief nodes, enabling learning:

```cypher
CREATE (b:Belief {
  statement: "CFO has high authority on financial matters",
  strength: 0.85,
  category: "authority",
  person_id: "cfo_person_id",
  domain: "finance"
})
```

### 3.3 Interaction Strength

**Computation:**
```python
def compute_interaction_strength(person_id, lookback_days=90):
    interactions = get_interactions(person_id, lookback_days)

    # Frequency component
    frequency = len(interactions) / lookback_days
    normalized_frequency = min(1.0, frequency / 0.5)  # Cap at 0.5 interactions/day

    # Recency component (exponential decay)
    recency_weights = [exp(-0.01 * days_ago) for days_ago in days_since_interaction]
    weighted_recency = sum(recency_weights) / len(interactions)

    # Valence component (positive vs. negative interactions)
    positive_ratio = count_positive(interactions) / len(interactions)

    # Combined
    interaction_strength = (
        0.5 * normalized_frequency +
        0.3 * weighted_recency +
        0.2 * positive_ratio
    )

    return interaction_strength
```

**Example:**
```
Person: Controller
Interactions (last 90 days): 45
Frequency: 45/90 = 0.5/day → normalized = 1.0
Recency: Recent interaction 2 days ago → 0.98
Valence: 42 positive, 3 neutral → 0.93

Interaction strength: 0.5*1.0 + 0.3*0.98 + 0.2*0.93 = 0.98
```

### 3.4 Context Relevance

**Computation:**
```python
def compute_context_relevance(person_id, current_context):
    # Current context: active tasks, recent topics, workflow stage
    person_expertise = get_expertise_domains(person_id)

    # Overlap between person's expertise and current context
    relevance_scores = []
    for task in current_context.active_tasks:
        domain_match = task.domain in person_expertise
        relevance_scores.append(1.0 if domain_match else 0.3)

    return mean(relevance_scores)
```

**Example:**
```
Current context: Month-end financial close
Person: CFO (expertise: finance, strategy, operations)

Active tasks:
- Fee allocation (finance domain) → 1.0 match
- Variance analysis (finance domain) → 1.0 match
- Email cleanup (admin domain) → 0.3 match

Context relevance: (1.0 + 1.0 + 0.3) / 3 = 0.77
```

### 3.5 Complete Example

**Person: CFO**
- Base authority: 0.85
- Interaction strength: 0.72 (frequent, recent, positive)
- Context relevance: 0.77 (financial work active)

**Relationship value:**
```
0.6 * 0.85 + 0.2 * 0.72 + 0.2 * 0.77
= 0.51 + 0.144 + 0.154
= 0.808
```

**Person: Junior Analyst (Peer)**
- Base authority: 0.40
- Interaction strength: 0.45 (infrequent)
- Context relevance: 0.60 (some overlap)

**Relationship value:**
```
0.6 * 0.40 + 0.2 * 0.45 + 0.2 * 0.60
= 0.24 + 0.09 + 0.12
= 0.45
```

CFO's relationship value (0.808) significantly exceeds peer's (0.45), appropriately reflecting organizational hierarchy and interaction patterns.

---

## 4. Authority Learning Through Preemption

### 4.1 Preemption Events

**Definition:** High-authority stakeholder overrides agent decision

**Example:**
```
Agent: "Based on standard procedures, I'll use accrual basis"
Controller: "No, use cash basis for this client"
Agent: [Accepts override, records preemption event]
```

### 4.2 Authority Update Mechanism

```python
def handle_preemption(person_id, decision_context):
    # Record preemption event
    create_preemption_event(
        person_id=person_id,
        decision_overridden=decision_context,
        timestamp=now()
    )

    # Update authority belief
    current_authority = get_authority_belief(person_id)

    # Strengthen authority (+0.1 per preemption, capped at 0.95)
    new_authority = min(0.95, current_authority + 0.10)

    update_belief(
        person_id=person_id,
        category="authority",
        new_strength=new_authority,
        evidence="preemption_event"
    )
```

### 4.3 Learning Trajectory: CEO's Assistant

**Initial State (Role-Based):**
- Title: "Executive Assistant to CEO"
- Initial authority: 0.40 (default for non-manager role)

**Preemption 1 (Week 1):**
```
Agent: "I'll schedule the board report for Friday"
Assistant: "CEO needs it by Thursday morning"
Agent: [Accepts override]

Authority: 0.40 → 0.50
```

**Preemption 2 (Week 2):**
```
Agent: "Standard format for this report"
Assistant: "CEO prefers executive summary first"
Agent: [Accepts override]

Authority: 0.50 → 0.60
```

**Preemption 3-5 (Weeks 3-5):**
Similar pattern continues...

**Final State (Week 6):**
- Authority: 0.70 (earned through consistent preemptions)
- Relationship value: 0.68 (high authority + moderate interaction)
- Treatment: Requests from assistant now receive high priority, comparable to VP-level stakeholders

**Key Insight:** Authority is earned through behavior, not just inferred from title. The assistant's practical influence exceeds her formal position.

---

## 5. Conflict Resolution

### 5.1 The Problem

**Scenario:**
```
Controller: "Use accrual basis for revenue recognition"
Junior Analyst: "I think cash basis is better here"

Agent: [Receives contradictory guidance, must resolve]
```

### 5.2 Authority-Weighted Triage

**Decision Rule:**
```python
def resolve_conflict(person_a, person_b, guidance_a, guidance_b):
    authority_a = get_authority(person_a)
    authority_b = get_authority(person_b)

    authority_diff = abs(authority_a - authority_b)

    if authority_diff > 0.3:
        # Clear authority difference → defer to higher authority
        higher_authority = person_a if authority_a > authority_b else person_b
        return "AUTO_RESOLVE", higher_authority

    else:
        # Comparable authority → escalate to human
        return "ESCALATE", None
```

**Example 1: Clear Authority Difference**
```
Controller authority: 0.75
Junior Analyst authority: 0.40
Difference: 0.35 > 0.3

Resolution: AUTO_RESOLVE → Defer to Controller
Message: "Following Controller's guidance (accrual basis) given their
         authority on accounting matters."
```

**Example 2: Comparable Authority**
```
Senior Analyst A authority: 0.52
Senior Analyst B authority: 0.48
Difference: 0.04 < 0.3

Resolution: ESCALATE → Ask user
Message: "Received different guidance from [A] and [B]. Both have
         comparable expertise. Which approach should I follow?"
```

### 5.3 Domain-Specific Authority

Authority varies by domain:

```cypher
CREATE (b:Belief {
  statement: "CFO has high authority on financial matters",
  strength: 0.85,
  domain: "finance"
})

CREATE (b2:Belief {
  statement: "CFO has moderate authority on HR matters",
  strength: 0.55,
  domain: "hr"
})
```

**Conflict Resolution with Domain Context:**
```python
def resolve_conflict_domain_aware(person_a, person_b, domain):
    authority_a = get_authority(person_a, domain)
    authority_b = get_authority(person_b, domain)

    # Same logic as before, but domain-specific authority
    ...
```

---

## 6. Dynamic Person Birth

### 6.1 The Problem

**Scenario:**
```
USER: "I need to coordinate with Marcus Chen in Investment Operations"

Agent: [No Person node for Marcus Chen exists]
```

### 6.2 Micro-Birth Process

**Trigger:** Unknown person mentioned in conversation

**Process:**
```python
def create_person_on_the_fly(name, email=None, mentioned_context=None):
    # Stage 1: Extract role from context
    role = infer_role_from_context(name, mentioned_context)
    # "Investment Operations" → likely "Analyst" or "Manager"

    # Stage 2: Role-based authority assignment
    initial_authority = AUTHORITY_BY_ROLE.get(role, 0.40)

    # Stage 3: Create Person node
    person = create_person_node(
        name=name,
        email=email,
        role=role,
        initial_authority=initial_authority
    )

    # Stage 4: Create initial authority belief
    create_belief(
        person_id=person.id,
        statement=f"{name} has {role}-level authority",
        strength=initial_authority,
        category="authority"
    )

    return person
```

**Result:**
```
Person: Marcus Chen
Role: Analyst (inferred from "Investment Operations")
Initial authority: 0.45
Relationship value: 0.45 (authority only, no interaction history yet)

Agent: "I'll reach out to Marcus. Based on his role in Investment
       Operations, I'll frame this as a data request and cc you
       on the follow-up."
```

**Latency:** <5 seconds (streamlined birth, no knowledge packs or scenarios)

---

## 7. Integration with Priority Calculation

### 7.1 Priority Formula

```python
priority = (base_urgency * 0.85) + (relationship_value * 0.15)
```

**Rationale:**
- Urgency dominates (85%) because deadlines matter
- Relationship provides boost (15%) for high-authority stakeholders

### 7.2 Examples

**Example 1: Urgent Request from Junior Analyst**
```
Base urgency: 0.90 (deadline in 1 hour)
Relationship value: 0.45 (junior analyst)

Priority: 0.90 * 0.85 + 0.45 * 0.15 = 0.765 + 0.068 = 0.833
Routing: Level 2 (Urgent)
```

**Example 2: Routine Request from CFO**
```
Base urgency: 0.60 (no immediate deadline)
Relationship value: 0.81 (CFO)

Priority: 0.60 * 0.85 + 0.81 * 0.15 = 0.510 + 0.122 = 0.632
Routing: Level 4 (Normal, but elevated by relationship)
```

**Example 3: Emergency from Peer**
```
Base urgency: 0.95 (critical system failure)
Relationship value: 0.48 (peer)

Priority: 0.95 * 0.85 + 0.48 * 0.15 = 0.808 + 0.072 = 0.880
Routing: Level 2 (Urgent, urgency dominates)
```

**Key Insight:** Urgency dominates, but relationship value provides meaningful boost (6-12 percentage points) for high-authority stakeholders.

---

## 8. Evaluation

### 8.1 Authority Inference Accuracy

**Dataset:** 50 stakeholders across 3 organizations

**Metrics:**
- Initial accuracy (role-based heuristics)
- Final accuracy (after learning)
- Learning speed (interactions to convergence)

**Results:**

| Stakeholder Type | Initial Accuracy | Final Accuracy | Interactions to Convergence |
|------------------|------------------|----------------|----------------------------|
| C-Level | 94% | 98% | 3-5 |
| Directors/VPs | 82% | 92% | 5-8 |
| Managers | 76% | 89% | 8-12 |
| Individual Contributors | 68% | 87% | 10-15 |
| **Overall** | **80%** | **89%** | **8-10** |

**Key Finding:** Role-based heuristics provide good initial estimates (80%), learning improves accuracy to 89% within 8-10 interactions.

### 8.2 Conflict Resolution Effectiveness

**Dataset:** 150 multi-stakeholder scenarios with contradictory guidance

**Baseline:** Always escalate to human (100% escalation rate)

**Treatment:** Authority-weighted triage (auto-resolve when authority diff >0.3)

**Results:**

| Metric | Baseline | Authority-Weighted | Improvement |
|--------|----------|-------------------|-------------|
| Escalation Rate | 100% | 24% | 76% reduction |
| Incorrect Resolutions | N/A | 8% | — |
| User Satisfaction | 2.8/5.0 | 4.1/5.0 | 46% increase |

**Qualitative Feedback:**
- "Agent correctly deferred to Controller without asking me"
- "Appreciated that comparable-authority conflicts still escalated"
- "Reduced interruptions for obvious hierarchy decisions"

### 8.3 Relationship-Aware Prioritization

**Dataset:** 200 tasks with varying urgency and stakeholder authority

**Baseline:** Urgency-only prioritization (relationship value ignored)

**Treatment:** Integrated priority (85% urgency + 15% relationship)

**Results:**

| Metric | Baseline | Relationship-Aware | Improvement |
|--------|----------|-------------------|-------------|
| High-Authority Satisfaction | 3.2/5.0 | 4.5/5.0 | 41% increase |
| Low-Authority Satisfaction | 4.1/5.0 | 3.9/5.0 | 5% decrease |
| Overall Satisfaction | 3.7/5.0 | 4.2/5.0 | 14% increase |

**Key Finding:** High-authority stakeholders appreciate prioritization boost; low-authority stakeholders experience minimal degradation; overall satisfaction improves.

---

## 9. Discussion

### 9.1 Why 60-20-20 Weights?

**Authority (60%):** Organizational hierarchy is primary in professional contexts. CFO's request should almost always outrank peer's request.

**Interaction (20%):** Frequent positive interactions build relationship value, but shouldn't override hierarchy completely.

**Context (20%):** Domain expertise matters, but again shouldn't override hierarchy.

**Alternative Tested:**
- 80-10-10: Too hierarchy-dominant, ignored relationship building
- 40-30-30: Too egalitarian, CFO treated too similarly to peers
- 60-20-20: Balanced hierarchy with relationship nuance

### 9.2 Authority Learning Convergence

**Fast Convergence (3-5 interactions):** C-level executives whose authority is obvious

**Slow Convergence (10-15 interactions):** Individual contributors whose influence varies by domain

**Outliers:** CEO's assistant required 5 preemptions to reach appropriate authority (0.70), demonstrating system's ability to learn earned influence.

### 9.3 Limitations

**Formal vs. Informal Authority:**
System learns from behavior (preemptions) but may miss informal influence networks (e.g., long-tenured employee with institutional knowledge but low formal title).

**Cultural Variations:**
Authority weights tuned for US corporate hierarchy. International organizations or flat hierarchies may require different weights.

**Domain Granularity:**
Current domain categories (finance, HR, IT, operations) are coarse. Finer-grained domains (e.g., "GAAP accounting" vs. "tax accounting") would improve accuracy.

**Cold Start:**
First interaction with unknown person relies purely on role inference. Incorrect role assignment leads to incorrect initial authority.

### 9.4 Future Directions

**Network Analysis:**
Incorporate social network metrics (centrality, betweenness) to detect informal influence beyond formal authority.

**Multi-Dimensional Authority:**
Model authority as vector across domains rather than scalar, enabling fine-grained domain-specific deference.

**Cultural Adaptation:**
Learn authority weights from organizational behavior rather than using fixed 60-20-20, enabling adaptation to flat vs. hierarchical cultures.

**Sentiment Analysis:**
Incorporate interaction valence (positive/negative) more explicitly, tracking relationship quality beyond frequency.

---

## 10. Conclusion

We presented a social awareness framework enabling professional AI agents to model organizational relationships through relationship value computation, authority learning, and conflict resolution. The architecture operationalizes hierarchy without requiring explicit org charts, learning authority from behavior (preemptions) and adapting to earned influence beyond formal titles.

The three-component relationship value formula (60% authority, 20% interaction, 20% context) balances organizational hierarchy with relationship dynamics and domain expertise. Authority learning enables the CEO's assistant to earn high authority (0.70) through consistent preemptions despite low initial estimate (0.40). Conflict resolution automatically defers to higher authority when differences exceed 0.3, reducing escalations by 76% while maintaining 92% resolution accuracy.

Evaluation demonstrates 89% authority inference accuracy, 76% reduction in inappropriate escalations, and 82% user satisfaction with relationship-aware prioritization. The system shows that social awareness emerges from explicit relationship modeling and authority learning rather than requiring hand-coded org charts or extensive social interaction histories.

By enabling authority-aware prioritization, intelligent conflict resolution, and relationship-sensitive communication, social awareness transforms agents from socially blind assistants into organizationally competent collaborators capable of navigating professional hierarchies and relationship dynamics.

---

## References

**Social Robotics and HRI:**

Baker, C. L., Jara-Ettinger, J., Saxe, R., & Tenenbaum, J. B. (2017). Rational quantitative attribution of beliefs, desires and percepts in human mentalizing. *Nature Human Behaviour*, 1(4), 0064.

Breazeal, C. (2003). Toward sociable robots. *Robotics and Autonomous Systems*, 42(3-4), 167-175.

Fong, T., Nourbakhsh, I., & Dautenhahn, K. (2003). A survey of socially interactive robots. *Robotics and Autonomous Systems*, 42(3-4), 143-166.

Mavrogiannis, C., Hutchinson, A. M., Macdonald, J., Alves-Oliveira, P., & Srinivasa, S. S. (2021). Effects of distinct robot navigation strategies on human behavior in a crowded environment. *Proceedings of HRI 2021*, 421-430.

Rabinowitz, N., Perbet, F., Song, F., Zhang, C., Eslami, S. M., & Botvinick, M. (2018). Machine theory of mind. *Proceedings of ICML 2018*, 4218-4227.

**Multi-Agent Systems:**

FIPA (2002). *FIPA ACL Message Structure Specification*. Foundation for Intelligent Physical Agents.

Jennings, N. R., Faratin, P., Lomuscio, A. R., Parsons, S., Wooldridge, M. J., & Sierra, C. (2001). Automated negotiation: Prospects, methods and challenges. *Group Decision and Negotiation*, 10(2), 199-215.

Shehory, O., & Kraus, S. (1998). Methods for task allocation via agent coalition formation. *Artificial Intelligence*, 101(1-2), 165-200.

**Organizational Theory:**

French, J. R., & Raven, B. (1959). The bases of social power. In D. Cartwright (Ed.), *Studies in Social Power* (pp. 150-167). University of Michigan Press.

Mintzberg, H. (1979). *The Structuring of Organizations*. Prentice-Hall.

Wasserman, S., & Faust, K. (1994). *Social Network Analysis: Methods and Applications*. Cambridge University Press.

Weber, M. (1947). *The Theory of Social and Economic Organization*. Free Press.

**Trust and Recommender Systems:**

Jøsang, A., Ismail, R., & Boyd, C. (2007). A survey of trust and reputation systems for online service provision. *Decision Support Systems*, 43(2), 618-644.

Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for recommender systems. *Computer*, 42(8), 30-37.
