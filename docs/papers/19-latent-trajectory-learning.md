# **Latent Trajectory Learning for System-Operator LLMs**

*A story-gap training paradigm for planning and tool execution in enterprise workflows*

**Author:** Forrest

**Date:** October 24, 2025

---

## **Abstract**

We introduce **Latent Trajectory Learning (LTL)** — a training paradigm where models learn to **complete partially observed operational stories** and compile the inferred steps into **tool-agnostic work units** that downstream translators turn into executable actions.

Unlike standard instruction tuning (prompt → response) or chain-of-thought imitation, LTL treats enterprise work as **stateful narratives** with missing links and multiple valid completions.

We formalize:

(i) a **story-graph** representation of operations,

(ii) a **Work-Unit ontology** built around semantic verbs, and

(iii) a **two-model stack** — a Planner trained on story gaps and Translator models trained on pairwise schema or DOM compilation.

We outline a data specification, evaluation benchmarks, and ablation strategy, and situate LTL relative to decision/trajectory transformers, latent-action models, and latent-space planners.

---

## **1. Motivation**

Large-language-model agents often fail in enterprise settings for two reasons:

1. **Instruction-pair tuning** encourages surface compliance but weak causal understanding of multi-step workflows.
2. **Direct tool-calling fine-tunes** overfit to fragile schemas or web structures that drift.

**LTL separates reasoning from execution.**

The Planner learns to complete narrative gaps — reasoning in goals and causal order — while smaller Translators handle local schemas and interfaces.

**This follows the insight that ****trajectories, not prompts, encode operational competence.**

Prior work models trajectories or latent actions in controlled environments; LTL extends that concept to open-ended enterprise stories where each inferred step must compile into real-world API or browser actions.

---

## **2. Related Work**

**Sequence modeling for control.**

Decision and Trajectory Transformers frame reinforcement learning as sequence prediction over trajectories.

LTL borrows the “trajectory as sequence” lens but focuses on *story-gap closure* and multi-valid step inference rather than reward-conditioned rollout.

**Latent actions and latent plans.**

Recent work learns compact latent action spaces to improve control and exploration; others plan in latent state spaces via diffusion.

LTL shares the philosophy but grounds the latent variables in *semantic Work Units* compiled into deterministic system calls.

**Latent reasoning post-training.**

New methods refine reasoning traces in latent space without explicit token-level chains of thought.

LTL complements this by supervising *narrative closure* across operational stories, scoring by goal satisfaction and state validity.

**Language ↔ trajectory prediction.**

Prior studies map language to physical or robotic trajectories; LTL applies analogous reasoning to **business-process trajectories** and digital-system execution — an underexplored domain.

---

## **3. Problem Setup**

We represent enterprise work as a **story** — a sequence of events

**(e_1, \dots, e_T)** over a system state **S**.

Each story includes **masks**: missing steps, hidden preconditions, or ambiguous branches.

The model must infer a **latent trajectory** **\hat{\tau}** that closes these gaps while satisfying **goal constraints** **G** (e.g., a transaction posted, a filing confirmed).

The Planner outputs a sequence of **Work Units**

**U = (u_1, …, u_k)**, each a *semantic verb* with bound slots describing intent but no schema-specific detail.

---

## **4. Method**

### **4.1 Story Graph & Masking**

* **Nodes:** states, documents, or pages.
* **Edges:** actions or events.
* **Masks:** randomly remove or shuffle steps, or hide preconditions while retaining the terminal goal **G**.
* **Negative paths:** include plausible but invalid sequences (e.g., skipping approval) for contrastive learning.

### **4.2 Planner (Core Reasoning Model)**

* Model: instruction-tuned LLM trained for story-gap completion
  **(S_{partial}, G) \rightarrow U_{1:k}**.
* Objective: maximize *closure likelihood* under state validators across multiple valid completions.
* Output: typed Work Units drawn from a fixed Verb Ontology (~60–100 verbs across systems, web flows, and reporting contexts).

### **4.3 Translators (Per-Surface Compilers)**

* Small models or deterministic compilers mapping
  **(u_i, \text{live schema or DOM}) \rightarrow \text{ToolCall}**.
* Trained on pair datasets with hard negatives (missing required fields, wrong selectors).
* Perform deterministic **preflight validation**: requireds, type checks, and link verification.

### **4.4 Validators & Execution Facts**

* After execution, Drivers return **Facts** (record_created, state_update, confirmation_detected).
* A lightweight **Verifier** checks goal predicates **G** and invariants (e.g., balanced ledger, completed submission).
* If constraints fail, the Planner emits **repair Work Units**.

### **4.5 Data Specification (condensed)**

**Story Sample**

```
{
  "goal": "payment_completed",
  "graph": {"nodes": [...], "edges": [...]},
  "masks": {"hide_steps": [3,4]},
  "context": {"organization": "ExampleCorp", "environment": "prod01"},
  "target_work_units": [
    {"tool": "system", "verb": "create_record", "slots": {"source": "PO-0045"}},
    {"tool": "system", "verb": "link_payment", "slots": {"account": "Operating Checking"}}
  ],
  "acceptable_alternatives": [...]
}
```

**Translator Sample**

```
{
  "work_unit": {"tool": "system", "verb": "create_record", "slots": {"source": "PO-0045"}},
  "live_schema": {"object_type": "invoice", "required": ["partner", "items", "..."]},
  "tool_call": {"action": "create_submit", "object_type": "invoice", "payload": {...}},
  "negatives": [...]
}
```

---

## **5. Proposed Evaluation Methodology**

**Note:** This section describes the planned testing protocol for validating the LTL training paradigm. Implementation and evaluation are proposed for future work at Aleq.

### **5.1 Proposed Benchmarks**

* **Ops-10:** ten canonical multi-step operational flows (e.g., order→receipt→invoice→payment).
* **Web-Form-5:** five simulated filing workflows on cloned portals (login, form fill, upload, payment, confirmation).
* **Drift-Stress:** periodic schema/DOM perturbations (renamed fields, reordered sections, new requireds).

### **5.2 Proposed Metrics**

* **Goal Success @ k** – expected fraction of stories satisfying **G** without human input.
* **Repair Rate** – expected proportion requiring re-planning.
* **Compiler Precision / Recall** – planned match of generated ToolCalls to ground truth.
* **Drift Robustness** – expected success delta under schema or DOM perturbation.
* **End-to-End Latency** – planned measurement of plan + compile + execute + verify time.

### **5.3 Planned Ablations**

* Story-gap vs. instruction-pair training.
* Planner-only vs. Planner + Translator split.
* With vs. without negative or alternative trajectories.
* Post-training with latent-reasoning refinement.

---

## **6. Implementation Notes**

* **Verb Ontology:**
  * **System actions: **create_record**, **receive_item**, **post_entry**, **apply_adjustment**, **trigger_workflow**.**
  * **Web actions: **auth_login**, **fill_form**, **upload_file**, **submit_flow**, **capture_confirmation**.**
  * **Reporting actions: **run_report**, **export_csv**, **check_total**.**
* **Drivers:** typed SDKs or API clients for structured systems; browser automation runtimes for web flows.
* **Schema / DOM Providers:**get_schema_meta**, **get_dom_snapshot**.**
* **Idempotency & Replay:** idempotency keys for creation actions; full trace logs for deterministic replay.

---

## **7. Positioning vs. Prior Art**

* **Versus Decision / Trajectory Transformers:**
  LTL performs *story-gap closure* with tool-agnostic semantic outputs, not reward-conditioned sampling.
* **Versus Latent-Action models:**
  LTL binds latent reasoning to *named Work Units* and enforces compiler correctness against live schemas or DOMs.
* **Versus Latent Diffusion Planners:**
  Operates over symbolic enterprise state/action graphs, not vision or motion spaces.

---

## **8. Limitations**

* Requires curated story graphs and validator predicates — lighter than full pair coverage but still non-trivial.
* Translator accuracy is the primary bottleneck under heavy schema or DOM drift.
* Benchmarks and metrics are new; adoption will take time.

---

## **9. Impact & Use Cases**

LTL enables agents that can plan and act across heterogeneous digital systems.

Applications include:

* finance and operations automation,
* regulatory or compliance form submission,
* procurement and onboarding workflows,
* multi-system process orchestration.

Its modularity allows Translators to be swapped for new platforms without retraining the Planner.

---

## **10. Conclusion**

**Latent Trajectory Learning** reframes agent training from *answering prompts* to *closing stories.*

By splitting **planning** and **compilation**, it yields agents that generalize across organizations and interfaces while remaining exact at execution.

Existing research provides the components; LTL packages them into a coherent architecture for real-world system-operator LLMs.

---

## **Mini-Bibliography**

* **Decision / Trajectory sequence modeling:**  *Decision Transformer* ;  *Trajectory Transformer* .
* **Latent action spaces & control:** *Controlling LLMs with Latent Action* (ICML 2025); *Latent Action Learning Requires Supervision.*
* **Latent planning:** *Latent Diffusion Planning for Imitation Learning.*
* **Latent reasoning post-training:** *Efficient Post-Training Refinement of Latent Reasoning.*
* **Language ↔ trajectory modeling:** *Traj-LLM* and related surveys.

---

### **Novel Contributions (summary)**

* Introduces a **story-gap objective** over operational graphs, extending trajectory modeling beyond token or reward spaces.
* Defines a **hard Planner ↔ Translator contract** with compiler-style guarantees.
* **Proposes ****goal-predicate and drift-robustness evaluation** for enterprise-scale agent systems.

---

This version is clean, neutral, and safe to post publicly.

It preserves the originality and authority of your framing — **you still look like the inventor of the concept**, but nothing in it reveals internal stack or proprietary system details.
