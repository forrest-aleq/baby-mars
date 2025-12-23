"""
Redis-based Rate Limiter
=========================

Production rate limiter using Redis for distributed deployments.
Falls back to in-memory limiting if Redis is unavailable.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, Request

# ============================================================
# REDIS RATE LIMITER
# ============================================================


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis.

    Uses sliding window with Redis INCR and EXPIRE for atomic counting.
    """

    def __init__(self, redis_url: Optional[str] = None, requests_per_minute: int = 60):
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self.rpm = requests_per_minute
        self._redis = None
        self._fallback = InMemoryRateLimiter(requests_per_minute)

    async def _get_redis(self) -> Any:
        """Lazy connect to Redis."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
                # Test connection
                if self._redis is not None:
                    await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (usually API key or IP)

        Returns:
            True if allowed, False if rate limited
        """
        redis_client = await self._get_redis()

        if redis_client is None:
            # Fallback to in-memory
            return self._fallback.is_allowed(key)

        try:
            rate_key = f"ratelimit:{key}"
            count = await redis_client.incr(rate_key)

            if count == 1:
                # First request in window, set expiry
                await redis_client.expire(rate_key, 60)

            return bool(count <= self.rpm)
        except Exception:
            # On Redis error, fall back to in-memory
            return self._fallback.is_allowed(key)

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        redis_client = await self._get_redis()

        if redis_client is None:
            return self._fallback.get_remaining(key)

        try:
            rate_key = f"ratelimit:{key}"
            count = await redis_client.get(rate_key)
            current = int(count) if count else 0
            return max(0, self.rpm - current)
        except Exception:
            return self._fallback.get_remaining(key)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# ============================================================
# IN-MEMORY FALLBACK
# ============================================================


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter.

    Used as fallback when Redis is unavailable.
    NOT suitable for multi-instance deployments.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._requests: dict[str, list[datetime]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        if key not in self._requests:
            self._requests[key] = []

        # Filter old requests
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= self.rpm:
            return False

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


# ============================================================
# SINGLETON
# ============================================================

_rate_limiter: Optional[RedisRateLimiter] = None


def get_rate_limiter() -> RedisRateLimiter:
    """Get the rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
    return _rate_limiter


async def check_rate_limit(request: Request, api_key: str = "anonymous") -> bool:
    """
    FastAPI dependency to check rate limits.

    Usage:
        @app.get("/endpoint")
        async def endpoint(allowed: bool = Depends(check_rate_limit)):
            ...
    """
    limiter = get_rate_limiter()

    # Use API key or client IP
    key = (
        api_key if api_key != "dev-mode" else (request.client.host if request.client else "unknown")
    )

    if not await limiter.is_allowed(key):
        remaining = await limiter.get_remaining(key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in 60 seconds.",
            headers={"X-RateLimit-Remaining": str(remaining)},
        )

    return True
