"""
Health Routes
=============

Health check and system info endpoints.
"""

import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Request

from ...persistence.database import get_pool
from ..schemas.common import HealthResponse

logger = logging.getLogger("baby_mars.api.health")

router = APIRouter()


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
async def health(request: Request) -> HealthResponse:
    """
    Health check with capability matrix.

    Returns status of each service and what capabilities are available.
    Per API_CONTRACT_V0.md section 8.3
    """
    # Check services
    services = {}
    capabilities = {}

    # Database
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        services["database"] = "unavailable"

    # Baby MARS core (always healthy if we're responding)
    services["baby_mars"] = "healthy"

    # Claude (check if client is configured)
    try:
        from ...claude_client import get_claude_client

        client = get_claude_client()
        services["claude"] = "healthy" if client else "unavailable"
    except Exception:
        services["claude"] = "unavailable"

    # ERPNext (stubbed for now)
    services["erpnext"] = "unavailable"  # Will be implemented with data endpoints

    # Determine capabilities based on service status
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

    # Overall status
    status: Literal["healthy", "degraded", "unavailable"]
    if all(s == "healthy" for s in services.values()):
        status = "healthy"
    elif services["baby_mars"] == "healthy" and services["claude"] == "healthy":
        status = "degraded"
    else:
        status = "unavailable"

    return HealthResponse(
        status=status,
        version="0.1.0",
        timestamp=datetime.now().isoformat(),
        services=services,
        capabilities=capabilities,
    )
