"""
API Schemas
===========

Pydantic models for request/response validation.
"""

from .common import (
    ErrorResponse,
    ErrorDetail,
    PaginatedResponse,
    APIError,
)
from .chat import (
    MessageRequest,
    MessageResponse,
    ChatInterruptRequest,
    ChatInterruptResponse,
    ContextPill,
    Reference,
)
from .birth import (
    BirthRequest,
    BirthResponse,
)
from .tasks import (
    TaskSummary,
    TaskDetail,
    TaskTimeline,
    TaskListResponse,
)
from .decisions import (
    DecisionDetail,
    DecisionExecuteRequest,
    DecisionExecuteResponse,
    DecisionUndoResponse,
)
from .beliefs import (
    BeliefResponse,
    BeliefDetailResponse,
    BeliefChallengeRequest,
    BeliefChallengeResponse,
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
