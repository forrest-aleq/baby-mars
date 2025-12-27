"""
Webhook Schemas
===============

Request/response models for email and Slack webhook endpoints.
Per planning.md Baby Mars capability: Webhook Triggers (Email/event → Task creation)
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ============================================================
# EMAIL WEBHOOK (Lockbox notifications)
# ============================================================


class EmailAttachment(BaseModel):
    """Email attachment metadata."""

    filename: str
    content_type: str
    size_bytes: int
    content_id: Optional[str] = None
    # Base64 content provided separately for large files
    content_base64: Optional[str] = None


class EmailWebhookPayload(BaseModel):
    """
    Incoming email webhook payload.

    Supports common email webhook providers (SendGrid, Mailgun, etc.)
    """

    # Core fields
    from_address: str = Field(..., alias="from")
    to_address: str = Field(..., alias="to")
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None

    # Metadata
    message_id: str
    timestamp: datetime
    headers: dict[str, str] = Field(default_factory=dict)

    # Attachments (for lockbox PDFs)
    attachments: list[EmailAttachment] = Field(default_factory=list)

    # Provider-specific
    provider: Optional[str] = None
    raw_payload: Optional[dict[str, Any]] = None

    class Config:
        populate_by_name = True


class EmailWebhookResponse(BaseModel):
    """Response after processing email webhook."""

    accepted: bool
    task_id: Optional[str] = None
    message: str
    attachment_count: int = 0
    pdf_count: int = 0


# ============================================================
# SLACK WEBHOOK
# ============================================================


class SlackUser(BaseModel):
    """Slack user info from webhook."""

    id: str
    username: Optional[str] = None
    name: Optional[str] = None


class SlackChannel(BaseModel):
    """Slack channel info from webhook."""

    id: str
    name: Optional[str] = None


class SlackWebhookPayload(BaseModel):
    """
    Incoming Slack webhook payload.

    Supports both slash commands and event subscriptions (mentions).
    """

    # Event type
    type: Literal["slash_command", "app_mention", "message", "url_verification"]

    # For url_verification challenge
    challenge: Optional[str] = None

    # Slash command fields
    command: Optional[str] = None
    text: Optional[str] = None
    response_url: Optional[str] = None
    trigger_id: Optional[str] = None

    # Event subscription fields (app_mention, message)
    event: Optional[dict[str, Any]] = None

    # Common fields
    user: Optional[SlackUser] = None
    channel: Optional[SlackChannel] = None
    team_id: Optional[str] = None
    timestamp: Optional[str] = None

    # Verification
    token: Optional[str] = None


class SlackWebhookResponse(BaseModel):
    """Response for Slack webhook."""

    # For url_verification
    challenge: Optional[str] = None

    # For commands/mentions
    response_type: Optional[Literal["in_channel", "ephemeral"]] = None
    text: Optional[str] = None
    blocks: Optional[list[dict[str, Any]]] = None

    # Internal tracking
    task_id: Optional[str] = None


# ============================================================
# GENERIC WEBHOOK
# ============================================================


class GenericWebhookPayload(BaseModel):
    """
    Generic webhook for custom integrations.

    Allows any JSON payload with required org_id and event_type.
    """

    org_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    idempotency_key: Optional[str] = None


class GenericWebhookResponse(BaseModel):
    """Response for generic webhook."""

    accepted: bool
    task_id: Optional[str] = None
    message: str
