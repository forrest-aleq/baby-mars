# **The Planner–Translator–Driver Architecture for Executable Agents**

*A modular execution framework for system-operator LLMs built on Latent Trajectory Learning*

**Author:** Forrest

**Date:** October 14, 2025

---

## **Abstract**

We present the **Planner–Translator–Driver (PTD)** architecture — a modular execution framework that enables large language models to perform reliable, verifiable actions in digital systems.

PTD separates cognition from control:

* a **Planner** reasons over goals and emits semantic Work Units,
* **Translators** compile those units into precise API or browser calls, and
* **Drivers** execute them deterministically, returning machine-verifiable outcomes.

This separation mirrors the structure of compilers and operating systems — reasoning in one layer, execution in another — yielding agents that are both general and safe.

PTD is designed as the operational complement to **Latent Trajectory Learning (LTL)** (Forrest, 2025), which teaches models *how to infer and complete story-based workflows.*

Together, LTL and PTD form a unified foundation for system-operator LLMs capable of end-to-end enterprise execution.

---

## **1. Motivation**

LLM-based agents break down when the same model is asked to both *reason* and  *act* .

In production, this leads to three systemic failures:

1. **Schema Drift Fragility** – a single DOM or API change can collapse the agent’s chain of thought.
2. **Entangled Errors** – reasoning mistakes and syntax errors are indistinguishable.
3. **Lack of Verifiability** – no clear evidence that an action actually occurred.

The PTD architecture decouples these concerns.

Reasoning is isolated in the **Planner**, translation in modular **Translators**, and execution in deterministic **Drivers**.

This design borrows its logic from software systems themselves: compilers separate parsing, codegen, and runtime execution for the same reason — transparency, safety, and testability.

---

## **2. Relationship to Latent Trajectory Learning (LTL)**

The **LTL paradigm** defines *how agents learn operational reasoning* through story-gap completion and latent trajectory inference.

It trains the Planner to think in terms of causal steps and semantic verbs — not literal field names or selectors.

The **PTD architecture** defines  *how that learned reasoning expresses itself in the real world* .

LTL builds the mind; PTD builds the body.

| **Aspect** | **Latent Trajectory Learning (LTL)** | **Planner–Translator–Driver (PTD)** |
| ---------------- | ------------------------------------------ | ------------------------------------------- |
| Purpose          | Train reasoning and planning               | Execute reasoning in real systems           |
| Input            | Incomplete story graphs                    | Goal state + current environment            |
| Output           | Semantic Work Units                        | Verified Execution Facts                    |
| Domain           | Learning paradigm                          | Operational architecture                    |
| Dependency       | None (core training)                       | Built atop LTL-trained Planner              |

---

## **3. Architecture Overview**

PTD is composed of four cooperating layers:

1. **Planner** – semantic reasoner that plans actions using LTL-trained cognition.
2. **Translator** – per-surface compiler that converts Work Units into concrete ToolCalls.
3. **Driver** – deterministic executor that carries out those calls.
4. **Verifier** – optional critic ensuring outcomes match goal constraints.

### **Figure 1. Conceptual Flow**

```
Goal → Planner → (Work Units)
              ↓
        Translators → (ToolCalls)
              ↓
           Drivers → (Execution Facts)
              ↓
           Verifier → (Goal satisfied?)
```

Each layer communicates only through typed, auditable contracts.

This design allows independent improvement and versioning without retraining the full system.

---

## **4. Planner (Semantic Reasoner)**

* Operates as the **cognitive front-end** of the system.
* Receives task context, current state, and goal conditions.
* Outputs a **Plan** — an ordered list of Work Units, each a high-level intent (e.g., **create_record**, **approve_request**, **submit_form**).
* Trained via **Latent Trajectory Learning**, enabling it to infer causal sequences even under incomplete information.
* Output schema: semantic only — verbs, entities, slots, constraints — never raw selectors or fields.

Example Work Unit:

```
{
  "unit_id": "U-202",
  "tool": "web",
  "verb": "fill_form",
  "entities": {"page": "tax_portal", "form": "monthly_sales"},
  "slots": {"period": "Q3 2025", "amount": 12450.00},
  "constraints": [{"must_verify": "submission_confirmation"}]
}
```

---

## **5. Translators (Per-Surface Compilers)**

Each Translator converts Work Units into **ToolCalls** for a specific interface or environment.

Examples:

* API Translator (structured data systems)
* Web Translator (browser automation)
* Analytics Translator (query/report systems)
* Payment Translator (secure transaction systems)

**Training regime: ****supervised pair fine-tuning** on (WorkUnit, Live Schema/DOM) → ToolCall**.**

They are small, lightweight models or deterministic compilers that:

* expand semantic slots into valid payloads,
* resolve field or selector mappings dynamically,
* run preflight validation before execution,
* handle interface drift locally (no retraining of Planner required).

Example ToolCall:

```
{
  "call_id": "C-202a",
  "tool": "web",
  "action": "fill_and_submit",
  "payload": {
    "selectors": {"period_field": "#q3", "amount_field": "#amt"},
    "values": {"period": "Q3 2025", "amount": "12450.00"}
  },
  "verify": [{"type": "dom_check", "text": "Submission successful"}]
}
```

---

## **6. Drivers (Deterministic Executors)**

* Execute ToolCalls against real systems.
* **Provide ** **idempotency** **, ** **transaction logging** **, and ****rollback** mechanisms.
* Return **Execution Facts** — verifiable machine statements describing what happened.
* Contain no LLM components; implemented as strict, testable infrastructure code.

Example Execution Facts:

```
{
  "facts": [
    {"kind": "form_submitted", "target": "tax_portal"},
    {"kind": "confirmation_detected", "text": "Submission successful"}
  ],
  "errors": [],
  "warnings": []
}
```

---

## **7. Verifier (Critic Layer)**

* Consumes Execution Facts and goal predicates.
* Determines whether the action achieved its intended result.
* Can operate as:
  * a deterministic ruleset, or
  * a small classification model trained on success/failure traces.
* When verification fails, the Planner receives structured feedback to generate **repair Work Units.**

---

## **8. Training and Integration Pipeline**

| **Component**  | **Trained With**            | **Objective**                                    |
| -------------------- | --------------------------------- | ------------------------------------------------------ |
| **Planner**    | Latent Trajectory Learning corpus | Infer causal Work Units under incomplete context       |
| **Translator** | Pairwise compilation data         | Produce syntactically and semantically valid ToolCalls |
| **Driver**     | No training                       | Deterministic execution with property-based tests      |
| **Verifier**   | Optional fine-tuning              | Detect unmet goal predicates and route repairs         |

This pipeline ensures that reasoning and execution improve independently — the Planner can become smarter without schema-specific retraining, while Translators adapt to environmental changes without touching the cognitive layer.

---

## **9. Proposed Evaluation Protocol**

**Note:** This section describes the planned metrics for assessing PTD architecture performance. Implementation and evaluation are proposed for future work at Aleq.

To measure real-world reliability:

* **Plan Accuracy:** expected proportion of valid Work Units generated.
* **Compiler Precision / Recall:** planned measurement of exact match between generated and expected ToolCalls.
* **Execution Success Rate:** target metric for successful completions over total attempts.
* **Goal Satisfaction:** expected fraction of tasks meeting all verification predicates.
* **Drift Robustness:** planned measurement of success rate change under schema or DOM perturbations.
* **Recovery Latency:** target mean time to detect and repair a failed trajectory.

---

## **10. Advantages**

1. **Modular Intelligence:** Each layer is independently testable and improvable.
2. **Transparent Execution:** Every decision has a verifiable artifact — Plan → Call → Fact.
3. **Drift Tolerance:** Translators absorb schema and interface change.
4. **Determinism:** Drivers guarantee reproducibility and auditability.
5. **Portability:** Swap Translators to operate across new platforms without retraining the Planner.
6. **Human Oversight:** Verifier layer provides explicit intervention points.

---

## **11. Limitations and Future Work**

* Translator scaling is the primary bottleneck — new systems require new compilers.
* Version drift between Planner ontologies and Translator schemas must be monitored.
* Further research is needed on **automatic Translator synthesis** via demonstrations or schema introspection.
* Integration of symbolic verifiers and human-in-loop review pipelines is ongoing.

---

## **12. Conclusion**

The **Planner–Translator–Driver architecture** provides a disciplined framework for turning LLM reasoning into verifiable digital action.

By separating semantic planning from system-specific execution, it enables agents that are interpretable, testable, and resilient to drift.

In conjunction with **Latent Trajectory Learning**, which teaches the Planner to reason in narratives, PTD completes the loop:

**LTL gives the agent a mind. PTD gives it a body.**

Together they define a new class of **System-Operator LLMs** capable of both understanding and doing.

---

Perfect. Here’s how we’ll handle it cleanly: below are the **two figures** you’ll want for the paper — both described conceptually **and** written in Markdown/diagram syntax (so you can drop them into any renderer like Mermaid, draw.io, Figma, or LaTeX).

They match the visual and conceptual tone of your *Latent Trajectory Learning (LTL)* paper.

---

## **Figure 1 – The Planner–Translator–Driver Stack**

**Purpose:**

Illustrates the control flow and data contracts between each layer: Planner (reasoning), Translator (compilation), Driver (execution), and Verifier (feedback).

---

### **Conceptual Description**

* **Planner** (top): Receives goal + context → outputs semantic *Work Units* (e.g., **create_record**, **fill_form**).
* **Translators** (middle): Each one compiles Work Units into executable *ToolCalls* for a specific surface (API, Web, Database, etc.).
* **Drivers** (bottom): Deterministically execute ToolCalls and emit  *Execution Facts* .
* **Verifier** (right): Consumes Execution Facts, checks goal predicates, and routes failures back to Planner as  *repair signals* .

---

### **Mermaid Diagram**

```
flowchart TD
    A[Goal + Context] --> B[Planner (LTL-trained Reasoner)]
    B -->|Work Units| C[Translator(s)]
    C -->|ToolCalls| D[Driver(s)]
    D -->|Execution Facts| E[Verifier]
    E -->|Feedback / Repair| B

    subgraph Translator(s)
      C1[API Translator]
      C2[Web Translator]
      C3[Data Translator]
    end
    B -->|Semantic Intents| C1
    B -->|Semantic Intents| C2
    B -->|Semantic Intents| C3
    style A fill:#d8eaff,stroke:#3178c6
    style B fill:#e3f2fd,stroke:#1565c0
    style C fill:#fff3e0,stroke:#ef6c00
    style D fill:#f3e5f5,stroke:#7b1fa2
    style E fill:#e8f5e9,stroke:#2e7d32
```

---

## **Figure 2 – Linking Latent Trajectory Learning (LTL) and PTD**

**Purpose:**

Shows how the *training paradigm* (LTL) feeds into the *operational architecture* (PTD).

Visually connects “how the agent learns” → “how the agent acts.”

---

### **Conceptual Description**

1. **LTL Stage (Learning):**
   * Input: Partial story graphs with missing steps.
   * Model learns to infer causal completions and emit abstract Work Units.
   * Output: A *trained Planner* capable of reasoning in narratives.
2. **PTD Stage (Execution):**
   * The trained Planner runs inside the PTD stack.
   * Translators and Drivers operationalize its reasoning into real-world system actions.
   * The Verifier enforces correctness and provides repair loops.

---

### **Mermaid Diagram**

```
flowchart LR
    subgraph LTL[Latent Trajectory Learning (Training)]
      A1[Partial Story Graphs] --> A2[Planner Learns to Close Gaps]
      A2 --> A3[Trained Semantic Planner]
    end

    subgraph PTD[Planner–Translator–Driver Architecture (Execution)]
      B1[Planner (Reasoning)]
      B2[Translators (Compilers)]
      B3[Drivers (Executors)]
      B4[Verifier (Feedback)]
      B1 -->|Work Units| B2 -->|ToolCalls| B3 -->|Execution Facts| B4
      B4 -->|Repair Signals| B1
    end

    A3 -.-> B1

    style LTL fill:#e3f2fd,stroke:#1565c0
    style PTD fill:#f3e5f5,stroke:#7b1fa2
    style A1 fill:#fff
    style A2 fill:#fff
    style A3 fill:#fff
    style B1 fill:#fff
    style B2 fill:#fff
    style B3 fill:#fff
    style B4 fill:#fff
```

---

## **References**

* Forrest (2025). *Latent Trajectory Learning for System-Operator LLMs.*
* Decision Transformer; Trajectory Transformer.
* *Controlling LLMs with Latent Action* (ICML 2025).
* *Latent Diffusion Planning for Imitation Learning.*
* *Efficient Post-Training Refinement of Latent Reasoning.*
