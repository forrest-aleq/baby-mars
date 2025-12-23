"""
Beliefs Routes
==============

Belief system endpoints with challenge functionality.
Per API_CONTRACT_V0.md section 4
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ...graphs.belief_graph_manager import get_org_belief_graph
from ..schemas.beliefs import (
    BeliefChallengeRequest,
    BeliefChallengeResponse,
    BeliefDetailResponse,
    BeliefResponse,
    BeliefStatus,
    BeliefVersion,
)

logger = logging.getLogger("baby_mars.api.beliefs")

router = APIRouter()


@router.get("/{org_id}", response_model=list[BeliefResponse])
async def list_beliefs(
    org_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
) -> list[BeliefResponse]:
    """
    List beliefs for an organization.

    Filterable by category (moral, competence, technical, preference, identity)
    and status (active, superseded, invalidated, disputed, archived).
    """
    try:
        graph = await get_org_belief_graph(org_id)
        beliefs = graph.get_all_beliefs()

        # Filter
        if category:
            beliefs = [b for b in beliefs if b.get("category") == category]
        if status:
            beliefs = [b for b in beliefs if b.get("status", "active") == status]

        # Paginate
        total = len(beliefs)
        beliefs = beliefs[offset : offset + limit]

        return [
            BeliefResponse(
                belief_id=b["belief_id"],
                statement=b["statement"],
                category=b["category"],
                strength=b.get("strength", 0.5),
                context_key=str(b.get("context_key", "*|*|*")),
                status=b.get("status") or "active",  # type: ignore[arg-type]
                is_immutable=bool(b.get("is_immutable", False)),
            )
            for b in beliefs
        ]

    except Exception as e:
        logger.error(f"Failed to get beliefs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{org_id}/{belief_id}", response_model=BeliefDetailResponse)
async def get_belief(org_id: str, belief_id: str) -> BeliefDetailResponse:
    """
    Get full belief detail with history and evidence.

    Per API_CONTRACT_V0.md section 4.3, shows:
    - Current state
    - Version history
    - Evidence supporting/challenging
    - Related beliefs
    """
    try:
        graph = await get_org_belief_graph(org_id)
        belief = graph.get_belief(belief_id)

        if not belief:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "BELIEF_NOT_FOUND",
                        "message": f"Belief {belief_id} not found",
                        "severity": "warning",
                    }
                },
            )

        # Build version history (placeholder - will be enhanced)
        created_at_str = str(belief.get("created_at") or datetime.now().isoformat())
        versions = [
            BeliefVersion(
                version=1,
                statement=belief["statement"],
                strength=belief.get("strength", 0.5),
                changed_at=created_at_str,
                changed_by="system",
                reason="Initial creation",
            )
        ]

        # Build evidence list (placeholder)
        evidence: list[Any] = []

        requires_role_val = belief.get("requires_role")
        active_challenge_val = belief.get("active_challenge")

        return BeliefDetailResponse(
            belief_id=belief["belief_id"],
            statement=belief["statement"],
            category=belief["category"],
            strength=belief.get("strength", 0.5),
            context_key=str(belief.get("context_key", "*|*|*")),
            status=belief.get("status") or "active",  # type: ignore[arg-type]
            is_immutable=bool(belief.get("is_immutable", False)),
            requires_role=str(requires_role_val) if requires_role_val else None,
            versions=versions,
            current_version=1,
            evidence=evidence,
            supports=belief.get("supports", []),
            supported_by=belief.get("supported_by", []),
            source=str(belief.get("source") or "system"),
            created_at=created_at_str,
            updated_at=str(belief.get("updated_at") or datetime.now().isoformat()),
            challenge_count=int(str(belief.get("challenge_count", 0) or 0)),
            active_challenge=str(active_challenge_val) if active_challenge_val else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get belief: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{org_id}/{belief_id}/challenge", response_model=BeliefChallengeResponse)
async def challenge_belief(
    org_id: str,
    belief_id: str,
    request: BeliefChallengeRequest,
) -> BeliefChallengeResponse:
    """
    Challenge a belief.

    Per API_CONTRACT_V0.md section 4.1:
    - Users cannot directly edit beliefs, they challenge
    - Shows existing evidence
    - If disputed, strength significantly decreases
    - Related decisions are flagged for review

    Identity beliefs (is_immutable=true) cannot be challenged.
    """
    try:
        graph = await get_org_belief_graph(org_id)
        belief = graph.get_belief(belief_id)

        if not belief:
            raise HTTPException(status_code=404, detail="Belief not found")

        # Check if immutable
        if belief.get("is_immutable"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BELIEF_IMMUTABLE",
                        "message": "This is a core identity belief and cannot be challenged",
                        "severity": "warning",
                        "recoverable": False,
                    }
                },
            )

        # Show existing evidence (placeholder)
        existing_evidence: list[Any] = []

        # Generate challenge ID
        challenge_id = f"challenge_{uuid.uuid4().hex[:12]}"

        # Calculate what strength would be after challenge (reduces by ~50%)
        old_strength = belief.get("strength", 0.5)
        projected_strength = max(0.1, old_strength * 0.5)
        projected_status: BeliefStatus = "disputed" if projected_strength < 0.4 else "active"

        # TODO: Implement proper challenge flow with graph.challenge_belief()
        # For now, we only record the challenge without persisting the change
        belief_updated = False

        logger.info(
            f"Belief challenge recorded: org={org_id}, belief={belief_id}, "
            f"current_strength={old_strength:.2f}, projected_strength={projected_strength:.2f}"
        )

        return BeliefChallengeResponse(
            challenge_id=challenge_id,
            belief_id=belief_id,
            accepted=True,
            belief_updated=belief_updated,
            new_strength=projected_strength,
            new_status=projected_status,
            existing_evidence=existing_evidence,
            message=f"Challenge recorded. If accepted, strength would change from {old_strength:.2f} to {projected_strength:.2f}. "
            f"Note: Full challenge flow not yet implemented - this is a preview.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to challenge belief: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
