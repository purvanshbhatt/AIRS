"""
Pydantic schemas for Tech Stack Lifecycle Registry.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TechStackItemCreate(BaseModel):
    """Schema for creating a tech stack item."""
    component_name: str = Field(..., min_length=1, max_length=255)
    version: Optional[str] = Field(None, max_length=50)
    lts_status: str = Field("active", pattern="^(lts|active|deprecated|eol)$")
    major_versions_behind: int = Field(0, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class TechStackItemUpdate(BaseModel):
    """Schema for updating a tech stack item."""
    component_name: Optional[str] = Field(None, max_length=255)
    version: Optional[str] = Field(None, max_length=50)
    lts_status: Optional[str] = Field(None, pattern="^(lts|active|deprecated|eol)$")
    major_versions_behind: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class TechStackItemResponse(BaseModel):
    """Response schema for a tech stack item."""
    id: str
    org_id: str
    component_name: str
    version: Optional[str] = None
    lts_status: str = "active"
    major_versions_behind: int = 0
    category: Optional[str] = None
    notes: Optional[str] = None
    risk_level: str = "low"                      # computed: "high", "medium", "low"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TechStackSummary(BaseModel):
    """Summary of tech stack risk posture."""
    total_components: int = 0
    eol_count: int = 0
    deprecated_count: int = 0
    outdated_count: int = 0                      # >2 major versions behind
    risk_breakdown: dict = {}                     # {"high": N, "medium": N, "low": N}
    upgrade_governance_summary: Optional[str] = None  # LLM-generated narrative (if enabled)


class TechStackListResponse(BaseModel):
    """List response for tech stack items."""
    items: List[TechStackItemResponse] = []
    summary: TechStackSummary = TechStackSummary()
    total: int = 0
