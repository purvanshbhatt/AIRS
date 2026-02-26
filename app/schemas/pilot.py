"""Schemas for pilot request APIs."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

from app.core.sanitize import strip_dangerous


class PilotRequestCreate(BaseModel):
    """Legacy pilot request form (used by /api/pilot-request)."""
    company_name: str = Field(..., min_length=1, max_length=255)
    team_size: str = Field(..., min_length=1, max_length=64)
    current_security_tools: Optional[str] = Field(default=None, max_length=4000)
    email: EmailStr

    @field_validator("company_name", "team_size", "current_security_tools", mode="before")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        return strip_dangerous(v)


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
    current_siem_provider: Optional[str] = Field(default=None, max_length=100)

    @field_validator(
        "company_name", "contact_name", "industry", "company_size",
        "team_size", "current_security_tools", "ai_usage_description",
        "current_siem_provider", mode="before",
    )
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        return strip_dangerous(v)


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
    current_siem_provider: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

