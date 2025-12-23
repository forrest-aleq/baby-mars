"""
Baby MARS Cognitive Loop
=========================

LangGraph implementation of the five-step cognitive loop:
1. Trigger → 2. Cognitive Activation → 3. Appraisal →
4. Action Selection → 5. Execution → 6. Verification → 7. Feedback

This is the core orchestration that implements the research.
"""

import os
import time
from collections.abc import AsyncIterator
from typing import Any, Literal, Optional, Union

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..observability import get_instrumentation, get_logger
from ..state.schema import BabyMARSState

logger = get_logger(__name__)

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


async def cognitive_activation_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Load cognitive context from graphs.
    Implements fetch_active_subgraph pattern.
    """
    # TODO: Import from nodes/cognitive_activation.py
    from .nodes.cognitive_activation import process

    return await process(state)


async def appraisal_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Analyze situation against activated beliefs.
    Use Claude to perform rich appraisal.
    """
    from .nodes.appraisal import process

    return await process(state)


async def dialectical_resolution_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Handle goal conflicts.
    """
    from .nodes.dialectical_resolution import process

    return await process(state)


async def action_selection_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Select action based on appraisal and beliefs.
    Determine autonomy level (Paper #1).
    """
    from .nodes.action_selection import process

    return await process(state)


async def action_proposal_node(state: BabyMARSState) -> dict[str, Any]:
    """
    HITL interrupt node for action approval.
    Pauses execution until human approves or rejects.
    """
    from .nodes.action_proposal import process

    return await process(state)


async def execution_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Execute action via MCP servers.
    PTD Driver layer.
    """
    from .nodes.execution import process

    return await process(state)


async def verification_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Paper #3: Self-Correcting Validation
    Run validators on execution results.
    """
    from .nodes.verification import process

    return await process(state)


async def feedback_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Update beliefs and create memories based on outcome.
    Papers #1, #9, #11, #12
    """
    from .nodes.feedback import process

    return await process(state)


async def response_generation_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Generate final response based on supervision mode.
    """
    from .nodes.response_generation import process

    return await process(state)


async def personality_gate_node(state: BabyMARSState) -> dict[str, Any]:
    """
    Final validation against immutable personality beliefs.
    Ensures response doesn't violate core constraints.
    """
    from .nodes.personality_gate import process

    return await process(state)


# ============================================================
# GRAPH CONSTRUCTION
# ============================================================


def create_cognitive_loop_graph(
    checkpointer: Optional[Union[MemorySaver, PostgresSaver]] = None,
) -> CompiledStateGraph[BabyMARSState]:
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

    builder: StateGraph[BabyMARSState] = StateGraph(BabyMARSState)

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
    actual_checkpointer: Union[MemorySaver, PostgresSaver] = (
        checkpointer if checkpointer is not None else MemorySaver()
    )

    return builder.compile(checkpointer=actual_checkpointer)  # type: ignore[return-value]


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

# Singleton checkpointer (initialized once)
_checkpointer: Optional[PostgresSaver] = None
_checkpointer_ctx: Optional[Any] = None  # Context manager reference for cleanup


def cleanup_checkpointer() -> None:
    """
    Clean up checkpointer on application shutdown.

    Call this during application shutdown or register with atexit.
    """
    global _checkpointer, _checkpointer_ctx
    if _checkpointer is not None and _checkpointer_ctx is not None:
        try:
            _checkpointer_ctx.__exit__(None, None, None)
        except Exception:
            # Log but don't fail on cleanup errors
            import logging

            logging.getLogger(__name__).debug("Error during checkpointer cleanup", exc_info=True)
        finally:
            _checkpointer = None
            _checkpointer_ctx = None


def get_checkpointer() -> PostgresSaver:
    """
    Get or create the Postgres checkpointer.
    Calls setup() on first use to create tables.

    Note: The checkpointer stays alive for the application lifetime.
    Use cleanup_checkpointer() on application shutdown to properly release resources.
    """
    global _checkpointer, _checkpointer_ctx
    if _checkpointer is None:
        postgres_url = os.environ.get("DATABASE_URL")
        if not postgres_url:
            raise ValueError(
                "DATABASE_URL environment variable required for persistence. "
                "Use create_graph_in_memory() for testing without a database."
            )
        # Enter context manager and store reference for cleanup on shutdown
        _checkpointer_ctx = PostgresSaver.from_conn_string(postgres_url)
        _checkpointer = _checkpointer_ctx.__enter__()
        _checkpointer.setup()

        # Register cleanup on application exit
        import atexit

        atexit.register(cleanup_checkpointer)
    return _checkpointer


def create_graph_with_postgres(
    postgres_url: Optional[str] = None,
) -> CompiledStateGraph[BabyMARSState]:
    """
    Create graph with Postgres persistence.

    Args:
        postgres_url: Optional override. If provided, permanently sets DATABASE_URL
                      and resets the singleton. If not provided, uses existing DATABASE_URL.

    Returns:
        Compiled graph with Postgres checkpointer.

    Note:
        The checkpointer is a singleton. If you need multiple connections to different
        databases, manage PostgresSaver instances directly.
    """
    if postgres_url:
        # Permanently update DATABASE_URL and reset singleton
        os.environ["DATABASE_URL"] = postgres_url
        global _checkpointer, _checkpointer_ctx
        if _checkpointer is not None:
            cleanup_checkpointer()

    return create_cognitive_loop_graph(get_checkpointer())


def create_graph_in_memory() -> CompiledStateGraph[BabyMARSState]:
    """Create graph with in-memory persistence (for testing)"""
    return create_cognitive_loop_graph(MemorySaver())


# ============================================================
# MAIN ENTRY POINT
# ============================================================


async def invoke_cognitive_loop(
    state: BabyMARSState,
    graph: Optional[CompiledStateGraph[BabyMARSState]] = None,
    config: Optional[RunnableConfig] = None,
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

    thread_id = config.get("configurable", {}).get("thread_id", "default")
    org_id = state.get("org_id", "unknown")

    inst = get_instrumentation()
    inst.on_loop_start(thread_id, org_id)
    start_time = time.time()

    try:
        result: BabyMARSState = await graph.ainvoke(state, config)  # type: ignore[assignment]
        duration_ms = (time.time() - start_time) * 1000
        inst.on_loop_end("success", duration_ms)
        return result
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        inst.on_error(e, "graph")
        inst.on_loop_end("error", duration_ms)
        raise


async def stream_cognitive_loop(
    state: BabyMARSState,
    graph: Optional[CompiledStateGraph[BabyMARSState]] = None,
    config: Optional[RunnableConfig] = None,
) -> AsyncIterator[Any]:
    """
    Stream events from the cognitive loop.

    Yields events as they occur for real-time UI updates.
    """
    if graph is None:
        graph = create_graph_in_memory()

    if config is None:
        config = {"configurable": {"thread_id": state.get("thread_id", "default")}}

    thread_id = config.get("configurable", {}).get("thread_id", "default")
    org_id = state.get("org_id", "unknown")

    inst = get_instrumentation()
    inst.on_loop_start(thread_id, org_id)
    start_time = time.time()

    try:
        async for event in graph.astream_events(state, config, version="v2"):
            yield event
        duration_ms = (time.time() - start_time) * 1000
        inst.on_loop_end("success", duration_ms)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        inst.on_error(e, "graph")
        inst.on_loop_end("error", duration_ms)
        raise
