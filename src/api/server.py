"""
Baby MARS API Server
=====================

Production FastAPI server for Baby MARS cognitive architecture.
This is the real deal - proper streaming, proper error handling, proper everything.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import uuid
import json

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..birth.birth_system import birth_person, create_initial_state, quick_birth
from ..cognitive_loop.graph import (
    create_graph_with_postgres,
    create_graph_in_memory,
    invoke_cognitive_loop,
    stream_cognitive_loop,
)
from ..graphs.belief_graph_manager import (
    get_belief_graph_manager,
    get_org_belief_graph,
    reset_belief_graph_manager,
)
from ..persistence.database import init_database, close_pool, get_pool
from .auth import add_auth_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("baby_mars")


# ============================================================
# LIFESPAN - Startup/Shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize and cleanup resources"""
    logger.info("Starting Baby MARS API...")

    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped (will use in-memory): {e}")

    # Create graph (Postgres if available, else in-memory)
    try:
        if os.environ.get("DATABASE_URL"):
            app.state.graph = create_graph_with_postgres()
            logger.info("Using Postgres checkpointer")
        else:
            app.state.graph = create_graph_in_memory()
            logger.info("Using in-memory checkpointer")
    except Exception as e:
        logger.warning(f"Postgres graph failed, using in-memory: {e}")
        app.state.graph = create_graph_in_memory()

    # Store active sessions
    app.state.sessions = {}

    logger.info("Baby MARS API ready")

    yield

    # Cleanup
    logger.info("Shutting down Baby MARS API...")
    try:
        await close_pool()
    except Exception:
        pass
    reset_belief_graph_manager()
    logger.info("Shutdown complete")


# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(
    title="Baby MARS API",
    description="Production cognitive architecture implementing Aleq's research papers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (skips /health, /docs, /)
add_auth_middleware(app)


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class BirthRequest(BaseModel):
    """Request to birth a new person into the system"""
    person_id: Optional[str] = None
    name: str
    email: str
    role: str = "Controller"
    org_id: Optional[str] = None
    org_name: str = "Default Organization"
    industry: str = "general"
    org_size: str = "mid_market"
    capabilities_override: Optional[dict] = None


class BirthResponse(BaseModel):
    """Response from birth"""
    person_id: str
    org_id: str
    birth_mode: str
    salience: float
    belief_count: int
    session_id: str


class MessageRequest(BaseModel):
    """Request to send a message"""
    session_id: str
    message: str
    stream: bool = False


class MessageResponse(BaseModel):
    """Response from message"""
    session_id: str
    response: str
    supervision_mode: str
    belief_strength: float
    approval_needed: bool
    approval_summary: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request to approve/reject an action"""
    session_id: str
    approved: bool
    feedback: Optional[str] = None


class BeliefResponse(BaseModel):
    """Belief information"""
    belief_id: str
    statement: str
    category: str
    strength: float
    context_key: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    database: str
    belief_cache_size: int


# ============================================================
# HEALTH & INFO
# ============================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "name": "Baby MARS",
        "version": "0.1.0",
        "description": "Cognitive architecture with a rented brain",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check"""
    manager = get_belief_graph_manager()

    # Check database
    db_status = "disconnected"
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now().isoformat(),
        database=db_status,
        belief_cache_size=manager.cache_size,
    )


# ============================================================
# BIRTH
# ============================================================

@app.post("/birth", response_model=BirthResponse)
async def birth(request: BirthRequest):
    """
    Birth a new person into Baby MARS.

    Creates initial beliefs, goals, and session state.
    Returns session_id for subsequent interactions.
    """
    person_id = request.person_id or f"person_{uuid.uuid4().hex[:12]}"
    org_id = request.org_id or f"org_{uuid.uuid4().hex[:12]}"

    try:
        # Birth the person
        birth_result = birth_person(
            person_id=person_id,
            name=request.name,
            email=request.email,
            role=request.role,
            org_id=org_id,
            org_name=request.org_name,
            industry=request.industry,
            org_size=request.org_size,
            capabilities_override=request.capabilities_override,
        )

        # Create session
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        # Store birth result in session
        app.state.sessions[session_id] = {
            "birth_result": birth_result,
            "state": None,  # Will be created on first message
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
        }

        logger.info(f"Birth complete: person={person_id}, org={org_id}, session={session_id}")

        return BirthResponse(
            person_id=person_id,
            org_id=org_id,
            birth_mode=birth_result["birth_mode"],
            salience=birth_result["salience"],
            belief_count=birth_result["belief_count"],
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Birth failed: {e}")
        raise HTTPException(status_code=500, detail=f"Birth failed: {str(e)}")


# ============================================================
# MESSAGES
# ============================================================

@app.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """
    Send a message and get a response.

    This runs the full cognitive loop:
    1. Cognitive Activation
    2. Appraisal
    3. Action Selection
    4. Execution (if autonomous)
    5. Verification
    6. Feedback
    7. Response Generation
    8. Personality Gate
    """
    session = app.state.sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Create or update state
        if session["state"] is None:
            session["state"] = create_initial_state(
                session["birth_result"],
                request.message
            )
        else:
            # Add new message to existing state
            session["state"]["messages"].append({
                "role": "user",
                "content": request.message
            })
            session["state"]["current_turn"] += 1

        session["message_count"] += 1

        # Run cognitive loop
        config = {
            "configurable": {
                "thread_id": session["state"]["thread_id"]
            }
        }

        result = await invoke_cognitive_loop(
            state=session["state"],
            graph=app.state.graph,
            config=config,
        )

        # Update session state
        session["state"] = result

        # Extract response
        final_response = result.get("final_response", "")
        supervision_mode = result.get("supervision_mode", "guidance_seeking")
        belief_strength = result.get("belief_strength_for_action", 0.0)

        # Check if approval needed
        approval_needed = supervision_mode == "action_proposal"
        approval_summary = result.get("approval_summary") if approval_needed else None

        logger.info(
            f"Message processed: session={request.session_id}, "
            f"mode={supervision_mode}, strength={belief_strength:.2f}"
        )

        return MessageResponse(
            session_id=request.session_id,
            response=final_response,
            supervision_mode=supervision_mode,
            belief_strength=belief_strength,
            approval_needed=approval_needed,
            approval_summary=approval_summary,
        )

    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/message/stream")
async def send_message_stream(request: MessageRequest):
    """
    Send a message and stream the response via SSE.

    Events:
    - node_start: {node: "name"} - Node execution started
    - node_end: {node: "name", updates: {...}} - Node completed
    - token: {text: "..."} - Response token (when streaming response)
    - complete: {response: "...", mode: "..."} - Final result
    - error: {message: "..."} - Error occurred
    """
    session = app.state.sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        try:
            # Create or update state
            if session["state"] is None:
                session["state"] = create_initial_state(
                    session["birth_result"],
                    request.message
                )
            else:
                session["state"]["messages"].append({
                    "role": "user",
                    "content": request.message
                })
                session["state"]["current_turn"] += 1

            session["message_count"] += 1

            config = {
                "configurable": {
                    "thread_id": session["state"]["thread_id"]
                }
            }

            # Stream events from cognitive loop
            async for event in stream_cognitive_loop(
                state=session["state"],
                graph=app.state.graph,
                config=config,
            ):
                event_type = event.get("event", "")

                if event_type == "on_chain_start":
                    node_name = event.get("name", "unknown")
                    yield {
                        "event": "node_start",
                        "data": json.dumps({"node": node_name})
                    }

                elif event_type == "on_chain_end":
                    node_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", {})

                    # Update session state with outputs
                    if isinstance(output, dict):
                        session["state"].update(output)

                    yield {
                        "event": "node_end",
                        "data": json.dumps({
                            "node": node_name,
                            "supervision_mode": session["state"].get("supervision_mode"),
                        })
                    }

                elif event_type == "on_llm_stream":
                    # Token from Claude
                    chunk = event.get("data", {}).get("chunk", "")
                    if chunk:
                        yield {
                            "event": "token",
                            "data": json.dumps({"text": chunk})
                        }

            # Send completion event
            yield {
                "event": "complete",
                "data": json.dumps({
                    "response": session["state"].get("final_response", ""),
                    "supervision_mode": session["state"].get("supervision_mode", ""),
                    "belief_strength": session["state"].get("belief_strength_for_action", 0.0),
                    "approval_needed": session["state"].get("supervision_mode") == "action_proposal",
                })
            }

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(event_generator())


# ============================================================
# APPROVAL (HITL)
# ============================================================

@app.post("/approve", response_model=MessageResponse)
async def approve_action(request: ApprovalRequest):
    """
    Approve or reject a proposed action.

    When supervision_mode is "action_proposal", the system waits
    for explicit approval before executing.
    """
    session = app.state.sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="No active state")

    if state.get("supervision_mode") != "action_proposal":
        raise HTTPException(status_code=400, detail="No pending approval")

    try:
        # Update approval status
        state["approval_status"] = "approved" if request.approved else "rejected"

        if request.feedback:
            state["notes"].append({
                "note_id": f"approval_feedback_{uuid.uuid4().hex[:8]}",
                "content": request.feedback,
                "created_at": datetime.now().isoformat(),
                "ttl_hours": 24,
                "priority": 0.8,
                "source": "user",
                "context": {"approval": request.approved}
            })

        # Continue cognitive loop from approval
        config = {
            "configurable": {
                "thread_id": state["thread_id"]
            }
        }

        result = await invoke_cognitive_loop(
            state=state,
            graph=app.state.graph,
            config=config,
        )

        session["state"] = result

        logger.info(f"Approval processed: session={request.session_id}, approved={request.approved}")

        return MessageResponse(
            session_id=request.session_id,
            response=result.get("final_response", ""),
            supervision_mode=result.get("supervision_mode", ""),
            belief_strength=result.get("belief_strength_for_action", 0.0),
            approval_needed=False,
            approval_summary=None,
        )

    except Exception as e:
        logger.error(f"Approval processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# BELIEFS
# ============================================================

@app.get("/beliefs/{org_id}", response_model=list[BeliefResponse])
async def get_beliefs(org_id: str, category: Optional[str] = None):
    """Get beliefs for an organization"""
    try:
        graph = await get_org_belief_graph(org_id)

        beliefs = graph.get_all_beliefs()

        if category:
            beliefs = [b for b in beliefs if b.get("category") == category]

        return [
            BeliefResponse(
                belief_id=b["belief_id"],
                statement=b["statement"],
                category=b["category"],
                strength=b.get("strength", 0.5),
                context_key=b.get("context_key", "*|*|*"),
            )
            for b in beliefs
        ]

    except Exception as e:
        logger.error(f"Failed to get beliefs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beliefs/{org_id}/{belief_id}")
async def get_belief(org_id: str, belief_id: str):
    """Get a specific belief with full details"""
    try:
        graph = await get_org_belief_graph(org_id)
        belief = graph.get_belief(belief_id)

        if not belief:
            raise HTTPException(status_code=404, detail="Belief not found")

        return belief

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get belief: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SESSIONS
# ============================================================

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    session = app.state.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "message_count": session["message_count"],
        "org_id": session["birth_result"]["org"]["org_id"],
        "person_name": session["birth_result"]["person"]["name"],
        "supervision_mode": session["state"].get("supervision_mode") if session["state"] else None,
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id not in app.state.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del app.state.sessions[session_id]
    logger.info(f"Session deleted: {session_id}")

    return {"status": "deleted", "session_id": session_id}


# ============================================================
# RUN SERVER
# ============================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the server"""
    import uvicorn
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_server(reload=True)
