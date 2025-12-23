"""
API Routes
==========

All route modules for Baby MARS API.
"""

from fastapi import APIRouter

from .beliefs import router as beliefs_router
from .birth import router as birth_router
from .chat import router as chat_router
from .decisions import router as decisions_router
from .events import router as events_router
from .health import router as health_router
from .sessions import router as sessions_router
from .tasks import router as tasks_router


def register_routes(app):
    """Register all route modules with the FastAPI app"""
    # Health/info at root level
    app.include_router(health_router, tags=["Health"])

    # Domain routes with prefixes
    app.include_router(birth_router, prefix="/birth", tags=["Birth"])
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
    app.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
    app.include_router(beliefs_router, prefix="/beliefs", tags=["Beliefs"])
    app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
    app.include_router(decisions_router, prefix="/decisions", tags=["Decisions"])
    app.include_router(events_router, prefix="/events", tags=["Events"])


__all__ = [
    "register_routes",
    "health_router",
    "birth_router",
    "chat_router",
    "sessions_router",
    "beliefs_router",
    "tasks_router",
    "decisions_router",
    "events_router",
]
