"""
API Schemas
===========

Pydantic models for request/response validation.
"""

from .beliefs import (
    BeliefChallengeRequest,
    BeliefChallengeResponse,
    BeliefDetailResponse,
    BeliefResponse,
)
from .birth import (
    BirthRequest,
    BirthResponse,
)
from .chat import (
    ChatInterruptRequest,
    ChatInterruptResponse,
    ContextPill,
    MessageRequest,
    MessageResponse,
    Reference,
)
from .common import (
    APIError,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
)
from .decisions import (
    DecisionDetail,
    DecisionExecuteRequest,
    DecisionExecuteResponse,
    DecisionUndoResponse,
)
from .tasks import (
    TaskDetail,
    TaskListResponse,
    TaskSummary,
    TaskTimeline,
)

__all__ = [
    # Common
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "APIError",
    # Chat
    "MessageRequest",
    "MessageResponse",
    "ChatInterruptRequest",
    "ChatInterruptResponse",
    "ContextPill",
    "Reference",
    # Birth
    "BirthRequest",
    "BirthResponse",
    # Tasks
    "TaskSummary",
    "TaskDetail",
    "TaskTimeline",
    "TaskListResponse",
    # Decisions
    "DecisionDetail",
    "DecisionExecuteRequest",
    "DecisionExecuteResponse",
    "DecisionUndoResponse",
    # Beliefs
    "BeliefResponse",
    "BeliefDetailResponse",
    "BeliefChallengeRequest",
    "BeliefChallengeResponse",
]
