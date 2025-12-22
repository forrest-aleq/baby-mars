"""
Birth Schemas
=============

Request/response models for agent initialization.
"""

from typing import Optional
from pydantic import BaseModel, Field


class BirthRequest(BaseModel):
    """Request to birth a new agent into the system"""
    person_id: Optional[str] = Field(
        None,
        description="Custom person ID (auto-generated if not provided)"
    )
    name: str = Field(..., description="Person's display name")
    email: str = Field(..., description="Person's email")
    role: str = Field("Controller", description="Role: Controller, CFO, Staff, etc.")
    org_id: Optional[str] = Field(
        None,
        description="Custom org ID (auto-generated if not provided)"
    )
    org_name: str = Field("Default Organization", description="Organization name")
    industry: str = Field("general", description="Industry for knowledge packs")
    org_size: str = Field(
        "mid_market",
        description="Org size: startup, smb, mid_market, enterprise"
    )
    capabilities_override: Optional[dict] = Field(
        None,
        description="Override default capabilities"
    )


class BirthResponse(BaseModel):
    """Response from birth"""
    person_id: str
    org_id: str
    birth_mode: str = Field(..., description="full, standard, or micro")
    salience: float = Field(..., ge=0, le=1, description="Initial relationship salience")
    belief_count: int = Field(..., description="Number of initial beliefs seeded")
    session_id: str = Field(..., description="Use this for subsequent chat requests")
