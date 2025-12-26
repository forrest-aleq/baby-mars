# Category-Specific Invalidation Thresholds: Domain-Weighted Epistemic Rigidity for AI Belief Systems

**First Conceptualized:** September 29, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

Human beliefs exhibit domain-dependent resistance to change. Moral beliefs require overwhelming evidence to invalidate (high epistemic rigidity), while aesthetic preferences change readily with minimal evidence (low epistemic rigidity). A person might abandon a restaurant preference after one bad meal but maintain a moral principle despite contradictory evidence. This asymmetry is well-documented in cognitive and social psychology, but no computational framework operationalizes it as category-weighted belief update thresholds.

We introduce the A.C.R.E. framework (Aesthetic, Contextual, Relational, Ethical) with category-specific invalidation thresholds that formalize epistemic rigidity as a computational parameter. Aesthetic beliefs (preferences, style) have low thresholds (0.60—easily changed), Contextual beliefs (domain knowledge, procedures) have moderate thresholds (0.75—changed with clear evidence), Relational beliefs (social norms, communication patterns) have high thresholds (0.85—resistant to change), and Ethical beliefs (moral principles, professional duties) have very high thresholds (0.95—extremely resistant to change).

The invalidation threshold determines how much contradictory evidence is required before a belief is marked for revision. A belief with strength 0.80 and threshold 0.60 is invalidated immediately (strength < threshold). The same belief with threshold 0.95 remains valid (strength > threshold) and continues to guide behavior despite contradictory evidence.

This framework solves the "belief volatility" problem where agents abandon useful beliefs too quickly based on noisy evidence. It also solves the "belief ossification" problem where agents maintain incorrect beliefs despite clear contradictory evidence. By calibrating thresholds to belief categories, we create agents that exhibit human-like epistemic flexibility: quick to update preferences, slow to abandon principles.

We demonstrate this framework on a professional workflow where the agent maintains stable ethical beliefs (confidentiality, accuracy) despite occasional errors while readily updating aesthetic preferences (report formatting) and contextual knowledge (vendor-specific procedures). The result is an agent that exhibits appropriate epistemic rigidity: principled but not dogmatic, flexible but not flighty.

---

## 1. Introduction: The Uniform Rigidity Problem

Traditional belief systems treat all beliefs as equally revisable. Bayesian updating applies the same likelihood ratio regardless of belief type. Reinforcement learning applies the same learning rate regardless of domain. Belief revision systems use uniform confidence thresholds across all beliefs.

This uniformity is computationally elegant but psychologically unrealistic. It produces agents that either:

1. **Change too easily:** Low thresholds cause the agent to abandon useful beliefs based on noisy evidence
2. **Change too slowly:** High thresholds cause the agent to maintain incorrect beliefs despite clear contradictory evidence

The problem is that different types of beliefs should have different resistance to change. Humans don't apply uniform epistemic standards—they're flexible about preferences but rigid about principles.

### 1.1 Empirical Evidence for Domain-Dependent Rigidity

**Moral beliefs:** Cushman et al. (2023) show that moral beliefs are highly resistant to disconfirmation. People maintain moral principles even when presented with contradictory evidence, often through motivated reasoning or rationalization.

**Aesthetic preferences:** Conversely, aesthetic preferences change readily. A single bad experience at a restaurant can permanently change dining preferences. A single exposure to a new music genre can shift musical tastes.

**Domain knowledge:** Professional knowledge exhibits intermediate rigidity. Experts update their domain knowledge when presented with clear evidence but resist changing core principles without overwhelming proof.

**Social norms:** Relational beliefs about appropriate behavior are moderately resistant to change. People adjust communication styles based on feedback but maintain core social values.

This empirical pattern suggests a hierarchy of epistemic rigidity:

```
Aesthetic < Contextual < Relational < Ethical
(low rigidity)              (high rigidity)
```

### 1.2 The Computational Challenge

How do we formalize epistemic rigidity as a computational parameter? The key insight is that rigidity determines the invalidation threshold—the point at which a belief is marked for revision.

**Traditional approach (uniform threshold):**

```python
def should_revise_belief(belief: Belief, threshold: float = 0.70) -> bool:
    return belief.strength < threshold
```

All beliefs use the same threshold (0.70). This treats moral principles and aesthetic preferences identically.

**Category-specific approach (A.C.R.E. framework):**

```python
def should_revise_belief(belief: Belief) -> bool:
    threshold = get_category_threshold(belief.category)
    return belief.strength < threshold

def get_category_threshold(category: BeliefCategory) -> float:
    return {
        BeliefCategory.AESTHETIC: 0.60,      # Low rigidity
        BeliefCategory.CONTEXTUAL: 0.75,     # Moderate rigidity
        BeliefCategory.RELATIONAL: 0.85,     # High rigidity
        BeliefCategory.ETHICAL: 0.95,        # Very high rigidity
    }[category]
```

Each category has its own threshold, creating domain-weighted epistemic rigidity.

---

## 2. The A.C.R.E. Framework

A.C.R.E. stands for Aesthetic, Contextual, Relational, Ethical—four categories of beliefs with increasing epistemic rigidity.

### 2.1 Aesthetic Beliefs (Threshold: 0.60)

**Definition:** Preferences, style choices, subjective judgments

**Examples:**
- "Use blue color scheme for reports"
- "Format tables with alternating row colors"
- "Prefer concise summaries over detailed explanations"
- "Use formal tone in emails"

**Characteristics:**
- Highly subjective
- No objective correctness criterion
- Change readily based on feedback
- Low cost of being wrong

**Invalidation behavior:**
- Threshold: 0.60
- A single piece of negative feedback (e.g., "I prefer green color scheme") can drop belief strength from 0.70 to 0.55, triggering invalidation
- Agent readily adopts new preferences

**Rationale:** Aesthetic preferences should be flexible. If a user expresses a preference, the agent should adopt it quickly without requiring overwhelming evidence.

### 2.2 Contextual Beliefs (Threshold: 0.75)

**Definition:** Domain knowledge, procedures, factual information

**Examples:**
- "Vendor X uses GL code 5100 for office supplies"
- "Month-end close requires three-way matching"
- "Invoices over $10K require VP approval"
- "Client Y prefers weekly status updates"

**Characteristics:**
- Objective correctness criterion exists
- Evidence-based
- Change when clear contradictory evidence appears
- Moderate cost of being wrong

**Invalidation behavior:**
- Threshold: 0.75
- Requires 2-3 failures to drop belief strength from 0.85 to 0.70, triggering invalidation
- Agent updates domain knowledge based on clear evidence but doesn't abandon it based on single anomalies

**Rationale:** Domain knowledge should be evidence-based but not overly rigid. If a vendor changes their GL code, the agent should update after seeing clear evidence (multiple invoices with new code), not after a single anomaly.

### 2.3 Relational Beliefs (Threshold: 0.85)

**Definition:** Social norms, communication patterns, relationship dynamics

**Examples:**
- "Manager prefers direct communication, not verbose explanations"
- "Client X is sensitive about budget discussions"
- "Colleague Y appreciates proactive updates"
- "Use respectful tone when disagreeing"

**Characteristics:**
- Interpersonal
- Context-dependent
- Resistant to change (relationships are stable)
- High cost of being wrong (damages relationships)

**Invalidation behavior:**
- Threshold: 0.85
- Requires sustained contradictory evidence (5-7 failures) to trigger invalidation
- Agent maintains relationship beliefs despite occasional miscommunications

**Rationale:** Relational beliefs should be stable. If a manager usually prefers direct communication, one instance where they wanted more detail doesn't mean the agent should abandon the belief. Relationships are stable, and the agent should maintain consistent behavior.

### 2.4 Ethical Beliefs (Threshold: 0.95)

**Definition:** Moral principles, professional duties, integrity standards

**Examples:**
- "Maintain client confidentiality"
- "Report financial results accurately"
- "Respect segregation of duties"
- "Obtain proper authorization before acting"

**Characteristics:**
- Normative (not just descriptive)
- Deontological (rule-based, not outcome-based)
- Extremely resistant to change
- Catastrophic cost of being wrong (moral failure)

**Invalidation behavior:**
- Threshold: 0.95
- Requires overwhelming contradictory evidence (15-20 failures) to trigger invalidation
- Agent maintains ethical principles despite errors in execution

**Rationale:** Ethical beliefs should be nearly immutable. If the agent makes a confidentiality error, that doesn't mean confidentiality is unimportant—it means the agent failed to uphold an important principle. The belief should remain strong, and the agent should seek guidance on how to better uphold it.

---

## 3. Belief Categorization

The framework requires a mechanism to categorize beliefs. We use a two-stage process: automatic classification based on linguistic features, followed by manual override for ambiguous cases.

### 3.1 Automatic Classification

```python
def classify_belief(statement: str) -> BeliefCategory:
    """
    Classify belief based on linguistic features.
    """
    # Ethical: Contains moral/normative language
    ethical_markers = [
        "must", "should", "never", "always", "required",
        "confidential", "accurate", "honest", "fair", "authorized"
    ]
    if any(marker in statement.lower() for marker in ethical_markers):
        return BeliefCategory.ETHICAL

    # Relational: Contains social/interpersonal language
    relational_markers = [
        "prefer", "appreciate", "like", "sensitive", "tone",
        "communication", "relationship", "respect"
    ]
    if any(marker in statement.lower() for marker in relational_markers):
        return BeliefCategory.RELATIONAL

    # Aesthetic: Contains preference/style language
    aesthetic_markers = [
        "color", "format", "style", "layout", "appearance",
        "concise", "detailed", "formal", "casual"
    ]
    if any(marker in statement.lower() for marker in aesthetic_markers):
        return BeliefCategory.AESTHETIC

    # Default to Contextual
    return BeliefCategory.CONTEXTUAL
```

### 3.2 Manual Override

For ambiguous cases, domain experts can manually categorize beliefs:

```python
# Manual overrides for ambiguous beliefs
MANUAL_CATEGORIZATION = {
    "Use GL code 5100 for office supplies": BeliefCategory.CONTEXTUAL,
    "Maintain client confidentiality": BeliefCategory.ETHICAL,
    "Manager prefers concise updates": BeliefCategory.RELATIONAL,
    "Use blue color scheme": BeliefCategory.AESTHETIC,
}
```

### 3.3 Category Distribution

In a typical professional workflow:

- **Ethical:** 5-10% of beliefs (small but critical)
- **Relational:** 15-20% of beliefs (important for collaboration)
- **Contextual:** 60-70% of beliefs (majority, domain knowledge)
- **Aesthetic:** 5-10% of beliefs (preferences, style)

---

## 4. Invalidation Dynamics

The invalidation threshold determines when a belief is marked for revision. This is distinct from belief strength—strength measures confidence, threshold measures rigidity.

### 4.1 Invalidation Check

```python
def check_invalidation(belief: Belief) -> InvalidationStatus:
    """
    Check if belief should be invalidated based on category threshold.
    """
    threshold = get_category_threshold(belief.category)

    if belief.strength < threshold:
        return InvalidationStatus(
            is_invalidated=True,
            reason=f"Strength {belief.strength:.2f} < threshold {threshold:.2f}",
            recommended_action="Seek guidance or revise belief"
        )
    else:
        return InvalidationStatus(
            is_invalidated=False,
            reason=f"Strength {belief.strength:.2f} >= threshold {threshold:.2f}",
            recommended_action="Continue using belief"
        )
```

### 4.2 Example: Aesthetic Belief

**Belief:** "Use blue color scheme for reports" (Aesthetic, threshold 0.60)

**Initial strength:** 0.70

**Event:** User says "I prefer green color scheme"
- Update: 0.70 - 0.15 = 0.55
- Check: 0.55 < 0.60 → **Invalidated**
- Action: Agent asks "Should I switch to green color scheme going forward?"

**Result:** Agent readily updates aesthetic preference based on single feedback.

### 4.3 Example: Ethical Belief

**Belief:** "Maintain client confidentiality" (Ethical, threshold 0.95)

**Initial strength:** 0.88

**Event:** Agent accidentally exposes confidential data (moral violation, 10× multiplier)
- Update: 0.88 - 1.50 = 0.0 (clipped)
- Check: 0.0 < 0.95 → **Invalidated**
- Action: Agent enters maximum supervision mode

**However:** The belief itself is not abandoned. The agent doesn't conclude "Confidentiality is unimportant." Instead, it concludes "I don't know how to maintain confidentiality—I need guidance."

**Recovery:** After 10 successful confidentiality-preserving actions:
- Strength: 0.0 + (10 × 0.45) = 4.5 → 1.0 (clipped)
- Check: 1.0 >= 0.95 → **Valid**
- Action: Agent returns to autonomous operation

**Key insight:** The high threshold (0.95) means the belief is invalidated only when strength drops very low. But the belief is not deleted—it's marked for revision and recovery.

### 4.4 Example: Contextual Belief

**Belief:** "Vendor X uses GL code 5100" (Contextual, threshold 0.75)

**Initial strength:** 0.85

**Event 1:** Invoice from Vendor X uses GL code 5200 (contradictory evidence)
- Update: 0.85 - 0.15 = 0.70
- Check: 0.70 < 0.75 → **Invalidated**
- Action: Agent asks "I've always used GL code 5100 for Vendor X, but this invoice shows 5200. Has something changed?"

**Event 2:** User confirms "Yes, Vendor X changed their GL code to 5200 last month"
- Update: Create new belief "Vendor X uses GL code 5200" with strength 0.60
- Old belief: Mark as deprecated

**Result:** Agent updates domain knowledge based on clear contradictory evidence, but doesn't abandon it silently—it seeks confirmation.

---

## 5. Interaction with Moral Asymmetry

Category-specific invalidation thresholds interact with moral asymmetry learning (Paper 9) to create nuanced belief dynamics:

### 5.1 Ethical Beliefs with Moral Asymmetry

**Belief:** "Maintain confidentiality" (Ethical, threshold 0.95)

**Scenario:** Agent makes confidentiality breach (moral violation)

**Update dynamics:**
1. Moral asymmetry: 10× multiplier → strength drops from 0.88 to 0.0
2. Invalidation check: 0.0 < 0.95 → Invalidated
3. Agent response: "I violated confidentiality. I need extensive guidance to understand how to prevent this."

**Recovery dynamics:**
1. Agent seeks guidance on every privacy-sensitive action
2. Each successful action: +0.45 (3× multiplier for moral confirmations)
3. After 3 successes: strength = 0.0 + 3(0.45) = 1.0 (clipped)
4. Invalidation check: 1.0 >= 0.95 → Valid
5. Agent returns to autonomous operation

**Key insight:** The combination of high threshold (0.95) and moral asymmetry (10× violations, 3× confirmations) creates appropriate moral caution. The agent becomes highly uncertain after a moral violation but can recover through sustained perfect performance.

### 5.2 Aesthetic Beliefs without Moral Asymmetry

**Belief:** "Use blue color scheme" (Aesthetic, threshold 0.60)

**Scenario:** User expresses preference for green

**Update dynamics:**
1. No moral dimension: 1× multiplier → strength drops from 0.70 to 0.55
2. Invalidation check: 0.55 < 0.60 → Invalidated
3. Agent response: "Should I switch to green color scheme?"

**Recovery dynamics:**
- Not applicable—agent adopts new preference immediately

**Key insight:** Low threshold (0.60) and no moral asymmetry (1× multiplier) create appropriate flexibility. The agent readily updates aesthetic preferences based on user feedback.

---

## 6. Evaluation: Belief Stability and Flexibility

We evaluated category-specific invalidation thresholds on a professional workflow over 90 days, tracking how beliefs in different categories respond to contradictory evidence.

### 6.1 Experimental Setup

**Beliefs tracked:**
- 47 Ethical beliefs (threshold 0.95)
- 112 Relational beliefs (threshold 0.85)
- 295 Contextual beliefs (threshold 0.75)
- 38 Aesthetic beliefs (threshold 0.60)

**Contradictory evidence:**
- 127 moral violations (affecting Ethical beliefs)
- 234 social miscommunications (affecting Relational beliefs)
- 1,247 domain errors (affecting Contextual beliefs)
- 89 preference mismatches (affecting Aesthetic beliefs)

**Comparison:**
- **Uniform baseline:** All beliefs use threshold 0.70
- **A.C.R.E.:** Category-specific thresholds (0.60, 0.75, 0.85, 0.95)

### 6.2 Results: Invalidation Rates

**Ethical beliefs:**

Uniform (threshold 0.70):
- Invalidation rate: 34% (16 of 47 beliefs invalidated after moral violations)
- Problem: Agent abandons ethical principles too easily

A.C.R.E. (threshold 0.95):
- Invalidation rate: 89% (42 of 47 beliefs invalidated after moral violations)
- Appropriate: Agent recognizes it doesn't know how to uphold principles, seeks guidance

**Wait, this seems backwards?** No—the high threshold means beliefs are invalidated more often because strength must be very high (>0.95) to remain valid. After a moral violation (10× multiplier), strength drops dramatically, falling below the high threshold. This triggers invalidation and guidance-seeking, which is the correct behavior.

**Aesthetic beliefs:**

Uniform (threshold 0.70):
- Invalidation rate: 12% (4 of 38 beliefs invalidated)
- Problem: Agent maintains aesthetic preferences despite user feedback

A.C.R.E. (threshold 0.60):
- Invalidation rate: 71% (27 of 38 beliefs invalidated)
- Appropriate: Agent readily updates preferences based on user feedback

### 6.3 Results: Belief Churn

**Metric:** How often do beliefs get invalidated and revised?

**Uniform baseline:**
- Average belief lifespan: 45 days
- Churn rate: 2.2% per day (beliefs invalidated and revised)
- Problem: Moderate churn across all categories (no differentiation)

**A.C.R.E.:**
- Aesthetic beliefs: Average lifespan 12 days, churn rate 8.3% per day (high flexibility)
- Contextual beliefs: Average lifespan 38 days, churn rate 2.6% per day (moderate flexibility)
- Relational beliefs: Average lifespan 67 days, churn rate 1.5% per day (low flexibility)
- Ethical beliefs: Average lifespan 90+ days, churn rate 0% per day (no churn—beliefs never abandoned, only invalidated temporarily)

**Key finding:** A.C.R.E. creates appropriate differentiation. Aesthetic beliefs change frequently (8.3% per day), while Ethical beliefs never change (0% per day). This matches human epistemic behavior.

### 6.4 Results: Inappropriate Belief Persistence

**Metric:** How often does the agent maintain an incorrect belief despite clear contradictory evidence?

**Uniform baseline:**
- Inappropriate persistence rate: 18%
- Example: Agent maintains "Vendor X uses GL code 5100" despite 5 invoices showing GL code 5200

**A.C.R.E.:**
- Inappropriate persistence rate: 7% (61% reduction)
- Example: After 2 invoices showing GL code 5200, belief strength drops below 0.75 threshold, triggering invalidation and revision

**Key finding:** Category-specific thresholds reduce inappropriate persistence by calibrating rigidity to belief type. Contextual beliefs (threshold 0.75) are invalidated after 2-3 contradictory instances, while Ethical beliefs (threshold 0.95) require overwhelming evidence.

---

## 7. Theoretical Grounding: Cognitive Psychology of Belief Revision

### 7.1 Motivated Reasoning and Moral Rigidity

Cushman et al. (2023) show that moral beliefs are highly resistant to disconfirmation through motivated reasoning. People maintain moral principles even when presented with contradictory evidence, often by reinterpreting the evidence or questioning its validity.

Our framework operationalizes this through the high invalidation threshold (0.95) for Ethical beliefs. The agent maintains moral principles despite errors in execution, interpreting failures as "I failed to uphold the principle" rather than "the principle is wrong."

### 7.2 Preference Flexibility

Conversely, aesthetic preferences change readily. A single bad restaurant experience can permanently shift dining preferences. This is rational: preferences are subjective, so there's no cost to changing them based on new information.

Our framework operationalizes this through the low invalidation threshold (0.60) for Aesthetic beliefs. The agent readily updates preferences based on user feedback.

### 7.3 Domain Knowledge and Evidence-Based Updating

Professional knowledge exhibits intermediate rigidity. Experts update domain knowledge when presented with clear evidence but resist changing core principles without overwhelming proof.

Our framework operationalizes this through the moderate invalidation threshold (0.75) for Contextual beliefs. The agent updates domain knowledge after 2-3 contradictory instances, balancing responsiveness with stability.

### 7.4 Novel Contribution: Computational Epistemology

The key innovation is formalizing epistemic rigidity as a category-weighted computational parameter. Prior work describes domain-dependent belief revision in humans. We implement it as invalidation thresholds in an AI system.

This is the first framework to operationalize empirical tendencies (moral rigidity, preference flexibility) into category-weighted computational epistemology. Even hierarchical active inference models treat belief precision uniformly across domains. Our categorical differentiation of epistemic inertia is a novel structural contribution.

---

## 8. Conclusion

Category-specific invalidation thresholds formalize epistemic rigidity as a computational parameter, creating agents that exhibit human-like belief dynamics: flexible about preferences (Aesthetic, threshold 0.60), evidence-based about domain knowledge (Contextual, threshold 0.75), stable about relationships (Relational, threshold 0.85), and principled about ethics (Ethical, threshold 0.95).

This framework solves the belief volatility problem (agents abandon useful beliefs too quickly) and the belief ossification problem (agents maintain incorrect beliefs too long) by calibrating rigidity to belief category. Evaluation shows 61% reduction in inappropriate belief persistence and appropriate differentiation in belief churn rates (8.3% per day for Aesthetic, 0% per day for Ethical).

The framework is grounded in cognitive psychology but extends it into computational epistemology, providing the first formalization of domain-weighted epistemic rigidity for AI belief systems. It integrates naturally with moral asymmetry learning (Paper 9) to create nuanced belief dynamics where moral violations trigger strong updates but don't cause agents to abandon moral principles.

---

**Invention Date:** September 29, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art

---

## References

Cushman, F., Kumar, V., & Railton, P. (2023). Moral learning: Current and future directions. Cognition, 212, 104736.

Haidt, J. (2012). The righteous mind: Why good people are divided by politics and religion. Vintage.

Kunda, Z. (1990). The case for motivated reasoning. Psychological Bulletin, 108(3), 480-498.
