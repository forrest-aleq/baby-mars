"""
Common Schemas
==============

Shared models for errors, pagination, and base types.
Per API_CONTRACT_V0.md section 8.1
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


class ErrorAction(BaseModel):
    """An action the user can take to recover from an error"""
    label: str = Field(..., description="Button/link text")
    action: Optional[str] = Field(None, description="Frontend action identifier")
    href: Optional[str] = Field(None, description="Link URL if navigating")


class RetryConfig(BaseModel):
    """Retry configuration for retryable errors"""
    after_seconds: int = Field(..., description="Wait this long before retrying")
    max_attempts: int = Field(3, description="Maximum retry attempts")
    strategy: Literal["fixed", "exponential"] = Field("exponential")


class ErrorDetail(BaseModel):
    """
    Structured error response per API contract.

    Every error should be actionable - tell users what to do next.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")
    details: Optional[dict[str, Any]] = Field(None, description="Additional context")
    severity: Literal["info", "warning", "error", "critical"] = Field("error")
    recoverable: bool = Field(True, description="Can user retry/continue?")
    retryable: bool = Field(False, description="Should client auto-retry?")
    retry: Optional[RetryConfig] = Field(None, description="Retry config if retryable")
    actions: list[ErrorAction] = Field(default_factory=list, description="Recovery options")


class ErrorResponse(BaseModel):
    """Wrapper for error responses"""
    error: ErrorDetail


class PaginatedResponse(BaseModel):
    """Base for paginated list responses"""
    total: int = Field(..., description="Total count of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(0, description="Current offset")
    has_more: bool = Field(..., description="More items available")


class HealthService(BaseModel):
    """Individual service health status"""
    status: Literal["healthy", "degraded", "unavailable"]
    latency_ms: Optional[int] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """
    Health check response with capability matrix.
    Per API_CONTRACT_V0.md section 8.3
    """
    status: Literal["healthy", "degraded", "unavailable"]
    version: str
    timestamp: str
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Status of each dependency"
    )
    capabilities: dict[str, str] = Field(
        default_factory=dict,
        description="What's currently available"
    )


# Custom exception for API errors
class APIError(Exception):
    """
    Raise this to return a structured error response.

    Usage:
        raise APIError(
            code="INVOICE_ALREADY_PAID",
            message="This invoice was paid on Oct 1",
            details={"invoice_id": "...", "paid_date": "..."},
            severity="warning",
            actions=[{"label": "View payment", "href": "/payments/..."}]
        )
    """
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict] = None,
        severity: Literal["info", "warning", "error", "critical"] = "error",
        recoverable: bool = True,
        retryable: bool = False,
        retry: Optional[dict] = None,
        actions: Optional[list[dict]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.severity = severity
        self.recoverable = recoverable
        self.retryable = retryable
        self.retry = retry
        self.actions = actions or []
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert to ErrorResponse"""
        return ErrorResponse(
            error=ErrorDetail(
                code=self.code,
                message=self.message,
                details=self.details,
                severity=self.severity,
                recoverable=self.recoverable,
                retryable=self.retryable,
                retry=RetryConfig(**self.retry) if self.retry else None,
                actions=[ErrorAction(**a) for a in self.actions],
            )
        )
