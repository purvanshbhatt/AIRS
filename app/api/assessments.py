"""
Assessment API routes.

All endpoints enforce tenant isolation using Firebase user UID.
Users can only access their own assessments and related data.

In demo mode (ENV=demo), write operations are blocked with 403 Forbidden.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.core.demo_guard import require_writable
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from io import BytesIO
from app.db.database import get_db
from app.db.firestore import (
    firestore_get_assessment_lifecycle,
    firestore_set_assessment_lifecycle,
    firestore_get_finding_tracking_map,
    firestore_save_finding_tracking,
)
from app.core.logging import event_logger
from app.core.auth import require_auth, User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentDetail,
    AssessmentSummary,
    AssessmentSummaryResponse,
    AssessmentStartRequest,
    AssessmentSubmitResponse,
    AssessmentRerunRequest,
    AnswerBulkSubmit,
    AnswerResponse,
    ComputeScoreResponse,
    FindingCreate,
    FindingUpdate,
    FindingResponse,
    ScoreResponse,
)
from app.schemas.report import ReportCreate, ReportResponse
from app.services.assessment import AssessmentService
from app.services.report import ReportService
from app.services.integrations import dispatch_assessment_scored_webhooks
from app.services.audit import record_audit_event
from app.services.demo_seed import ensure_demo_seed_data
from app.services.compliance_export import export_compliance_report_to_gcs
from app.services.smart_annotations import generate_annotations
from app.reports.pdf import ProfessionalPDFGenerator
from app.models.assessment import Assessment
from app.models.finding import Finding, Severity as FindingSeverity
from app.models.roadmap_item import RoadmapItem
from app.schemas.integrations import (
    RoadmapTrackerItemCreate,
    RoadmapTrackerItemUpdate,
    RoadmapTrackerItemResponse,
    RoadmapTrackerListResponse,
)

router = APIRouter()


def get_assessment_service(db: Session, user: User) -> AssessmentService:
    """Get assessment service with tenant isolation."""
    return AssessmentService(db, owner_uid=user.uid if user else None)


def get_report_service(db: Session, user: User) -> ReportService:
    """Get report service with tenant isolation."""
    return ReportService(db, owner_uid=user.uid)


def _severity_rank(severity: str) -> int:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(str(severity).lower(), 4)


def _build_siem_export_payload(summary: Dict[str, Any]) -> Dict[str, Any]:
    findings_export = []
    for finding in summary.get("findings", []):
        refs = finding.get("framework_refs") or {}
        findings_export.append(
            {
                "severity": finding.get("severity"),
                "category": finding.get("domain"),
                "title": finding.get("title"),
                "description": finding.get("description") or finding.get("evidence"),
                "mitre_refs": refs.get("mitre", []),
                "cis_refs": refs.get("cis", []),
                "owasp_refs": refs.get("owasp", []),
                "remediation": finding.get("recommendation"),
            }
        )

    findings_export = sorted(
        findings_export,
        key=lambda item: _severity_rank(str(item.get("severity", ""))),
    )

    return {
        "organization": summary.get("organization_name"),
        "assessment_id": summary.get("id"),
        "score": summary.get("overall_score"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings": findings_export,
    }


def _public_assessment_status(assessment: Assessment) -> str:
    """Return cloud lifecycle status with Firestore metadata override."""
    lifecycle = firestore_get_assessment_lifecycle(assessment.id)
    cloud_status = lifecycle.get("status")
    if isinstance(cloud_status, str) and cloud_status in {"submitted", "scored"}:
        return cloud_status
    return str(getattr(assessment.status, "value", assessment.status))


# ----- Assessment CRUD -----

@router.post(
    "/{organization_id}/start",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Assessment",
    description="Create and immediately start an in-progress assessment for an organization.",
)
async def start_assessment(
    organization_id: str,
    data: AssessmentStartRequest = AssessmentStartRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = get_assessment_service(db, user)
    try:
        assessment = service.start(
            organization_id=organization_id,
            title=data.title,
            version=data.version,
        )
        record_audit_event(
            db=db,
            org_id=organization_id,
            action="assessment.started",
            actor=user.uid,
        )
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment",
    description="Create a new AI readiness assessment for an organization owned by the authenticated user.",
    responses={
        201: {"description": "Assessment created successfully"},
        400: {"description": "Invalid request (e.g., organization not found or not owned by user)"},
        401: {"description": "Authentication required"}
    }
)
async def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Create a new assessment for an organization owned by the current user."""
    service = get_assessment_service(db, user)
    try:
        assessment = service.create(data)
        event_logger.assessment_created(
            assessment_id=assessment.id,
            organization_id=assessment.organization_id,
            title=assessment.title or ""
        )
        record_audit_event(
            db=db,
            org_id=assessment.organization_id,
            action="assessment.created",
            actor=user.uid,
        )
        return assessment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[AssessmentSummary])
async def list_assessments(
    organization_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List assessments owned by the current user, optionally filtered by organization."""
    ensure_demo_seed_data(db, user.uid if user else None)
    service = get_assessment_service(db, user)
    assessments = service.get_all(organization_id=organization_id, skip=skip, limit=limit)
    
    # Add organization name to summaries
    result = []
    for a in assessments:
        summary = {
            "id": a.id,
            "organization_id": a.organization_id,
            "organization_name": a.organization.name if a.organization else None,
            "title": a.title,
            "status": _public_assessment_status(a),
            "overall_score": a.overall_score,
            "maturity_level": a.maturity_level,
            "created_at": a.created_at
        }
        result.append(summary)
    
    return result


@router.get("/{organization_id}/history", response_model=List[AssessmentSummary])
async def get_assessment_history(
    organization_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Return assessment history/version timeline for an organization."""
    service = get_assessment_service(db, user)
    try:
        assessments = service.get_history(organization_id, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return [
        {
            "id": a.id,
            "organization_id": a.organization_id,
            "organization_name": a.organization.name if a.organization else None,
            "title": a.title,
            "status": _public_assessment_status(a),
            "overall_score": a.overall_score,
            "maturity_level": a.maturity_level,
            "created_at": a.created_at,
        }
        for a in assessments
    ]


@router.get("/{assessment_id}", response_model=AssessmentDetail)
async def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get assessment detail (must be owned by current user)."""
    service = get_assessment_service(db, user)
    result = service.get_detail(assessment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    lifecycle = firestore_get_assessment_lifecycle(assessment_id)
    cloud_status = lifecycle.get("status")
    if isinstance(cloud_status, str) and cloud_status in {"submitted", "scored"}:
        result["status"] = cloud_status
    return result


@router.get(
    "/{assessment_id}/summary",
    response_model=AssessmentSummaryResponse,
    summary="Get Assessment Summary",
    description="""Get comprehensive assessment summary for executive dashboard (must be owned by current user). 
Includes scores, findings, roadmap, baseline comparisons, and optional AI-generated narratives.""",
    responses={
        200: {"description": "Complete assessment summary with all metrics and narratives"},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def get_assessment_summary(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get comprehensive assessment summary for executive dashboard (owned by current user)."""
    service = get_assessment_service(db, user)
    result = service.get_summary(assessment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if result.get("overall_score") == 0 and not result.get("domain_scores"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )
    
    # Log summary fetch
    event_logger.summary_fetched(
        assessment_id=assessment_id,
        llm_used=result.get("executive_summary_text") is not None
    )
    lifecycle = firestore_get_assessment_lifecycle(assessment_id)
    cloud_status = lifecycle.get("status")
    if isinstance(cloud_status, str) and cloud_status in {"submitted", "scored"}:
        result["status"] = cloud_status
    
    return result


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Update an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    assessment = service.update(assessment_id, data)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Archive an assessment (soft delete - must be owned by current user)."""
    service = get_assessment_service(db, user)
    if not service.archive(assessment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )


# ----- Answers -----

@router.post(
    "/{assessment_id}/answers",
    response_model=List[AnswerResponse],
    summary="Submit Answers",
    description="Submit or update answers for an assessment (must be owned by current user). Uses upsert semantics.",
    responses={
        200: {"description": "Answers submitted successfully"},
        404: {"description": "Assessment not found"}
    }
)
async def submit_answers(
    assessment_id: str,
    data: AnswerBulkSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Submit answers for an assessment owned by current user."""
    service = get_assessment_service(db, user)
    try:
        answers = service.submit_answers(assessment_id, data.answers)
        event_logger.answers_submitted(
            assessment_id=assessment_id,
            answer_count=len(answers)
        )
        return answers
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{assessment_id}/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Transition an in-progress assessment to submitted state."""
    service = get_assessment_service(db, user)
    try:
        assessment = service.submit(assessment_id)
        submitted_at = datetime.now(timezone.utc).isoformat()
        firestore_set_assessment_lifecycle(assessment_id, "submitted", submitted_at=submitted_at)
        submitted_at = assessment.updated_at or datetime.now(timezone.utc)
        return {
            "assessment_id": assessment.id,
            "status": "submitted",
            "submitted_at": submitted_at,
        }
    except ValueError as e:
        detail = str(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in detail.lower() else status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


@router.post("/{assessment_id}/rerun", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def rerun_assessment(
    assessment_id: str,
    data: AssessmentRerunRequest = AssessmentRerunRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Create a new assessment iteration from an existing assessment."""
    service = get_assessment_service(db, user)
    try:
        assessment = service.rerun(
            assessment_id,
            title=data.title,
            clone_answers=data.clone_answers,
        )
        record_audit_event(
            db=db,
            org_id=assessment.organization_id,
            action="assessment.rerun_created",
            actor=user.uid,
        )
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{assessment_id}/answers", response_model=List[AnswerResponse])
async def get_answers(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all answers for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return service.get_answers(assessment_id)


# ----- Scoring -----

@router.post(
    "/{assessment_id}/score",
    response_model=ComputeScoreResponse,
    summary="Compute Score",
    description="Calculate and persist scores and findings for an assessment (must be owned by current user).",
    responses={
        200: {"description": "Scores computed and persisted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def compute_score(
    assessment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Compute and persist scores and findings for an assessment owned by current user."""
    service = get_assessment_service(db, user)
    try:
        result = service.compute_score(assessment_id)
        firestore_set_assessment_lifecycle(
            assessment_id,
            "scored",
            scored_at=datetime.now(timezone.utc).isoformat(),
        )
        
        # Log scoring event
        event_logger.scoring_executed(
            assessment_id=assessment_id,
            overall_score=result["overall_score"],
            findings_count=result["findings_count"]
        )
        
        # Convert Score objects to response format
        domain_scores = []
        for score in result["domain_scores"]:
            domain_scores.append({
                "id": score.id,
                "domain_id": score.domain_id,
                "domain_name": score.domain_name,
                "score": score.score,
                "max_score": score.max_score,
                "weight": score.weight,
                "weighted_score": score.weighted_score,
                "raw_points": score.raw_points,
                "max_raw_points": score.max_raw_points,
                "created_at": score.created_at
            })
        
        # Fire integration webhooks in background (non-blocking)
        assessment = service.get(assessment_id)
        if assessment:
            critical_findings = (
                db.query(Finding)
                .filter(
                    Finding.assessment_id == assessment_id,
                    Finding.severity == FindingSeverity.CRITICAL,
                )
                .count()
            )
            webhook_payload = {
                "event_type": "assessment.scored",
                "org_id": assessment.organization_id,
                "assessment_id": assessment_id,
                "score": result["overall_score"],
                "critical_findings": critical_findings,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            background_tasks.add_task(
                dispatch_assessment_scored_webhooks,
                assessment.organization_id,
                webhook_payload,
            )
            background_tasks.add_task(
                export_compliance_report_to_gcs,
                assessment_id,
                user.uid if user else None,
            )
            record_audit_event(
                db=db,
                org_id=assessment.organization_id,
                action="assessment.score_generated",
                actor=user.uid,
            )

        return {
            "assessment_id": result["assessment_id"],
            "overall_score": result["overall_score"],
            "maturity_level": result["maturity_level"],
            "maturity_name": result["maturity_name"],
            "domain_scores": domain_scores,
            "findings_count": result["findings_count"],
            "high_severity_count": result["high_severity_count"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{assessment_id}/scores", response_model=List[ScoreResponse])
async def get_scores(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all domain scores for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return assessment.scores


# ----- Findings -----

@router.get("/{assessment_id}/findings", response_model=List[FindingResponse])
async def get_findings(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all findings for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    findings = service.get_findings(assessment_id)
    tracking_map = firestore_get_finding_tracking_map(assessment_id)

    merged: List[Dict[str, Any]] = []
    for finding in findings:
        row = {
            "id": finding.id,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "status": finding.status,
            "domain_id": finding.domain_id,
            "domain_name": finding.domain_name,
            "question_id": finding.question_id,
            "evidence": finding.evidence,
            "recommendation": finding.recommendation,
            "priority": finding.priority,
            "nist_function": finding.nist_function,
            "nist_category": finding.nist_category,
            "created_at": finding.created_at,
        }
        tracking = tracking_map.get(finding.id, {})
        for key in ("owner", "due_date", "control_id", "framework_tag"):
            if key in tracking:
                row[key] = tracking.get(key)
        merged.append(row)

    return merged


@router.post("/{assessment_id}/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def add_finding(
    assessment_id: str,
    data: FindingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Add a manual finding to an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    try:
        finding = service.add_finding(assessment_id, data)
        background_tasks.add_task(
            export_compliance_report_to_gcs,
            assessment_id,
            user.uid if user else None,
        )
        return finding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{assessment_id}/findings/{finding_id}", response_model=FindingResponse)
async def update_finding(
    assessment_id: str,
    finding_id: str,
    data: FindingUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Update finding lifecycle details such as status, owner, due date, and control mapping."""
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}",
        )

    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.assessment_id == assessment_id)
        .first()
    )
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    update_data = data.model_dump(exclude_unset=True)

    # Guard invalid lifecycle transitions.
    if "status" in update_data:
        current = str(finding.status.value if hasattr(finding.status, "value") else finding.status)
        requested = str(update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"])
        transitions = {
            "open": {"in_progress", "resolved", "accepted"},
            "in_progress": {"open", "resolved", "accepted"},
            "resolved": {"open"},
            "accepted": {"open"},
        }
        if requested != current and requested not in transitions.get(current, set()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid finding status transition: {current} -> {requested}",
            )

    db_updates: Dict[str, Any] = {}
    for key in ("title", "description", "severity", "status", "evidence", "recommendation"):
        if key in update_data:
            db_updates[key] = update_data[key]

    for key, value in db_updates.items():
        setattr(finding, key, value)

    db.commit()
    db.refresh(finding)

    tracking_updates: Dict[str, Any] = {}
    for key in ("owner", "due_date", "control_id", "framework_tag"):
        if key in update_data:
            tracking_updates[key] = update_data[key]
    if tracking_updates:
        firestore_save_finding_tracking(assessment_id, finding_id, tracking_updates)

    merged = {
        "id": finding.id,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity,
        "status": finding.status,
        "domain_id": finding.domain_id,
        "domain_name": finding.domain_name,
        "question_id": finding.question_id,
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
        "priority": finding.priority,
        "nist_function": finding.nist_function,
        "nist_category": finding.nist_category,
        "created_at": finding.created_at,
    }
    merged.update(tracking_updates)

    background_tasks.add_task(
        export_compliance_report_to_gcs,
        assessment_id,
        user.uid if user else None,
    )

    return merged


@router.post("/{assessment_id}/findings/annotate")
async def annotate_findings(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """
    Generate AI-powered executive context annotations for findings.
    
    Uses Gemini Flash to produce 1-sentence business-context blurbs.
    Falls back to deterministic templates when LLM is unavailable.
    """
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}",
        )

    findings = service.get_findings(assessment_id)
    if not findings:
        return {"annotations": [], "llm_generated": False}

    findings_dicts = [
        {
            "title": f.title,
            "severity": str(f.severity.value) if hasattr(f.severity, "value") else str(f.severity),
            "domain": f.domain_name or f.domain_id or "",
            "nist_category": f.nist_category or "",
            "recommendation": f.recommendation or "",
        }
        for f in findings
    ]

    result = await generate_annotations(findings_dicts)
    return result


# ----- Reports -----

@router.post(
    "/{assessment_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and Save Report",
    description="Generate a new report for the assessment and save it persistently. The report captures a snapshot of the assessment data at generation time.",
    responses={
        201: {"description": "Report created successfully"},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def create_report(
    assessment_id: str,
    data: ReportCreate = ReportCreate(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Generate and save a report for an assessment owned by current user."""
    assessment_service = get_assessment_service(db, user)
    assessment_detail = assessment_service.get_detail(assessment_id)
    
    if not assessment_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if assessment_detail.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )
    
    # Create persistent report
    report_service = get_report_service(db, user)
    try:
        report = report_service.create(assessment_id, data)
        
        # Log report creation
        event_logger.report_generated(assessment_id=assessment_id, format="pdf")
        
        return {
            "id": report.id,
            "owner_uid": report.owner_uid,
            "organization_id": report.organization_id,
            "organization_name": report.organization.name if report.organization else None,
            "assessment_id": report.assessment_id,
            "assessment_title": report.assessment.title if report.assessment else None,
            "report_type": report.report_type,
            "title": report.title,
            "overall_score": report.overall_score,
            "maturity_level": report.maturity_level,
            "maturity_name": report.maturity_name,
            "findings_count": report.findings_count,
            "created_at": report.created_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{assessment_id}/report",
    summary="Generate PDF Report (Legacy)",
    description="Generate and download a professional PDF report for the assessment (must be owned by current user). Consider using POST /assessments/{id}/reports to create a persistent report.",
    responses={
        200: {"description": "PDF report file", "content": {"application/pdf": {}}},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def generate_report(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Generate PDF report for an assessment owned by current user."""
    service = get_assessment_service(db, user)
    result = service.get_detail(assessment_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if result.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )

    # Enrich report payload with analytics/mapping data for executive summary pages.
    summary = service.get_summary(assessment_id)
    if summary:
        for field in ("analytics", "framework_mapping", "detailed_roadmap", "roadmap"):
            if field in summary:
                result[field] = summary[field]

    # Generate PDF using professional generator
    generator = ProfessionalPDFGenerator()
    pdf_content = generator.generate(result)
    
    # Log report generation
    event_logger.report_generated(assessment_id=assessment_id, format="pdf")
    
    # Create filename
    org_name = result.get("organization_name", "unknown").replace(" ", "_")
    filename = f"ResilAI_Report_{org_name}_{assessment_id[:8]}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get(
    "/{assessment_id}/executive-summary",
    summary="Download Executive Risk Summary (1-page)",
    description="Generate and download a one-page executive risk summary PDF for the assessment.",
    responses={
        200: {"description": "Executive summary PDF", "content": {"application/pdf": {}}},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"},
    },
)
async def download_executive_summary(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = get_assessment_service(db, user)
    detail = service.get_detail(assessment_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}",
        )
    if detail.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first.",
        )

    summary = service.get_summary(assessment_id)
    payload = summary or detail

    generator = ProfessionalPDFGenerator()
    pdf_content = generator.generate_executive_summary_page(payload)

    org_name = str(payload.get("organization_name", "unknown")).replace(" ", "_")
    filename = f"{payload.get('product', {}).get('name', 'ResilAI')}_Executive_Risk_Summary_{org_name}_{assessment_id[:8]}.pdf"

    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/{assessment_id}/export",
    summary="Export Findings for SIEM",
    description="Export assessment findings in a SIEM-friendly JSON schema.",
)
async def export_assessment_for_siem(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = get_assessment_service(db, user)
    summary = service.get_summary(assessment_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}",
        )
    return _build_siem_export_payload(summary)


def _resolve_assessment_for_tracker(
    db: Session,
    service: AssessmentService,
    candidate_id: str,
) -> Optional[Assessment]:
    """
    Backward-compatible resolver for roadmap tracker routes.

    Accepts either:
    - assessment_id (preferred)
    - organization_id (legacy frontend behavior)
    """
    assessment = service.get(candidate_id)
    if assessment:
        return assessment

    return (
        service._base_query()
        .filter(Assessment.organization_id == candidate_id)
        .order_by(Assessment.created_at.desc())
        .first()
    )


@router.get("/{assessment_id}/roadmap", response_model=RoadmapTrackerListResponse)
async def list_roadmap_items(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = get_assessment_service(db, user)
    assessment = _resolve_assessment_for_tracker(db, service, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    items = (
        db.query(RoadmapItem)
        .filter(
            RoadmapItem.assessment_id == assessment.id,
            RoadmapItem.owner_uid == user.uid,
        )
        .order_by(RoadmapItem.created_at.desc())
        .all()
    )
    return {"items": items, "total": len(items)}


@router.post("/{assessment_id}/roadmap", response_model=RoadmapTrackerItemResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap_item(
    assessment_id: str,
    data: RoadmapTrackerItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = get_assessment_service(db, user)
    assessment = _resolve_assessment_for_tracker(db, service, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    item = RoadmapItem(
        assessment_id=assessment.id,
        owner_uid=user.uid,
        title=data.title,
        description=data.description,
        phase=data.phase,
        status=data.status,
        priority=data.priority,
        owner=data.owner,
        due_date=data.due_date,
        notes=data.notes,
        effort=data.effort,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{assessment_id}/roadmap/{item_id}", response_model=RoadmapTrackerItemResponse)
async def update_roadmap_item(
    assessment_id: str,
    item_id: str,
    data: RoadmapTrackerItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = get_assessment_service(db, user)
    assessment = _resolve_assessment_for_tracker(db, service, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    item = (
        db.query(RoadmapItem)
        .filter(
            RoadmapItem.id == item_id,
            RoadmapItem.assessment_id == assessment.id,
            RoadmapItem.owner_uid == user.uid,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{assessment_id}/roadmap/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap_item(
    assessment_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = get_assessment_service(db, user)
    assessment = _resolve_assessment_for_tracker(db, service, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    item = (
        db.query(RoadmapItem)
        .filter(
            RoadmapItem.id == item_id,
            RoadmapItem.assessment_id == assessment.id,
            RoadmapItem.owner_uid == user.uid,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")
    db.delete(item)
    db.commit()
