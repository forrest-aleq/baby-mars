# Baby MARS API Overview

Quick reference for all external API calls in the codebase.

## Summary

| Service | Model/Type | Calls per Loop | Purpose |
|---------|-----------|----------------|---------|
| Anthropic Claude | claude-sonnet-4-5-20250929 | 3-7 | Cognitive processing |
| PostgreSQL | asyncpg | varies | Persistence |

**Total Claude calls per cognitive loop: 3-7** (depending on path taken)

---

## 1. Anthropic Claude API

### Configuration (`src/claude_client.py`)

```python
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
STRUCTURED_OUTPUTS_BETA = "structured-outputs-2025-11-13"

ClaudeConfig:
  max_tokens: 4096
  temperature: 0.7
  use_structured_outputs: True
```

### API Methods Available

| Method | Output Type | Use Case |
|--------|-------------|----------|
| `complete()` | Text | Simple responses |
| `complete_structured()` | Pydantic model | Reliable JSON |
| `complete_json()` | Dict | Raw JSON schema |
| `complete_with_tools()` | Tool use blocks | MCP integration |
| `stream()` | Async generator | Real-time output |

---

## 2. Claude Calls by Cognitive Loop Node

### Always Called (3 minimum)

| Node | File | Output Model | Skills Used | Purpose |
|------|------|--------------|-------------|---------|
| **Appraisal** | `nodes/appraisal.py:141` | `AppraisalOutput` | situation_appraisal, accounting_domain | Analyze situation, detect threats, assess goals |
| **Action Selection** | `nodes/action_selection.py:140` | `ActionSelectionOutput` | work_unit_vocabulary, accounting_domain | Select action, build work units |
| **Response Generation** | `nodes/response_generation.py:195` | `ResponseOutput` | response_generation, accounting_domain | Generate user-facing response |

### Conditionally Called (0-4 additional)

| Node | File | Output Model | Condition | Purpose |
|------|------|--------------|-----------|---------|
| **Dialectical Resolution** | `nodes/dialectical_resolution.py:119` | `DialecticalOutput` | Goal conflict detected | Resolve competing goals |
| **Verification** | `nodes/verification.py:364` | `ValidationOutput` | Complex validation needed | Claude-based validation |
| **Personality Gate** | `nodes/personality_gate.py:129` | Text | Always (safety check) | Check immutable beliefs |
| **Personality Gate** | `nodes/personality_gate.py:202` | Text | Violation detected | Generate boundary response |

### Call Paths

```
Minimum Path (guidance_seeking):
  appraisal → action_selection → response_generation → personality_gate
  = 3 Claude calls + 1 gate check

Maximum Path (autonomous + retry + violation):
  appraisal → action_selection → execution → verification (Claude)
  → feedback → response_generation → personality_gate (violation)
  → regenerate (x2)
  = 7 Claude calls
```

---

## 3. Pydantic Models for Structured Outputs

Defined in `src/claude_client.py:320-369`:

```python
class AppraisalOutput:
    face_threat_level: float        # 0.0-1.0
    expectancy_violation: Optional[str]
    goal_alignment: dict[str, float]
    urgency: float                  # 0.0-1.0
    uncertainty_areas: list[str]
    recommended_approach: str       # seek_guidance | propose_action | execute
    relevant_belief_ids: list[str]
    difficulty_assessment: int      # 1-5
    involves_ethical_beliefs: bool
    reasoning: str

class ActionSelectionOutput:
    action_type: str
    work_units: list[dict]
    tool_requirements: list[str]
    confidence: float
    requires_human_approval: bool
    approval_reason: Optional[str]
    estimated_difficulty: int

class ResponseOutput:
    main_content: str
    tone: str
    action_items: list[str]
    questions: list[str]           # For guidance_seeking
    confirmation_prompt: Optional[str]  # For action_proposal
    awaiting_input: bool

class ValidationOutput:
    all_passed: bool
    results: list[dict]
    recommended_action: str         # proceed | retry | escalate
    fix_suggestions: list[str]

class DialecticalOutput:
    synthesis: str
    chosen_goal_id: str
    deferred_goal_ids: list[str]
    resolution_reasoning: str
    requires_human_input: bool
```

---

## 4. PostgreSQL Database

### Configuration (`src/persistence/database.py`)

```python
# Connection via asyncpg
Pool: min_size=2, max_size=10
URL: DATABASE_URL environment variable
```

### Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `beliefs` | Belief persistence | belief_id, org_id, strength, context_states |
| `memories` | Episodic/procedural memory | memory_id, org_id, outcome, emotional_intensity |
| `feedback_events` | Audit log (immutable) | event_id, org_id, belief_updates |
| LangGraph checkpoint tables | Conversation state | Created by `PostgresSaver.setup()` |

### Operations

| Operation | File | When Called |
|-----------|------|-------------|
| `save_belief()` | `persistence/beliefs.py` | After each belief update |
| `load_beliefs_for_org()` | `persistence/beliefs.py` | On cache miss |
| `save_beliefs_batch()` | `persistence/beliefs.py` | Bulk save |

---

## 5. What's NOT Here

Baby MARS intentionally excludes:

- **No Neo4j** - Beliefs use NetworkX in-memory (Postgres for persistence)
- **No Apollo API** - Birth system is self-contained
- **No external enrichment APIs** - No third-party data
- **No MCP servers yet** - Execution uses mock handlers

---

## 6. Cost Estimation

Rough token estimates per cognitive loop:

| Node | Input Tokens | Output Tokens |
|------|-------------|---------------|
| Appraisal | ~1,500 | ~400 |
| Action Selection | ~1,200 | ~300 |
| Response Generation | ~1,000 | ~200 |
| Personality Gate | ~500 | ~50 |
| **Total (typical)** | **~4,200** | **~950** |

With claude-sonnet-4-5-20250929 pricing, estimate ~$0.02-0.05 per full loop.

---

## 7. Environment Variables

```bash
# Required
ANTHROPIC_API_KEY="sk-..."
DATABASE_URL="postgresql://user:pass@localhost:5432/baby_mars"
```
