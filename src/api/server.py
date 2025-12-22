"""
Baby MARS API Server
=====================

Production FastAPI server for Baby MARS cognitive architecture.
Restructured into modular routes per API_CONTRACT_V0.md.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import register_routes
from .schemas.common import APIError, ErrorResponse
from .auth import add_auth_middleware
from ..persistence.database import init_database, close_pool
from ..cognitive_loop.graph import create_graph_with_postgres, create_graph_in_memory
from ..graphs.belief_graph_manager import reset_belief_graph_manager

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

    # Initialize session store
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
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# MIDDLEWARE
# ============================================================

# CORS for frontend
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

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
async def api_error_handler(request: Request, exc: APIError):
    """Handle structured API errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
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
                "retry": {
                    "after_seconds": 5,
                    "max_attempts": 3,
                    "strategy": "exponential"
                },
                "actions": [
                    {"label": "Try again", "action": "retry"},
                    {"label": "Report issue", "href": "https://github.com/anthropics/claude-code/issues"},
                ]
            }
        }
    )


# ============================================================
# REGISTER ROUTES
# ============================================================

register_routes(app)


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
