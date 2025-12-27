"""
Webhook Routes
==============

Email and Slack webhook endpoints for task creation.
Per planning.md Baby Mars: Webhook Triggers (Email/event → Task creation)
"""

from typing import Any

from fastapi import APIRouter, Header, Request

from ...observability import get_logger
from ..schemas.webhooks import (
    EmailWebhookPayload,
    EmailWebhookResponse,
    GenericWebhookPayload,
    GenericWebhookResponse,
    SlackWebhookPayload,
    SlackWebhookResponse,
)
from .events import publish_task_created
from .tasks import create_task

logger = get_logger("baby_mars.api.webhooks")

router = APIRouter()


# ============================================================
# EMAIL WEBHOOK
# ============================================================


def _count_pdf_attachments(payload: EmailWebhookPayload) -> int:
    """Count PDF attachments in email."""
    return sum(
        1
        for att in payload.attachments
        if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf")
    )


def _extract_org_id_from_email(to_address: str) -> str:
    """Extract org_id from email address (e.g., lockbox+org123@aleq.ai)."""
    local_part = to_address.split("@")[0]
    if "+" in local_part:
        return local_part.split("+")[1]
    return "default"


def _build_task_summary(payload: EmailWebhookPayload, pdf_count: int) -> str:
    """Build task summary from email payload."""
    if pdf_count > 0:
        return f"Process {pdf_count} lockbox PDF(s) from {payload.from_address}"
    return f"Review email from {payload.from_address}: {payload.subject[:50]}"


@router.post("/email", response_model=EmailWebhookResponse)
async def email_webhook(
    payload: EmailWebhookPayload,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
) -> EmailWebhookResponse:
    """
    Receive email webhook for lockbox processing.

    Creates a task for each email with PDF attachments.
    PDFs are queued for OCR extraction.
    """
    logger.info(f"Email webhook received: {payload.subject} from {payload.from_address}")

    # TODO: Verify webhook signature based on provider

    pdf_count = _count_pdf_attachments(payload)
    org_id = _extract_org_id_from_email(payload.to_address)

    if pdf_count == 0:
        # No PDFs - might be a general inquiry
        return EmailWebhookResponse(
            accepted=True,
            message="Email received but no PDFs to process",
            attachment_count=len(payload.attachments),
            pdf_count=0,
        )

    # Create lockbox processing task
    summary = _build_task_summary(payload, pdf_count)
    task_id = create_task(
        task_type="lockbox_processing",
        summary=summary,
        source="email_webhook",
        priority=0.7,
        difficulty=2,
        description=f"Subject: {payload.subject}\nFrom: {payload.from_address}",
    )

    # Publish event for real-time UI update
    await publish_task_created(org_id, task_id, "lockbox_processing", summary)

    logger.info(f"Created lockbox task {task_id} for {pdf_count} PDFs")

    return EmailWebhookResponse(
        accepted=True,
        task_id=task_id,
        message=f"Created task to process {pdf_count} lockbox PDF(s)",
        attachment_count=len(payload.attachments),
        pdf_count=pdf_count,
    )


# ============================================================
# SLACK WEBHOOK
# ============================================================


def _handle_url_verification(payload: SlackWebhookPayload) -> SlackWebhookResponse:
    """Handle Slack URL verification challenge."""
    return SlackWebhookResponse(challenge=payload.challenge)


def _extract_slack_text(payload: SlackWebhookPayload) -> str:
    """Extract text content from Slack payload."""
    if payload.text:
        return payload.text
    if payload.event and "text" in payload.event:
        return str(payload.event["text"])
    return ""


def _build_slack_task_summary(payload: SlackWebhookPayload, text: str) -> str:
    """Build task summary from Slack payload."""
    prefix = payload.command or "@aleq"
    truncated = text[:50] + "..." if len(text) > 50 else text
    return f"Slack request: {prefix} {truncated}"


async def _process_slack_command(payload: SlackWebhookPayload) -> SlackWebhookResponse:
    """Process Slack slash command or mention."""
    text = _extract_slack_text(payload)
    summary = _build_slack_task_summary(payload, text)
    org_id = payload.team_id or "default"

    task_id = create_task(
        task_type="slack_request",
        summary=summary,
        source="slack_webhook",
        priority=0.6,
        difficulty=2,
    )

    await publish_task_created(org_id, task_id, "slack_request", summary)

    logger.info(f"Created Slack task {task_id}")

    return SlackWebhookResponse(
        response_type="ephemeral",
        text=f"Got it! I'm working on that. (Task: {task_id})",
        task_id=task_id,
    )


@router.post("/slack", response_model=SlackWebhookResponse)
async def slack_webhook(
    payload: SlackWebhookPayload,
    x_slack_signature: str | None = Header(None, alias="X-Slack-Signature"),
    x_slack_request_timestamp: str | None = Header(None, alias="X-Slack-Request-Timestamp"),
) -> SlackWebhookResponse:
    """
    Receive Slack webhook for commands and mentions.

    Supports:
    - URL verification (initial setup)
    - Slash commands (/aleq)
    - App mentions (@Aleq)
    """
    logger.info(f"Slack webhook received: type={payload.type}")

    # TODO: Verify Slack signature using signing secret

    # Handle URL verification challenge
    if payload.type == "url_verification":
        return _handle_url_verification(payload)

    # Process command or mention
    return await _process_slack_command(payload)


# ============================================================
# GENERIC WEBHOOK
# ============================================================


def _build_generic_task_summary(payload: GenericWebhookPayload) -> str:
    """Build task summary from generic payload."""
    return f"Process {payload.event_type} from {payload.source or 'webhook'}"


@router.post("/generic", response_model=GenericWebhookResponse)
async def generic_webhook(
    payload: GenericWebhookPayload,
    request: Request,
) -> GenericWebhookResponse:
    """
    Generic webhook for custom integrations.

    Accepts any JSON payload with org_id and event_type.
    Creates appropriate task based on event_type.
    """
    logger.info(f"Generic webhook: {payload.event_type} for org {payload.org_id}")

    # Map event types to task types
    task_type_map: dict[str, str] = {
        "invoice_received": "invoice_processing",
        "payment_received": "payment_posting",
        "document_uploaded": "document_processing",
        "approval_needed": "approval_request",
    }

    task_type = task_type_map.get(payload.event_type, "generic_task")
    summary = _build_generic_task_summary(payload)

    task_id = create_task(
        task_type=task_type,
        summary=summary,
        source=payload.source or "generic_webhook",
        priority=0.5,
        difficulty=2,
    )

    await publish_task_created(payload.org_id, task_id, task_type, summary)

    return GenericWebhookResponse(
        accepted=True,
        task_id=task_id,
        message=f"Created {task_type} task",
    )


# ============================================================
# WEBHOOK HEALTH CHECK
# ============================================================


@router.get("/health")
async def webhook_health() -> dict[str, Any]:
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "endpoints": ["email", "slack", "generic"],
    }
