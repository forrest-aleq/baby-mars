"""
Shared Test Fixtures
=====================

Pytest fixtures for Baby MARS tests.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================
# SCHEMA FIXTURES
# ============================================================


@pytest.fixture
def sample_belief():
    """Create a sample belief for testing."""
    from src.state.schema import create_belief

    return create_belief(
        statement="Test belief statement",
        category="competence",
        initial_strength=0.7,
        context_key="test|*|*",
    )


@pytest.fixture
def sample_moral_belief():
    """Create a sample moral belief for testing."""
    from src.state.schema import create_belief

    return create_belief(
        statement="Financial records must be accurate",
        category="moral",
        initial_strength=0.95,
        context_key="*|*|*",
    )


@pytest.fixture
def sample_identity_belief():
    """Create a sample immutable identity belief."""
    from src.state.schema import create_belief

    belief = create_belief(
        statement="I never assist with fraud",
        category="identity",
        initial_strength=1.0,
        context_key="*|*|*",
    )
    belief["immutable"] = True
    return belief


@pytest.fixture
def sample_state():
    """Create a sample BabyMARSState for testing."""
    from src.state.schema import create_initial_state

    return create_initial_state(
        thread_id="test-thread-123", org_id="test-org-456", user_id="test-user-789"
    )


@pytest.fixture
def sample_state_with_message(sample_state):
    """Create a state with a user message."""
    sample_state["messages"] = [
        {"role": "user", "content": "Process invoice #1234 for $5,000 from Acme Corp"}
    ]
    return sample_state


@pytest.fixture
def sample_state_with_action(sample_state_with_message):
    """Create a state with a selected action."""
    sample_state_with_message["selected_action"] = {
        "action_type": "process_invoice",
        "work_units": [
            {
                "unit_id": "wu-001",
                "tool": "erp",
                "verb": "process_invoice",
                "entities": {"invoice_id": "INV-1234"},
                "slots": {"amount": 5000, "vendor": "Acme Corp"},
                "constraints": [],
            }
        ],
        "requires_tools": ["erp"],
        "estimated_difficulty": 2,
    }
    sample_state_with_message["supervision_mode"] = "action_proposal"
    return sample_state_with_message


@pytest.fixture
def sample_person():
    """Create a sample person for testing."""
    from src.state.schema import create_person

    return create_person(name="Jane Smith", role="Controller", authority=0.8)


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    from src.state.schema import create_memory

    return create_memory(
        description="Processed invoice successfully",
        outcome="success",
        context_key="invoice_processing|*|*",
        difficulty_level=2,
        emotional_intensity=0.3,
    )


@pytest.fixture
def sample_note():
    """Create a sample note for testing."""
    return {
        "note_id": "note-001",
        "content": "Follow up on vendor payment",
        "created_at": datetime.now().isoformat(),
        "ttl_hours": 24,
        "priority": 0.7,
        "source": "system",
        "context": {},
    }


# ============================================================
# BELIEF GRAPH FIXTURES
# ============================================================


@pytest.fixture
def empty_belief_graph():
    """Create an empty belief graph for testing."""
    from src.graphs.belief_graph import BeliefGraph

    return BeliefGraph()


@pytest.fixture
def populated_belief_graph(sample_belief, sample_moral_belief):
    """Create a belief graph with some beliefs."""
    from src.graphs.belief_graph import BeliefGraph

    graph = BeliefGraph()
    graph.add_belief(sample_belief)
    graph.add_belief(sample_moral_belief)
    return graph


@pytest.fixture
def hierarchical_belief_graph():
    """Create a belief graph with support relationships."""
    from src.graphs.belief_graph import BeliefGraph
    from src.state.schema import create_belief

    graph = BeliefGraph()

    # Foundation belief
    foundation = create_belief(
        statement="Financial accuracy is paramount", category="moral", initial_strength=0.95
    )
    graph.add_belief(foundation)

    # Derived beliefs
    derived1 = create_belief(
        statement="Invoices must be validated before processing",
        category="competence",
        initial_strength=0.7,
    )
    graph.add_belief(derived1)

    derived2 = create_belief(
        statement="Journal entries require double-entry", category="technical", initial_strength=0.8
    )
    graph.add_belief(derived2)

    # Add support relationships
    graph.add_support_relationship(foundation["belief_id"], derived1["belief_id"], 0.9)
    graph.add_support_relationship(foundation["belief_id"], derived2["belief_id"], 0.8)

    return graph, foundation, derived1, derived2


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    from src.graphs.belief_graph import reset_belief_graph
    from src.graphs.belief_graph_manager import reset_belief_graph_manager

    reset_belief_graph()
    reset_belief_graph_manager()

    yield

    # Clean up after test
    reset_belief_graph()
    reset_belief_graph_manager()


# ============================================================
# MOCK FIXTURES
# ============================================================


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client for testing."""
    mock = AsyncMock()
    mock.complete.return_value = "Mock response from Claude"
    mock.complete_structured.return_value = MagicMock(
        synthesis=None,
        chosen_goal_id="goal-1",
        deferred_goal_ids=[],
        resolution_reasoning="Test resolution",
        requires_human_input=False,
    )
    return mock


@pytest.fixture
def mock_db_pool():
    """Create a mock database pool for testing."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = "INSERT 1"
    mock_conn.fetch.return_value = []
    mock_conn.fetchrow.return_value = None
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()

    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()

    return mock_pool, mock_conn


# ============================================================
# DATABASE FIXTURES
# ============================================================


@pytest.fixture
def mock_database_url(monkeypatch):
    """Set up mock database URL."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")


@pytest.fixture
def sample_belief_row():
    """Create a sample belief row as returned from database."""
    return {
        "belief_id": "test-belief-001",
        "statement": "Test belief from DB",
        "category": "competence",
        "strength": 0.75,
        "context_key": "*|*|*",
        "context_states": "{}",
        "supports": [],
        "supported_by": [],
        "support_weights": "{}",
        "last_updated": datetime.now(),
        "success_count": 5,
        "failure_count": 1,
        "is_end_memory_influenced": False,
        "peak_intensity": 0.0,
        "invalidation_threshold": 0.75,
        "is_distrusted": False,
        "moral_violation_count": 0,
        "immutable": False,
        "tags": [],
    }


# ============================================================
# WORK UNIT FIXTURES
# ============================================================


@pytest.fixture
def sample_work_unit():
    """Create a sample work unit for testing."""
    return {
        "unit_id": "wu-test-001",
        "tool": "erp",
        "verb": "process_invoice",
        "entities": {"invoice_id": "INV-1234"},
        "slots": {"amount": 1000, "gl_code": "5000"},
        "constraints": [],
    }


@pytest.fixture
def sample_bank_work_unit():
    """Create a sample bank work unit for testing."""
    return {
        "unit_id": "wu-test-002",
        "tool": "bank",
        "verb": "process_payment",
        "entities": {"payment_id": "PMT-5678"},
        "slots": {"amount": 2500, "payment_date": "2024-01-15"},
        "constraints": [],
    }


# ============================================================
# RAPPORT FIXTURES
# ============================================================


@pytest.fixture
def sample_rapport_state():
    """Create a fresh rapport state for testing."""
    from src.persistence.rapport import RapportState

    return RapportState(
        rapport_id="rapport_test123",
        org_id="org_test",
        person_id="person_test",
        person_name="Test User",
        rapport_level=0.3,
        trust_level=0.3,
        familiarity=0.0,
        interaction_count=0,
        positive_interactions=0,
        negative_interactions=0,
        last_interaction=None,
        first_interaction="2024-01-01T00:00:00+00:00",
        memorable_moments=[],
        topics_discussed={},
        preferences_learned={},
        inside_references=[],
        preferred_formality="casual",
        preferred_verbosity="concise",
        humor_receptivity=0.5,
        first_impression_given=False,
        first_impression_text=None,
        first_impression_at=None,
    )


@pytest.fixture
def high_rapport_state(sample_rapport_state):
    """Create a rapport state after many positive interactions."""
    state = dict(sample_rapport_state)
    state["rapport_level"] = 0.85
    state["trust_level"] = 0.75
    state["familiarity"] = 0.7
    state["interaction_count"] = 50
    state["positive_interactions"] = 45
    state["negative_interactions"] = 5
    state["inside_references"] = ["the month-end incident", "lockbox humor"]
    state["topics_discussed"] = {"invoices": 20, "payments": 15, "reconciliation": 10}
    state["preferences_learned"] = {"communication_style": "brief", "humor": True}
    return state


@pytest.fixture
def sample_rapport_db_row():
    """Create a sample database row for rapport testing."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("UTC"))
    return {
        "rapport_id": "rapport_db_test",
        "org_id": "org_test",
        "person_id": "person_test",
        "person_name": "Test User",
        "rapport_level": 0.5,
        "trust_level": 0.4,
        "familiarity": 0.3,
        "interaction_count": 10,
        "positive_interactions": 8,
        "negative_interactions": 2,
        "last_interaction": now,
        "first_interaction": now,
        "memorable_moments": [{"summary": "test moment", "outcome": "positive"}],
        "topics_discussed": {"invoices": 5},
        "preferences_learned": {"detail_level": "high"},
        "inside_references": ["test reference"],
        "preferred_formality": "casual",
        "preferred_verbosity": "concise",
        "humor_receptivity": 0.6,
        "first_impression_given": True,
        "first_impression_text": "Nice to meet you!",
        "first_impression_at": now,
    }


@pytest.fixture
def mock_rapport_db(mock_db_pool):
    """Create a mock database configured for rapport operations."""
    _, mock_conn = mock_db_pool
    mock_conn.fetchrow.return_value = None  # Default: no rapport exists
    mock_conn.fetch.return_value = []
    mock_conn.execute.return_value = "UPDATE 1"
    return mock_conn


@pytest.fixture
def sample_birth_request():
    """Create a sample birth API request."""
    return {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "CFO",
        "org_name": "Acme Corp",
        "industry": "manufacturing",
        "timezone": "America/New_York",
    }
