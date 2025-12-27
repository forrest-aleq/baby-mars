"""
Baby MARS Authentication
=========================

Simple API key authentication for production use.
Can be extended to support OAuth, JWT, etc.
"""

import hashlib
import os
import secrets
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ============================================================
# API KEY AUTH
# ============================================================

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)


def get_api_keys() -> set[str]:
    """
    Get valid API keys from environment.

    Set BABY_MARS_API_KEYS as comma-separated list:
    BABY_MARS_API_KEYS=key1,key2,key3
    """
    keys_str = os.environ.get("BABY_MARS_API_KEYS", "")
    if not keys_str:
        return set()

    return {k.strip() for k in keys_str.split(",") if k.strip()}


def hash_key(key: str) -> str:
    """Hash an API key for comparison."""
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(
    header_key: Optional[str] = Security(API_KEY_HEADER),
    query_key: Optional[str] = Security(API_KEY_QUERY),
) -> str:
    """
    Verify API key from header or query parameter.

    Returns the verified key, raises HTTPException if invalid.
    """
    valid_keys = get_api_keys()

    # If no keys configured, allow all (dev mode)
    if not valid_keys:
        return "dev-mode"

    # Check header first, then query
    provided_key = header_key or query_key

    if not provided_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header or api_key query parameter.",
        )

    if provided_key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return provided_key


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"bmars_{secrets.token_urlsafe(32)}"


# ============================================================
# ORG-SCOPED AUTH
# ============================================================


class OrgAuth:
    """
    Organization-scoped authentication.

    Maps API keys to organizations for multi-tenant deployments.
    """

    def __init__(self) -> None:
        self._key_to_org: dict[str, str] = {}
        self._org_permissions: dict[str, set[str]] = {}

    def register_key(
        self, api_key: str, org_id: str, permissions: Optional[list[str]] = None
    ) -> None:
        """Register an API key for an organization."""
        self._key_to_org[api_key] = org_id
        self._org_permissions[org_id] = set(permissions or ["read", "write"])

    def get_org_id(self, api_key: str) -> Optional[str]:
        """Get organization ID for an API key."""
        return self._key_to_org.get(api_key)

    def has_permission(self, org_id: str, permission: str) -> bool:
        """Check if organization has a permission."""
        perms = self._org_permissions.get(org_id, set())
        return permission in perms or "admin" in perms


# Singleton org auth
_org_auth = OrgAuth()


def get_org_auth() -> OrgAuth:
    """Get the organization auth manager."""
    return _org_auth


# ============================================================
# RATE LIMITING
# ============================================================


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, use Redis-based rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.rpm = requests_per_minute
        self._requests: dict[str, list[datetime]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Get requests in the last minute
        if key not in self._requests:
            self._requests[key] = []

        # Filter old requests
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        # Check limit
        if len(self._requests[key]) >= self.rpm:
            return False

        # Record this request
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        if key not in self._requests:
            return self.rpm

        current = len([t for t in self._requests[key] if t > cutoff])
        return max(0, self.rpm - current)


# Singleton rate limiter
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the rate limiter."""
    return _rate_limiter


async def check_rate_limit(
    request: Request,
    api_key: str = Depends(verify_api_key),
) -> str:
    """
    Dependency to check rate limits.

    Use as a dependency on routes that need rate limiting.
    """
    limiter = get_rate_limiter()

    # Use API key or IP for rate limiting
    key = (
        api_key if api_key != "dev-mode" else (request.client.host if request.client else "unknown")
    )

    if not limiter.is_allowed(key):
        remaining = limiter.get_remaining(key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in 60 seconds.",
            headers={"X-RateLimit-Remaining": str(remaining)},
        )

    return api_key


# ============================================================
# MIDDLEWARE
# ============================================================


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for all routes.

    Skips auth for health checks and docs.
    """

    SKIP_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip auth for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

        valid_keys = get_api_keys()

        # If keys are configured, require auth
        if valid_keys and api_key not in valid_keys:
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

        # Store key in request state for later use
        request.state.api_key = api_key or "dev-mode"

        return await call_next(request)


def add_auth_middleware(app: FastAPI) -> None:
    """Add authentication middleware to an app."""
    app.add_middleware(AuthMiddleware)


# ============================================================
# COMMON DEPENDENCIES
# ============================================================


async def get_current_org(
    request: Request,
    api_key: str = Depends(verify_api_key),
) -> str:
    """
    Get the current organization ID from the request.

    Extracts org_id from:
    1. X-Org-ID header
    2. Query parameter org_id
    3. API key to org mapping

    For development, defaults to "dev_org" if no org is specified.
    """
    # Check header
    org_id = request.headers.get("X-Org-ID")
    if org_id:
        return org_id

    # Check query parameter
    org_id = request.query_params.get("org_id")
    if org_id:
        return org_id

    # Check API key mapping
    org_auth = get_org_auth()
    mapped_org = org_auth.get_org_id(api_key)
    if mapped_org:
        return mapped_org

    # Default for development
    if api_key == "dev-mode":
        return "dev_org"

    raise HTTPException(
        status_code=400,
        detail="Organization ID required. Provide X-Org-ID header or org_id query parameter.",
    )
