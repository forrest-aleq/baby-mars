"""
Health Routes
=============

Health check and system info endpoints.
"""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter

from ...observability import get_logger
from ...persistence.database import get_pool
from ..schemas.common import HealthResponse

logger = get_logger("baby_mars.api.health")

router = APIRouter()


async def _check_database() -> str:
    """Check database connectivity."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return "unavailable"


def _check_claude() -> str:
    """Check Claude client availability."""
    try:
        from ...claude_singleton import get_claude_client

        client = get_claude_client()
        return "healthy" if client else "unavailable"
    except Exception:
        return "unavailable"


def _determine_capabilities(services: dict[str, str]) -> dict[str, str]:
    """Determine capabilities based on service status."""
    capabilities: dict[str, str] = {}

    if services["database"] == "healthy":
        capabilities["view_tasks"] = "full"
        capabilities["view_beliefs"] = "full"
    else:
        capabilities["view_tasks"] = "cached"
        capabilities["view_beliefs"] = "cached"

    if services["claude"] == "healthy":
        capabilities["chat"] = "full"
    else:
        capabilities["chat"] = "unavailable"

    if services["erpnext"] == "healthy":
        capabilities["execute_decisions"] = "full"
        capabilities["view_widgets"] = "full"
        capabilities["drill_down"] = "full"
    else:
        capabilities["execute_decisions"] = "queued"
        capabilities["view_widgets"] = "cached"
        capabilities["drill_down"] = "unavailable"

    return capabilities


def _determine_status(services: dict[str, str]) -> Literal["healthy", "degraded", "unavailable"]:
    """Determine overall health status from services."""
    if all(s == "healthy" for s in services.values()):
        return "healthy"
    elif services["baby_mars"] == "healthy" and services["claude"] == "healthy":
        return "degraded"
    else:
        return "unavailable"


@router.get("/", response_model=dict)
async def root() -> dict[str, str]:
    """Root endpoint - API info"""
    return {
        "name": "Baby MARS",
        "version": "0.1.0",
        "description": "Cognitive architecture with a rented brain",
        "docs": "/docs",
    }


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check with capability matrix. Per API_CONTRACT_V0.md section 8.3"""
    services = {
        "database": await _check_database(),
        "baby_mars": "healthy",  # Always healthy if we're responding
        "claude": _check_claude(),
        "erpnext": "unavailable",  # Stubbed for now
    }

    return HealthResponse(
        status=_determine_status(services),
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
        capabilities=_determine_capabilities(services),
    )
