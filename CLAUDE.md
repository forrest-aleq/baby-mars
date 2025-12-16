# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Baby MARS is a production cognitive architecture implementing Aleq's 20 research papers using Claude API + LangGraph. It's MARS with a "rented brain" - same cognitive architecture, but using Claude instead of TAMI (custom fine-tuned model).

**Key Distinction:** This is NOT a typical LLM wrapper. It implements a sophisticated belief system, memory with peak-end weighting, hierarchical goals, and competence-based autonomy.

## Build & Run Commands

```bash
# Install
pip install -e .

# Run tests
pytest

# Run single test
pytest tests/test_beliefs.py -v

# Run test scenarios
python -m test_runner                      # Default scenario
python -m test_runner invoice_processing   # Specific scenario
python -m test_runner all                  # All scenarios
python -m test_runner stream invoice_processing  # With streaming

# Type checking
mypy src/

# Linting
ruff check src/
```

## Architecture

### Core Cognitive Loop (src/cognitive_loop/graph.py)

The system implements a 7-node LangGraph that processes every interaction:

```
START → cognitive_activation → [dialectical_resolution?] → appraisal → action_selection
         ↓                                                                    ↓
    load beliefs,                                               route by autonomy:
    goals, context                                              - guidance_seeking → response
                                                                - action_proposal → response
                                                                - autonomous → execution
                                                                          ↓
                                                               verification → [retry?] → feedback
                                                                                            ↓
                                                                               response_generation → personality_gate → END
```

### The 6 Things (src/birth/birth_system.py)

Every agent has these 6 distinct types of information:
1. **Capabilities** - Binary flags (can/can't do something)
2. **Relationships** - Org structure facts (reports_to, authority)
3. **Knowledge** - Certain facts (no strength, just true)
4. **Beliefs** - Uncertain claims WITH strength (0.0-1.0)
5. **Goals** - What to accomplish (has priority)
6. **Style** - How to behave (tone, verbosity, formality)

### Belief System (src/graphs/belief_graph.py)

NetworkX-backed belief graph implementing:
- **Paper #4**: Context-conditional beliefs with backoff resolution (ClientA|month-end|>10K → ClientA|month-end|* → *|*|*)
- **Paper #9**: Moral asymmetry (ethical failures update 10x faster than successes)
- **Paper #10**: A.C.R.E. category thresholds (ethical: 0.95, aesthetic: 0.60)
- **Paper #11**: Hierarchical beliefs with cascading updates (SUPPORTS edges)
- **Paper #12**: Peak-end rule for memory weighting

### Autonomy (Paper #1)

Belief strength determines supervision mode:
- `< 0.4`: guidance_seeking (ask for help)
- `0.4-0.7`: action_proposal (propose and wait for approval)
- `>= 0.7`: autonomous (execute directly)

### State Schema (src/state/schema.py)

Three-Column Working Memory (Paper #8):
- **Column 1**: Active Tasks (3-4 max capacity)
- **Column 2**: Notes (TTL-based queue)
- **Column 3**: Objects (people, entities, beliefs, temporal context)

### Immutable Beliefs (Personality)

Located in `src/birth/birth_system.py` as `IMMUTABLE_BELIEFS`. These NEVER change and are checked by `personality_gate_node` before every response. They include:
- Never assist with fraud
- Acknowledge uncertainty
- Escalate beyond authority
- Protect confidential information

## Key Files

- `src/cognitive_loop/graph.py` - LangGraph definition and routing
- `src/state/schema.py` - All TypedDicts and constants from research papers
- `src/graphs/belief_graph.py` - NetworkX belief DAG with all paper implementations
- `src/birth/birth_system.py` - Birth modes (full/standard/micro) and initial belief seeding
- `src/skills/*.md` - Claude prompt templates for domain knowledge
- `test_runner.py` - Scenario-based testing harness

## Research Paper Constants

From `src/state/schema.py` (MARS taxonomy: moral, competence, technical, preference, identity):

```python
# Paper #9: Moral Asymmetry Multipliers
CATEGORY_MULTIPLIERS = {
    "moral": {"success": 3.0, "failure": 10.0},      # Trust violations = massive impact
    "competence": {"success": 1.0, "failure": 2.0},  # How to do things
    "technical": {"success": 1.0, "failure": 1.5},   # Domain-specific facts
    "preference": {"success": 1.0, "failure": 1.0},  # Style choices
    "identity": {"success": 0.0, "failure": 0.0},    # IMMUTABLE - A.C.R.E. firewall
}

# Paper #10: A.C.R.E. Invalidation Thresholds
INVALIDATION_THRESHOLDS = {
    "moral": 0.95,       # Very hard to invalidate
    "competence": 0.75,  # Moderate threshold
    "technical": 0.70,   # Technical facts can be updated
    "preference": 0.60,  # Preferences are flexible
    "identity": 1.0,     # NEVER invalidate
}

# Paper #1: Autonomy Thresholds
AUTONOMY_THRESHOLDS = {
    "guidance_seeking": 0.4,
    "action_proposal": 0.7,
    "autonomous": 1.0,
}
```

## Environment Variables

```bash
ANTHROPIC_API_KEY="sk-..."  # Required for Claude API
DATABASE_URL="postgresql://user:pass@localhost:5432/baby_mars"  # Required for persistence
```

## Persistence Layer

Located in `src/persistence/`:

- **database.py** - Postgres connection pool, table creation
- **beliefs.py** - Save/load beliefs to/from database

Key features:
- Beliefs persisted after every update (durability over performance)
- One row per belief (queryable across orgs)
- LRU cache for org graphs (`src/graphs/belief_graph_manager.py`)
- LangGraph checkpointing via `PostgresSaver.setup()`

## HITL Interrupts

The `action_proposal` node (`src/cognitive_loop/nodes/action_proposal.py`) uses LangGraph's `interrupt()` to pause for human approval:

```python
from langgraph.types import interrupt

# Graph pauses here until human responds
human_response = interrupt({
    "type": "action_proposal",
    "summary": "Human-readable action summary",
    "options": ["approve", "reject"]
})
```

Approval flow:
- **approve**: Continue to execution node
- **reject**: Go to response_generation with guidance_seeking mode

## Testing a Scenario

To trace through the cognitive loop:
1. `birth_system.py:birth_person()` creates initial state with beliefs
2. `cognitive_loop/graph.py` processes through nodes
3. Each node in `cognitive_loop/nodes/` has a `process(state)` function
4. `personality_gate_node` validates final response against immutable beliefs
