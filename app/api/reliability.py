"""
Reliability Risk Index (RRI) API routes.

Staging-only endpoints for reliability exposure scoring,
downtime budget analysis, SLA advising, board simulation,
Reliability Confidence Score (RCS), auto-recommendation,
and historical trend tracking.
"""

import logging
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request, status
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
    AcceptRecommendationRequest,
    ReliabilityConfidenceScoreSchema,
    RRISnapshotSchema,
)

router = APIRouter()
logger = logging.getLogger("airs.api.reliability")

# ── Simple rate limiter for simulation endpoint ──────────────────────
_simulate_calls: dict = defaultdict(list)  # uid -> [timestamps]
SIMULATE_RATE_LIMIT = 10  # max calls per minute


def _check_rate_limit(user_uid: str):
    """Block if user exceeds simulation rate limit."""
    now = time.time()
    window = [t for t in _simulate_calls[user_uid] if now - t < 60]
    _simulate_calls[user_uid] = window
    if len(window) >= SIMULATE_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded — max 10 simulations per minute",
        )
    _simulate_calls[user_uid].append(now)


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
        "monitoring & detection, and BCDR validation into a single 0-100 exposure score. "
        "Also returns Breach Exposure Badge, Autonomous Advisories, RCS, and auto-recommendations."
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


# ── Reliability Confidence Score ─────────────────────────────────────

@router.get(
    "/{org_id}/reliability-index/confidence",
    response_model=ReliabilityConfidenceScoreSchema,
    summary="Get Reliability Confidence Score (RCS)",
    description=(
        "Calculate the Reliability Confidence Score (RCS) — the second axis "
        "of the resilience matrix. RRI = Exposure, RCS = Confidence. "
        "Five sub-dimensions: DR test recency, backup validation, IR tabletop, "
        "monitoring coverage, architecture redundancy. 0-100 scale."
    ),
    tags=["reliability"],
)
async def get_reliability_confidence(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/reliability-index/confidence"""
    from app.services.governance.reliability_engine import calculate_rcs, _gather_latest_answers
    from app.models.tech_stack import TechStackItem

    org = _get_org(db, user, org_id)

    answers = _gather_latest_answers(db, org.id)
    tech_items = db.query(TechStackItem).filter(
        TechStackItem.org_id == org.id
    ).all() if org.id else []
    audit_entries = []
    try:
        from app.models.audit_calendar import AuditCalendarEntry
        audit_entries = db.query(AuditCalendarEntry).filter(
            AuditCalendarEntry.org_id == org.id
        ).all()
    except Exception:
        pass

    rcs = calculate_rcs(answers, tech_items, audit_entries)
    return rcs.to_dict()


# ── Board Simulation Mode ────────────────────────────────────────────

@router.post(
    "/{org_id}/reliability-index/simulate",
    response_model=BreachSimulationResponse,
    summary="Simulate SLA Change (Board Mode)",
    description=(
        "Board Simulation Mode: 'What if we upgrade/downgrade our SLA?' "
        "Shows the impact on downtime budget, required improvements, "
        "control gaps, and readiness delta. Rate-limited to 10/min."
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

    _check_rate_limit(user.uid if user else "anonymous")
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


# ── Accept Auto-Recommendation ──────────────────────────────────────

@router.post(
    "/{org_id}/reliability-index/accept-recommendation",
    summary="Accept Auto-Detected Recommendation",
    description=(
        "Accept the auto-detected tier/SLA recommendation and apply it "
        "to the organization configuration. Removes dead-end states."
    ),
    tags=["reliability"],
)
async def accept_recommendation(
    org_id: str,
    body: AcceptRecommendationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
    _writable: None = Depends(require_writable),
):
    """POST /api/governance/{org_id}/reliability-index/accept-recommendation"""
    org = _get_org(db, user, org_id)

    # Apply recommendation
    updated_fields = []
    if body.recommended_tier:
        org.application_tier = body.recommended_tier.lower().replace(" ", "_")
        updated_fields.append(f"tier={org.application_tier}")
    if body.recommended_sla:
        org.sla_target = body.recommended_sla
        updated_fields.append(f"sla={org.sla_target}")

    db.commit()

    # Log audit event
    try:
        from app.models.audit_event import AuditEvent
        event = AuditEvent(
            org_id=org.id,
            action=f"recommendation_accepted|{','.join(updated_fields)}",
            actor=user.uid if user else "system",
        )
        db.add(event)
        db.commit()
    except Exception:
        pass

    logger.info("Recommendation accepted for %s: %s", org_id, updated_fields)
    return {
        "status": "accepted",
        "org_id": org_id,
        "applied": updated_fields,
    }


# ── RRI History / Snapshots ──────────────────────────────────────────

@router.get(
    "/{org_id}/reliability-index/history",
    response_model=list[RRISnapshotSchema],
    summary="Get RRI History (last 90 days)",
    description=(
        "Retrieve RRI score history from audit trail for trend visualization. "
        "Returns snapshots reconstructed from audit events, up to 90 days."
    ),
    tags=["reliability"],
)
async def get_reliability_history(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/reliability-index/history"""
    from datetime import datetime, timedelta

    org = _get_org(db, user, org_id)

    # Query audit events for RRI calculations in last 90 days
    snapshots = []
    try:
        from app.models.audit_event import AuditEvent
        cutoff = datetime.utcnow() - timedelta(days=90)
        events = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.org_id == org.id,
                AuditEvent.action.like("rri_calculated%"),
                AuditEvent.timestamp >= cutoff,
            )
            .order_by(AuditEvent.timestamp.asc())
            .all()
        )

        for evt in events:
            # Parse "rri_calculated|score=X|rcs=Y"
            parts = evt.action.split("|")
            rri_score = 0.0
            rcs_score = 0.0
            for part in parts:
                if part.startswith("score="):
                    try:
                        rri_score = float(part.split("=")[1])
                    except (ValueError, IndexError):
                        pass
                elif part.startswith("rcs="):
                    try:
                        rcs_score = float(part.split("=")[1])
                    except (ValueError, IndexError):
                        pass

            # Determine bands from scores
            if rri_score <= 25:
                risk_band = "Low"
            elif rri_score <= 50:
                risk_band = "Moderate"
            elif rri_score <= 75:
                risk_band = "High"
            else:
                risk_band = "Critical"

            if rcs_score >= 75:
                confidence_band = "Verified"
            elif rcs_score >= 50:
                confidence_band = "Moderate"
            elif rcs_score >= 25:
                confidence_band = "Low"
            else:
                confidence_band = "Unvalidated"

            snapshots.append({
                "org_id": org.id,
                "timestamp": evt.timestamp.isoformat() if evt.timestamp else "",
                "rri_score": rri_score,
                "rcs_score": rcs_score,
                "risk_band": risk_band,
                "confidence_band": confidence_band,
                "dimensions": {},
            })

    except Exception as exc:
        logger.warning("Failed to fetch RRI history for %s: %s", org_id, exc)

    return snapshots


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
