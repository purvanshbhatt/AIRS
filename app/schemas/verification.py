"""
Pydantic schemas for the Verification & Audit Trail API.

Defines request/response models for:
  - Finding verification status (SOC-Verified / Provisional / Contradicted)
  - Audit trail with integrity hash
  - Liability-to-ROI metrics
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Verification Status
# ---------------------------------------------------------------------------

class VerificationStatusEnum(str, Enum):
    """Badge status for a finding after SIEM cross-reference."""
    SOC_VERIFIED = "SOC-Verified"
    PROVISIONAL = "Provisional"
    CONTRADICTED = "Contradicted"
    CONNECTION_ERROR = "Connection Error"
    STALE_CONNECTION = "Stale Connection"
    NOT_APPLICABLE = "Not Applicable"


# ---------------------------------------------------------------------------
# Verification Result (per-finding)
# ---------------------------------------------------------------------------

class VerificationResultSchema(BaseModel):
    """Result of cross-referencing a single finding against SIEM logs."""
    finding_id: Optional[str] = None
    rule_id: str
    title: str
    status: VerificationStatusEnum
    evidence_summary: str = Field(
        ..., description="Plain-English explanation of what SIEM evidence was found (or not)."
    )
    siem_source: Optional[str] = Field(
        None, description="Which SIEM provided the evidence: 'splunk', 'wazuh', 'elastic', or None."
    )
    siem_query_used: Optional[str] = None
    event_count: int = 0
    log_event_ids: List[str] = Field(default_factory=list)
    verified_at: str = Field(
        ..., description="ISO-8601 UTC timestamp of when verification was performed."
    )


class VerifiedFindingSchema(BaseModel):
    """A finding enriched with its verification status."""
    rule_id: str
    title: str
    domain_id: str
    domain_name: str
    severity: str
    evidence: str
    recommendation: str
    reference: Optional[str] = None
    remediation_effort: str = "medium"
    risk_impact: str = "medium"
    nist_category: Optional[str] = None
    nist_function: Optional[str] = None
    verification: VerificationResultSchema


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

class AuditTrailFindingSchema(BaseModel):
    """Compact finding representation inside the audit trail."""
    rule_id: str
    title: str
    severity: str
    domain_id: str
    verification_status: VerificationStatusEnum
    evidence_summary: str
    siem_source: Optional[str] = None
    log_event_ids: List[str] = Field(default_factory=list)
    verified_at: str


class AuditTrailSchema(BaseModel):
    """Tamper-evident audit trail for an assessment's scoring + verification."""
    integrity_hash: str = Field(
        ..., description="SHA-256 hash of the canonical JSON payload (scores + findings)."
    )
    generated_at: str
    assessment_id: Optional[str] = None
    organization_id: Optional[str] = None

    # GHI context
    ghi_score_current: Optional[float] = None
    ghi_score_previous: Optional[float] = None
    ghi_score_delta: Optional[float] = None
    overall_score: Optional[float] = None

    # Methodology
    methodology: str = (
        "Deterministic rule-based scoring per ResilAI Rubric v2.0.0. "
        "SIEM verification performed against live Wazuh/Splunk telemetry. "
        "No LLM subjectivity applied to scores or classifications."
    )

    # Findings
    findings: List[AuditTrailFindingSchema] = Field(default_factory=list)

    # Summary
    total_findings: int = 0
    soc_verified_count: int = 0
    provisional_count: int = 0
    contradicted_count: int = 0


# ---------------------------------------------------------------------------
# Liability-to-ROI
# ---------------------------------------------------------------------------

class RemediationROISchema(BaseModel):
    """Per-remediation cost/time ROI metrics."""
    finding_rule_id: str
    finding_title: str
    severity: str
    remediation_effort: str

    estimated_hours_saved: float = Field(
        ..., description="Incident response hours saved if this control is remediated."
    )
    estimated_cost_avoided_usd: float = Field(
        ..., description="Dollar value of breach risk reduced."
    )
    liability_reduction_pct: float = Field(
        ..., description="Percentage reduction in breach probability for this control."
    )
    roi_percentage: float = Field(
        ..., description="(cost_avoided - remediation_cost) / remediation_cost × 100"
    )
    remediation_cost_usd: float = Field(
        ..., description="Estimated cost to implement the remediation."
    )
    time_to_value_days: int = Field(
        ..., description="Estimated implementation timeline in days."
    )
    calculation_methodology: str = Field(
        ..., description="Plain-English explanation of how each number was derived."
    )


class PortfolioROISchema(BaseModel):
    """Aggregate ROI across all remediation actions."""
    total_cost_avoided_usd: float
    total_remediation_cost_usd: float
    total_roi_percentage: float
    total_hours_saved: float
    aggregate_liability_reduction_pct: float
    items: List[RemediationROISchema]
    benchmark_source: str = "IBM Cost of a Data Breach 2023, Ponemon Institute, Mandiant M-Trends 2024"
    calculated_at: str


# ---------------------------------------------------------------------------
# MTTR Executive Summary
# ---------------------------------------------------------------------------

class MTTRChartDataPoint(BaseModel):
    """Single data point for the Executive Risk-Reduction Recharts graph."""
    month: str
    mttrDays: float
    ghiScore: float
    liabilityExposureM: float


class MTTRMetadata(BaseModel):
    """Deterministic metadata backing the MTTR summary."""
    overall_mttr_days: float = 0.0
    mttr_trend: str = "insufficient_data"
    ghi_current: float = 0.0
    ghi_delta: float = 0.0
    liability_current_m: float = 0.0
    liability_reduction_m: float = 0.0
    assessment_count: int = 0
    generated_at: str = ""
    methodology: str = ""


class MTTRExecutiveSummarySchema(BaseModel):
    """Board-ready MTTR + risk-reduction executive summary."""
    narrative: str
    chartData: List[MTTRChartDataPoint]
    keyHighlights: List[str]
    metadata: Optional[MTTRMetadata] = None


# ---------------------------------------------------------------------------
# API Response wrappers
# ---------------------------------------------------------------------------

class VerifyAssessmentResponse(BaseModel):
    """Response for POST /verification/assess/{id}/verify"""
    assessment_id: str
    verified_at: str
    total_findings: int
    soc_verified_count: int
    provisional_count: int
    contradicted_count: int
    findings: List[VerifiedFindingSchema]


class AuditTrailResponse(BaseModel):
    """Response for GET /verification/assess/{id}/audit-trail"""
    audit_trail: AuditTrailSchema
