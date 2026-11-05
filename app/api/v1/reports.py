"""
Reports API — Board Story JSON and server-side PDF generation.

PRODUCT_MOAT invariants enforced here:
  - All numbers in the PDF body are sourced from the scoring snapshot (never fabricated client-side).
  - LLM only fills prose; it never scores.
  - PDF generation is server-side only via reportlab.
"""
import io
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth
from app.models.organization import Organization
from app.models.assessment import Assessment
from app.services.ai_narrative import generate_board_story
from app.schemas.board_story import BoardStory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


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

