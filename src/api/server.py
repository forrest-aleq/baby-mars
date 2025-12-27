"""
Baby MARS API Server
=====================

Production FastAPI server for Baby MARS cognitive architecture.
Restructured into modular routes per API_CONTRACT_V0.md.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..cognitive_loop.checkpointer import cleanup_async_checkpointer
from ..cognitive_loop.graph import (
    create_graph_in_memory,
    create_graph_with_async_postgres,
)
from ..graphs.belief_graph_manager import reset_belief_graph_manager
from ..observability import get_logger, setup_logging
from ..persistence.database import close_pool, init_database
from ..scheduler import get_pulse_scheduler
from .auth import add_auth_middleware
from .routes import register_routes
from .schemas.common import APIError

# Configure structured logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_JSON", "false").lower() == "true",
)
logger = get_logger("baby_mars")


# ============================================================
# LIFESPAN - Startup/Shutdown
# ============================================================


def _init_langsmith() -> None:
    """Initialize LangSmith tracing if configured."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        logger.debug("LangSmith not configured - set LANGSMITH_API_KEY to enable tracing")
        return

    project = os.getenv("LANGSMITH_PROJECT", "baby-mars")
    # LangSmith auto-detects env vars, but we log for visibility
    logger.info("LangSmith tracing enabled", project=project)


async def _startup(app: FastAPI) -> None:
    """Initialize all application resources on startup."""
    _init_langsmith()
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped (will use in-memory): {e}")

    try:
        if os.environ.get("DATABASE_URL"):
            app.state.graph = await create_graph_with_async_postgres()
            logger.info("Using async Postgres checkpointer")
        else:
            app.state.graph = create_graph_in_memory()
            logger.info("Using in-memory checkpointer")
    except Exception as e:
        logger.warning(f"Postgres graph failed, using in-memory: {e}")
        app.state.graph = create_graph_in_memory()

    app.state.sessions = {}

    if os.getenv("PULSE_SCHEDULER_ENABLED", "true").lower() == "true":
        try:
            scheduler = get_pulse_scheduler()
            await scheduler.start()
            app.state.scheduler = scheduler
            logger.info("SYSTEM_PULSE scheduler started")
        except Exception as e:
            logger.warning(f"Scheduler failed to start: {e}")


async def _shutdown(app: FastAPI) -> None:
    """Cleanup all application resources on shutdown."""
    if hasattr(app.state, "scheduler"):
        try:
            await app.state.scheduler.stop()
        except Exception:
            pass
    try:
        await cleanup_async_checkpointer()
    except Exception:
        pass
    try:
        await close_pool()
    except Exception:
        pass
    reset_belief_graph_manager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan - initialize and cleanup resources."""
    logger.info("Starting Baby MARS API...")
    await _startup(app)
    logger.info("Baby MARS API ready")
    yield
    logger.info("Shutting down Baby MARS API...")
    await _shutdown(app)
    logger.info("Shutdown complete")


# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(
    title="Baby MARS API",
    description="Production cognitive architecture implementing Aleq's research papers",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# MIDDLEWARE
# ============================================================

# CORS for frontend (strip whitespace from origins)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Auth middleware (skips /health, /docs, /)
add_auth_middleware(app)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle structured API errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with structured format"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "severity": "error",
                "recoverable": True,
                "retryable": True,
                "retry": {"after_seconds": 5, "max_attempts": 3, "strategy": "exponential"},
                "actions": [
                    {"label": "Try again", "action": "retry"},
                ],
            }
        },
    )


# ============================================================
# REGISTER ROUTES
# ============================================================

register_routes(app)


# ============================================================
# RUN SERVER
# ============================================================


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
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
