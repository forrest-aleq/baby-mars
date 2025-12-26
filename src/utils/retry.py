"""
Retry Utilities
================

Unified retry logic with exponential backoff, jitter, and circuit breaker.
Consolidates retry patterns from across the codebase.

Usage:
    from src.utils.retry import retry_async, RetryConfig, CircuitBreaker

    # Simple retry with defaults
    result = await retry_async(my_async_func, args=(arg1, arg2))

    # Custom config
    config = RetryConfig(max_attempts=5, base_delay=0.5, max_delay=30.0)
    result = await retry_async(my_async_func, config=config)

    # With circuit breaker
    breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)
    result = await retry_async(my_async_func, circuit_breaker=breaker)
"""

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any, Awaitable, Callable, Optional, TypeVar

from ..observability import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """Retry strategy types."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CONSTANT_DELAY = "constant_delay"
    NO_RETRY = "no_retry"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: tuple[type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)."""
        if self.strategy == RetryStrategy.NO_RETRY:
            return 0.0

        if self.strategy == RetryStrategy.CONSTANT_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * (attempt + 1)
        else:  # EXPONENTIAL_BACKOFF
            delay = self.base_delay * (self.exponential_base**attempt)

        delay = min(delay, self.max_delay)

        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.0, delay)


# Default configs for common use cases
DEFAULT_RETRY_CONFIG = RetryConfig()

CLAUDE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=(Exception,),  # Will be filtered by is_retryable
)

STARGATE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=60.0,
    jitter=True,
)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and call is rejected."""

    def __init__(self, message: str, reset_after: float):
        super().__init__(message)
        self.reset_after = reset_after


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    States:
    - CLOSED: Normal operation, failures are counted
    - OPEN: Failures exceeded threshold, calls are rejected
    - HALF_OPEN: After reset_timeout, one call is allowed to test recovery
    """

    failure_threshold: int = 5
    reset_timeout: float = 60.0
    half_open_max_calls: int = 1

    # State tracking
    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: str = field(default="closed", init=False)
    half_open_calls: int = field(default=0, init=False)

    def _check_reset(self) -> None:
        """Check if circuit should reset from open to half-open."""
        if self.state == "open":
            if time() - self.last_failure_time > self.reset_timeout:
                self.state = "half_open"
                self.half_open_calls = 0
                logger.info("Circuit breaker transitioning to half-open")

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        self._check_reset()

        if self.state == "closed":
            return True
        elif self.state == "half_open":
            return self.half_open_calls < self.half_open_max_calls
        else:  # open
            return False

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == "half_open":
            self.state = "closed"
            self.failures = 0
            logger.info("Circuit breaker closed after successful test")
        elif self.state == "closed":
            self.failures = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time()

        if self.state == "half_open":
            self.state = "open"
            logger.warning("Circuit breaker re-opened after half-open failure")
        elif self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failures} failures. "
                f"Reset after {self.reset_timeout}s."
            )

    def get_reset_time(self) -> float:
        """Get seconds until circuit might reset."""
        if self.state != "open":
            return 0.0
        elapsed = time() - self.last_failure_time
        return max(0.0, self.reset_timeout - elapsed)


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Override this or pass custom logic to retry_async for specific behavior.
    """
    error_str = str(error).lower()

    # Non-retryable patterns
    non_retryable = [
        "invalid_api_key",
        "authentication",
        "unauthorized",
        "forbidden",
        "not_found",
        "invalid_request",
        "validation",
    ]

    for pattern in non_retryable:
        if pattern in error_str:
            return False

    # Retryable patterns
    retryable = [
        "timeout",
        "connection",
        "rate_limit",
        "overloaded",
        "temporarily",
        "503",
        "502",
        "504",
        "529",
    ]

    for pattern in retryable:
        if pattern in error_str:
            return True

    # Default: retry on transient-looking errors
    return True


def _check_circuit_before_attempt(breaker: Optional[CircuitBreaker]) -> None:
    """Check circuit breaker state before attempt."""
    if breaker is None:
        return
    if not breaker.can_execute():
        reset_time = breaker.get_reset_time()
        raise CircuitOpenError(
            f"Circuit breaker is open. Retry after {reset_time:.1f}s.",
            reset_after=reset_time,
        )
    if breaker.state == "half_open":
        breaker.half_open_calls += 1


def _should_retry_error(
    error: Exception,
    attempt: int,
    config: RetryConfig,
    is_retryable: Callable[[Exception], bool],
) -> bool:
    """Determine if error should trigger a retry."""
    is_last_attempt = attempt >= config.max_attempts - 1
    return (
        not is_last_attempt
        and isinstance(error, config.retryable_exceptions)
        and is_retryable(error)
    )


async def retry_async(
    func: Callable[..., Awaitable[T]],
    args: tuple[Any, ...] = (),
    kwargs: Optional[dict[str, Any]] = None,
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    is_retryable: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> T:
    """Execute async function with retry logic."""
    if kwargs is None:
        kwargs = {}
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    if is_retryable is None:
        is_retryable = is_retryable_error

    last_error: Optional[Exception] = None

    for attempt in range(config.max_attempts):
        _check_circuit_before_attempt(circuit_breaker)

        try:
            result = await func(*args, **kwargs)
            if circuit_breaker is not None:
                circuit_breaker.record_success()
            return result

        except Exception as e:
            last_error = e
            if circuit_breaker is not None:
                circuit_breaker.record_failure()

            if not _should_retry_error(e, attempt, config, is_retryable):
                raise

            delay = config.calculate_delay(attempt)
            if on_retry:
                on_retry(attempt, e, delay)
            else:
                logger.warning(f"Retry {attempt + 1}/{config.max_attempts}: {e}")
            await asyncio.sleep(delay)

    raise RetryExhaustedError(
        f"All {config.max_attempts} retry attempts exhausted",
        last_exception=last_error,
    )


async def with_timeout(
    coro: Awaitable[T],
    timeout_seconds: float,
    timeout_message: str = "Operation timed out",
) -> T:
    """
    Execute coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout_seconds: Maximum time to wait
        timeout_message: Message for TimeoutError

    Returns:
        Result of coroutine

    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(timeout_message)
