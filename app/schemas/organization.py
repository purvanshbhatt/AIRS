"""
Pydantic schemas for Organization.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base schema for organization data."""
    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, pattern="^(1-50|51-200|201-1000|1000\\+)$")
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, pattern="^(1-50|51-200|201-1000|1000\\+)$")
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrganizationWithAssessments(OrganizationResponse):
    """Organization with assessment count."""
    assessment_count: int = 0
