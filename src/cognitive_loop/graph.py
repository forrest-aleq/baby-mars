"""
Baby MARS Cognitive Loop
=========================

LangGraph implementation of the five-step cognitive loop:
1. Trigger → 2. Cognitive Activation → 3. Appraisal →
4. Action Selection → 5. Execution → 6. Verification → 7. Feedback

This is the core orchestration that implements the research.
"""

import os
from typing import Literal, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from ..state.schema import BabyMARSState

# ============================================================
# ROUTING FUNCTIONS
# ============================================================


def route_after_activation(state: BabyMARSState) -> Literal["dialectical_resolution", "appraisal"]:
    """Check for goal conflicts after cognitive activation"""
    if state.get("goal_conflict_detected", False):
        return "dialectical_resolution"
    return "appraisal"


def route_after_action_selection(
    state: BabyMARSState,
) -> Literal["response_generation", "action_proposal", "execution"]:
    """
    Route based on autonomy level.
    Paper #1: Competence-Based Autonomy
    """
    mode = state.get("supervision_mode", "guidance_seeking")

    if mode == "guidance_seeking":
        return "response_generation"  # Go straight to response
    elif mode == "action_proposal":
        return "action_proposal"  # HITL interrupt
    else:
        return "execution"  # Autonomous execution


def route_after_action_proposal(
    state: BabyMARSState,
) -> Literal["execution", "response_generation"]:
    """
    Route based on human approval response.
    Called after action_proposal node resumes from interrupt.
    """
    approval_status = state.get("approval_status", "")

    if approval_status == "approved":
        return "execution"
    else:
        # Rejected or no action - generate guidance response
        return "response_generation"


def route_after_verification(state: BabyMARSState) -> Literal["retry", "feedback", "escalate"]:
    """
    Route based on validation results.
    Paper #3: Self-Correcting Validation
    """
    results = state.get("validation_results", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # Check for failures
    failures = [r for r in results if not r.get("passed", True)]

    if not failures:
        return "feedback"  # All passed

    if retry_count < max_retries:
        # Check if fixable (low severity)
        fixable = all(f.get("severity", 1.0) < 0.7 for f in failures)
        if fixable:
            return "retry"

    return "escalate"  # Give up, ask human


# ============================================================
# NODE STUBS (to be implemented in nodes/*.py)
# ============================================================


async def cognitive_activation_node(state: BabyMARSState) -> dict:
    """
    Load cognitive context from graphs.
    Implements fetch_active_subgraph pattern.
    """
    # TODO: Import from nodes/cognitive_activation.py
    from .nodes.cognitive_activation import process

    return await process(state)


async def appraisal_node(state: BabyMARSState) -> dict:
    """
    Analyze situation against activated beliefs.
    Use Claude to perform rich appraisal.
    """
    from .nodes.appraisal import process

    return await process(state)


async def dialectical_resolution_node(state: BabyMARSState) -> dict:
    """
    Handle goal conflicts.
    """
    from .nodes.dialectical_resolution import process

    return await process(state)


async def action_selection_node(state: BabyMARSState) -> dict:
    """
    Select action based on appraisal and beliefs.
    Determine autonomy level (Paper #1).
    """
    from .nodes.action_selection import process

    return await process(state)


async def action_proposal_node(state: BabyMARSState) -> dict:
    """
    HITL interrupt node for action approval.
    Pauses execution until human approves or rejects.
    """
    from .nodes.action_proposal import process

    return await process(state)


async def execution_node(state: BabyMARSState) -> dict:
    """
    Execute action via MCP servers.
    PTD Driver layer.
    """
    from .nodes.execution import process

    return await process(state)


async def verification_node(state: BabyMARSState) -> dict:
    """
    Paper #3: Self-Correcting Validation
    Run validators on execution results.
    """
    from .nodes.verification import process

    return await process(state)


async def feedback_node(state: BabyMARSState) -> dict:
    """
    Update beliefs and create memories based on outcome.
    Papers #1, #9, #11, #12
    """
    from .nodes.feedback import process

    return await process(state)


async def response_generation_node(state: BabyMARSState) -> dict:
    """
    Generate final response based on supervision mode.
    """
    from .nodes.response_generation import process

    return await process(state)


async def personality_gate_node(state: BabyMARSState) -> dict:
    """
    Final validation against immutable personality beliefs.
    Ensures response doesn't violate core constraints.
    """
    from .nodes.personality_gate import process

    return await process(state)


# ============================================================
# GRAPH CONSTRUCTION
# ============================================================


def create_cognitive_loop_graph(checkpointer=None) -> StateGraph:
    """
    Create the main cognitive loop graph.

    The loop implements the five-step process from first principles:
    1. Trigger (implicit - user message)
    2. Cognitive Activation
    3. Appraisal
    4. Action Selection
    5. Feedback

    Extended with:
    - Dialectical Resolution (goal conflicts)
    - Execution (PTD architecture)
    - Verification (self-correction)
    """

    builder = StateGraph(BabyMARSState)

    # ============================================================
    # NODES
    # ============================================================

    # Core cognitive loop
    builder.add_node("cognitive_activation", cognitive_activation_node)
    builder.add_node("appraisal", appraisal_node)
    builder.add_node("action_selection", action_selection_node)
    builder.add_node("action_proposal", action_proposal_node)  # HITL interrupt node
    builder.add_node("feedback", feedback_node)
    builder.add_node("response_generation", response_generation_node)
    builder.add_node("personality_gate", personality_gate_node)

    # Extended nodes
    builder.add_node("dialectical_resolution", dialectical_resolution_node)
    builder.add_node("execution", execution_node)
    builder.add_node("verification", verification_node)

    # ============================================================
    # EDGES
    # ============================================================

    # Entry point
    builder.add_edge(START, "cognitive_activation")

    # After activation: check for goal conflicts
    builder.add_conditional_edges(
        "cognitive_activation",
        route_after_activation,
        {"dialectical_resolution": "dialectical_resolution", "appraisal": "appraisal"},
    )

    # After dialectical resolution, continue to appraisal
    builder.add_edge("dialectical_resolution", "appraisal")

    # After appraisal, select action
    builder.add_edge("appraisal", "action_selection")

    # After action selection: check supervision mode
    builder.add_conditional_edges(
        "action_selection",
        route_after_action_selection,
        {
            "response_generation": "response_generation",  # guidance_seeking goes here
            "action_proposal": "action_proposal",  # HITL interrupt
            "execution": "execution",  # autonomous
        },
    )

    # After action proposal: route based on approval
    builder.add_conditional_edges(
        "action_proposal",
        route_after_action_proposal,
        {
            "execution": "execution",  # approved
            "response_generation": "response_generation",  # rejected
        },
    )

    # After execution, verify
    builder.add_edge("execution", "verification")

    # After verification: retry, feedback, or escalate
    builder.add_conditional_edges(
        "verification",
        route_after_verification,
        {"retry": "execution", "feedback": "feedback", "escalate": "response_generation"},
    )

    # After feedback, generate response
    builder.add_edge("feedback", "response_generation")

    # After response generation, validate with personality gate
    builder.add_edge("response_generation", "personality_gate")

    # Exit after personality gate
    builder.add_edge("personality_gate", END)

    # Compile with checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

# Singleton checkpointer (initialized once)
_checkpointer: Optional[PostgresSaver] = None


def get_checkpointer() -> PostgresSaver:
    """
    Get or create the Postgres checkpointer.
    Calls setup() on first use to create tables.
    """
    global _checkpointer
    if _checkpointer is None:
        postgres_url = os.environ.get("DATABASE_URL")
        if not postgres_url:
            raise ValueError(
                "DATABASE_URL environment variable required for persistence. "
                "Use create_graph_in_memory() for testing without a database."
            )
        _checkpointer = PostgresSaver.from_conn_string(postgres_url)
        # Create tables if they don't exist
        _checkpointer.setup()
    return _checkpointer


def create_graph_with_postgres(postgres_url: str = None) -> StateGraph:
    """
    Create graph with Postgres persistence.

    Args:
        postgres_url: Optional override. If not provided, uses DATABASE_URL env var.
    """
    if postgres_url:
        checkpointer = PostgresSaver.from_conn_string(postgres_url)
        checkpointer.setup()
    else:
        checkpointer = get_checkpointer()
    return create_cognitive_loop_graph(checkpointer)


def create_graph_in_memory() -> StateGraph:
    """Create graph with in-memory persistence (for testing)"""
    return create_cognitive_loop_graph(MemorySaver())


# ============================================================
# MAIN ENTRY POINT
# ============================================================


async def invoke_cognitive_loop(
    state: BabyMARSState, graph: StateGraph = None, config: dict = None
) -> BabyMARSState:
    """
    Main entry point for running the cognitive loop.

    Args:
        state: Initial state with user message
        graph: Pre-compiled graph (optional)
        config: LangGraph config with thread_id etc.

    Returns:
        Updated state after cognitive processing
    """
    if graph is None:
        graph = create_graph_in_memory()

    if config is None:
        config = {"configurable": {"thread_id": state.get("thread_id", "default")}}

    result = await graph.ainvoke(state, config)
    return result


async def stream_cognitive_loop(
    state: BabyMARSState, graph: StateGraph = None, config: dict = None
):
    """
    Stream events from the cognitive loop.

    Yields events as they occur for real-time UI updates.
    """
    if graph is None:
        graph = create_graph_in_memory()

    if config is None:
        config = {"configurable": {"thread_id": state.get("thread_id", "default")}}

    async for event in graph.astream_events(state, config, version="v2"):
        yield event
