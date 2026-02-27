"""
Compliance Drift Detection API routes.

Staging-only endpoints for drift analysis, baseline management,
and Shadow AI governance.

All routes are gated: 404 when ENV is not staging.
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

router = APIRouter()
logger = logging.getLogger("airs.api.drift")


# ── Staging-only guard ───────────────────────────────────────────────

def _require_staging():
    """Block all drift endpoints unless ENV=staging."""
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


# ── Baseline Management ─────────────────────────────────────────────

@router.post(
    "/{org_id}/drift/baseline",
    summary="Create Drift Baseline",
    description="Captures an immutable snapshot of the organization's current compliance posture.",
    tags=["drift"],
)
async def create_drift_baseline(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
    _writable: None = Depends(require_writable),
):
    """POST /api/governance/{org_id}/drift/baseline"""
    from app.services.governance.drift_engine import create_baseline

    _ = _get_org(db, user, org_id)  # tenant check

    try:
        baseline = create_baseline(db, org_id)
        return {
            "status": "created",
            "baseline": baseline.to_dict(),
            "message": f"Baseline v{baseline.version} captured — GHI: {baseline.ghi:.1f} ({baseline.ghi_grade})",
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to create baseline for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create compliance baseline",
        )


# ── Drift Analysis ──────────────────────────────────────────────────

@router.get(
    "/{org_id}/drift",
    summary="Calculate Compliance Drift",
    description=(
        "Analyzes current compliance posture against the most recent baseline. "
        "Returns drift signals, DIS score, and severity classification."
    ),
    tags=["drift"],
)
async def get_drift_analysis(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/drift"""
    from app.services.governance.drift_engine import calculate_drift

    _ = _get_org(db, user, org_id)

    try:
        result = calculate_drift(db, org_id)
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Drift analysis failed for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Drift analysis failed",
        )


# ── Drift Timeline ──────────────────────────────────────────────────

@router.get(
    "/{org_id}/drift/timeline",
    summary="Drift Timeline",
    description="Returns chronological drift history for visualization.",
    tags=["drift"],
)
async def get_drift_timeline(
    org_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/drift/timeline"""
    from app.services.governance.drift_engine import get_drift_timeline

    _ = _get_org(db, user, org_id)

    try:
        timeline = get_drift_timeline(org_id, limit=limit)
        return {
            "organization_id": org_id,
            "entries": [e.to_dict() for e in timeline],
            "count": len(timeline),
        }
    except Exception as exc:
        logger.error("Drift timeline failed for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drift timeline",
        )


# ── Shadow AI Check ─────────────────────────────────────────────────

@router.get(
    "/{org_id}/drift/shadow-ai",
    summary="Shadow AI Governance Check",
    description=(
        "Scans the tech stack for unsanctioned AI models and governance violations. "
        "Returns CRITICAL findings for HIGH-sensitivity unsanctioned AI."
    ),
    tags=["drift"],
)
async def check_shadow_ai(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/drift/shadow-ai"""
    from app.services.governance.drift_engine import check_shadow_ai_risk

    org = _get_org(db, user, org_id)

    try:
        signals = check_shadow_ai_risk(list(org.tech_stack_items))
        return {
            "organization_id": org_id,
            "shadow_ai_signals": [s.to_dict() for s in signals],
            "count": len(signals),
            "has_critical": any(s.severity == "critical" for s in signals),
        }
    except Exception as exc:
        logger.error("Shadow AI check failed for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shadow AI governance check failed",
        )


# ── Compliance Sustainability Index ─────────────────────────────────

@router.get(
    "/{org_id}/drift/sustainability",
    summary="Compliance Sustainability Index",
    description=(
        "Calculates the Compliance Sustainability Index (CSI) — "
        "how sustainable and maintainable is the organization's compliance posture."
    ),
    tags=["drift"],
)
async def get_sustainability_index(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/drift/sustainability"""
    from app.services.governance.drift_engine import (
        calculate_sustainability_index,
        calculate_audit_failure_probability,
    )

    _ = _get_org(db, user, org_id)

    try:
        csi = calculate_sustainability_index(db, org_id)
        afp = calculate_audit_failure_probability(db, org_id)
        return {
            "organization_id": org_id,
            "compliance_sustainability_index": csi,
            "audit_failure_probability": afp,
            "csi_band": (
                "Excellent" if csi >= 80 else
                "Good" if csi >= 60 else
                "Fair" if csi >= 40 else
                "At Risk"
            ),
            "afp_band": (
                "Low Risk" if afp <= 20 else
                "Moderate" if afp <= 50 else
                "High Risk" if afp <= 75 else
                "Critical"
            ),
        }
    except Exception as exc:
        logger.error("Sustainability index failed for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate sustainability index",
        )


# ── Regulatory Forecast ─────────────────────────────────────────────

@router.get(
    "/{org_id}/drift/regulatory-forecast",
    summary="Regulatory Forecast",
    description=(
        "Predicts compliance posture degradation from upcoming regulatory "
        "changes (EU AI Act, PCI DSS v4.0, SEC Cyber Disclosure, etc.). "
        "Returns projected GHI drop within the specified horizon."
    ),
    tags=["drift"],
)
async def get_regulatory_forecast(
    org_id: str,
    horizon_days: int = 180,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _staging: None = Depends(_require_staging),
):
    """GET /api/governance/{org_id}/drift/regulatory-forecast"""
    from app.services.governance.drift_engine import calculate_regulatory_lag

    _ = _get_org(db, user, org_id)

    try:
        forecast = calculate_regulatory_lag(db, org_id, horizon_days=horizon_days)
        return {
            "organization_id": org_id,
            **forecast,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Regulatory forecast failed for %s: %s", org_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Regulatory forecast failed",
        )
