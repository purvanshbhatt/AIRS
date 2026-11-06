"""
Pydantic schemas for Report.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.core.sanitize import strip_dangerous


class ReportType(str, Enum):
    """Report template identifier. Every value maps to a server-side builder in
    ``app.reports.templates`` (PDF) and a snapshot built in ``app.reports.readiness_source``."""
    EXECUTIVE_PDF = "executive_pdf"
    BOARD_STORY = "board_story"
    MONTHLY_OPS = "monthly_ops"
    HIPAA_AUDIT = "hipaa_audit"
    TECHNICAL_TELEMETRY = "technical_telemetry"
    BOSS_REPORT = "boss_report"
    CYBER_INSURANCE = "cyber_insurance"
    MSP_SUMMARY = "msp_summary"


class ReportFormat(str, Enum):
    """Output format. Only ``pdf`` is rendered server-side; ``json`` returns the
    stored snapshot; ``csv`` is a flat export of findings."""
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"


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


class GenerateReportRequest(BaseModel):
    """Request body for ``POST /api/v1/reports/generate``.

    ``org_id`` is accepted as an alias of ``organization_id`` so the shared
    ``require_entitlement`` dependency (which reads ``org_id`` from the body)
    gates on the same organization.
    """
    organization_id: Optional[str] = Field(None, max_length=64)
    org_id: Optional[str] = Field(None, max_length=64)
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    title: Optional[str] = Field(None, max_length=255)
    assessment_id: Optional[str] = Field(None, max_length=64)
    parameters: Optional[Dict[str, Any]] = None

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v: Optional[str]) -> Optional[str]:
        return strip_dangerous(v)

    @property
    def resolved_org_id(self) -> Optional[str]:
        return (self.organization_id or self.org_id or "").strip() or None


class GenerateReportResponse(BaseModel):
    """Response for a generated report. All numbers are server-computed."""
    id: str
    title: str
    report_type: str
    format: str
    status: str
    created_at: datetime
    organization_id: str
    organization_name: Optional[str] = None
    overall_score: Optional[float] = None
    findings_count: int = 0
    persisted: bool = True
    download_url: Optional[str] = None


class ReportResponse(BaseModel):
    """Report metadata response."""
    id: str
    owner_uid: str
    organization_id: str
    organization_name: Optional[str] = None
    assessment_id: Optional[str] = None
    assessment_title: Optional[str] = None
    report_type: str
    title: str
    format: Optional[str] = "pdf"
    status: Optional[str] = "completed"
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
