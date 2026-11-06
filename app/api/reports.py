"""
Reports API routes.

Provides persistent report management with tenant isolation.
All endpoints enforce access control using Firebase user UID.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from io import BytesIO
from app.db.database import get_db
from app.core.logging import event_logger
from app.core.auth import require_auth, User
from app.core.demo_guard import require_writable
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportDetailResponse,
    ReportListResponse,
    ReportType,
)
from app.services.report import ReportService
from app.services.assessment import AssessmentService
from app.reports.pdf import ProfessionalPDFGenerator
from app.models.organization import Organization
from app.models.report import Report
import json

router = APIRouter()


def get_report_service(db: Session, user: User) -> ReportService:
    """Get report service with tenant isolation."""
    return ReportService(db, owner_uid=user.uid)


# ----- Report CRUD -----

@router.get(
    "",
    response_model=ReportListResponse,
    summary="List Reports",
    description="List all reports owned by the authenticated user with optional filters.",
    responses={
        200: {"description": "List of reports"},
        401: {"description": "Authentication required"}
    }
)
async def list_reports(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List reports owned by the current user."""
    service = get_report_service(db, user)
    reports, total = service.list(
        organization_id=organization_id,
        assessment_id=assessment_id,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    
    # Enrich with org/assessment names
    result = []
    for report in reports:
        result.append({
            "id": report.id,
            "owner_uid": report.owner_uid,
            "organization_id": report.organization_id,
            "organization_name": report.organization.name if report.organization else None,
            "assessment_id": report.assessment_id,
            "assessment_title": report.assessment.title if report.assessment else None,
            "report_type": report.report_type,
            "title": report.title,
            "format": getattr(report, "format", None) or "pdf",
            "status": getattr(report, "status", None) or "completed",
            "overall_score": report.overall_score,
            "maturity_level": report.maturity_level,
            "maturity_name": report.maturity_name,
            "findings_count": report.findings_count,
            "created_at": report.created_at,
        })
    
    return {"reports": result, "total": total}


@router.get(
    "/{report_id}",
    summary="Get Report Details",
    description="Get report metadata and snapshot data (must be owned by current user).",
    responses={
        200: {"description": "Report details with snapshot"},
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"}
    }
)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get report with full snapshot data."""
    service = get_report_service(db, user)
    result = service.get_with_snapshot(report_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    
    return result


@router.get(
    "/{report_id}/download",
    summary="Download Report PDF",
    description="Download the PDF file for a report (must be owned by current user).",
    responses={
        200: {"description": "PDF report file", "content": {"application/pdf": {}}},
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"}
    }
)
async def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Download a report.

    Dispatches on ``report_type``:
      - ``executive_pdf`` with an ``assessment_id``: legacy questionnaire PDF
        (``ProfessionalPDFGenerator``), delivered via a signed GCS URL.
      - every template report (board_story, boss_report, msp_summary, ...):
        rendered server-side from the stored readiness snapshot and streamed
        directly as PDF / JSON / CSV bytes.
    """
    service = get_report_service(db, user)
    result = service.get_with_snapshot(report_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )

    is_legacy_executive = (
        result["report_type"] == ReportType.EXECUTIVE_PDF.value
        and bool(result.get("assessment_id"))
        and (result.get("snapshot") or {}).get("template") is None
    )
    if not is_legacy_executive:
        return _stream_template_report(db, user, result)
    
    # Get assessment detail for PDF generation
    assessment_service = AssessmentService(db, owner_uid=user.uid)
    assessment_detail = assessment_service.get_detail(result["assessment_id"])
    
    if not assessment_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found for report: {report_id}"
        )

    # Enrich payload with summary analytics for executive risk page.
    assessment_summary = assessment_service.get_summary(result["assessment_id"])
    if assessment_summary:
        for field in ("analytics", "framework_mapping", "detailed_roadmap", "roadmap"):
            if field in assessment_summary:
                assessment_detail[field] = assessment_summary[field]

    # Generate PDF using professional generator
    generator = ProfessionalPDFGenerator()
    pdf_content = generator.generate(assessment_detail)
    
    # Log download
    event_logger.report_generated(assessment_id=result["assessment_id"], format="pdf")
    
    # Create filename
    org_name = (result.get("organization_name") or "unknown").replace(" ", "_")
    filename = f"ResilAI_Report_{org_name}_{report_id[:8]}.pdf"
    
    # Upload to GCS and generate signed URL
    from app.core.gcs import upload_and_sign_pdf
    signed_url = upload_and_sign_pdf(pdf_content, filename)
    
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure download URL."
        )
        
    return {"url": signed_url}


def _stream_template_report(db: Session, user: User, result: dict) -> StreamingResponse:
    """Render a template report from its stored snapshot (regenerating the
    readiness data when the stored snapshot predates the template schema)."""
    from app.reports.readiness_source import build_template_snapshot
    from app.reports.templates import TEMPLATE_IDS, render

    report_type = result["report_type"]
    if report_type not in TEMPLATE_IDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown report template: {report_type}",
        )

    snapshot = result.get("snapshot") or {}
    if not snapshot.get("readiness"):
        org = db.query(Organization).filter(Organization.id == result["organization_id"]).first()
        snapshot = build_template_snapshot(
            db,
            result["organization_id"],
            report_type,
            fmt=result.get("format") or "pdf",
            org=org,
            owner_uid=user.uid,
            assessment_id=result.get("assessment_id"),
        )
        try:
            report = db.query(Report).filter(Report.id == result["id"]).first()
            if report:
                report.snapshot = json.dumps(snapshot, default=str)
                report.overall_score = snapshot.get("overall_score")
                report.findings_count = snapshot.get("findings_count", 0)
                db.commit()
        except Exception:  # pragma: no cover - persistence of regenerated snapshot is best-effort
            db.rollback()

    fmt = result.get("format") or snapshot.get("format") or "pdf"
    content, media_type, ext = render(report_type, fmt, snapshot)
    event_logger.report_generated(assessment_id=result.get("assessment_id") or result["organization_id"], format=ext)

    org_name = (result.get("organization_name") or snapshot.get("organization", {}).get("name") or "org")
    safe_org = "".join(ch if ch.isalnum() else "_" for ch in org_name)[:40]
    filename = f"ResilAI_{report_type}_{safe_org}_{result['id'][:8]}.{ext}"
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Report",
    description="Delete a report (must be owned by current user).",
    responses={
        204: {"description": "Report deleted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"}
    }
)
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable)
):
    """Delete a report."""
    service = get_report_service(db, user)
    success = service.delete(report_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    
    return None
