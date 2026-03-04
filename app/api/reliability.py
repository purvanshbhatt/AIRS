"""
Reliability Risk Index (RRI) API routes.

Staging-only endpoints for reliability exposure scoring,
downtime budget analysis, SLA advising, and board simulation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.core.config import settings, Environment
from app.core.demo_guard import require_writable
from app.models.organization import Organization
from app.services.organization import OrganizationService
from app.schemas.reliability import (
    RRIResponse,
    BreachSimulationRequest,
    BreachSimulationResponse,
)

router = APIRouter()
logger = logging.getLogger("airs.api.reliability")


# ── Staging-only guard ───────────────────────────────────────────────

def _require_staging():
    """Block all reliability endpoints unless ENV=staging."""
    if settings.ENV != Environment.STAGING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )


def _get_org(db: Session, user: User, org_id: str) -> Organization:
    """Resolve org with tenant isolation."""
    service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )
    return org


# ── Reliability Risk Index ───────────────────────────────────────────

@router.get(
    "/{org_id}/reliability-index",
    response_model=RRIResponse,
    summary="Get Reliability Risk Index",
    description=(
        "Calculate the Reliability Risk Index (RRI) for an organization. "
        "Combines SLA commitment risk, recovery capability, redundancy & HA, "
        "monitoring & detection, and BCDR validation into a single 0-100 exposure score."
    ),
    tags=["reliability"],
)
async def get_reliability_index(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/reliability-index"""
    from app.services.governance.reliability_engine import calculate_rri

    org = _get_org(db, user, org_id)

    try:
        result = calculate_rri(db, org)
        return result.to_dict()
    except Exception as exc:
        logger.error("RRI calculation failed for %s: %s", org_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reliability Risk Index calculation failed",
        )


# ── Board Simulation Mode ────────────────────────────────────────────

@router.post(
    "/{org_id}/reliability-index/simulate",
    response_model=BreachSimulationResponse,
    summary="Simulate SLA Change (Board Mode)",
    description=(
        "Board Simulation Mode: 'What if we upgrade/downgrade our SLA?' "
        "Shows the impact on downtime budget, required improvements, "
        "control gaps, and readiness delta."
    ),
    tags=["reliability"],
)
async def simulate_reliability(
    org_id: str,
    body: BreachSimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """POST /api/governance/{org_id}/reliability-index/simulate"""
    from app.services.governance.reliability_engine import simulate_breach

    org = _get_org(db, user, org_id)

    try:
        result = simulate_breach(db, org, body.simulated_sla)
        return result.to_dict()
    except Exception as exc:
        logger.error("Breach simulation failed for %s: %s", org_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Breach simulation failed",
        )


# ── SLA Advisor ──────────────────────────────────────────────────────

@router.get(
    "/{org_id}/reliability-index/advisor",
    summary="Smart SLA Advisor",
    description=(
        "Industry-aware SLA recommendation based on organization profile. "
        "Suggests optimal tier and SLA range with rationale."
    ),
    tags=["reliability"],
)
async def get_sla_advisor(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/reliability-index/advisor"""
    from app.services.governance.reliability_engine import get_sla_advisor as advisor

    org = _get_org(db, user, org_id)

    return advisor(org.industry).to_dict()


# ── Downtime Budget ──────────────────────────────────────────────────

@router.get(
    "/{org_id}/reliability-index/downtime-budget",
    summary="Downtime Budget Calculator",
    description=(
        "Calculate annual and monthly downtime budgets from the organization's SLA target."
    ),
    tags=["reliability"],
)
async def get_downtime_budget(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/reliability-index/downtime-budget"""
    from app.services.governance.reliability_engine import calculate_downtime_budget

    org = _get_org(db, user, org_id)

    sla = org.sla_target
    if not sla:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SLA target not configured for this organization",
        )

    return calculate_downtime_budget(sla).to_dict()
