# AI Years: A Temporal Framework for Measuring Epistemic Maturity in Autonomous Agents

**First Conceptualized:** October 20th, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

Clock time is the wrong yardstick for judging autonomous agents. What matters is earned reliability across composite, real workflows—not how many FLOPs were spent or how long a model has been deployed. We introduce AI Years, a domain-scoped, hardware-agnostic unit of epistemic maturity that advances when an agent earns another "nine" of composite success on a fixed workflow.

Formally, with a workflow chain of length n, one AI Year is the smallest number of validated interaction cycles required to move the workflow's per-step geometric-mean reliability from 0.90 to 0.99, thus lifting chain reliability from 0.9^n to 0.99^n. Subsequent years generalize analogously (0.99 → 0.999, etc.).

The framework centers time on experience and refinement, not clock duration. An agent that processes 2,000 validated cycles per day might complete its first AI Year in 9 days, while a human analyst processing 100 cycles per day takes 180 days to reach the same reliability threshold. This is time dilation: maturity is a function of cycles, not wall time.

We present a formal model for workflows as explicit DAGs, a reliability function that composes step reliabilities under quality gates, a learning dynamic over a belief graph with bounded confidence scores, an AI time-dilation law that maps interaction throughput into experience rate, and a measurement protocol with telemetry schema for product display. The framework is audit-reconstructible, compatible with regulated environments, and directly comparable to junior human teams and static LLM/RPA baselines.

---

## 1. Introduction: The Measurement Problem

Per-step error compounds. A 10-step chain at 90% per-step reliability yields only 0.9^10 ≈ 0.349 chain success—commercially useless. More parameters alone do not fix composite brittleness. The correct focus is earning nines in production via feedback, reflection, and anti-brittle control policies that prevent silent failure.

Current evaluation approaches fail to capture this reality. Benchmarks measure one-shot task success: "Can the agent complete task X correctly?" This is the wrong question for learning agents. The right question is: "How quickly does the agent move from 35% chain success to 90% chain success through accumulated experience?"

Consider two agents:

- Agent A: 95% one-shot success on novel tasks, no learning mechanism
- Agent B: 60% one-shot success on novel tasks, learns from feedback

On day 1, Agent A outperforms Agent B. On day 60, Agent B might achieve 92% success while Agent A remains at 95%. On day 180, Agent B might reach 97% while Agent A is still at 95%. Which agent is more valuable? The answer depends on the deployment timeline and the importance of continuous improvement.

Traditional metrics cannot answer this question because they don't measure learning velocity. They provide a snapshot, not a trajectory. AI Years solves this by defining maturity as the time required to earn reliability milestones, measured in validated interaction cycles rather than clock time.

---

## 2. System Model

### 2.1 Workflow as Explicit DAG

A workflow W is an explicit directed acyclic graph G = (V, E) defined in the knowledge base:

- Each node v ∈ V is a subtask with preconditions, invariants, and outputs
- Each edge e = (u → v) encodes sequencing and data dependency
- A run instantiates a topological traversal; linear chains are a special case with n = |V|

Scope rule (fixed spec): During an AI Year, G is held fixed. If a new subtask is added (chain length n → n+1), the "year clock pauses." Mastery must include the new node.

This formalization is critical. We cannot measure reliability improvement if the workflow keeps changing. The year clock only advances when the agent is learning to execute a fixed set of tasks better, not when we're adding new tasks to the set.

### 2.2 Interaction Cycle (Atomic Experience Unit)

An interaction cycle occurs at subtask granularity:

(Trigger) → (Appraisal) → (Action) → (Feedback)

Only cycles with validated feedback count as experience. Valid feedback sources:

- Human-confirmed corrections (highest weight)
- Systemic checks (e.g., bank/ledger reconciliation, double-entry invariants)
- Robust self-consistency (e.g., multi-pass agreement, ensemble cross-checks) when paired with downstream invariants

The key insight is that not all interactions are learning events. If the agent executes an action but receives no feedback on whether it was correct, that cycle doesn't contribute to maturity. Learning requires a closed loop: action → outcome → validated assessment of correctness.

### 2.3 Belief Graph

The agent maintains a belief graph layered over knowledge and memory:

- Knowledge nodes: policies, procedures, constraints (program templates)
- Memory nodes: event-sourced records (Cycle, Context, Outcome)
- Belief nodes: propositions about how to act in a given workflow state, each with strength B ∈ [0,1]

Update principle (bounded confidence):

B' ← clip(B + α·Δ+ - β·Δ-)

where Δ+ and Δ- aggregate positive/negative evidence from validated cycles, weighted by rater trust, recency, and outcome severity; α, β > 0 are learning rates; clip(·) truncates to [0,1].

Noisy labels: Disputed human guidance contributes low-trust (down-weighted) memory. Reconciled ledger outcomes can override prior low-trust evidence. The belief graph integrates all signals; there is no "last-in-wins."

### 2.4 Quality Gates (Anti-Brittle Control)

A subtask v is guarded by three canonical gates:

1. Uncertainty Gate: if B_v < τ_u, do not guess—clarify
2. Policy Gate: if rule checks fail (e.g., segregation of duties, amount limits), escalate or route to compliant path
3. Social Gate: selects the correct interaction stance (e.g., "request confirmation" vs. "issue decision") based on stakeholder profile and context

Gating transforms potential silent failures into explicit clarifications that preserve chain progress and produce high-value learning signals.

This is the anti-brittle mechanism. Rather than allowing the agent to guess when uncertain (which would produce failures that corrupt the reliability measurement), we force it to clarify. The clarification itself is counted as a success in the reliability calculation because the outcome is correct—the agent didn't fail, it appropriately deferred.

### 2.5 Step and Chain Reliability

Let r_i denote effective success probability for step i under gating:

- Let π_i = Pr(B_i ≥ τ_u) (probability agent attempts autonomously)
- Let s_i = Pr(correct | attempt) (autonomous success)
- Let q_i = Pr(correct | clarify) (post-clarify success; typically near 1, bounded by human/ledger error)

Then, empirically from logs:

r_i ≈ π_i · s_i + (1 - π_i) · q_i

where clarify events are counted as non-failures (learning-positive, cost-bearing successes).

For a linear chain of length n, chain reliability:

R_chain = ∏(i=1 to n) r_i

g ≡ (R_chain)^(1/n) = exp((1/n) ∑(i=1 to n) ln r_i)

with g the per-step geometric-mean reliability.

For DAGs with branches, R_chain composes along realized paths.

---

## 3. Formal Definition of an AI Year

**Definition (AI Year, Year k):**

Fix a workflow G with chain length n. Let g_t denote the measured per-step geometric-mean reliability at time t (accumulated cycles). The agent completes AI Year k when g_t crosses target:

g_k = 1 - 10^(-k)

starting from at least g_(k-1). Thus Year 1 is 0.90 → 0.99; Year 2 is 0.99 → 0.999, etc.

**Minimal cycles interpretation:**

Let Y_k be the minimal number of validated interaction cycles required to advance from g_(k-1) to g_k on G. Y_k is the length of AI Year k in experience units (hardware-agnostic).

**Scope change rule:** If n increases, the year pauses; targets apply to the augmented chain.

This definition has several important properties:

1. **Domain-scoped**: Each workflow has its own age. An agent can be "2.3 AI Years old" at accounts payable while "0.7 AI Years old" at accounts receivable.
2. **Hardware-agnostic**: The year is measured in cycles, not seconds. A faster system completes years faster in wall time, but the experience requirement is the same.
3. **Comparable**: We can compare agent maturity to human maturity by measuring how many cycles each requires to reach the same reliability threshold.
4. **Audit-reconstructible**: Every cycle is logged with full context. A regulator can replay the learning history and verify that the agent actually earned its claimed maturity.

---

## 4. AI Time Dilation (Experience Rate vs. Clock Time)

Let:

- Y_1 = cycles to complete Year 1 on workflow G
- λ = validated cycles per day (throughput; depends on usage, not hardware alone)
- AI-years-per-day = λ / Y_1 (locally around Year 1; generalize with Y_k)

Human comparison: If a junior analyst accrues λ_h ≈ 100 validated cycles/day and takes ~6 months to reach g = 0.99 (≈ 18,000 cycles), while the agent accrues λ_a ≈ 2,000 cycles/day with higher feedback density via 24/7 operation and automated checks, then:

AI Year 1 length ≈ 18,000 cycles
AI time ≈ 18,000 / 2,000 = 9 days

This is time dilation: maturity is a function of cycles, not wall time.

The implications are profound. An agent that operates 24/7 with automated validation can accumulate experience 20x faster than a human working 8 hours/day with manual validation. This doesn't mean the agent is "smarter"—it means it has more opportunities to learn.

Conversely, an agent deployed in a low-volume environment might take longer in wall time to reach maturity than a human, even if it learns from each cycle more efficiently. If the agent only processes 10 invoices per day while a human processes 50, the human accumulates experience faster despite being slower per cycle.

---

## 5. Developmental Epochs (Domain-Scoped "Age")

Define epochs by g thresholds and operational behaviors:

| Stage        | Symbol | Criterion (per-step g) | Operational Character                       |
| ------------ | ------ | ---------------------- | ------------------------------------------- |
| Infant       | 🧠₀   | g < 0.90               | Reactive; asks often; heavy gating          |
| Juvenile     | 🧠₁   | 0.90 ≤ g < 0.95       | Begins stable clarifications; fewer repeats |
| Apprentice   | 🧠₂   | 0.95 ≤ g < 0.99       | Executes with supervision; tight loops      |
| Professional | 🧠₃   | 0.99 ≤ g < 0.995      | Self-reflective; low clarify rate           |
| Expert       | 🧠₄   | 0.995 ≤ g < 0.999     | Autonomous in-domain; rare escalation       |
| Master       | 🧠₅   | g ≥ 0.999             | Meta-reasoning; resilient to drift          |

The agent reports age per workflow (e.g., AP vs. AR can have different ages).

These epochs provide intuitive labels for maturity levels. Rather than saying "the agent has 0.992 per-step reliability," we say "the agent is a Professional (Year 1.2) at accounts payable." This communicates both the quantitative measure and the qualitative operational character.

---

## 6. Benchmark Sketch: 10-Step AP Workflow

**Setup:** Linear chain n = 10: intake → header parse → line-item code → three-way match → exception route → approval → payment file creation → bank release → ledger post → reconciliation.

**Initial state:** g_0 = 0.90 ⇒ R_0 = 0.9^10 ≈ 0.349

**Gating policy:** τ_u = 0.7 at start, rising to 0.85 as beliefs strengthen; Policy Gate enforces segregation of duties and amount caps; Social Gate chooses request tone per approver profile.

**Observed over Year 1 (illustrative but numerically coherent):**

- Validated cycles: Y_1 ≈ 18,000
- Clarify rate c: 0.27 → 0.11
- Mean ΔB per reflection epoch: +0.09
- Error half-life t_(1/2)^e: 1,100 → 520 cycles
- Per-step geometric mean g: 0.90 → 0.992
- Chain reliability R_chain: 0.349 → 0.927

**Practical reliability:** When counting clarify-then-correct as success (the right operational metric—customers care about outcome, not ego), live success exceeds 97% by mid-Year-1 due to aggressive gating. Autonomous-only success lags initially but converges as c decays.

**Contrast baselines:**

- Static LLM (no learning, no gates): remains at ~35% chain success; sporadic silent failures
- RPA: brittle outside scripted exceptions; fails open when novel invoices appear
- Junior human team: reaches similar g in ~4-6 months of intermittent exposure; higher variance; limited 24/7 cadence

The key insight is that the agent reaches professional-level reliability (g > 0.99) faster than a human in wall time (9 days vs. 180 days) because it accumulates cycles faster, but the experience requirement is comparable (18,000 cycles for both).

---

## 7. Commercial Telemetry and the Maturity Badge

Expose a Maturity Badge per workflow:

```
AP v3 — Age 1.2 AI Years — 99.1% per-step (91.8% chain) — Clarify 12% — Last audit: pass
```

API (read-only) excerpt:

```json
{
  "workflow_id": "AP:v3",
  "age_ai_years": 1.2,
  "g": 0.991,
  "R_chain": 0.918,
  "clarify_rate": 0.12,
  "audit_status": "pass",
  "updated_at": "2025-10-19T10:32:00Z"
}
```

The badge serves multiple purposes:

1. **Trust signal**: Customers can see the agent's maturity level before relying on it
2. **Deployment decision**: Organizations can set policies like "only deploy agents with Age > 1.0"
3. **Continuous monitoring**: Declining g or rising clarify rate signals drift or degradation
4. **Competitive differentiation**: "Our agent is 2.3 AI Years old" is more meaningful than "our model has 70B parameters"

Pricing linkage is intentionally deferred; the badge's purpose is trust, not monetization.

---

## 8. Governance, Risk, and Drift

### 8.1 Drift and Useful Life

Drift metric: Error resurgence rate—the reappearance frequency of previously-extinguished error classes. Rising resurgence signals misalignment with evolving reality (policies, data distributions).

Useful life: A workflow's "age" is valid as long as resurgence remains below threshold and audits pass. Exceeding thresholds triggers maintenance: policy updates, retraining, or new gate tuning. Updates rejuvenate the agent—knowledge refresh without erasing earned beliefs.

This addresses a critical concern: does the agent's maturity degrade over time? The answer is: it depends on whether the environment changes. If policies, vendors, and procedures remain stable, the agent's maturity persists. If the environment shifts (new regulations, new vendors, new approval thresholds), the agent must relearn, and its effective maturity decreases.

The error resurgence metric provides an early warning system. If errors that were extinguished months ago start reappearing, that signals drift. The agent's beliefs are no longer aligned with reality, and intervention is required.

### 8.2 Auditability Requirements

- Event-sourced memory → Turn linkage
- Tamper-evident hashes for artifacts and reconciliations
- Deterministic replay of belief updates per reflection epoch
- Retention aligned to sector overlays (HIPAA, GLBA, 17a-4, etc.)

For regulated industries (finance, healthcare, legal), auditability is non-negotiable. The AI Years framework is designed with this in mind. Every cycle is logged with full context: what the agent believed, what action it took, what feedback it received, how beliefs updated. A regulator can replay this history and verify that the agent's claimed maturity is grounded in actual validated performance, not inflated metrics.

---

## 9. Conclusion

AI Years reframes time for agents: maturity equals nines earned, not seconds elapsed. The unit is domain-scoped, workflow-exact, hardware-agnostic, and audit-reconstructible. It rewards anti-brittle designs—uncertainty gating, policy checks, social awareness—and provides a crisp, comparable signal of trust for customers and regulators.

The framework solves the measurement problem that plagues current agent evaluation. Rather than asking "Can this agent complete task X?" (a static question), we ask "How quickly does this agent move from 35% to 90% chain success?" (a dynamic question). The answer—measured in AI Years—provides a meaningful, comparable metric of epistemic maturity.

For practitioners, AI Years provides a deployment framework: don't ask "Is this agent ready?" Ask "How old is this agent at this workflow?" An agent that's 0.3 AI Years old is still learning and requires supervision. An agent that's 2.0 AI Years old is mature and can operate autonomously. The age is objective, auditable, and grounded in validated performance.

For researchers, AI Years provides a benchmark framework that measures what matters: learning velocity, not one-shot performance. It enables comparisons across agents, across domains, and across time—comparisons that current benchmarks cannot support.

The future of autonomous agents is not about building systems that are perfect on day one. It's about building systems that learn, improve, and earn trust through accumulated validated experience. AI Years provides the temporal framework to measure that journey.

---

**Invention Date:** June 15, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art
