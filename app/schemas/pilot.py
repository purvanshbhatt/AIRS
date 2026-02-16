"""Schemas for pilot request APIs."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PilotRequestCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    team_size: str = Field(..., min_length=1, max_length=64)
    current_security_tools: str | None = Field(default=None, max_length=4000)
    email: EmailStr


class PilotRequestResponse(BaseModel):
    id: str
    company_name: str
    team_size: str
    current_security_tools: str | None = None
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

