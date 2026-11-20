"""
Questionnaire answer packs.

GET /api/v1/questionnaires/insurance?org_id=...      the pack as JSON
GET /api/v1/questionnaires/insurance/pdf?org_id=...  the same pack as a PDF to review and sign

Answers come from ``app.services.questionnaires.insurance_answers``: one
deterministic answer per question of the generic small-business
cyber-insurance question bank, each with its evidence source, evidence time
and coverage. ResilAI never submits the application; the customer signs it.

Access follows the other v1 organisation reads (``/network/topology``):
explicit demo workspaces are readable without a token and return sample
data; every other organisation needs its signed-in owner.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import User, get_optional_user
from app.core.config import settings
from app.db.database import get_db

logger = logging.getLogger("airs.api.questionnaires")

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


def _resolve(db: Session, org_id: str, user: Optional[User]) -> Tuple[Any, bool]:
    """Return ``(organization or None, is_demo)``; raise 401/404 like the other v1 org reads."""
    from app.models.organization import Organization
    from app.reports.readiness_source import is_demo_org

    org_id = (org_id or "").strip()
    if not org_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization ID is required.")

    demo = is_demo_org(db, org_id)
    if settings.is_auth_required and user is None and not demo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if demo:
        return db.query(Organization).filter(Organization.id == org_id).first(), True

    org = None
    if user is not None:
        from app.services.organization import OrganizationService
        try:
            org = OrganizationService(db, owner_uid=user.uid).get(org_id)
        except Exception as exc:
            logger.error("Organization access check failed for user=%s org=%s: %s", user.uid, org_id, exc)
            org = None
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ORGANIZATION_NOT_FOUND",
                "message": f"Organization '{org_id}' not found or access not authorized.",
                "organization_id": org_id,
            },
        )
    return org, False


def _pack(db: Session, org_id: str, user: Optional[User]) -> Dict[str, Any]:
    from app.services.questionnaires.insurance_answers import build_insurance_pack

    org, demo = _resolve(db, org_id, user)
    return build_insurance_pack(db, org_id.strip(), demo=demo, org=org)


@router.get(
    "/insurance",
    summary="Cyber-insurance application answer pack",
    description=(
        "Answers a generic small-business cyber-insurance application from live evidence. Every answer "
        "carries its evidence source, evidence time and coverage. Missing, stale (older than 48 hours) or "
        "failed-connector evidence gives `not_verified`; questions no telemetry can answer are `human_only`. "
        "Deterministic; no language model is involved."
    ),
)
async def get_insurance_answer_pack(
    org_id: str = Query(..., min_length=1, description="Organization ID (active workspace)"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    return _pack(db, org_id, user)


@router.get(
    "/insurance/pdf",
    summary="Cyber-insurance answer pack as a PDF",
    description="The same pack as a PDF with the attestation notice on page one and a blank signature block.",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def get_insurance_answer_pack_pdf(
    org_id: str = Query(..., min_length=1, description="Organization ID (active workspace)"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    from app.reports.questionnaire_pdf import render_answer_pack_pdf

    pack = _pack(db, org_id, user)
    content = render_answer_pack_pdf(pack)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    safe_org = "".join(ch for ch in org_id.strip()[:24] if ch.isalnum() or ch in "-_") or "org"
    filename = f"resilai_insurance_answer_pack_{safe_org}_{stamp}.pdf"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
