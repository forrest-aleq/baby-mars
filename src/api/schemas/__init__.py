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
from .triggers import (
    CreateTriggerRequest,
    FireTriggerRequest,
    SchedulerStatusResponse,
    TriggerFireResult,
    TriggerListResponse,
    TriggerResponse,
    UpdateTriggerRequest,
)
from .webhooks import (
    EmailAttachment,
    EmailWebhookPayload,
    EmailWebhookResponse,
    GenericWebhookPayload,
    GenericWebhookResponse,
    SlackChannel,
    SlackUser,
    SlackWebhookPayload,
    SlackWebhookResponse,
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
    # Triggers
    "CreateTriggerRequest",
    "UpdateTriggerRequest",
    "FireTriggerRequest",
    "TriggerResponse",
    "TriggerListResponse",
    "TriggerFireResult",
    "SchedulerStatusResponse",
    # Webhooks
    "EmailAttachment",
    "EmailWebhookPayload",
    "EmailWebhookResponse",
    "SlackUser",
    "SlackChannel",
    "SlackWebhookPayload",
    "SlackWebhookResponse",
    "GenericWebhookPayload",
    "GenericWebhookResponse",
]
