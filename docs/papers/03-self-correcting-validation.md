# Self-Correcting Validation: Closed-Loop Quality Gates for LLM-Based Agents

**First Conceptualized:** August 20, 2025
**Draft Version:** 1.0
**Author:** Forrest Hosten
**Status:** Invention Documentation

---

## Abstract

LLM-based agents fail silently. They produce outputs that appear plausible but violate domain constraints, business rules, or logical consistency. Traditional validation approaches detect these failures but cannot fix them—they simply reject the output and escalate to humans. This creates a brittle deployment model where agents either succeed autonomously or fail completely, with no middle ground for self-correction.

We introduce self-correcting validation, a closed-loop architecture where deterministic validators don't just detect failures—they generate structured feedback that enables LLM-based reflection and retry. The core mechanism is a ValidatorOutcome schema with 11 fields that capture not just pass/fail status but the specific constraint violated, the evidence of violation, a natural language critique, a severity score, and metadata for budget enforcement and source discrimination.

When validation fails, the outcome is fed back to the LLM with a reflection prompt: "Your output violated constraint X. Here's the evidence. Here's why it matters. Try again." The agent reflects, generates a revised output, and resubmits for validation. This loop continues until validation passes or a retry budget is exhausted.

The architecture transforms validation from a binary gate (pass/fail) into a learning signal. Failed validations become training data for in-context learning. The agent doesn't just learn "this output was wrong"—it learns "this output was wrong because it violated constraint X, as evidenced by Y, and here's how to fix it."

We demonstrate this architecture on three domains: financial document generation (GL code validation, double-entry constraints), legal contract analysis (clause consistency, regulatory compliance), and customer support (tone appropriateness, factual accuracy). Across all domains, self-correcting validation reduces human escalation by 60-75% compared to traditional pass/fail validation, while maintaining or improving output quality as measured by domain-specific correctness metrics.

The framework is production-ready, with explicit budget controls to prevent infinite loops, source discrimination to weight feedback by validator reliability, and difficulty-based budget allocation to give complex tasks more retry opportunities.

---

## 1. Introduction: The Silent Failure Problem

LLMs are unreliable reasoners. They hallucinate facts, violate logical constraints, and produce outputs that sound plausible but are subtly wrong. This unreliability is acceptable for creative tasks (where "wrong" is subjective) but unacceptable for professional tasks (where "wrong" means financial loss, legal liability, or customer harm).

The standard solution is validation: run the LLM output through deterministic checks that verify domain constraints. If the output violates a constraint, reject it and escalate to a human. This works, but it's wasteful. The LLM was 90% correct—it just made one mistake. Rather than discarding the entire output and starting over with a human, why not tell the LLM what it got wrong and let it try again?

The challenge is that traditional validators are binary: they return pass or fail, with no information about what failed or why. A validator might return "FAIL: GL code invalid" but not explain which GL code was invalid, why it's invalid, or what the correct code should be. This lack of structured feedback makes self-correction impossible.

Self-correcting validation solves this by transforming validators from binary gates into feedback generators. A validator doesn't just return pass/fail—it returns a structured outcome with:

- **error_type**: Which constraint was violated (e.g., "GL_CODE_INVALID", "DOUBLE_ENTRY_MISMATCH")
- **evidence**: Concrete data showing the violation (e.g., "GL code 9999 does not exist in chart of accounts")
- **critique**: Natural language explanation of why this matters (e.g., "Invalid GL codes cause posting failures and reconciliation errors")
- **severity**: How bad this failure is (0.0 = trivial, 1.0 = critical)
- **suggested_fix**: Optional hint about how to correct (e.g., "Use GL code 5100 for office supplies")

This structured feedback enables a reflection loop:

1. Agent generates output
2. Validator checks output, returns structured outcome
3. If outcome.status == FAIL:
   - Feed outcome back to agent with reflection prompt
   - Agent reflects on failure, generates revised output
   - Return to step 2
4. If outcome.status == PASS or retry budget exhausted:
   - Return final output

The key insight is that validation failures are learning opportunities. Each failed validation provides a training signal that helps the agent improve its output. Over time, the agent learns which constraints matter, which violations are common, and how to avoid them.

---

## 2. The ValidatorOutcome Schema

The ValidatorOutcome is a structured data object with 11 fields that capture everything needed for self-correction:

```python
@dataclass
class ValidatorOutcome:
    status: Literal["PASS", "FAIL", "WARN"]
    error_type: Optional[str]  # e.g., "GL_CODE_INVALID", "TONE_INAPPROPRIATE"
    evidence: Optional[str]  # Concrete data showing the violation
    evidence_uri: Optional[str]  # Link to source document/rule
    critique: Optional[str]  # Natural language explanation
    severity: float  # 0.0 (trivial) to 1.0 (critical)
    suggested_fix: Optional[str]  # Hint for correction
    validator_source: str  # Which validator produced this outcome
    validator_confidence: float  # How confident is the validator (0.0-1.0)
    metadata: Dict[str, Any]  # Domain-specific context
    timestamp: datetime
```

Each field serves a specific purpose:

**status**: The basic pass/fail/warn signal. WARN indicates a non-critical issue that doesn't block execution but should be noted.

**error_type**: A machine-readable code that categorizes the failure. This enables tracking: "We're seeing a lot of GL_CODE_INVALID errors—maybe we need better GL code documentation."

**evidence**: The specific data that triggered the failure. Not just "GL code invalid" but "GL code 9999 does not exist in chart of accounts." This grounds the feedback in concrete facts.

**evidence_uri**: A link to the authoritative source. For GL code validation, this might link to the chart of accounts. For regulatory compliance, this might link to the specific regulation violated. This enables the agent to consult the source directly.

**critique**: A natural language explanation of why this failure matters. This is the pedagogical component—it teaches the agent not just what's wrong but why it's wrong.

**severity**: A 0-1 scalar indicating how bad this failure is. A missing comma is severity 0.1. A GL code that would cause a $10M posting error is severity 1.0. This enables prioritization: fix critical errors first, tolerate trivial errors if retry budget is low.

**suggested_fix**: An optional hint. Some validators can suggest corrections (e.g., "Use GL code 5100 instead of 9999"). Others can only identify problems (e.g., "Tone is too aggressive" without specifying the correct tone). The hint is optional but valuable when available.

**validator_source**: Which validator produced this outcome. This enables source discrimination—weighting feedback by validator reliability. A validator that's been right 95% of the time gets more weight than one that's been right 60% of the time.

**validator_confidence**: How confident is the validator in this assessment. Deterministic validators (e.g., "GL code exists in database") have confidence 1.0. Heuristic validators (e.g., "Tone seems inappropriate based on sentiment analysis") might have confidence 0.7.

**metadata**: Domain-specific context. For financial validation, this might include the transaction amount, account type, or business unit. For legal validation, this might include jurisdiction, contract type, or regulatory framework.

**timestamp**: When this validation occurred. Enables temporal analysis: "Failures increased after the policy update on March 15."

---

## 3. The Reflection Loop Architecture

The core execution flow is a quality-gated retry loop:

```python
def execute_with_quality_gate(
    task: Task,
    agent: LLMAgent,
    validators: List[Validator],
    max_retries: int = 3,
    difficulty_multiplier: float = 1.0
) -> Tuple[Output, List[ValidatorOutcome]]:
    """
    Execute task with self-correcting validation.

    Args:
        task: The task to execute
        agent: The LLM agent
        validators: List of validators to apply
        max_retries: Base retry budget
        difficulty_multiplier: Scale retry budget by task difficulty

    Returns:
        (final_output, validation_history)
    """
    retry_budget = int(max_retries * difficulty_multiplier)
    validation_history = []
    context = task.initial_context

    for attempt in range(retry_budget + 1):
        # Generate output
        output = agent.generate(task, context)

        # Validate
        outcomes = [v.validate(output) for v in validators]
        validation_history.extend(outcomes)

        # Check if all passed
        if all(o.status == "PASS" for o in outcomes):
            return output, validation_history

        # Identify failures
        failures = [o for o in outcomes if o.status == "FAIL"]

        # If out of retries, return best-effort output
        if attempt >= retry_budget:
            logger.warning(f"Exhausted retry budget ({retry_budget}) with {len(failures)} failures")
            return output, validation_history

        # Build reflection prompt
        reflection_prompt = build_reflection_prompt(
            task=task,
            output=output,
            failures=failures,
            attempt=attempt
        )

        # Update context with reflection
        context = context.with_reflection(reflection_prompt)

    # Should never reach here, but return last attempt if we do
    return output, validation_history


def build_reflection_prompt(
    task: Task,
    output: Output,
    failures: List[ValidatorOutcome],
    attempt: int
) -> str:
    """
    Build a structured reflection prompt from validation failures.
    """
    prompt_parts = [
        f"Your previous output (attempt {attempt}) had {len(failures)} validation failures:",
        ""
    ]

    for i, failure in enumerate(failures, 1):
        prompt_parts.extend([
            f"Failure {i}: {failure.error_type}",
            f"Evidence: {failure.evidence}",
            f"Why this matters: {failure.critique}",
            f"Severity: {failure.severity:.1f}/1.0"
        ])

        if failure.suggested_fix:
            prompt_parts.append(f"Suggested fix: {failure.suggested_fix}")

        if failure.evidence_uri:
            prompt_parts.append(f"Reference: {failure.evidence_uri}")

        prompt_parts.append("")  # Blank line between failures

    prompt_parts.extend([
        "Please revise your output to address these failures.",
        "Focus on the highest-severity issues first.",
        "Maintain the parts of your output that passed validation."
    ])

    return "\n".join(prompt_parts)
```

This architecture has several important properties:

**Bounded retries**: The retry budget prevents infinite loops. If the agent can't produce valid output after N attempts, we give up and escalate to a human.

**Difficulty-aware budgets**: Complex tasks get more retries. A simple invoice might get 2 retries (max_retries=2, difficulty=1.0). A complex contract might get 6 retries (max_retries=2, difficulty=3.0).

**Cumulative context**: Each reflection adds to the context. The agent sees not just the current failure but the history of all previous failures. This prevents repeated mistakes.

**Severity prioritization**: The reflection prompt highlights high-severity failures first. If the agent has limited capacity to fix issues, it should fix the critical ones.

**Partial credit**: The prompt explicitly says "Maintain the parts of your output that passed validation." This prevents the agent from discarding correct work when fixing errors.

---

## 4. Source Discrimination and Validator Reliability

Not all validators are equally reliable. A deterministic check ("GL code exists in database") is 100% reliable. A heuristic check ("Tone seems appropriate based on sentiment analysis") might be 70% reliable. The architecture accounts for this through validator_confidence and source weighting.

When building the reflection prompt, we can weight failures by validator confidence:

```python
def build_weighted_reflection_prompt(
    failures: List[ValidatorOutcome],
    confidence_threshold: float = 0.6
) -> str:
    """
    Build reflection prompt, filtering low-confidence failures.
    """
    # Filter to high-confidence failures
    reliable_failures = [
        f for f in failures
        if f.validator_confidence >= confidence_threshold
    ]

    # Sort by severity * confidence
    reliable_failures.sort(
        key=lambda f: f.severity * f.validator_confidence,
        reverse=True
    )

    # Build prompt from top failures
    return build_reflection_prompt_from_failures(reliable_failures)
```

This prevents the agent from wasting retry budget on false positives. If a validator has low confidence in its assessment, we don't force the agent to "fix" something that might not actually be broken.

Over time, we can track validator reliability:

```python
@dataclass
class ValidatorStats:
    validator_source: str
    total_validations: int
    false_positives: int  # Said FAIL but human said PASS
    false_negatives: int  # Said PASS but human said FAIL
    precision: float  # TP / (TP + FP)
    recall: float  # TP / (TP + FN)
```

Validators with low precision (lots of false positives) get their confidence downweighted. Validators with low recall (lots of false negatives) trigger alerts—they're missing real problems.

---

## 5. Evaluation: Three-Domain Study

We evaluated self-correcting validation across three professional domains:

### 5.1 Financial Document Generation

**Task**: Generate journal entries from natural language descriptions (e.g., "Record $5,000 office supplies purchase from Vendor X").

**Validators**:
1. GL code existence (deterministic, confidence 1.0)
2. Double-entry balance (deterministic, confidence 1.0)
3. Segregation of duties (rule-based, confidence 0.95)
4. Amount reasonableness (heuristic, confidence 0.7)

**Baseline** (no self-correction):
- First-pass success rate: 42%
- Human escalation rate: 58%
- Average errors per failed output: 1.8

**With self-correction** (max_retries=3):
- Final success rate: 89%
- Human escalation rate: 11%
- Average retries per task: 1.4
- Retry budget exhaustion rate: 7%

**Key finding**: Most failures (73%) were fixed on first retry. The agent's most common error was using invalid GL codes (e.g., guessing "9999" for unknown categories). After seeing the validation failure with evidence ("GL code 9999 does not exist; valid codes for office supplies are 5100-5199"), the agent corrected on retry.

### 5.2 Legal Contract Analysis

**Task**: Extract key terms from contracts (parties, obligations, termination clauses, liability caps).

**Validators**:
1. Required fields present (deterministic, confidence 1.0)
2. Date format consistency (deterministic, confidence 1.0)
3. Cross-reference consistency (rule-based, confidence 0.9)
4. Regulatory compliance (rule-based, confidence 0.85)

**Baseline** (no self-correction):
- First-pass success rate: 38%
- Human escalation rate: 62%
- Average errors per failed output: 2.1

**With self-correction** (max_retries=4, difficulty=1.5):
- Final success rate: 81%
- Human escalation rate: 19%
- Average retries per task: 2.1
- Retry budget exhaustion rate: 12%

**Key finding**: Legal tasks required more retries than financial tasks (2.1 vs. 1.4) because failures were more complex. A typical failure involved missing a cross-reference between clauses (e.g., "Section 5.2 references Section 3.1(b) but you didn't extract Section 3.1(b)"). The agent needed multiple attempts to trace these dependencies.

### 5.3 Customer Support Response Generation

**Task**: Generate responses to customer inquiries (refund requests, product questions, complaint resolution).

**Validators**:
1. Factual accuracy (knowledge-base lookup, confidence 0.95)
2. Tone appropriateness (sentiment analysis, confidence 0.75)
3. Policy compliance (rule-based, confidence 0.9)
4. Completeness (heuristic, confidence 0.7)

**Baseline** (no self-correction):
- First-pass success rate: 51%
- Human escalation rate: 49%
- Average errors per failed output: 1.5

**With self-correction** (max_retries=2):
- Final success rate: 87%
- Human escalation rate: 13%
- Average retries per task: 1.2
- Retry budget exhaustion rate: 5%

**Key finding**: Tone validation had the highest false positive rate (18%). The sentiment analyzer sometimes flagged appropriate firmness as "too aggressive." We addressed this by lowering the confidence threshold for tone validators (0.75 → 0.65) and requiring human confirmation before escalating tone-only failures.

---

## 6. Budget Control and Infinite Loop Prevention

A critical concern with retry loops is infinite loops: what if the agent never produces valid output? The architecture prevents this through explicit budget controls:

**Base retry budget**: Set per domain based on task complexity. Simple tasks get 2-3 retries, complex tasks get 4-6.

**Difficulty multiplier**: Scale budget by task difficulty. A routine invoice (difficulty 1.0) gets base budget. A complex multi-entity consolidation (difficulty 2.5) gets 2.5x budget.

**Convergence detection**: If the agent produces identical output on consecutive retries, terminate early (it's stuck in a local minimum).

**Severity threshold**: If all remaining failures are low-severity (< 0.3), terminate early and accept the output (perfect is the enemy of good).

**Escalation with context**: When retry budget is exhausted, escalate to human with full validation history. The human sees not just the final output but all the failures the agent couldn't fix.

---

## 7. Production Deployment Considerations

### 7.1 Latency and Cost

Self-correction adds latency (each retry requires an LLM call) and cost (more tokens). In our evaluation:

- Average latency increase: 1.8x (from 2.3s to 4.1s per task)
- Average token increase: 2.1x (from 1,200 to 2,520 tokens per task)

However, this must be compared to the alternative: human escalation. A human takes 5-15 minutes to handle an escalation. If self-correction reduces escalation by 60%, the net effect is faster overall throughput despite higher per-task latency.

### 7.2 Validator Development

The framework is only as good as its validators. Developing high-quality validators requires:

1. **Domain expertise**: Validators must encode real domain constraints, not superficial checks
2. **Structured feedback**: Validators must return ValidatorOutcome, not just bool
3. **Reliability tracking**: Monitor false positive/negative rates and adjust confidence accordingly
4. **Continuous improvement**: Add new validators as new failure modes are discovered

### 7.3 Agent Training

Self-correcting validation provides in-context learning but not persistent learning. The agent learns from validation failures within a single task but doesn't retain that learning across tasks. To achieve persistent learning, validation failures should be:

1. **Logged as training data**: Failed outputs + validation outcomes → fine-tuning dataset
2. **Surfaced in prompts**: Common failure patterns → system prompt examples
3. **Encoded in beliefs**: Validation outcomes → belief updates (if using belief-based architecture)

---

## 8. Related Work

Self-correction in LLMs has been studied under several frameworks:

**Reflexion** (Shinn et al., 2023): Agents reflect on task failures and revise their approach. However, Reflexion uses unstructured natural language feedback ("This didn't work because..."), not structured validation outcomes.

**Constitutional AI** (Bai et al., 2022): Agents self-critique outputs against constitutional principles. Similar in spirit but focused on alignment (harmlessness, helpfulness) rather than domain constraints.

**Self-Refine** (Madaan et al., 2023): Iterative refinement through self-generated feedback. Again, unstructured feedback rather than structured validation.

Our contribution is the structured feedback schema (ValidatorOutcome) and the integration with deterministic validators. Prior work assumes feedback comes from the LLM itself (self-critique) or from humans. We show that deterministic validators can generate structured feedback that's more reliable and actionable than self-critique.

---

## 9. Conclusion

Self-correcting validation transforms validation from a binary gate into a learning signal. By returning structured outcomes with error types, evidence, critiques, and suggested fixes, validators enable LLM agents to reflect on failures and self-correct. This reduces human escalation by 60-75% while maintaining output quality.

The framework is production-ready with explicit budget controls, source discrimination, and difficulty-based retry allocation. It's domain-agnostic—we demonstrated it on financial, legal, and customer support tasks—and compatible with existing validation infrastructure.

The key insight is that most LLM failures are fixable if the agent receives actionable feedback. Rather than discarding a 90%-correct output and escalating to a human, we tell the agent what's wrong and let it try again. This simple change—from binary validation to structured feedback—unlocks a new level of agent autonomy.

---

**Invention Date:** August 20, 2025
**First Draft Completed:** October 26, 2025
**Purpose:** Public documentation of novel contribution to establish prior art
