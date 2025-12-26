# Aleq Gulfstream Reference Document

## Why Gulfstream?

The G280 didn't just compete in the super-midsize category—it **dominated**. Best range, best speed, best cabin in its class, by margins that weren't even close. When Gulfstream builds an aircraft, it's not an MVP. It's the definitive answer for that mission profile.

**Aleq follows the same philosophy.** Baby Mars isn't a stripped-down prototype—it's the best-in-class cognitive system for accounts payable automation. Compact, focused, uncompromising.

---

## The Fleet

| Aircraft       | Range   | Aleq System         | Mission Profile                                   |
| -------------- | ------- | ------------------- | ------------------------------------------------- |
| **G300** | 3,600nm | **Baby Mars** | Single-domain mastery. Replace Maria Santos.      |
| **G400** | 4,200nm | **Baby Mars** | Same system, more edge cases hardened.            |
| **G500** | 5,300nm | **Mars-Lite** | Multi-domain. Full appraisal. Birth system.       |
| **G600** | 6,600nm | **Mars-Lite** | + A.C.R.E. error recovery. Belief dynamics.       |
| **G700** | 7,750nm | **Mars**      | Full cognitive architecture. All research papers. |
| **G800** | 8,000nm | **Olympus**   | Multi-agent. Self-tuning. The summit.             |

---

## Baby Mars (G300/G400 Class)

**The G300 replaced the G280 as Gulfstream's super-midsize flagship. Baby Mars is that: compact, focused, best-in-class for its mission.**

### Mission: Replace Maria Santos

Maria processes lockbox payments. Baby Mars does her job—not helps her, **replaces** her. When Baby Mars hits an edge case it can't resolve, it escalates to Maria's boss, exactly like Maria would.

### Complete Capability Set

| Capability                      | Implementation                      | Status     |
| ------------------------------- | ----------------------------------- | ---------- |
| **Webhook Triggers**      | Email/event → Task creation        | Production |
| **PDF Extraction**        | OCR with confidence scoring         | Production |
| **Entity Resolution**     | "SeaBreeze" → "SB Yacht Club LLC"  | Production |
| **Invoice Matching**      | Stargate → Recurly/NetSuite        | Production |
| **Payment Posting**       | Stargate execution layer            | Production |
| **Belief Learning**       | EMA updates on correction           | Production |
| **Error Acknowledgment**  | "Got it, I'll fix that" + update    | Production |
| **HITL Escalation**       | Decision card → Maria's boss       | Production |
| **Autonomy Modes**        | 3-tier confidence thresholds        | Production |
| **Timeline Transparency** | Every step visible, expandable      | Production |
| **Retry Logic**           | Exponential backoff on failures     | Production |
| **Context Pills**         | @references persist in conversation | Production |

### Autonomy Thresholds

```
Belief Strength < 0.4   → guidance_seeking (ask boss)
Belief Strength 0.4-0.7 → action_proposal (propose, await approval)
Belief Strength ≥ 0.7   → autonomous (execute, log for review)
```

### What Baby Mars Doesn't Need

| Feature                | Why Not                                       |
| ---------------------- | --------------------------------------------- |
| A.C.R.E. state machine | Simple acknowledgment is enough for AP errors |
| Belief cascading       | Flat beliefs work for invoice matching        |
| Working memory slots   | Conversation context suffices                 |
| Voice reflexes         | Lockbox is async email, not real-time voice   |
| Full policy layer      | Basic quality gate is sufficient              |
| Scheduler/SYSTEM_PULSE | Webhook-driven is the right model             |

### The Proof: Lockbox Processing

```
9:31:04  ● Received 6 lockbox PDFs from First Republic
9:31:47  ● Extracted 47 payments (94% OCR confidence)
9:32:15  ● Matched 47 customers to records
         └─ Correction: "SeaBreeze" → "SB Yacht Club LLC"
9:32:44  ● Matched 46 of 47 invoices
9:33:02  ○ DECISION NEEDED
         └─ MdR Storage sent $875 for invoice belonging to MdR Services
         └─ [Apply to Services] [Hold] [Handle in Books]
9:33:47  ● User: "Apply to Services"
9:33:49  ● Payment posted to MdR Services invoice
9:33:52  ● Journal entry JE-2025-4001 created
9:33:52  ● Belief learned: "MdR Storage pays for MdR Services" (0.70)
9:33:52  ✓ Task Complete (2m 48s)
```

**Second lockbox arrives with another MdR Storage payment:**

- Belief strength 0.70 ≥ 0.7 → autonomous mode
- Auto-applies without asking
- Timeline shows: "Applied based on learned relationship"

**That's the G300. Best in class. No compromises.**

---

## Mars-Lite (G500/G600 Class)

**When you need to fly further than Baby Mars can take you.**

### Mission: Multi-Domain Cognitive System

Baby Mars masters one domain (AP/lockbox). Mars-Lite handles multiple domains, new organizations, and recovers gracefully from errors.

### Additions Over Baby Mars

| Capability                        | G500                  | G600                                    |
| --------------------------------- | --------------------- | --------------------------------------- |
| **Full Appraisal Pipeline** | ✅ 8 nodes            | ✅ 8 nodes                              |
| **Birth System**            | ✅ <90s onboarding    | ✅ <90s onboarding                      |
| **DecisionBundle**          | ✅ Causal attribution | ✅ Causal attribution                   |
| **Working Memory**          | Basic context         | ✅ 3-4 slot model                       |
| **A.C.R.E. Recovery**       | —                    | ✅ 5-state machine                      |
| **Belief Cascading**        | —                    | ✅ SUPPORTS relationships               |
| **Full Policy Layer**       | Basic                 | ✅ Hedging + Personality + Authenticity |
| **Scheduler**               | —                    | ✅ Context prediction                   |

### Appraisal Pipeline (8 Nodes)

```
Input → Perception → Emotion → Politeness → Face Threat →
        Covariation → Knowledge Gap → Hesitation → Severity → Output
```

### A.C.R.E. Error Recovery (G600)

```
DETECTED → ACKNOWLEDGED → CORRECTED → REASSURED → EVOLVED

Service Recovery Paradox: Exceptional error handling creates
stronger trust than never making mistakes.
```

### Birth System

```
New Org Signs Up (t=0)
    │
    ├── Create Organization node
    ├── Create Person nodes from signup
    ├── Apollo API enrichment
    ├── Load Knowledge packs (accounting procedures)
    ├── Generate initial Beliefs (0.4-0.6 strength)
    └── Scenario prompts → seed edge-case awareness
    │
    ▼
Graph Ready (t<90s) → First interaction begins
```

---

## Mars (G700 Class)

**The full cognitive architecture. Every research paper implemented.**

### Mission: General-Purpose Cognitive Agent

Mars isn't domain-specific. It's the complete system that can be configured for any financial operations role.

### The Full Stack

```
BIRTH SYSTEM (6 modules)
├── Organization/Person creation
├── Apollo enrichment
├── Knowledge packs
├── Initial beliefs (0.4-0.6)
└── Scenario seeding

PERCEPTION (webhook + vision + voice)
├── Channel routing
├── Hesitation detection
└── Perception correction loop

WORKING MEMORY (8 modules)
├── 3-4 active slots
├── Notes queue with TTL
├── Objects column (salience-based)
├── Thrashing detection
└── Eviction formulas

APPRAISAL (13 modules)
├── Emotion detection
├── Politeness (P+D+R)
├── Face threat analysis
├── Covariation check
├── Knowledge gap detection
├── Hesitation signals
├── Perception correction
├── Data availability check
└── Severity classification

PLANNING (6 modules)
├── Conflict resolution (4 strategies)
├── Execution planning
├── Action routing
├── Sufficiency checking
└── EVT gating

POLICY (4 modules)
├── Personality gate
├── Quality gate
├── Hedging enforcement
└── Authenticity scoring

RECOVERY (5 modules)
├── A.C.R.E. orchestrator
├── Correction detection
├── Severity classification
├── Response templates
└── Uncertainty handling

FEEDBACK (core)
├── Focused belief updates
├── Cascade propagation
├── Memory consolidation
└── Turn recording

SCHEDULER (5 modules)
├── Context predictor (87% accuracy)
├── Preloader (94% latency reduction)
├── Calendar/email/goal/workflow triggers
└── SYSTEM_PULSE architecture

LOOP (8 modules)
├── Trigger handling
├── Cognitive activation
├── Reflex system (voice latency)
├── Feedback loop
├── Turn zero handling
├── Temporal context
├── Objects column
└── Correction loop
```

### Research Papers Implemented

| Paper | Title                                  | Module                      |
| ----- | -------------------------------------- | --------------------------- |
| #4    | Context-Conditional Beliefs            | `belief_context_state.py` |
| #5    | Causal Attribution via DecisionBundles | `decision_bundle.py`      |
| #11   | Hierarchical Belief Cascading          | `cascade.py`              |
| #19   | Social Awareness                       | `social.py`               |
| #20   | Cognitive Engrams (Multimodal Memory)  | `perception.py`           |
| #21   | Three-Column Working Memory            | `working_memory/`         |
| #22   | Time-Based Context Activation          | `scheduler/`              |

### Capability Count

- **Total modules:** 121 ported from research
- **Implemented:** 85%
- **Production-ready:** Yes

---

## Olympus (G800 Class)

**Named for Olympus Mons—the tallest mountain in the solar system, located on Mars. The summit.**

### Mission: The Theoretical Peak

Olympus represents capabilities that extend beyond current implementation—features that require breakthroughs in coordination, learning, or safety guarantees.

### Additions Over Mars

| Capability                            | Description                                            | Status      |
| ------------------------------------- | ------------------------------------------------------ | ----------- |
| **Multi-Agent Coordination**    | AP agent, AR agent, Controller agent working together  | Research    |
| **Proactive Goal Pursuit**      | Aleq identifies goals from patterns, not just reactive | Research    |
| **Self-Tuning Autonomy**        | Thresholds adjust based on success/failure rates       | Research    |
| **Long-Horizon Planning**       | Multi-day task planning with dependencies              | Research    |
| **Cross-Conversation Learning** | Optimize belief updates across all interactions        | Research    |
| **Cross-Organization Learning** | Federated learning across customers (anonymized)       | Theoretical |
| **Self-Modification**           | Aleq rewrites its own policy rules                     | Theoretical |
| **Formal Verification**         | Prove decisions are correct before execution           | Theoretical |

### Why Olympus Is The Summit

These aren't just "nice to have" features. They represent fundamental advances:

- **Multi-agent** requires solving coordination and delegation
- **Self-tuning** requires safety guarantees on threshold changes
- **Cross-org learning** requires privacy/legal framework
- **Self-modification** requires alignment guarantees

Olympus is where we're headed. Mars is where we ship.

---

## Feature Boundaries: The Complete Matrix

### Tier 1: Input & Triggers

| Feature                      | Baby Mars | Mars-Lite | Mars | Olympus |
| ---------------------------- | --------- | --------- | ---- | ------- |
| Email webhook                | ✅        | ✅        | ✅   | ✅      |
| Slack webhook                | ✅        | ✅        | ✅   | ✅      |
| Voice input                  | —        | —        | ✅   | ✅      |
| Vision/images                | —        | ✅        | ✅   | ✅      |
| SYSTEM_PULSE (time triggers) | —        | ✅        | ✅   | ✅      |
| Multi-channel routing        | —        | ✅        | ✅   | ✅      |

### Tier 2: Perception & Extraction

| Feature                    | Baby Mars | Mars-Lite | Mars | Olympus |
| -------------------------- | --------- | --------- | ---- | ------- |
| PDF/OCR extraction         | ✅        | ✅        | ✅   | ✅      |
| Confidence scoring         | ✅        | ✅        | ✅   | ✅      |
| Entity resolution          | ✅        | ✅        | ✅   | ✅      |
| Hesitation detection       | —        | ✅        | ✅   | ✅      |
| Perception correction loop | —        | ✅        | ✅   | ✅      |
| VLM image analysis         | —        | ✅        | ✅   | ✅      |
| Voice transcription        | —        | —        | ✅   | ✅      |

### Tier 3: Working Memory

| Feature                     | Baby Mars | Mars-Lite | Mars | Olympus |
| --------------------------- | --------- | --------- | ---- | ------- |
| Conversation context        | ✅        | ✅        | ✅   | ✅      |
| Context pills (@references) | ✅        | ✅        | ✅   | ✅      |
| 3-4 slot model              | —        | ✅        | ✅   | ✅      |
| Notes queue with TTL        | —        | ✅        | ✅   | ✅      |
| Objects column (salience)   | —        | —        | ✅   | ✅      |
| Thrashing detection         | —        | —        | ✅   | ✅      |
| Cross-conversation memory   | —        | —        | —   | ✅      |

### Tier 4: Appraisal

| Feature                     | Baby Mars | Mars-Lite | Mars | Olympus |
| --------------------------- | --------- | --------- | ---- | ------- |
| Basic intent classification | ✅        | ✅        | ✅   | ✅      |
| Emotion detection           | —        | ✅        | ✅   | ✅      |
| Politeness (P+D+R)          | —        | ✅        | ✅   | ✅      |
| Face threat analysis        | —        | ✅        | ✅   | ✅      |
| Covariation check           | —        | ✅        | ✅   | ✅      |
| Knowledge gap detection     | —        | ✅        | ✅   | ✅      |
| Severity classification     | —        | ✅        | ✅   | ✅      |
| Preemption detection        | —        | —        | ✅   | ✅      |
| Uncertainty triggers        | —        | —        | ✅   | ✅      |

### Tier 5: Belief System

| Feature                     | Baby Mars | Mars-Lite | Mars | Olympus |
| --------------------------- | --------- | --------- | ---- | ------- |
| Belief storage (Neo4j)      | ✅        | ✅        | ✅   | ✅      |
| EMA strength updates        | ✅        | ✅        | ✅   | ✅      |
| Flat belief updates         | ✅        | —        | —   | —      |
| Context-conditional beliefs | —        | ✅        | ✅   | ✅      |
| DecisionBundle (causal)     | —        | ✅        | ✅   | ✅      |
| Belief cascading (SUPPORTS) | —        | ✅        | ✅   | ✅      |
| Interference decay          | —        | —        | ✅   | ✅      |
| Cross-org belief patterns   | —        | —        | —   | ✅      |

### Tier 6: Autonomy & Decision

| Feature                    | Baby Mars | Mars-Lite | Mars | Olympus |
| -------------------------- | --------- | --------- | ---- | ------- |
| 3-tier autonomy thresholds | ✅        | ✅        | ✅   | ✅      |
| HITL decision cards        | ✅        | ✅        | ✅   | ✅      |
| Timeline transparency      | ✅        | ✅        | ✅   | ✅      |
| Conflict resolution        | —        | ✅        | ✅   | ✅      |
| Execution planning         | —        | ✅        | ✅   | ✅      |
| EVT gating                 | —        | —        | ✅   | ✅      |
| Self-tuning thresholds     | —        | —        | —   | ✅      |
| Multi-agent delegation     | —        | —        | —   | ✅      |

### Tier 7: Policy & Guardrails

| Feature                 | Baby Mars | Mars-Lite | Mars | Olympus |
| ----------------------- | --------- | --------- | ---- | ------- |
| Basic quality gate      | ✅        | ✅        | ✅   | ✅      |
| Retry with backoff      | ✅        | ✅        | ✅   | ✅      |
| Hedging enforcement     | —        | ✅        | ✅   | ✅      |
| Personality gate        | —        | ✅        | ✅   | ✅      |
| Authenticity scoring    | —        | —        | ✅   | ✅      |
| 11-field validator      | —        | —        | ✅   | ✅      |
| Self-modifying policies | —        | —        | —   | ✅      |

### Tier 8: Error Recovery

| Feature                     | Baby Mars | Mars-Lite | Mars | Olympus |
| --------------------------- | --------- | --------- | ---- | ------- |
| Simple acknowledgment       | ✅        | —        | —   | —      |
| A.C.R.E. (5-state machine)  | —        | ✅        | ✅   | ✅      |
| Severity-calibrated apology | —        | ✅        | ✅   | ✅      |
| Root cause analysis         | —        | ✅        | ✅   | ✅      |
| Service Recovery Paradox    | —        | ✅        | ✅   | ✅      |
| Predictive error prevention | —        | —        | —   | ✅      |

### Tier 9: Execution & Output

| Feature                  | Baby Mars | Mars-Lite | Mars | Olympus |
| ------------------------ | --------- | --------- | ---- | ------- |
| Stargate API calls       | ✅        | ✅        | ✅   | ✅      |
| Email formatting         | ✅        | ✅        | ✅   | ✅      |
| Slack formatting         | ✅        | ✅        | ✅   | ✅      |
| Voice response (<20s)    | —        | —        | ✅   | ✅      |
| Reflex system (fillers)  | —        | —        | ✅   | ✅      |
| Channel-specific motor   | —        | —        | ✅   | ✅      |
| Multi-agent output merge | —        | —        | —   | ✅      |

### Tier 10: Learning & Feedback

| Feature                         | Baby Mars | Mars-Lite | Mars | Olympus |
| ------------------------------- | --------- | --------- | ---- | ------- |
| Memory consolidation            | ✅        | ✅        | ✅   | ✅      |
| Turn recording                  | ✅        | ✅        | ✅   | ✅      |
| Focused belief updates          | ✅        | ✅        | ✅   | ✅      |
| Cascade propagation             | —        | ✅        | ✅   | ✅      |
| Authority learning              | —        | ✅        | ✅   | ✅      |
| Cross-conversation optimization | —        | —        | —   | ✅      |
| Federated learning              | —        | —        | —   | ✅      |

### Tier 11: Scheduling & Proactivity

| Feature                       | Baby Mars | Mars-Lite | Mars | Olympus |
| ----------------------------- | --------- | --------- | ---- | ------- |
| Webhook-driven (reactive)     | ✅        | ✅        | ✅   | ✅      |
| Context predictor             | —        | ✅        | ✅   | ✅      |
| Preloader (latency reduction) | —        | ✅        | ✅   | ✅      |
| SYSTEM_PULSE triggers         | —        | ✅        | ✅   | ✅      |
| Calendar/goal triggers        | —        | —        | ✅   | ✅      |
| Proactive goal pursuit        | —        | —        | —   | ✅      |
| Long-horizon planning         | —        | —        | —   | ✅      |

### Tier 12: Onboarding

| Feature                     | Baby Mars | Mars-Lite | Mars | Olympus |
| --------------------------- | --------- | --------- | ---- | ------- |
| Manual setup                | ✅        | —        | —   | —      |
| Birth system (<90s)         | —        | ✅        | ✅   | ✅      |
| Apollo enrichment           | —        | ✅        | ✅   | ✅      |
| Knowledge packs             | —        | ✅        | ✅   | ✅      |
| Scenario seeding            | —        | ✅        | ✅   | ✅      |
| Auto-organization detection | —        | —        | —   | ✅      |

---

## Summary: Feature Counts by Tier

| System              | Features | Research Papers | Module Count |
| ------------------- | -------- | --------------- | ------------ |
| **Baby Mars** | 24       | 0               | ~15          |
| **Mars-Lite** | 52       | 4               | ~60          |
| **Mars**      | 68       | 7               | ~121         |
| **Olympus**   | 80+      | 7+              | ~150+        |

---

## Current State

| System              | Aircraft Class | Status                    | This Repo        |
| ------------------- | -------------- | ------------------------- | ---------------- |
| **Baby Mars** | G300/G400      | Architecture doc complete | No               |
| **Mars-Lite** | G500/G600      | 85% implemented           | **Yes**    |
| **Mars**      | G700           | Target                    | Yes (this is it) |
| **Olympus**   | G800           | Research roadmap          | Future           |

### Where We Are

This repository (`mars-lite` branch) is building toward **Mars** (G700 class). The codebase currently sits at Mars-Lite level (G500/G600) with 85% of modules implemented.

**Baby Mars** is a separate, simpler system described in the architecture document. It doesn't need most of what's in this repo—it's a G300 flying NYC→Miami, not a G700 flying NYC→Tokyo.

---

## The Takeaway

| If You Need...                   | Use...                             |
| -------------------------------- | ---------------------------------- |
| Single-domain AP automation      | **Baby Mars** (G300)         |
| Multi-domain with error recovery | **Mars-Lite** (G600)         |
| Full cognitive architecture      | **Mars** (G700)              |
| Multi-agent coordination         | **Olympus** (G800) - not yet |

**Don't build a G700 to fly routes a G300 handles perfectly.**
