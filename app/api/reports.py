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
    """Download report as PDF."""
    service = get_report_service(db, user)
    result = service.get_with_snapshot(report_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    
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
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
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
