# Baby MARS

> Production cognitive architecture using Claude + LangGraph.  
> Implementation of Aleq's 20 research papers without custom model training.

## What Is This?

Baby MARS is MARS with a rented brain. It implements the complete Aleq cognitive research using off-the-shelf components:

| MARS | Baby MARS |
|------|-----------|
| TAMI (trained LLM) | Claude API |
| Neo4j Graph | NetworkX + Postgres |
| Custom Connectors | MCP Servers |

**What stays the same:** LangGraph orchestration, belief system, cognitive loop, state schema.

## Quick Start

```bash
# Install
pip install -e .

# Set API key
export ANTHROPIC_API_KEY="sk-..."

# Run
python -m baby_mars.main
```

## Research Papers Implemented

### Beliefs
- [x] Paper #1: Competence-Based Autonomy
- [x] Paper #4: Context-Conditional Beliefs
- [x] Paper #9: Moral Asymmetry
- [x] Paper #10: A.C.R.E. (Category-Specific Invalidation)
- [x] Paper #11: Hierarchical Beliefs with Cascading

### Memory
- [x] Paper #12: Peak-End Rule
- [x] Paper #13: Interference-Based Decay

### Social
- [x] Paper #17: Social Awareness and Relationships

### Systems
- [x] Paper #3: Self-Correcting Validation
- [x] Paper #7: Event Sourcing
- [x] Paper #8: Three-Column Working Memory
- [x] Paper #15: Birth System
- [x] Paper #16: Duration Estimation
- [x] Paper #20: Planner-Translator-Driver

### Not Implemented (Requires Fine-Tuning)
- [ ] Paper #19: Latent Trajectory Learning

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LangGraph Orchestration                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   START → [cognitive_activation] → [appraise] → [select]    │
│              │                          │            │       │
│              ▼                          │            ▼       │
│        NetworkX                         │      [execute]     │
│    (beliefs, social)                    │            │       │
│                                         │            ▼       │
│                                    [verify] → [feedback]     │
│                                         │            │       │
│                                         ▼            ▼       │
│                              [response_generation] → END     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## State Schema

See `src/state/schema.py` for complete TypedDict definitions implementing:

- Three-Column Working Memory (Active Tasks, Notes, Objects)
- Context-Conditional Beliefs
- Hierarchical Belief Graph
- Social Relationship Graph
- Event-Sourced Audit Trail

## Migration to MARS

When TAMI is ready:

```python
# Before (Baby MARS)
response = client.messages.create(model="claude-sonnet-4-20250514", ...)

# After (MARS)  
response = tami_client.inference(model="tami-medium-2025", ...)
```

Everything else stays the same.

## License

Proprietary - Aleq, Inc.
