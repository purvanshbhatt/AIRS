"""Schemas for pilot request APIs."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class PilotRequestCreate(BaseModel):
    """Legacy pilot request form (used by /api/pilot-request)."""
    company_name: str = Field(..., min_length=1, max_length=255)
    team_size: str = Field(..., min_length=1, max_length=64)
    current_security_tools: Optional[str] = Field(default=None, max_length=4000)
    email: EmailStr


class EnterprisePilotLeadCreate(BaseModel):
    """Extended intake form for Enterprise Pilot Programme (/api/v1/pilot-leads)."""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    industry: Optional[str] = Field(default=None, max_length=100)
    company_size: Optional[str] = Field(default=None, max_length=64)
    team_size: Optional[str] = Field(default=None, max_length=64)
    current_security_tools: Optional[str] = Field(default=None, max_length=4000)
    ai_usage_description: Optional[str] = Field(default=None, max_length=4000)


class PilotRequestResponse(BaseModel):
    id: str
    company_name: str
    contact_name: Optional[str] = None
    team_size: str
    current_security_tools: Optional[str] = None
    email: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    ai_usage_description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

