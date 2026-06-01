"""
Verification & Audit Trail API — SIEM-corroborated finding verification.

Endpoints:
  POST /verification/assess/{assessment_id}/verify
    → Run all findings through SIEM verification, return verified list

  GET  /verification/assess/{assessment_id}/audit-trail
    → Return tamper-evident JSON audit trail with integrity hash

  GET  /verification/assess/{assessment_id}/findings/{finding_id}/status
    → Return verification status for a single finding

  POST /verification/assess/{assessment_id}/roi
    → Return Liability-to-ROI analysis for all remediation items

  POST /verification/forensic-trail
    → Generate a forensic trail from a SIEM log dump (agent-assisted)

  GET  /verification/org/{org_id}/mttr-summary
    → Board-ready MTTR + risk-reduction executive summary
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_auth, User
from app.db.database import get_db
from app.models.assessment import Assessment
from app.models.finding import Finding as FindingModel
from app.schemas.verification import (
    VerificationStatusEnum,
    VerifiedFindingSchema,
    VerificationResultSchema,
    AuditTrailResponse,
    VerifyAssessmentResponse,
    PortfolioROISchema,
    MTTRExecutiveSummarySchema,
)
from app.services.findings import FindingsEngine, generate_findings
from app.services.scoring import calculate_scores
from app.services.verification import VerificationService
from app.services.liability_roi import LiabilityROIEngine

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_assessment_or_404(
    assessment_id: str, user: User, db: Session
) -> Assessment:
    """Fetch assessment with ownership check."""
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id, Assessment.owner_uid == user.uid)
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return assessment


def _build_siem_clients():
    """Attempt to build SIEM clients from environment config.

    Returns (wazuh_client_or_none, splunk_service_or_none).
    """
    from app.core.config import settings

    wazuh = None
    splunk = None

    # Wazuh
    wazuh_host = getattr(settings, "WAZUH_HOST", None) or ""
    wazuh_key = getattr(settings, "WAZUH_API_KEY", None) or ""
    if wazuh_host and wazuh_key:
        try:
            from app.services.wazuh_client import WazuhClient
            wazuh = WazuhClient(host=wazuh_host, api_key=wazuh_key)
        except Exception as exc:
            logger.warning("Failed to init WazuhClient: %s", exc)

    # Splunk
    splunk_url = getattr(settings, "SPLUNK_BASE_URL", None) or getattr(settings, "SPLUNK_HOST", None) or ""
    splunk_token = getattr(settings, "SPLUNK_HEC_TOKEN", None) or ""
    if splunk_url and splunk_token:
        try:
            from app.services.splunk import SplunkService
            splunk = SplunkService(base_url=splunk_url, hec_token=splunk_token)
        except Exception as exc:
            logger.warning("Failed to init SplunkService: %s", exc)

    return wazuh, splunk


def _reconstruct_answers(assessment: Assessment) -> dict:
    """Reconstruct the answers dict from an assessment's stored answers."""
    import json

    raw = getattr(assessment, "answers_json", None) or getattr(assessment, "answers", None)
    if raw and isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    if raw and isinstance(raw, dict):
        return raw

    # Fallback: reconstruct from related Answer objects
    answers = {}
    for answer in getattr(assessment, "answers", []):
        if hasattr(answer, "question_id") and hasattr(answer, "value"):
            answers[answer.question_id] = answer.value
    return answers


# ---------------------------------------------------------------------------
# POST /verification/assess/{assessment_id}/verify
# ---------------------------------------------------------------------------

@router.post(
    "/assess/{assessment_id}/verify",
    response_model=VerifyAssessmentResponse,
    summary="Verify Assessment Findings Against SIEM",
    description=(
        "Cross-references all findings for an assessment against live "
        "Wazuh/Splunk SIEM evidence. Findings with corroborating telemetry "
        "receive a 'SOC-Verified' badge; others are 'Provisional'."
    ),
)
async def verify_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    assessment = _get_assessment_or_404(assessment_id, user, db)
    answers = _reconstruct_answers(assessment)

    # Generate findings and scores deterministically
    scores = calculate_scores(answers)
    engine = FindingsEngine()
    findings = engine.evaluate(answers, scores)

    if not findings:
        return VerifyAssessmentResponse(
            assessment_id=assessment_id,
            verified_at=datetime.now(timezone.utc).isoformat(),
            total_findings=0,
            soc_verified_count=0,
            provisional_count=0,
            contradicted_count=0,
            findings=[],
        )

    # Build SIEM clients and verify
    wazuh, splunk = _build_siem_clients()
    svc = VerificationService(wazuh_client=wazuh, splunk_service=splunk, db=db)
    verification_results = await svc.verify_all_findings(findings, answers)

    # Build response
    verified_findings = []
    for finding, vr in zip(findings, verification_results):
        severity_value = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        verified_findings.append(VerifiedFindingSchema(
            rule_id=finding.rule_id,
            title=finding.title,
            domain_id=finding.domain_id,
            domain_name=finding.domain_name,
            severity=severity_value,
            evidence=finding.evidence,
            recommendation=finding.recommendation,
            reference=finding.reference,
            remediation_effort=finding.remediation_effort,
            risk_impact=getattr(finding, "risk_impact", "medium"),
            nist_category=finding.nist_category,
            nist_function=finding.nist_function,
            verification=vr,
        ))

    now = datetime.now(timezone.utc).isoformat()
    soc_count = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.SOC_VERIFIED)
    prov_count = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.PROVISIONAL)
    contr_count = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.CONTRADICTED)

    return VerifyAssessmentResponse(
        assessment_id=assessment_id,
        verified_at=now,
        total_findings=len(findings),
        soc_verified_count=soc_count,
        provisional_count=prov_count,
        contradicted_count=contr_count,
        findings=verified_findings,
    )


# ---------------------------------------------------------------------------
# GET /verification/assess/{assessment_id}/audit-trail
# ---------------------------------------------------------------------------

@router.get(
    "/assess/{assessment_id}/audit-trail",
    response_model=AuditTrailResponse,
    summary="Get Assessment Audit Trail",
    description=(
        "Returns a tamper-evident JSON audit trail with SHA-256 integrity hash "
        "for the assessment's scores and verification status. Suitable for "
        "external auditor review."
    ),
)
async def get_audit_trail(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    assessment = _get_assessment_or_404(assessment_id, user, db)
    answers = _reconstruct_answers(assessment)

    scores = calculate_scores(answers)
    engine = FindingsEngine()
    findings = engine.evaluate(answers, scores)

    # Verify
    wazuh, splunk = _build_siem_clients()
    svc = VerificationService(wazuh_client=wazuh, splunk_service=splunk, db=db)
    verification_results = await svc.verify_all_findings(findings, answers)

    # Generate audit trail
    trail = svc.generate_audit_trail(
        findings=findings,
        verification_results=verification_results,
        scores=scores,
        assessment_id=assessment_id,
        organization_id=getattr(assessment, "organization_id", None),
    )

    return AuditTrailResponse(audit_trail=trail)


# ---------------------------------------------------------------------------
# GET /verification/assess/{assessment_id}/findings/{finding_rule_id}/status
# ---------------------------------------------------------------------------

@router.get(
    "/assess/{assessment_id}/findings/{finding_rule_id}/status",
    response_model=VerificationResultSchema,
    summary="Get Finding Verification Status",
    description="Returns the SIEM verification status for a specific finding.",
)
async def get_finding_verification_status(
    assessment_id: str,
    finding_rule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    assessment = _get_assessment_or_404(assessment_id, user, db)
    answers = _reconstruct_answers(assessment)

    scores = calculate_scores(answers)
    engine = FindingsEngine()
    findings = engine.evaluate(answers, scores)

    target_finding = None
    for f in findings:
        if f.rule_id == finding_rule_id:
            target_finding = f
            break

    if not target_finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with rule_id '{finding_rule_id}' not found in this assessment.",
        )

    wazuh, splunk = _build_siem_clients()
    svc = VerificationService(wazuh_client=wazuh, splunk_service=splunk, db=db)
    result = await svc.verify_finding(target_finding, answers)
    return result


# ---------------------------------------------------------------------------
# POST /verification/assess/{assessment_id}/roi
# ---------------------------------------------------------------------------

@router.post(
    "/assess/{assessment_id}/roi",
    response_model=PortfolioROISchema,
    summary="Calculate Liability-to-ROI",
    description=(
        "Maps every remediation action for the assessment to a specific "
        "time-saved/cost-saved metric using industry benchmarks."
    ),
)
async def calculate_assessment_roi(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    assessment = _get_assessment_or_404(assessment_id, user, db)
    answers = _reconstruct_answers(assessment)

    scores = calculate_scores(answers)
    engine = FindingsEngine()
    findings = engine.evaluate(answers, scores)

    if not findings:
        from datetime import datetime, timezone
        return PortfolioROISchema(
            total_cost_avoided_usd=0,
            total_remediation_cost_usd=0,
            total_roi_percentage=0,
            total_hours_saved=0,
            aggregate_liability_reduction_pct=0,
            items=[],
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    roi_engine = LiabilityROIEngine()
    return roi_engine.calculate_portfolio_roi(findings)


# ---------------------------------------------------------------------------
# POST /verification/forensic-trail
# ---------------------------------------------------------------------------

class ForensicTrailRequest(BaseModel):
    """Request body for forensic trail generation."""
    assessment_id: Optional[str] = None
    organization_id: Optional[str] = None
    siem_log_dump: dict = {}
    current_ghi_score: float
    previous_ghi_score: Optional[float] = None


@router.post(
    "/forensic-trail",
    summary="Generate Forensic Audit Trail",
    description=(
        "Analyzes the provided SIEM log dump, correlates with the GHI score, "
        "and generates a JSON audit trail that justifies the score change "
        "without using LLM subjectivity."
    ),
)
async def generate_forensic_trail(
    payload: ForensicTrailRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    from app.services.forensic_trail import get_forensic_trail_agent

    # If assessment_id provided, load findings
    findings_data = []
    if payload.assessment_id:
        assessment = _get_assessment_or_404(payload.assessment_id, user, db)
        answers = _reconstruct_answers(assessment)
        scores = calculate_scores(answers)
        engine = FindingsEngine()
        findings = engine.evaluate(answers, scores)

        for f in findings:
            severity_val = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            findings_data.append({
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": severity_val,
                "domain_id": f.domain_id,
                "evidence": f.evidence,
            })

    agent = get_forensic_trail_agent()
    trail = agent.execute_forensic_trail(
        siem_log_dump=payload.siem_log_dump,
        current_ghi_score=payload.current_ghi_score,
        previous_ghi_score=payload.previous_ghi_score,
        findings=findings_data,
        assessment_id=payload.assessment_id,
        organization_id=payload.organization_id,
    )

    return trail


# ---------------------------------------------------------------------------
# GET /verification/org/{org_id}/mttr-summary
# ---------------------------------------------------------------------------

@router.get(
    "/org/{org_id}/mttr-summary",
    response_model=MTTRExecutiveSummarySchema,
    summary="Executive MTTR Risk-Reduction Summary",
    description=(
        "Generates a board-ready executive summary focusing on Mean Time to "
        "Remediation (MTTR) and financial impact. All metrics are derived "
        "deterministically from audit logs and assessment history."
    ),
)
async def get_mttr_summary(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    from app.models.organization import Organization
    from app.services.mttr_analyst import get_mttr_analyst_agent

    org = (
        db.query(Organization)
        .filter(Organization.id == org_id, Organization.owner_uid == user.uid)
        .first()
    )
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    agent = get_mttr_analyst_agent()
    result = agent.generate_executive_summary(
        db_session=db,
        org_id=org_id,
        org_name=org.name,
    )
    return result
