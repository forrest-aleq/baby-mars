# Academic Paper Drafts - Invention Documentation

**Purpose:** These drafts document novel contributions to establish prior art and priority dates. Each paper represents a genuinely novel concept that was first conceptualized during the development of the Aleq MIND professional AI agent system.

**Status:** First drafts completed October 26, 2025

**Total Papers:** 20 completed first drafts

---

## Research Timeline Context

**Foundation:** The "where-it-started" conversation (end of July 2025) established first principles:
- Beliefs as compositional structures (assumptions + opinions + experiences)
- Context-conditional activation
- Memory vs Belief distinction
- Goals as the driving force (not stimulus-response)
- 5-step cognitive interaction loop

**Research Period:** August 1 - October 25, 2025 (86 days of focused invention)

**Key Milestone:** Aletheia CHI 2026 submission (September 29, 2025) - synthesis paper combining Competence-Based Autonomy, Context-Conditional Beliefs, Self-Correcting Validation, Causal Attribution, and ACRE.

---

## Complete Paper Inventory (20 Papers)

### Tier 1: Genuinely Novel (★★★★★) - 7 Papers

**1. Competence-Based Adaptive Autonomy for AI Agents**
- File: `01-competence-based-autonomy.md`
- Invention Date: **~August 1, 2025**
- Novelty: AI-centric autonomy that adjusts based on the AI's own belief strength, not human trust
- Category: Autonomy
- Key Innovation: Dynamic supervision levels (guidance-seeking, action proposal, autonomous) mapped to belief strength with task-specific competence tracking
- Target Venue: CHI 2026 (submitted Sept 29 as Aletheia)

**4. Event-Sourced Belief Updates with Moral Asymmetry**
- File: `07-moral-asymmetry-event-sourcing.md`
- Invention Date: **~August 10, 2025**
- Novelty: Immutable event log with asymmetric weighting (failures weighted β×more than successes) enabling temporal analysis and audit reconstruction
- Category: Beliefs
- Key Innovation: Event sourcing + configurable moral asymmetry (β parameter) + severity weighting + counterfactual analysis
- Target Venue: Cognitive Science

**6. AI Years: A Temporal Framework for Measuring Epistemic Maturity**
- File: `02-ai-years-epistemic-maturity.md`
- Invention Date: **~August 15, 2025**
- Novelty: Time measured in validated interaction cycles to earn "nines" of reliability, not clock time
- Category: Benchmarks
- Key Innovation: Hardware-agnostic maturity metric where one AI Year = cycles required to move from 0.90 to 0.99 per-step reliability
- Target Venue: NeurIPS Datasets & Benchmarks

**8. Self-Correcting Validation: Closed-Loop Quality Gates for LLM Agents**
- File: `03-self-correcting-validation.md`
- Invention Date: **August 20, 2025**
- Novelty: Structured 11-field ValidatorOutcome schema that transforms validation failures into actionable feedback for LLM reflection
- Category: Autonomy
- Key Innovation: Deterministic validators generate structured feedback (error_type, evidence, critique, severity, suggested_fix) enabling self-correction loops with budget controls
- Target Venue: ICML/NeurIPS

**10. Moral Asymmetry as a Learning Multiplier**
- File: `09-moral-asymmetry-multiplier.md`
- Invention Date: **~August 28, 2025**
- Novelty: Internalizing normative asymmetry as belief update dynamics (violations 10×, confirmations 3×)
- Category: Beliefs
- Key Innovation: First framework to translate phenomenological moral asymmetry into algorithmic learning rates with category-specific moral sensitivity
- Target Venue: Cognitive Science / AAAI

**12. Category-Specific Invalidation Thresholds (A.C.R.E.)**
- File: `10-category-specific-invalidation-thresholds.md`
- Invention Date: **~September 6, 2025**
- Novelty: Domain-weighted epistemic rigidity (Aesthetic 0.60, Contextual 0.75, Relational 0.85, Ethical 0.95)
- Category: Beliefs
- Key Innovation: First formalization of category-dependent belief revision thresholds for AI, operationalizing empirical psychological tendencies
- Target Venue: Cognitive Science / CogSci
- Note: Referenced in Aletheia submission (Sept 29)

**19. Three-Column Working Memory for Relationship-Aware AI Agents**
- File: `08-three-column-working-memory.md`
- Invention Date: **October 20, 2025**
- Novelty: Structured separation of Active Tasks (3-4 slots), Notes (TTL queue), and Objects (salience-based ambient context)
- Category: Memory
- Key Innovation: No explicit pointers between columns (LLM reasons implicitly), TTL-based note expiration, salience-based object population
- Target Venue: ICRA or Cognitive Systems Research

### Tier 2: Novel Applications (★★★★☆) - 13 Papers

**2. Context-Conditional Belief Surfaces for Situated AI Competence**
- File: `04-context-conditional-beliefs.md`
- Invention Date: **~August 3, 2025**
- Novelty: Hierarchical backoff resolution (from NLP) applied to belief systems with independent temporal state per context
- Category: Beliefs
- Key Innovation: Statistical admission criteria to prevent overfitting; independent temporal state per context prevents global state contamination
- Target Venue: ICML

**3. Interference-Based Memory Decay for Cognitive Load Modeling**
- File: `13-interference-based-memory-decay.md`
- Invention Date: **August 5, 2025**
- Novelty: Two-factor decay model combining time + domain-specific cognitive interference
- Category: Memory
- Key Innovation: Busy work accelerates forgetting through pattern competition; spacing effect bonus for distributed practice
- Target Venue: Cognitive Science

**5. Peak-End Rule for Episodic Memory Weighting**
- File: `12-peak-end-rule-memory-weighting.md`
- Invention Date: **August 12, 2025**
- Novelty: First procedural application of Kahneman's peak-end rule to AI belief formation
- Category: Memory
- Key Innovation: Salience-based weighting (peak 2×, end 1.5×, middle 1×) creating psychologically realistic memory dynamics
- Target Venue: CogSci / Cognitive Science

**7. The Birth System: Solving Cold Start Without Belief Inheritance**
- File: `15-birth-system-cold-start.md`
- Invention Date: **~August 18, 2025**
- Novelty: External data synthesis (Apollo API + knowledge packs + scenarios) → 0.4-0.6 strength beliefs in 90 seconds
- Category: Systems
- Key Innovation: Zero-dependency cold start; dual-mode operation (full birth + micro-birth); no organizational memory required
- Target Venue: AAAI / Systems

**9. Causal Attribution for Focused Belief Updates in Learning Agents**
- File: `05-causal-attribution.md`
- Invention Date: **~August 25, 2025**
- Novelty: LLM-generated influence weights for belief-specific updates, solving the "innocent bystander" problem
- Category: Beliefs
- Key Innovation: Decision bundles with influence weights; focused updates scaled by influence; competence preservation metric
- Target Venue: AAAI/IJCAI

**11. Hierarchical Beliefs with Cascading Strength Updates**
- File: `11-hierarchical-beliefs-cascading-updates.md`
- Invention Date: **~September 1, 2025**
- Novelty: Extension of active inference hierarchies with concrete belief nodes and explicit SUPPORTS relationships
- Category: Beliefs
- Key Innovation: Practical implementation of hierarchical belief propagation with efficient cascading updates and interpretable belief DAG
- Target Venue: ICML / Cognitive Systems Research

**13. ACT: A Three-Phase Longitudinal Benchmark for Evaluating Learning Agents**
- File: `06-act-benchmark.md`
- Invention Date: **~September 10, 2025**
- Novelty: 60-day longitudinal evaluation measuring learning velocity, not one-shot performance
- Category: Benchmarks
- Key Innovation: Three phases (Acquisition, Consolidation, Transfer); five dimensions (learning velocity, competence quality, relationship calibration, safety, stability)
- Target Venue: NeurIPS Datasets & Benchmarks

**14. Duration Estimation and Intelligent Task Scheduling for Professional AI Agents**
- File: `16-duration-estimation-task-scheduling.md`
- Invention Date: **October 12, 2025**
- Novelty: Three-layer estimation (knowledge baselines + skill beliefs + action history) + seven-level routing
- Category: Social
- Key Innovation: Relationship-aware priority (85% urgency + 15% relationship value); post-task learning updates skill beliefs
- Target Venue: ICRA / Cognitive Systems Research

**15. Latent Trajectory Learning for System-Operator LLMs**
- File: `19-latent-trajectory-learning.md`
- Invention Date: **October 14, 2025**
- Novelty: Story-gap training paradigm where models learn to complete partially observed operational stories and compile inferred steps into tool-agnostic work units
- Category: Systems
- Key Innovation: Separates planning (Planner) from compilation (Translators); extends trajectory modeling to open-ended enterprise stories
- Target Venue: ICML / NeurIPS
- Cross-Reference: Paired with PTD architecture (Paper 16)

**16. The Planner–Translator–Driver Architecture for Executable Agents**
- File: `20-planner-translator-driver.md`
- Invention Date: **October 14, 2025**
- Novelty: Modular execution framework separating cognition from control with verifiable execution
- Category: Systems
- Key Innovation: Planner (semantic reasoning) → Translators (per-surface compilers) → Drivers (deterministic executors) → Verifier (critic layer)
- Target Venue: ICML / NeurIPS
- Cross-Reference: Operational complement to LTL (Paper 15)

**17. Social Awareness and Relationship Dynamics in Professional AI Agents**
- File: `17-social-awareness-relationship-dynamics.md`
- Invention Date: **October 18, 2025**
- Novelty: Relationship value (60% authority + 20% interaction + 20% context) + authority learning through preemption
- Category: Social
- Key Innovation: Earned influence beyond formal titles; conflict resolution via authority-weighted triage (>0.3 auto-resolve)
- Target Venue: Social Robotics / CogSci

**18. Cognitive Engrams: Offline Multimodal Fusion for Real-Time Experiential Memory**
- File: `14-cognitive-engrams-multimodal-memory.md`
- Invention Date: **October 19, 2025**
- Novelty: Offline multimodal fusion (text + prosody + screen context) → compact vectors → real-time priming
- Category: Memory
- Key Innovation: Experiential memory depth without latency/privacy tradeoffs; derived features only (no raw audio/video)
- Target Venue: CHI / HCI

**20. Time-Based Context Activation: Proactive Memory Pre-Loading for Responsive AI Agents**
- File: `18-time-based-context-activation.md`
- Invention Date: **October 25, 2025**
- Novelty: Background workers pre-load context before user interactions based on temporal/event triggers
- Category: Memory
- Key Innovation: 94% latency reduction (380ms vs 6.2s); moves latency from critical path to background
- Target Venue: Systems / HCI

---

## Corrected Invention Timeline

```
August 1, 2025     → Competence-Based Adaptive Autonomy
August 3, 2025     → Context-Conditional Beliefs
August 5, 2025     → Interference-Based Memory Decay
August 10, 2025    → Moral Asymmetry with Event Sourcing
August 12, 2025    → Peak-End Rule for Memory Weighting
August 15, 2025    → AI Years Framework
August 18, 2025    → Birth System for Cold Start
August 20, 2025    → Self-Correcting Validation
August 25, 2025    → Causal Attribution
August 28, 2025    → Moral Asymmetry as Learning Multiplier
September 1, 2025  → Hierarchical Beliefs with Cascading Updates
September 6, 2025  → Category-Specific Invalidation (A.C.R.E.)
September 10, 2025 → ACT Benchmark
September 29, 2025 → Aletheia CHI 2026 Submission (synthesis paper)
October 12, 2025   → Duration Estimation & Task Scheduling
October 14, 2025   → Latent Trajectory Learning (LTL) + Planner-Translator-Driver (PTD)
October 18, 2025   → Social Awareness & Relationship Dynamics
October 19, 2025   → Cognitive Engrams for Multimodal Memory
October 20, 2025   → Three-Column Working Memory
October 25, 2025   → Time-Based Context Activation
```

---

## Key Statistics

**Total Papers:** 20 completed first drafts
**Genuinely Novel (Tier 1):** 7 papers (★★★★★)
**Novel Applications (Tier 2):** 13 papers (★★★★☆)
**Total Word Count:** ~165,000 words (estimated)
**Total Pages:** ~330 pages (estimated, single-column format)
**Invention Period:** August 1 - October 25, 2025 (86 days)
**Research Velocity:** ~2.3 papers per week during focused period

### Category Distribution

- **Memory:** 5 papers (3, 5, 18, 19, 20)
- **Beliefs:** 6 papers (2, 4, 9, 10, 11, 12)
- **Autonomy:** 2 papers (1, 8)
- **Social:** 2 papers (14, 17)
- **Systems:** 3 papers (7, 15, 16)
- **Benchmarks:** 2 papers (6, 13)

---

## Publication Strategy

### Year 1 (2026)
- **CHI 2026** (Submitted Sept 29, 2025): Aletheia - Competence-Based Autonomy synthesis
- **CogSci 2026** (Submit Feb 2026): Moral Asymmetry as Learning Multiplier + Category-Specific Invalidation (A.C.R.E.)
- **NeurIPS 2026 Datasets** (Submit May 2026): AI Years + ACT Benchmark
- **ICML 2026** (Submit Feb 2026): Latent Trajectory Learning + Planner-Translator-Driver

### Year 2 (2027)
- **AAAI 2027**: Causal Attribution
- **Cognitive Science**: Event-Sourced Moral Asymmetry + Peak-End Rule + Interference-Based Memory Decay
- **Cognitive Systems Research**: Three-Column Working Memory + Hierarchical Beliefs
- **HCI/CHI 2027**: Cognitive Engrams + Time-Based Context Activation
- **Social Robotics**: Social Awareness & Relationship Dynamics

---

## Next Steps

1. **Review/Refine Drafts:** Ensure technical accuracy for all 20 papers
2. **Add Empirical Results:** Incorporate data from Aleq MIND production deployment
3. **Create Visuals:** Figures/diagrams for key concepts
4. **Identify Co-authors:** If applicable
5. **Finalize Target Venues:** Confirm journals/conferences for all 20
6. **Prepare Supplementary Materials:** Code snippets, datasets, demos
7. **Publish Preprints (arXiv):** Crucial for establishing public priority dates
8. **Submit to Venues:** Follow refined publication strategy

---

## Cross-References

**LTL ↔ PTD (Papers 15 & 16):**
- Latent Trajectory Learning defines HOW agents learn operational reasoning
- Planner-Translator-Driver defines HOW that reasoning executes in real systems
- Both invented October 14, 2025
- Companion papers for submission

**Moral Asymmetry Family (Papers 4 & 10):**
- Event-Sourced Belief Updates (Paper 4): Architectural implementation
- Learning Multiplier (Paper 10): Cognitive principle
- Both explore asymmetric weighting but at different abstraction levels

**ACRE in Aletheia (Paper 12):**
- Invented ~Sept 6, 2025
- Referenced in Aletheia submission Sept 29, 2025
- Core component of adaptive autonomy framework

---

## Legal Notice

These drafts document novel contributions for the purpose of establishing prior art and priority dates. All concepts were first developed between August 1, 2025 and October 25, 2025 during the design and implementation of the Aleq MIND professional AI agent system.

**Philosophical Foundation:** "where-it-started" conversation (end of July 2025)

**Author:** Forrest Hosten
**Organization:** Aleq, Inc.
**First Draft Completion:** October 26, 2025
**License:** To be determined

---

## Contact

For questions about these papers or collaboration opportunities:
- Email: [To be added]
- Website: [To be added]
