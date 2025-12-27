"""
Birth Routes
============

Agent initialization endpoint with first impression psychology.
"""

import uuid
from datetime import datetime
from typing import Optional, cast

from fastapi import APIRouter, HTTPException, Request

from ...birth.birth_system import birth_person
from ...cognitive_loop.graph import create_graph_in_memory, invoke_cognitive_loop
from ...observability import get_logger
from ...persistence.rapport import create_rapport
from ...scheduler.defaults import seed_org_triggers
from ...scheduler.message_factory import create_birth_state
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

        # Seed default triggers for proactive behaviors (SYSTEM_PULSE)
        org_timezone = request_data.timezone
        try:
            await seed_org_triggers(org_id, org_timezone)
            logger.info(f"Seeded default triggers for org {org_id}")
        except Exception as e:
            # Non-fatal: org can still function without triggers
            logger.warning(f"Failed to seed triggers for org {org_id}: {e}")

        # Create session
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        # ============================================================
        # FIRST IMPRESSION: Generate Aleq's greeting
        # ============================================================
        # This is the critical first moment of rapport building.
        # Research shows first impressions form in 7 seconds and persist.
        greeting: Optional[str] = None
        try:
            # Create birth state for first impression
            birth_state = create_birth_state(
                org_id=org_id,
                person_name=request_data.name,
                person_role=request_data.role,
                industry=request_data.industry,
                org_timezone=org_timezone,
            )

            # Run through cognitive loop for authentic, belief-informed greeting
            from ...state.schema import BabyMARSState

            graph = create_graph_in_memory()
            result_state = await invoke_cognitive_loop(cast(BabyMARSState, birth_state), graph)

            # Extract greeting from final response
            greeting = result_state.get("final_response")
            if greeting:
                logger.info(f"First impression generated for {request_data.name}")
        except Exception as e:
            # Non-fatal: birth succeeds even if greeting fails
            logger.warning(f"Failed to generate first impression: {e}")
            greeting = None

        # ============================================================
        # CREATE RAPPORT: Initialize relationship tracking
        # ============================================================
        try:
            rapport = await create_rapport(
                org_id=org_id,
                person_id=person_id,
                person_name=request_data.name,
                first_impression_text=greeting,
            )
            if rapport:
                logger.info(f"Rapport initialized for {request_data.name}")
            else:
                logger.warning(f"Rapport already exists or failed for {request_data.name}")
        except Exception as e:
            # Non-fatal: we can create rapport later
            logger.warning(f"Failed to create rapport: {e}")

        # Store in app state (will be upgraded to Redis in Phase 2)
        request.app.state.sessions[session_id] = {
            "birth_result": birth_result,
            "state": None,  # Created on first message
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "context_pills": [],  # Active context items
            "interrupt_event": None,  # For chat interruption
            "first_impression_delivered": greeting is not None,
        }

        logger.info(
            f"Birth complete: person={person_id}, org={org_id}, "
            f"session={session_id}, mode={birth_result['birth_mode']}, "
            f"greeting={'generated' if greeting else 'skipped'}"
        )

        return BirthResponse(
            person_id=person_id,
            org_id=org_id,
            birth_mode=birth_result["birth_mode"],
            salience=birth_result["salience"],
            belief_count=birth_result["belief_count"],
            session_id=session_id,
            greeting=greeting,
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
