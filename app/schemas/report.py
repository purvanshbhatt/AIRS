"""
Pydantic schemas for Report.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.core.sanitize import strip_dangerous


class ReportType(str, Enum):
    """Report type."""
    EXECUTIVE_PDF = "executive_pdf"


# ----- Snapshot Schema -----

class DomainScoreSnapshot(BaseModel):
    """Domain score snapshot data."""
    domain_id: str
    domain_name: str
    score: float
    score_5: float  # 0-5 scale
    weight: float
    earned_points: Optional[float] = None
    max_points: Optional[float] = None


class FindingSnapshot(BaseModel):
    """Finding snapshot data."""
    id: str
    title: str
    severity: str
    domain: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    description: Optional[str] = None


class ReportSnapshot(BaseModel):
    """
    Point-in-time snapshot of assessment data.
    This ensures report consistency even if rubric changes later.
    """
    # Assessment info
    assessment_id: str
    assessment_title: Optional[str] = None
    organization_id: str
    organization_name: Optional[str] = None
    
    # Scoring
    overall_score: float
    maturity_level: int
    maturity_name: str
    
    # Domain breakdown
    domain_scores: List[DomainScoreSnapshot]
    
    # Findings
    findings: List[FindingSnapshot]
    findings_count: int
    critical_high_count: int
    
    # Baseline comparison
    baseline_selected: Optional[str] = None
    baseline_profiles: Optional[Dict[str, Dict[str, float]]] = None
    
    # LLM metadata (informational only)
    llm_enabled: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_mode: Optional[str] = None
    
    # Narrative content
    executive_summary: Optional[str] = None
    roadmap_narrative: Optional[str] = None
    
    # Metadata
    rubric_version: Optional[str] = None
    generated_at: datetime


# ----- Request/Response Schemas -----

class ReportCreate(BaseModel):
    """Request to generate a new report."""
    report_type: ReportType = ReportType.EXECUTIVE_PDF
    title: Optional[str] = Field(None, max_length=255)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        return strip_dangerous(v)


class ReportResponse(BaseModel):
    """Report metadata response."""
    id: str
    owner_uid: str
    organization_id: str
    organization_name: Optional[str] = None
    assessment_id: str
    assessment_title: Optional[str] = None
    report_type: str
    title: str
    overall_score: Optional[float] = None
    maturity_level: Optional[int] = None
    maturity_name: Optional[str] = None
    findings_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    """Report with full snapshot data."""
    snapshot: ReportSnapshot


class ReportListResponse(BaseModel):
    """List of reports response."""
    reports: List[ReportResponse]
    total: int


class ReportListFilters(BaseModel):
    """Filters for listing reports."""
    organization_id: Optional[str] = None
    assessment_id: Optional[str] = None
    report_type: Optional[ReportType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
