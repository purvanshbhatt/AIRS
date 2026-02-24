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
    # Phase 5: Governance & Analytics Control
    analytics_enabled: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: str
    integration_status: Optional[str] = "{}"
    analytics_enabled: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrganizationWithAssessments(OrganizationResponse):
    """Organization with assessment count."""
    assessment_count: int = 0


# ═══════════════════════════════════════════════════════════════════════
# Phase 8: Governance Profile
# ═══════════════════════════════════════════════════════════════════════

class OrganizationProfileUpdate(BaseModel):
    """Schema for updating the governance profile of an organization."""
    revenue_band: Optional[str] = Field(None, max_length=50)
    employee_count: Optional[int] = Field(None, ge=0)
    geo_regions: Optional[List[str]] = None
    processes_pii: Optional[bool] = None
    processes_phi: Optional[bool] = None
    processes_cardholder_data: Optional[bool] = None
    handles_dod_data: Optional[bool] = None
    uses_ai_in_production: Optional[bool] = None
    government_contractor: Optional[bool] = None
    financial_services: Optional[bool] = None
    application_tier: Optional[str] = Field(None, pattern="^(tier_1|tier_2|tier_3)$")
    sla_target: Optional[float] = Field(None, ge=0, le=100)


class OrganizationProfileResponse(BaseModel):
    """Full governance profile response."""
    org_id: str
    industry: Optional[str] = None
    revenue_band: Optional[str] = None
    employee_count: Optional[int] = None
    geo_regions: List[str] = []
    processes_pii: bool = False
    processes_phi: bool = False
    processes_cardholder_data: bool = False
    handles_dod_data: bool = False
    uses_ai_in_production: bool = False
    government_contractor: bool = False
    financial_services: bool = False
    application_tier: Optional[str] = None
    sla_target: Optional[float] = None

    class Config:
        from_attributes = True


class UptimeTierAnalysis(BaseModel):
    """Uptime tier comparison result."""
    application_tier: Optional[str] = None
    tier_sla: Optional[float] = None       # SLA for the chosen tier (e.g. 99.9)
    sla_target: Optional[float] = None     # User-specified target
    gap_pct: Optional[float] = None        # tier_sla - sla_target (positive = surplus)
    status: str = "not_configured"         # "on_track", "at_risk", "unrealistic", "not_configured"
    message: str = ""
