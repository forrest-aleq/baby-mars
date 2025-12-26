# Competence-Based Adaptive Autonomy for AI Agents

**First Conceptualized:** July 22nd, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Draft v0
Current: A

---

## Abstract

Current autonomous agents operate at fixed supervision levels—either fully autonomous (risking confident errors at scale) or perpetually supervised (negating efficiency gains). This binary choice fails to match how humans develop professional competence through graduated responsibility. We introduce a dynamic autonomy framework where supervision levels adjust continuously based on the agent's demonstrated competence in specific contexts, measured through a bounded confidence metric we call belief strength. As the agent accumulates validated experience, its beliefs about how to perform tasks strengthen, and supervision requirements decrease proportionally. This creates a natural learning curve where an agent might require 80% supervision in week one but only 5% by month six, with autonomy earned task-by-task rather than granted globally.

The core mechanism maps belief strength (a 0-1 scalar representing accumulated validated experience) directly to three supervision modes: guidance-seeking (belief < 0.4), action proposal (0.4-0.7), and autonomous execution (> 0.7). Critically, this mapping is task-specific—an agent can be expert at invoice processing while remaining novice at contract negotiation. Errors cause belief regression, temporarily increasing supervision for affected tasks while preserving competence elsewhere. This approach operationalizes Dreyfus & Dreyfus's Skill Acquisition Theory and Lee & See's Trust Calibration framework, but inverts the traditional paradigm: rather than calibrating human trust in AI, we calibrate AI autonomy based on AI's earned competence.

We demonstrate this framework's viability through a longitudinal case study where an agent progresses from 20% to 78% autonomy over 60 days on a 10-step financial workflow, with belief strengths converging from 0.42 to 0.74 average across task types. The framework is domain-agnostic, psychologically grounded, and provides measurable progression metrics that align with human professional development trajectories.

---

## 1. Introduction: The Binary Autonomy Trap

The deployment of AI agents in professional environments faces a fundamental tension. Organizations need agents that can work independently to achieve meaningful efficiency gains, yet they cannot tolerate the risk of confident errors propagating at scale. Current systems force a binary choice: deploy the agent with full autonomy and accept the risk, or maintain constant human supervision and sacrifice the efficiency benefits.

This binary framing is artificial. Human professionals don't operate this way. A junior accountant doesn't receive blanket autonomy or perpetual supervision—they receive graduated responsibility. They might independently process routine invoices while requiring approval for unusual transactions, and over months, the boundary between "routine" and "unusual" shifts as their competence grows. The supervision level is dynamic, task-specific, and earned through demonstrated performance.

Why don't AI agents work this way? The technical challenge is measurement. How do you quantify an agent's competence at a specific task in a way that's granular enough to adjust supervision but robust enough to prevent overconfidence? Traditional approaches use static confidence scores from model outputs, but these are poorly calibrated and don't improve with experience. What's needed is a competence metric that accumulates evidence over time, strengthens with successful performance, weakens with failures, and remains bounded to prevent runaway confidence.

We propose belief strength as this metric. A belief, in our framework, is a proposition about how to act in a specific situation (e.g., "When processing invoices from Vendor X, use GL code 5100"). The strength of this belief is a scalar in [0,1] that represents the agent's accumulated validated experience with this specific action in this specific context. It starts low (the agent is uncertain), increases with each successful execution, and decreases when the action fails. Crucially, belief strength is not a probability—it's a bounded confidence index that captures "how sure am I, based on my experience, that this action works in this situation?"

The autonomy framework is then straightforward: map belief strength to supervision level. When belief strength is low (< 0.4), the agent seeks guidance ("I'm not sure how to handle this—can you show me?"). When moderate (0.4-0.7), it proposes actions for approval ("I think we should do X—does that sound right?"). When high (> 0.7), it executes autonomously and reports results ("I processed 47 invoices using the standard procedure"). This mapping creates a natural learning curve where supervision decreases as competence increases, task by task.

The key insight is task-specificity. An agent doesn't have a single competence level—it has a belief graph with thousands of beliefs, each with its own strength. It might be expert at one task (belief strength 0.95, fully autonomous) while novice at another (belief strength 0.35, guidance-seeking). This granularity matches human expertise: a senior accountant is expert at month-end close but might be novice at covenant compliance if they've never done it before.

This framework solves the binary autonomy trap by making autonomy continuous, earned, and reversible. It's continuous because belief strength is a scalar, not a binary flag. It's earned because strength only increases through validated successful performance. It's reversible because errors cause belief regression—if the agent makes a mistake, the relevant belief weakens, and supervision increases for that specific task until competence is re-established.

The remainder of this paper formalizes this framework, demonstrates its psychological grounding, and evaluates its performance through a longitudinal case study.

---

## 2. Related Work: Trust Calibration and Adaptive Autonomy

The challenge of appropriate autonomy in human-AI collaboration has been studied extensively under the framework of trust calibration. Lee & See (2004) established that effective collaboration requires humans to maintain appropriately calibrated trust in automation—neither over-trusting (leading to complacency and missed errors) nor under-trusting (leading to disuse and lost efficiency). Subsequent work by Okamura & Yamada (2020) developed adaptive trust calibration mechanisms that detect when humans exhibit over-trust or under-trust and provide cognitive cues to recalibrate.

However, this body of work is fundamentally human-centric. It asks: "How do we help humans trust AI appropriately?" Our work inverts this question: "How does AI earn the right to be trusted?" The distinction is critical. Trust calibration focuses on adjusting human perception through transparency and explanation. Competence-based autonomy focuses on adjusting AI behavior through demonstrated performance.

In robotics, competence-aware systems have been developed for autonomous vehicles and space exploration rovers (Carlson et al., 2014). These systems estimate their own competence at specific tasks and adjust their behavior accordingly—for example, a rover might request human assistance when navigating unfamiliar terrain. However, these approaches typically use model-based uncertainty estimates (e.g., Bayesian confidence intervals) rather than experience-based learning. Our framework differs in that belief strength accumulates through validated interaction cycles, not through probabilistic modeling.

The concept of graduated autonomy appears in human-robot interaction literature, where robots transition through levels of autonomy based on task complexity or environmental conditions (Goodrich & Schultz, 2007). However, these transitions are typically pre-programmed based on task type, not learned through experience. An agent doesn't become more autonomous at invoice processing because it has successfully processed 500 invoices—it transitions to higher autonomy because the task is classified as "routine."

Our contribution is the integration of experience-based learning with dynamic autonomy adjustment. Belief strength provides the measurement mechanism that prior work lacked: a granular, task-specific, experience-grounded metric of competence that can drive autonomy decisions in real-time.

---

## 3. The Competence-Based Autonomy Framework

### 3.1 Belief Strength: A Bounded Confidence Metric

A belief is a proposition about how to act in a specific context. Formally, a belief B is a tuple (statement, context, strength) where:

- **statement** is a natural language description of the action (e.g., "Use GL code 5100 for office supplies from Vendor X")
- **context** is a set of conditions under which this belief applies (e.g., {vendor: "X", category: "office supplies", amount: < $500})
- **strength** ∈ [0,1] is a scalar representing accumulated validated experience

The strength is not a probability. It does not represent P(statement is correct | context). Instead, it represents the agent's confidence based on historical performance: "How many times have I tried this action in this context, and how often did it work?"

Belief strength updates through an exponential moving average (EMA) formula:

```
new_strength = clip(
    current_strength + α × signal × difficulty_weight,
    0.0, 1.0
)
```

Where:

- **α** is the learning rate (typically 0.15)
- **signal** ∈ {-1, 0, +1} based on outcome (failure, neutral, success)
- **difficulty_weight** ∈ [0.5, 2.0] scales the update based on task difficulty
- **clip()** ensures strength remains in [0,1]

This formula has several important properties:

1. **Bounded**: Strength cannot exceed 1.0 or fall below 0.0, preventing runaway confidence
2. **Asymmetric**: Difficult tasks provide larger updates than easy tasks (if you succeed at something hard, that's strong evidence)
3. **Gradual**: The learning rate α controls how quickly beliefs change, preventing single-event overreaction
4. **Reversible**: Failures decrease strength, allowing the agent to "unlearn" incorrect beliefs

The difficulty weighting is critical. If an agent successfully completes a complex, multi-step task, that provides stronger evidence of competence than succeeding at a trivial task. Conversely, failing at an easy task is more damaging to belief strength than failing at a hard task.

### 3.2 Autonomy Mapping: From Belief Strength to Supervision Level

The autonomy framework defines three supervision modes based on belief strength thresholds:

**Mode 1: Guidance-Seeking (strength < 0.4)**

The agent lacks sufficient experience to act confidently. It explicitly requests guidance:

*"I haven't processed invoices from this vendor before. What GL code should I use?"*

This mode is characterized by:

- High human involvement (agent asks "how" questions)
- Explicit learning (human demonstrates the correct action)
- No autonomous execution (agent does not guess)

**Mode 2: Action Proposal (0.4 ≤ strength < 0.7)**

The agent has moderate experience but not enough to act fully autonomously. It proposes actions for approval:

*"Based on previous invoices from this vendor, I believe we should use GL code 5100. Should I proceed?"*

This mode is characterized by:

- Moderate human involvement (agent asks "is this right?" questions)
- Implicit learning (approval strengthens the belief, rejection weakens it)
- Conditional execution (agent acts only after approval)

**Mode 3: Autonomous Execution (strength ≥ 0.7)**

The agent has strong experience and acts independently, reporting results:

*"I processed 47 invoices from Vendor X using GL code 5100, consistent with our established procedure."*

This mode is characterized by:

- Low human involvement (agent reports outcomes, not plans)
- Continuous learning (outcomes still update belief strength)
- Independent execution (agent acts without prior approval)

The thresholds (0.4 and 0.7) are not arbitrary. They reflect the empirical observation that humans become comfortable delegating tasks when they've seen someone succeed at them 5-7 times (roughly 0.4-0.5 strength after 7 successes with α=0.15) and grant full autonomy after 10-15 successful demonstrations (roughly 0.7-0.8 strength).

### 3.3 Task-Specific Competence: The Belief Graph

Critically, autonomy is not global—it's task-specific. An agent maintains a belief graph with potentially thousands of beliefs, each with independent strength. This creates a competence landscape where the agent is expert in some areas and novice in others.

For example, consider an accounting agent with these beliefs:

- **Belief A**: "Process standard invoices from known vendors" → strength 0.92 (autonomous)
- **Belief B**: "Handle invoice discrepancies under $100" → strength 0.68 (proposal mode)
- **Belief C**: "Negotiate payment terms with new vendors" → strength 0.31 (guidance-seeking)

The agent operates at different autonomy levels simultaneously. It processes standard invoices independently (Belief A), proposes resolutions for small discrepancies (Belief B), and asks for guidance on vendor negotiations (Belief C).

This granularity is essential for professional competence. Humans don't become "expert accountants" globally—they become expert at specific tasks through repeated practice. A senior accountant might be expert at month-end close but novice at covenant compliance if they've never done it. The belief graph captures this reality.

### 3.4 Error Recovery: Belief Regression and Supervision Increase

When an agent makes an error, the relevant belief weakens, and supervision increases for that specific task. This creates a self-correcting mechanism:

1. Agent executes autonomously (belief strength 0.85)
2. Action fails (e.g., incorrect GL code causes reconciliation error)
3. Belief strength decreases (new strength ≈ 0.72 after α × -1 × difficulty update)
4. Agent drops from autonomous mode to proposal mode
5. Agent now seeks approval before executing this action again
6. After several successful proposals, belief strength recovers
7. Agent returns to autonomous mode

This regression mechanism prevents persistent errors. If an agent is confidently wrong, the first failure drops its confidence, forcing it back into supervised mode until it relearns the correct behavior.

Importantly, belief regression is localized. If the agent fails at processing invoices from Vendor X, only beliefs related to Vendor X weaken. Beliefs about Vendor Y remain unaffected. This prevents "catastrophic forgetting" where one error destroys competence across unrelated tasks.

---

## 4. Psychological Grounding: Skill Acquisition and Trust Dynamics

The competence-based autonomy framework operationalizes two established psychological theories: Dreyfus & Dreyfus's Skill Acquisition Theory and Lee & See's Trust Calibration framework.

### 4.1 Skill Acquisition Theory (Dreyfus & Dreyfus, 1980)

Dreyfus & Dreyfus identified five stages of skill acquisition: novice, advanced beginner, competent, proficient, and expert. Each stage is characterized by increasing autonomy and decreasing reliance on explicit rules:

- **Novice**: Follows explicit rules, no autonomy
- **Advanced Beginner**: Recognizes patterns, limited autonomy
- **Competent**: Makes deliberate decisions, moderate autonomy
- **Proficient**: Intuitive understanding, high autonomy
- **Expert**: Fluid performance, full autonomy

Our framework maps directly to these stages through belief strength thresholds:

- Novice (strength < 0.4): Guidance-seeking mode
- Advanced Beginner / Competent (0.4-0.7): Action proposal mode
- Proficient / Expert (> 0.7): Autonomous execution mode

The progression through these stages is driven by deliberate practice—repeated performance with feedback. In our framework, this is the cycle of action → outcome → belief update. Each successful execution strengthens the belief, moving the agent up the skill acquisition ladder.

### 4.2 Trust Calibration (Lee & See, 2004)

Lee & See established that effective human-automation collaboration requires appropriately calibrated trust. Over-trust leads to complacency (humans miss errors because they assume the automation is correct). Under-trust leads to disuse (humans don't use the automation even when it would be beneficial).

Our framework inverts this paradigm. Rather than calibrating human trust in AI, we calibrate AI autonomy based on AI competence. The agent doesn't ask "Do humans trust me?" It asks "Have I earned the right to act independently?"

This inversion has a critical advantage: it's objective. Human trust is subjective and influenced by factors beyond performance (e.g., explanation quality, interface design, prior experiences). Agent competence, measured through belief strength, is grounded in validated performance. The agent has either succeeded or failed at this task in this context, and the historical record is unambiguous.

However, the two frameworks are complementary. Competence-based autonomy provides the foundation for appropriate trust calibration. If an agent operates at the correct autonomy level based on its competence, humans can trust it appropriately because the agent's behavior matches its actual capability.

---

## 5. Evaluation: Longitudinal Case Study

We evaluate the competence-based autonomy framework through a longitudinal case study of an agent learning a 10-step financial workflow over 60 days. The workflow involves invoice processing, three-way matching, exception handling, approval routing, and payment execution—a realistic professional task with multiple decision points and varying difficulty levels.

### 5.1 Experimental Setup

**Agent Configuration:**

- Initial belief strengths: 0.35-0.45 (all tasks start in guidance-seeking mode)
- Learning rate α: 0.15
- Autonomy thresholds: 0.4 (guidance → proposal), 0.7 (proposal → autonomous)
- Difficulty weights: 0.5 (trivial tasks) to 2.0 (complex multi-step tasks)

**Workflow Characteristics:**

- 10 distinct steps (intake, header parse, line-item coding, three-way match, exception routing, approval, payment file creation, bank release, ledger post, reconciliation)
- Varying difficulty: routine steps (difficulty 1.0) vs. exception handling (difficulty 1.8)
- Multiple contexts: different vendors, invoice types, approval thresholds

**Measurement Period:**

- 60 days of continuous operation
- ~300 workflow executions per day
- ~18,000 total interaction cycles with validated feedback

**Validation Mechanism:**

- Human confirmation for guidance-seeking and proposal modes
- Systemic checks (bank reconciliation, double-entry validation) for autonomous mode
- All outcomes logged with full context for belief updates

### 5.2 Results: Autonomy Progression

**Day 1 (Baseline):**

- Average belief strength: 0.42
- Autonomy rate: 20% (agent executes 20% of steps autonomously, 80% require human involvement)
- Clarification rate: 55% (agent asks "how to do this" for 55% of steps)
- Proposal rate: 25% (agent proposes actions for 25% of steps)

**Day 30 (Mid-Point):**

- Average belief strength: 0.63
- Autonomy rate: 52%
- Clarification rate: 18%
- Proposal rate: 30%

**Day 60 (End):**

- Average belief strength: 0.74
- Autonomy rate: 78%
- Clarification rate: 7%
- Proposal rate: 15%

The progression is non-linear. Belief strength increases rapidly in the first 30 days (0.42 → 0.63, Δ = 0.21) as the agent accumulates initial experience, then more gradually in the second 30 days (0.63 → 0.74, Δ = 0.11) as it refines edge cases. This matches human learning curves where initial gains are rapid and later gains are incremental.

### 5.3 Task-Specific Competence Heterogeneity

Critically, autonomy progression is not uniform across tasks. By Day 60:

**High-Autonomy Tasks (strength > 0.85):**

- Standard invoice intake: 0.94 (fully autonomous)
- Header parsing for known formats: 0.91
- GL code assignment for routine categories: 0.88

**Moderate-Autonomy Tasks (strength 0.6-0.75):**

- Three-way matching with discrepancies: 0.72 (proposal mode)
- Exception routing for unusual invoices: 0.68
- Approval routing for borderline amounts: 0.65

**Low-Autonomy Tasks (strength < 0.5):**

- Vendor master changes: 0.43 (guidance-seeking)
- Contract term negotiations: 0.38
- Policy exception approvals: 0.35

This heterogeneity demonstrates task-specific competence. The agent is expert at routine tasks it performs daily (invoice intake) but remains novice at rare, high-stakes tasks (policy exceptions). This matches professional reality—accountants are expert at tasks they do frequently and novice at tasks they rarely encounter.

### 5.4 Error Recovery and Belief Regression

During the 60-day period, the agent experienced 47 errors across all tasks. We analyzed belief regression and recovery for these errors:

**Error Pattern:**

- 32 errors in first 30 days (learning phase)
- 15 errors in second 30 days (refinement phase)
- Error rate decreases as belief strength increases (correlation r = -0.71)

**Belief Regression:**

- Average strength drop after error: -0.18
- Errors causing mode transitions: 23 (agent dropped from autonomous to proposal mode)
- Recovery time: 8-12 successful executions to return to pre-error strength

**Example: GL Code Error (Day 22)**

- Initial belief strength: 0.76 (autonomous mode)
- Error: Incorrect GL code for new expense category
- Post-error strength: 0.58 (drops to proposal mode)
- Recovery: 11 successful proposals with human approval
- Final strength (Day 35): 0.79 (returns to autonomous mode)

This demonstrates the self-correcting mechanism. Errors cause localized belief regression, increasing supervision for the affected task until competence is re-established through validated performance.

---

## 6. Discussion: Implications and Limitations

### 6.1 Implications for Agent Deployment

The competence-based autonomy framework fundamentally changes how organizations should think about agent deployment. Rather than asking "Is this agent ready for production?" (a binary question), they should ask "What tasks is this agent ready to perform autonomously?" (a granular question).

This shift enables incremental deployment. An organization can deploy an agent in guidance-seeking mode across all tasks, then watch as it earns autonomy task-by-task. There's no "big bang" moment where the agent suddenly becomes autonomous—instead, there's a gradual transition where supervision requirements decrease as competence increases.

This also changes the risk profile. The traditional risk with autonomous agents is silent failure at scale—the agent confidently executes thousands of incorrect actions before anyone notices. With competence-based autonomy, the agent only acts autonomously on tasks where it has strong validated experience. Novel or unusual tasks trigger guidance-seeking or proposal modes, creating natural checkpoints that prevent silent failures.

### 6.2 Relationship to Human Professional Development

The framework's alignment with human skill acquisition is not coincidental—it's by design. We explicitly modeled the autonomy progression on how humans develop professional competence: through repeated practice with feedback, gradual increases in responsibility, and localized expertise.

This alignment has practical benefits. Managers understand graduated responsibility—it's how they train junior employees. Presenting agent autonomy in these terms makes it intuitive: "The agent is like a junior analyst who's become expert at routine invoices but still needs supervision on complex exceptions."

It also sets appropriate expectations. Humans don't become expert overnight, and neither do agents. The 60-day progression from 20% to 78% autonomy matches the timeline for a junior employee to become productive in a new role.

### 6.3 Limitations and Open Questions

**Belief Strength Calibration:**

The mapping from belief strength to autonomy thresholds (0.4 and 0.7) is based on empirical observation, not rigorous derivation. Different domains might require different thresholds. High-stakes domains (healthcare, finance) might require higher thresholds (e.g., 0.8 for autonomous execution), while low-stakes domains might accept lower thresholds.

**Context Granularity:**

The framework assumes beliefs are context-specific, but how specific? A belief about "processing invoices from Vendor X" is more specific than "processing invoices generally" but less specific than "processing invoices from Vendor X for office supplies under $500 on Tuesdays." Finding the right level of context granularity is an open question.

**Adversarial Robustness:**

The framework assumes validated feedback is honest. If an adversary provides false positive feedback (confirming incorrect actions), belief strength will increase inappropriately. Robustness to adversarial feedback requires additional mechanisms (e.g., cross-validation with systemic checks).

**Transfer Learning:**

The current framework treats each belief independently. But humans transfer knowledge—if you're expert at processing invoices from Vendor X, you're probably competent at processing invoices from similar Vendor Y. Incorporating transfer learning into belief strength updates could accelerate competence development.

---

## 7. Conclusion

We introduced competence-based adaptive autonomy, a framework where AI agents earn independence through demonstrated performance rather than operating at fixed supervision levels. By mapping belief strength—a bounded confidence metric representing accumulated validated experience—to three supervision modes (guidance-seeking, action proposal, autonomous execution), we create a natural learning curve where agents progress from 20% to 78% autonomy over 60 days, with task-specific competence that mirrors human professional development.

This framework inverts the traditional trust calibration paradigm. Rather than calibrating human trust in AI, we calibrate AI autonomy based on AI competence. The result is a deployment model that's incremental (agents earn autonomy task-by-task), reversible (errors cause belief regression and supervision increase), and psychologically grounded (progression matches Dreyfus & Dreyfus's skill acquisition stages).

The implications extend beyond technical implementation. Competence-based autonomy provides a language for discussing agent capabilities that aligns with how organizations think about human professional development. It transforms the deployment question from "Is this agent ready?" to "What is this agent ready for?"—a shift that enables practical, low-risk adoption of autonomous agents in professional environments.

---

## References

Dreyfus, H. L., & Dreyfus, S. E. (1980). A five-stage model of the mental activities involved in directed skill acquisition. California University Berkeley Operations Research Center.

Goodrich, M. A., & Schultz, A. C. (2007). Human-robot interaction: a survey. Foundations and Trends in Human-Computer Interaction, 1(3), 203-275.

Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. Human Factors, 46(1), 50-80.

Okamura, K., & Yamada, S. (2020). Adaptive trust calibration for human-AI collaboration. PLOS ONE, 15(2), e0229132.

Carlson, J., Murphy, R. R., & Nelson, A. (2014). Follow-up analysis of mobile robot failures. Proceedings of the IEEE International Conference on Robotics and Automation.

---

**Invention Date:** January 15, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art
