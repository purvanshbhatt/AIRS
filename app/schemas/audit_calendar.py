"""
Pydantic schemas for Audit Calendar.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AuditCalendarCreate(BaseModel):
    """Schema for creating an audit calendar entry."""
    framework: str = Field(..., min_length=1, max_length=100)
    audit_date: datetime
    audit_type: str = Field("external", pattern="^(external|internal)$")
    reminder_days_before: int = Field(90, ge=1, le=365)
    notes: Optional[str] = Field(None, max_length=500)


class AuditCalendarUpdate(BaseModel):
    """Schema for updating an audit calendar entry."""
    framework: Optional[str] = Field(None, max_length=100)
    audit_date: Optional[datetime] = None
    audit_type: Optional[str] = Field(None, pattern="^(external|internal)$")
    reminder_days_before: Optional[int] = Field(None, ge=1, le=365)
    notes: Optional[str] = Field(None, max_length=500)


class AuditCalendarResponse(BaseModel):
    """Response schema for an audit calendar entry."""
    id: str
    org_id: str
    framework: str
    audit_date: datetime
    audit_type: str
    reminder_days_before: int = 90
    notes: Optional[str] = None
    days_until_audit: Optional[int] = None      # computed
    is_upcoming: bool = False                     # computed: within reminder window
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditForecast(BaseModel):
    """Pre-audit risk forecast for a scheduled audit."""
    audit_id: str
    framework: str
    audit_date: datetime
    days_until_audit: int
    related_findings_count: int = 0
    critical_high_count: int = 0
    risk_level: str = "low"                      # "critical", "high", "medium", "low"
    recommendation: str = ""


class AuditCalendarListResponse(BaseModel):
    """List response for audit calendar entries."""
    entries: List[AuditCalendarResponse] = []
    upcoming_count: int = 0
    total: int = 0
