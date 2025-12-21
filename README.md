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
# Clone and install
git clone <repo>
cd baby_mars
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 1: Run the API server
baby-mars serve

# Option 2: Interactive chat
baby-mars chat --name "Your Name" --role "Controller"

# Option 3: Docker (full stack with Postgres)
docker-compose up
```

## API Endpoints

```
POST /birth              - Birth a new person into the system
POST /message            - Send a message, get a response
POST /message/stream     - Stream response via SSE
POST /approve            - Approve/reject proposed actions (HITL)
GET  /beliefs/{org_id}   - View beliefs for an organization
GET  /health             - Health check
```

## CLI Commands

```bash
baby-mars serve          # Start API server (default: 0.0.0.0:8000)
baby-mars chat           # Interactive chat session
baby-mars birth <name>   # Birth a person and view beliefs
baby-mars beliefs        # View current belief graph
baby-mars version        # Version info
```

## Research Papers Implemented

### Beliefs
- [x] **Paper #1**: Competence-Based Autonomy (strength → supervision mode)
- [x] **Paper #4**: Context-Conditional Beliefs (hierarchical backoff)
- [x] **Paper #9**: Moral Asymmetry (10x failure multiplier)
- [x] **Paper #10**: A.C.R.E. (category-specific invalidation thresholds)
- [x] **Paper #11**: Hierarchical Beliefs with Cascading Updates

### Memory
- [x] **Paper #12**: Peak-End Rule (intensity weighting)
- [x] **Paper #13**: Interference-Based Decay

### Social
- [x] **Paper #17**: Social Awareness and Relationships

### Systems
- [x] **Paper #3**: Self-Correcting Validation
- [x] **Paper #7**: Event Sourcing (immutable audit trail)
- [x] **Paper #8**: Three-Column Working Memory
- [x] **Paper #15**: Birth System (The 6 Things)
- [x] **Paper #16**: Difficulty Weights
- [x] **Paper #20**: Planner-Translator-Driver Architecture

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI / WebSocket Layer                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   START → [cognitive_activation] → [appraisal] → [action]   │
│              │                          │            │       │
│              ▼                          │            ▼       │
│      BeliefGraph                        │   [action_proposal]│
│   (NetworkX + Postgres)                 │      (HITL)        │
│                                         │            │       │
│                                    [execute] ← ← ← ←/        │
│                                         │                    │
│                                    [verify]                  │
│                                         │                    │
│                                    [feedback]                │
│                                         │                    │
│                              [response_generation]           │
│                                         │                    │
│                              [personality_gate] → END        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Supervision Modes

Based on belief strength (Paper #1):

| Strength | Mode | Behavior |
|----------|------|----------|
| < 0.4 | `guidance_seeking` | Ask for help |
| 0.4 - 0.7 | `action_proposal` | Propose & wait for approval |
| ≥ 0.7 | `autonomous` | Execute directly |

## Key Constants

```python
# Paper #9: Moral Asymmetry
CATEGORY_MULTIPLIERS = {
    "moral": {"success": 3.0, "failure": 10.0},  # Trust violations hit HARD
    "identity": {"success": 0.0, "failure": 0.0},  # IMMUTABLE
}

# Paper #10: A.C.R.E. Thresholds
INVALIDATION_THRESHOLDS = {
    "moral": 0.95,       # Very hard to invalidate
    "competence": 0.75,
    "preference": 0.60,  # Flexible
    "identity": 1.0,     # NEVER
}

# Paper #1: Autonomy
AUTONOMY_THRESHOLDS = {
    "guidance_seeking": 0.4,
    "action_proposal": 0.7,
}

# Paper #12: Learning
LEARNING_RATE = 0.15
PEAK_END_MULTIPLIER = 3.0
```

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional - Database (uses in-memory if not set)
DATABASE_URL=postgresql://user:pass@localhost:5432/baby_mars

# Optional - Auth (allows all if not set)
BABY_MARS_API_KEYS=key1,key2,key3

# Optional - Logging
LOG_LEVEL=INFO
LOG_JSON=true
```

## Docker Deployment

```bash
# Start everything (API + Postgres)
docker-compose up -d

# With admin tools
docker-compose --profile admin up -d

# View logs
docker-compose logs -f api
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/
```

## Migration to MARS

When TAMI is ready:

```python
# Before (Baby MARS)
response = client.messages.create(model="claude-sonnet-4-5-20250929", ...)

# After (MARS)
response = tami_client.inference(model="tami-medium-2025", ...)
```

Everything else stays the same.

## License

Proprietary - Aleq, Inc.
