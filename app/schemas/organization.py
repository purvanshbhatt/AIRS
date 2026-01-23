"""
Pydantic schemas for Organization.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
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
    website_url: Optional[str] = Field(None, max_length=512)


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
    website_url: Optional[str] = Field(None, max_length=512)
    baseline_suggestion: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: str
    org_profile: Optional[str] = None
    baseline_suggestion: Optional[str] = None
    enriched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationWithAssessments(OrganizationResponse):
    """Organization with assessment count."""
    assessment_count: int = 0


class EnrichmentRequest(BaseModel):
    """Request schema for organization enrichment."""
    website_url: str = Field(..., max_length=512, pattern=r"^(https?://)?[a-zA-Z0-9][-a-zA-Z0-9]+(\.[a-zA-Z0-9][-a-zA-Z0-9]+)+\S*$")


class EnrichmentResponse(BaseModel):
    """Response schema for organization enrichment."""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []
    baseline_suggestion: Optional[str] = None
    confidence: float = 0.0
    source_url: str

