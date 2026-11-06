"""
Reports API — Board Story JSON and server-side PDF generation.

PRODUCT_MOAT invariants enforced here:
  - All numbers in the PDF body are sourced from the scoring snapshot (never fabricated client-side).
  - LLM only fills prose; it never scores.
  - PDF generation is server-side only via reportlab.
"""
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import User, get_optional_user, require_auth
from app.core.config import settings
from app.core.entitlements import require_entitlement
from app.models.organization import Organization
from app.models.assessment import Assessment
from app.services.ai_narrative import generate_board_story
from app.services.billing.entitlements import Entitlement
from app.schemas.board_story import BoardStory
from app.schemas.report import (
    GenerateReportRequest,
    GenerateReportResponse,
    ReportCreate,
    ReportFormat,
    ReportType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


# ─────────────────────────────────────────────────────────────────────────
# Template report generation
# ─────────────────────────────────────────────────────────────────────────

_executive_reports_guard = require_entitlement(Entitlement.EXECUTIVE_REPORTS)


async def _require_report_entitlement(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    """Gate generation with ``require_entitlement(Entitlement.EXECUTIVE_REPORTS)``.

    Explicit demo organizations are readable without a subscription (they
    only ever return demo telemetry), so the guard is skipped for them.
    Every other organization goes through the shared entitlement guard,
    which resolves ``org_id`` from the JSON body.
    """
    from app.reports.readiness_source import is_demo_org

    org_id: Optional[str] = None
    try:
        body = await request.json()
        if isinstance(body, dict):
            org_id = (body.get("organization_id") or body.get("org_id") or "").strip() or None
    except Exception:
        org_id = None

    if org_id and is_demo_org(db, org_id):
        return
    await _executive_reports_guard(request, user, db)


def _resolve_org_for_report(db: Session, user: User, org_id: str) -> tuple[Optional[Organization], bool]:
    """Return (org, is_demo). Raises 404 when a real org is not owned by the user."""
    from app.reports.readiness_source import is_demo_org
    from app.services.organization import OrganizationService

    demo = is_demo_org(db, org_id)
    org = OrganizationService(db, owner_uid=user.uid).get(org_id)
    if org is None and demo:
        # Demo orgs are readable by anyone; they may or may not be seeded locally.
        org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None and not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )
    return org, demo


@router.post(
    "/generate",
    response_model=GenerateReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a template report",
    responses={
        201: {"description": "Report generated and persisted"},
        401: {"description": "Authentication required"},
        402: {"description": "Subscription required"},
        404: {"description": "Organization not found"},
        422: {"description": "Unknown template or invalid payload"},
    },
)
async def generate_report(
    body: GenerateReportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _ent: None = Depends(_require_report_entitlement),
):
    """Build a server-side snapshot for ``report_type`` and persist a ``Report`` row.

    PRODUCT_MOAT: ``overall_score`` and ``findings_count`` in the response are
    read from the deterministic readiness snapshot; the client never computes
    them. The PDF/JSON/CSV is rendered on download from the stored snapshot.
    """
    from app.reports.readiness_source import build_template_snapshot
    from app.reports.templates import TEMPLATE_TITLES
    from app.services.report import ReportService

    org_id = body.resolved_org_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required.",
        )

    org, demo = _resolve_org_for_report(db, user, org_id)
    report_type = body.report_type.value
    fmt = body.format.value
    title = (body.title or "").strip() or TEMPLATE_TITLES.get(report_type, report_type)
    report_service = ReportService(db, owner_uid=user.uid)

    # Executive PDF tied to a questionnaire assessment keeps the legacy path.
    if body.report_type == ReportType.EXECUTIVE_PDF and body.assessment_id and not demo:
        try:
            report = report_service.create(
                assessment_id=body.assessment_id,
                data=ReportCreate(title=title, report_type=ReportType.EXECUTIVE_PDF),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        return GenerateReportResponse(
            id=report.id,
            title=report.title,
            report_type=report.report_type,
            format="pdf",
            status=report.status or "completed",
            created_at=report.created_at or datetime.now(timezone.utc),
            organization_id=report.organization_id,
            organization_name=org.name if org else None,
            overall_score=report.overall_score,
            findings_count=report.findings_count or 0,
        )

    try:
        snapshot = build_template_snapshot(
            db, org_id, report_type, fmt=fmt, org=org,
            owner_uid=None if demo else user.uid,
            assessment_id=body.assessment_id, demo=demo,
        )
    except Exception as exc:
        logger.exception("Snapshot build failed for org %s template %s: %s", org_id, report_type, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report snapshot could not be built from readiness data.",
        )

    org_name = (snapshot.get("organization") or {}).get("name")

    if org is None:
        # Unseeded demo org: nothing to attach a Report row to. Return a
        # stateless download link that regenerates from demo telemetry.
        now = datetime.now(timezone.utc)
        return GenerateReportResponse(
            id=f"demo-{uuid.uuid4().hex[:12]}",
            title=title,
            report_type=report_type,
            format=fmt,
            status="completed",
            created_at=now,
            organization_id=org_id,
            organization_name=org_name,
            overall_score=snapshot.get("overall_score"),
            findings_count=snapshot.get("findings_count", 0),
            persisted=False,
            download_url=f"/api/v1/reports/render?org_id={org_id}&report_type={report_type}&format={fmt}",
        )

    report = report_service.create_from_snapshot(
        organization_id=org.id,
        report_type=report_type,
        title=title,
        snapshot=snapshot,
        fmt=fmt,
        overall_score=snapshot.get("overall_score"),
        findings_count=snapshot.get("findings_count", 0),
        assessment_id=(snapshot.get("assessment") or {}).get("id") if snapshot.get("assessment") else None,
    )
    if not demo:
        try:
            from app.services.audit import record_audit_event
            record_audit_event(db, org.id, "report.generated", user.uid)
        except Exception as exc:  # pragma: no cover - audit is best-effort
            logger.debug("Audit event not recorded for report %s: %s", report.id, exc)

    return GenerateReportResponse(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        format=report.format or fmt,
        status=report.status or "completed",
        created_at=report.created_at or datetime.now(timezone.utc),
        organization_id=report.organization_id,
        organization_name=org_name,
        overall_score=report.overall_score,
        findings_count=report.findings_count or 0,
        download_url=f"/api/reports/{report.id}/download",
    )


@router.get(
    "/render",
    summary="Render a template report statelessly",
    responses={200: {"description": "Rendered report bytes"}, 401: {}, 404: {}},
)
async def render_template_report(
    org_id: str = Query(..., description="Organization ID"),
    report_type: ReportType = Query(..., description="Template id"),
    format: ReportFormat = Query(ReportFormat.PDF),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Render a template directly from live readiness data without persisting.

    Used for unseeded demo organizations (no ``Report`` row can exist) and as
    a preview. Real organizations require the authenticated owner.
    """
    from app.reports.readiness_source import build_template_snapshot, is_demo_org
    from app.reports.templates import render
    from app.services.organization import OrganizationService

    demo = is_demo_org(db, org_id)
    org = None
    if not demo:
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        org = OrganizationService(db, owner_uid=current_user.uid).get(org_id)
        if org is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    else:
        org = db.query(Organization).filter(Organization.id == org_id).first()

    snapshot = build_template_snapshot(
        db, org_id, report_type.value, fmt=format.value, org=org,
        owner_uid=None if demo or current_user is None else current_user.uid, demo=demo,
    )
    content, media_type, ext = render(report_type.value, format.value, snapshot)
    filename = f"resilai_{report_type.value}_{org_id[:12]}_{datetime.utcnow().strftime('%Y%m%d')}.{ext}"
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_summary_payload(org: Organization, assessment: Assessment | None) -> dict:
    """Build a scoring-snapshot-sourced payload. All numbers trace to the DB record."""
    overall_score = 0.0
    tier_label = "No Data"
    if assessment and assessment.overall_score is not None:
        overall_score = float(assessment.overall_score)
        if overall_score >= 80:
            tier_label = "Strong"
        elif overall_score >= 60:
            tier_label = "Good"
        elif overall_score >= 40:
            tier_label = "Needs Work"
        else:
            tier_label = "Critical"

    return {
        "organization_name": org.name,
        "overall_score": overall_score,
        "tier": {"label": tier_label},
        "domain_scores": [],
        "findings": [],
    }


@router.get("/board-story", response_model=BoardStory)
def get_board_story(
    org_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
):
    """
    Get the Board Story (Executive Narrative + Roadmap) as structured JSON for an organization.
    All numbers in the returned narrative are sourced from the scoring snapshot.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    assessment = db.query(Assessment).filter(
        Assessment.organization_id == org_id,
        Assessment.status != "archived",
    ).first()

    summary_payload = _build_summary_payload(org, assessment)
    board_story_data = generate_board_story(summary_payload)
    return board_story_data


@router.get("/board-story.pdf")
def download_board_story_pdf(
    org_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
):
    """
    Server-side PDF generation for the Board Story.

    All numbers embedded in the PDF are sourced directly from the scoring snapshot
    stored in the database. The frontend must never build PDFs client-side.

    Returns:
        StreamingResponse: application/pdf byte stream.

    Raises:
        HTTPException 404: org_id not found.
        HTTPException 422: org_id missing.
        HTTPException 503: PDF library unavailable.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        logger.error("reportlab not installed — cannot generate PDF server-side")
        raise HTTPException(status_code=503, detail="PDF generation service unavailable")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    assessment = db.query(Assessment).filter(
        Assessment.organization_id == org_id,
        Assessment.status != "archived",
    ).first()

    summary_payload = _build_summary_payload(org, assessment)

    # Generate narrative sections (LLM or deterministic fallback)
    board_story = generate_board_story(summary_payload)
    sections = board_story.get("sections", [])

    # ── Build PDF in-memory ──────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    BRAND_GREEN = colors.HexColor("#00C853")
    SLATE_900 = colors.HexColor("#0f172a")
    SLATE_500 = colors.HexColor("#64748b")

    title_style = ParagraphStyle(
        "ResilTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=SLATE_900,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    meta_style = ParagraphStyle(
        "ResilMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=SLATE_500,
        spaceAfter=12,
        fontName="Helvetica",
    )
    score_style = ParagraphStyle(
        "ResilScore",
        parent=styles["Normal"],
        fontSize=13,
        textColor=BRAND_GREEN,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    section_title_style = ParagraphStyle(
        "ResilSectionTitle",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=SLATE_900,
        spaceBefore=14,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "ResilBody",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
        leading=14,
        fontName="Helvetica",
    )

    # Source: scoring snapshot fields (PRODUCT_MOAT #4 compliance)
    overall_score: float = summary_payload["overall_score"]
    tier_label: str = summary_payload["tier"]["label"]
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    story = [
        Paragraph("ResilAI — Boardroom Briefing", title_style),
        Paragraph(
            f"Organization: <b>{org.name}</b> &nbsp;|&nbsp; "
            f"Generated: {generated_at} &nbsp;|&nbsp; "
            f"Source: Deterministic Scoring Snapshot",
            meta_style,
        ),
        HRFlowable(width="100%", thickness=1, color=BRAND_GREEN, spaceAfter=10),
        # All numbers here are from scoring snapshot — never fabricated
        Paragraph(
            f"Overall Readiness Score: <b>{overall_score:.1f}/100</b> &nbsp;|&nbsp; "
            f"Tier: <b>{tier_label}</b>",
            score_style,
        ),
        Spacer(1, 6),
    ]

    for i, section in enumerate(sections, start=1):
        sec_title = section.get("title", f"Section {i}")
        sec_content = section.get("content", "No content available.")
        story.append(Paragraph(f"{i}. {sec_title}", section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=4))
        # Escape any XML special chars for Paragraph safety
        safe_content = (
            sec_content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        story.append(Paragraph(safe_content, body_style))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE_500))
    story.append(
        Paragraph(
            "CONFIDENTIAL — This document contains proprietary security posture information. "
            "All metrics are sourced from the ResilAI deterministic scoring engine. "
            "Not for public redistribution.",
            meta_style,
        )
    )

    doc.build(story)
    buffer.seek(0)

    filename = f"resilai_board_story_{org_id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

