"""
Organization API routes.

All endpoints enforce tenant isolation using Firebase user UID.
Users can only access their own organizations.

In demo mode (ENV=demo), write operations are blocked.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.core.logging import event_logger
from app.core.auth import require_auth, User
from app.core.demo_guard import require_writable
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithAssessments
)
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.schemas.audit import AuditEventResponse
from app.models.audit_event import AuditEvent
from app.services.organization import OrganizationService
from app.services.assessment import AssessmentService
from app.services.audit import record_audit_event
from app.services.demo_seed import ensure_demo_seed_data
from app.models.assessment import Assessment
from app.models.roadmap_item import RoadmapItem
from app.schemas.integrations import RoadmapTrackerListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def get_org_service(db: Session, user: User) -> OrganizationService:
    """Get organization service with tenant isolation."""
    return OrganizationService(db, owner_uid=user.uid if user else None)


def get_assessment_service(db: Session, user: User) -> AssessmentService:
    """Get assessment service with tenant isolation."""
    return AssessmentService(db, owner_uid=user.uid if user else None)


class OrganizationAssessmentCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    version: str | None = Field(default="1.0.0", max_length=20)


def _to_remediation_status(status: str | None) -> str:
    value = (status or "not_started").lower()
    if value in {"open", "not_started", "todo"}:
        return "open"
    if value in {"in_progress", "doing"}:
        return "in_progress"
    if value in {"resolved", "completed", "done"}:
        return "resolved"
    return "open"


def _to_remediation_priority(priority: str | None) -> str:
    value = (priority or "medium").lower()
    if value in {"critical", "high", "medium", "low"}:
        return value
    return "medium"


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization owned by the authenticated user.",
    responses={
        201: {"description": "Organization created successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Demo mode - write operations disabled"}
    }
)
async def create_organization(
    request: Request,
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Create a new organization owned by the current user."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(
        f"[{request_id}] POST /api/orgs - Creating organization: name={data.name}, "
        f"user={user.uid}"
    )
    
    try:
        service = get_org_service(db, user)
        org = service.create(data)
        event_logger.organization_created(organization_id=org.id, name=org.name)
        logger.info(f"[{request_id}] POST /api/orgs -> 201 Created: org_id={org.id}")
        return org
    except Exception as e:
        logger.error(
            f"[{request_id}] POST /api/orgs -> 500 Error: {type(e).__name__}: {str(e)}"
        )
        raise


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List organizations owned by the current user."""
    # NOTE: ensure_demo_seed_data was removed from this endpoint.
    # Demo seeding ONLY runs when settings.is_demo_mode is True,
    # but invoking it on every real customer org list request is
    # architecturally wrong. Demo seeding belongs in the demo
    # environment startup, not in production API paths.
    service = get_org_service(db, user)
    return service.get_all(skip=skip, limit=limit)


@router.get(
    "/{org_id}/remediations",
    response_model=RoadmapTrackerListResponse,
    summary="List Organization Remediations",
    description="Return remediation/action items across assessments for the selected organization.",
)
async def list_org_remediations(
    org_id: str,
    limit: int = 200,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Organization-scoped remediations feed built from roadmap tracker items."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )

    safe_limit = max(1, min(limit, 500))
    items = (
        db.query(RoadmapItem)
        .join(Assessment, Assessment.id == RoadmapItem.assessment_id)
        .filter(
            Assessment.organization_id == org_id,
            RoadmapItem.owner_uid == user.uid,
        )
        .order_by(RoadmapItem.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    normalized = []
    for item in items:
        payload = {
            "id": item.id,
            "assessment_id": item.assessment_id,
            "title": item.title,
            "description": item.description,
            "phase": item.phase,
            "status": _to_remediation_status(item.status),
            "priority": _to_remediation_priority(item.priority),
            "owner": item.owner,
            "due_date": item.due_date,
            "notes": item.notes,
            "effort": item.effort,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        normalized.append(payload)

    return {"items": normalized, "total": len(normalized)}


@router.post(
    "/{org_id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization Assessment",
    description="Create a brand new assessment scoped to the organization. Previous assessments are preserved.",
)
async def create_organization_assessment(
    org_id: str,
    data: OrganizationAssessmentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Create a new append-only assessment for an organization owned by the current user."""
    service = get_assessment_service(db, user)

    # Org id comes from path and must always be the source of truth.
    assessment_payload = AssessmentCreate(
        organization_id=org_id,
        title=data.title,
        version=data.version,
    )

    try:
        assessment = service.create(assessment_payload)
        event_logger.assessment_created(
            assessment_id=assessment.id,
            organization_id=assessment.organization_id,
            title=assessment.title or "",
        )
        record_audit_event(
            db=db,
            org_id=assessment.organization_id,
            action="assessment.created",
            actor=user.uid,
        )
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}", response_model=OrganizationWithAssessments)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get organization by ID (must be owned by current user)."""
    service = get_org_service(db, user)
    result = service.get_with_assessment_count(org_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    return result


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Update an organization (must be owned by current user). Disabled in demo mode."""
    service = get_org_service(db, user)
    org = service.update(org_id, data)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Delete an organization (must be owned by current user). Disabled in demo mode."""
    service = get_org_service(db, user)
    if not service.delete(org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )


@router.get("/{org_id}/audit", response_model=List[AuditEventResponse])
async def list_organization_audit_events(
    org_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """List recent audit events for an organization owned by the current user."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )

    safe_limit = max(1, min(limit, 500))
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.org_id == org_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(safe_limit)
        .all()
    )
    return events


# ---------------------------------------------------------------------------
# Phase 5: Analytics toggle
# ---------------------------------------------------------------------------


class AnalyticsToggleRequest(BaseModel):
    analytics_enabled: bool


@router.patch(
    "/{org_id}/analytics",
    response_model=OrganizationResponse,
    summary="Toggle Analytics",
    description=(
        "Enable or disable anonymised telemetry for an organization. "
        "When disabled, the backend suppresses telemetry events and "
        "behavioral analytics logging for all assessments belonging to "
        "this organization."
    ),
)
async def toggle_analytics(
    org_id: str,
    body: AnalyticsToggleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """PATCH /api/orgs/{org_id}/analytics — update analytics_enabled flag."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organization not found: {org_id}")

    org.analytics_enabled = body.analytics_enabled
    db.commit()
    db.refresh(org)
    return org


# ---------------------------------------------------------------------------
# Phase 7: Audit export
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Question Suggestions
# ---------------------------------------------------------------------------

from app.schemas.suggestions import SuggestedQuestion, SuggestionsResponse
from app.services.question_suggestions import get_suggestions


@router.get(
    "/{org_id}/suggested-questions",
    response_model=SuggestionsResponse,
    summary="Get Suggested Questions",
    description=(
        "Return deterministic, rule-based question suggestions for the "
        "organization based on its weakest control functions and maturity."
    ),
    responses={
        200: {"description": "Suggestions returned"},
        404: {"description": "Organization not found"},
    },
)
async def list_suggested_questions(
    org_id: str,
    max_results: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/orgs/{org_id}/suggested-questions"""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )

    # Cap max_results to avoid abuse
    safe_max = max(1, min(max_results, 30))
    suggestions = get_suggestions(db, org_id, max_results=safe_max, industry=org.industry)

    # Derive org maturity & target functions from the suggestions
    org_maturity = None
    weakest_functions: list[str] = []
    if suggestions:
        from app.services.question_suggestions import (
            _compute_function_scores_from_db,
            _org_maturity_label,
        )
        fn_scores = _compute_function_scores_from_db(db, org_id)
        all_scores = [v for v in fn_scores.values() if v > 0]
        org_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        org_maturity = _org_maturity_label(org_avg)
        ranked = sorted(fn_scores.items(), key=lambda x: x[1])
        threshold = ranked[0][1] + 10.0
        weakest_functions = [fn for fn, sc in ranked if sc <= threshold]

    return SuggestionsResponse(
        suggestions=suggestions,
        total_count=len(suggestions),
        org_maturity=org_maturity,
        weakest_functions=weakest_functions or None,
    )


@router.get(
    "/{org_id}/audit/export",
    summary="Export Audit Trail",
    description="Download all audit events for an organization as a JSON file.",
)
async def export_audit_trail(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/orgs/{org_id}/audit/export — downloadable JSON audit log."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organization not found: {org_id}")

    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.org_id == org_id)
        .order_by(AuditEvent.timestamp.asc())
        .all()
    )

    payload = {
        "organization_id": org_id,
        "organization_name": org.name,
        "exported_events": len(events),
        "events": [
            {
                "id": e.id,
                "action": e.action,
                "actor": e.actor,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }
    json_bytes = json.dumps(payload, indent=2).encode("utf-8")
    filename = f"audit_{org_id[:8]}.json"
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─────────────────────────────────────────────────────────────────────
# Organization-Scoped Reports
# ─────────────────────────────────────────────────────────────────────

class OrgReportCreateRequest(BaseModel):
    """Request to generate a report for an organization."""
    assessment_id: str = Field(..., description="Assessment ID to generate report for")
    title: str | None = Field(None, max_length=255)


@router.post(
    "/{org_id}/reports",
    status_code=status.HTTP_201_CREATED,
    summary="Generate Organization Report",
    description="Generate a new executive report for the organization.",
    responses={
        201: {"description": "Report created"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization or assessment not found"},
    },
)
async def create_org_report(
    org_id: str,
    body: OrgReportCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Generate a new report for an organization."""
    from app.services.report import ReportService
    from app.schemas.report import ReportCreate, ReportType

    # Verify org ownership
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    report_service = ReportService(db, owner_uid=user.uid)

    try:
        report = report_service.create(
            assessment_id=body.assessment_id,
            data=ReportCreate(title=body.title, report_type=ReportType.EXECUTIVE_PDF),
        )
        record_audit_event(db, org_id, "report.generated", user.uid)
        return {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "created_at": report.created_at,
            "status": getattr(report, "status", "completed"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(e)}},
        )


@router.get(
    "/{org_id}/reports",
    summary="List Organization Reports",
    description="List all reports for an organization owned by the current user.",
    responses={
        200: {"description": "List of reports"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization not found"},
    },
)
async def list_org_reports(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """List reports for an organization."""
    from app.services.report import ReportService

    # Verify org ownership
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    report_service = ReportService(db, owner_uid=user.uid)
    reports, total = report_service.list(organization_id=org_id)

    return {
        "reports": [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type,
                "overall_score": r.overall_score,
                "findings_count": r.findings_count,
                "created_at": r.created_at,
                "status": getattr(r, "status", "completed"),
            }
            for r in reports
        ],
        "total": total,
    }


@router.get(
    "/{org_id}/reports/{report_id}",
    summary="Get Organization Report",
    description="Get report details for an organization.",
    responses={
        200: {"description": "Report details"},
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"},
    },
)
async def get_org_report(
    org_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Get a specific report with snapshot data."""
    from app.services.report import ReportService

    # Verify org ownership
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    report_service = ReportService(db, owner_uid=user.uid)
    result = report_service.get_with_snapshot(report_id)
    if not result or result.get("organization_id") != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Report not found."}},
        )

    return result


@router.get(
    "/{org_id}/reports/{report_id}/download",
    summary="Download Organization Report",
    description="Download the report as a PDF via a signed URL.",
    responses={
        200: {"description": "Signed URL for PDF download"},
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"},
    },
)
async def download_org_report(
    org_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Download a report as PDF via signed URL."""
    from app.services.report import ReportService
    from app.services.assessment import AssessmentService
    from app.reports.pdf import ProfessionalPDFGenerator

    # Verify org ownership
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    report_service = ReportService(db, owner_uid=user.uid)
    result = report_service.get_with_snapshot(report_id)
    if not result or result.get("organization_id") != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Report not found."}},
        )

    # Get assessment data for PDF generation
    assessment_service = AssessmentService(db, owner_uid=user.uid)
    assessment_detail = assessment_service.get_detail(result["assessment_id"])

    if not assessment_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ASSESSMENT_NOT_FOUND", "message": "Assessment not found for report."}},
        )

    # Enrich with summary analytics
    assessment_summary = assessment_service.get_summary(result["assessment_id"])
    if assessment_summary:
        for field in ("analytics", "framework_mapping", "detailed_roadmap", "roadmap"):
            if field in assessment_summary:
                assessment_detail[field] = assessment_summary[field]

    # Generate PDF
    generator = ProfessionalPDFGenerator()
    pdf_content = generator.generate(assessment_detail)

    record_audit_event(db, org_id, "report.downloaded", user.uid)

    # Upload to GCS and return signed URL
    try:
        from app.core.gcs import upload_and_sign_pdf
        org_name = (org.name or "unknown").replace(" ", "_")
        filename = f"ResilAI_Report_{org_name}_{report_id[:8]}.pdf"
        signed_url = upload_and_sign_pdf(pdf_content, filename)
        if signed_url:
            return {"url": signed_url}
    except Exception as e:
        logger.warning(f"GCS upload failed, returning inline PDF: {e}")

    # Fallback: return PDF inline
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    org_name = (org.name or "unknown").replace(" ", "_")
    filename = f"ResilAI_Report_{org_name}_{report_id[:8]}.pdf"
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
