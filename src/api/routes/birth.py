"""
Birth Routes
============

Agent initialization endpoint.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from ...birth.birth_system import birth_person
from ...observability import get_logger
from ..schemas.birth import BirthRequest, BirthResponse

logger = get_logger("baby_mars.api.birth")

router = APIRouter()


@router.post("", response_model=BirthResponse)
async def birth(request_data: BirthRequest, request: Request) -> BirthResponse:
    """
    Birth a new agent into Baby MARS.

    Creates initial beliefs, goals, capabilities, and session state.
    Returns session_id for subsequent interactions.

    The "birth" process makes Aleq human - seeding the knowledge and
    beliefs that allow intelligent, contextual responses.
    """
    person_id = request_data.person_id or f"person_{uuid.uuid4().hex[:12]}"
    org_id = request_data.org_id or f"org_{uuid.uuid4().hex[:12]}"

    try:
        # Birth the person with all 6 things
        birth_result = birth_person(
            person_id=person_id,
            name=request_data.name,
            email=request_data.email,
            role=request_data.role,
            org_id=org_id,
            org_name=request_data.org_name,
            industry=request_data.industry,
            # org_size and capabilities_override not supported by birth_person yet
        )

        # Create session
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        # Store in app state (will be upgraded to Redis in Phase 2)
        request.app.state.sessions[session_id] = {
            "birth_result": birth_result,
            "state": None,  # Created on first message
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "context_pills": [],  # Active context items
            "interrupt_event": None,  # For chat interruption
        }

        logger.info(
            f"Birth complete: person={person_id}, org={org_id}, "
            f"session={session_id}, mode={birth_result['birth_mode']}"
        )

        return BirthResponse(
            person_id=person_id,
            org_id=org_id,
            birth_mode=birth_result["birth_mode"],
            salience=birth_result["salience"],
            belief_count=birth_result["belief_count"],
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Birth failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "BIRTH_FAILED",
                    "message": "Failed to create agent. Please try again or contact support.",
                    "severity": "error",
                    "recoverable": True,
                    "actions": [
                        {"label": "Try again", "action": "retry"},
                    ],
                }
            },
        )
