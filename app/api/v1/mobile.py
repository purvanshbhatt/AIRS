"""
Mobile Executive API

Optimized, compressed endpoints for the iOS/Android executive dashboards.
Aggregates data from multiple domains (continuous scoring, alerts, inventory)
into single payloads to minimize mobile round-trips.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.auth import User, require_role, Role
from app.db.database import get_db
from app.models.organization import Organization
from app.models.score_snapshot import ScoreSnapshot
from app.models.simulation_result import SimulationResult
from app.models.governance_policy import PolicyEvaluationLog
from app.models.ai_asset import AIAsset

router = APIRouter(prefix="/mobile", tags=["mobile"])

# All mobile routes require at least org_member
mobile_member = require_role([Role.org_admin, Role.org_member, Role.auditor])


def get_org_or_404(db: Session, org_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return org


@router.get(
    "/dashboard/{org_id}",
    summary="Compact Executive Summary",
    description="Aggregates continuous score, active alerts count, and asset count into one payload.",
)
async def get_mobile_dashboard(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(mobile_member),
):
    """Return an aggregated executive summary for the mobile dashboard."""
    get_org_or_404(db, org_id)

    # 1. Get latest score
    latest_score = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.org_id == org_id
    ).order_by(desc(ScoreSnapshot.created_at)).first()

    # 2. Get active assets count
    assets_count = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.status == "active"
    ).count()

    # 3. Get recent critical policy violations (last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent_violations = db.query(PolicyEvaluationLog).filter(
        PolicyEvaluationLog.org_id == org_id,
        PolicyEvaluationLog.result == "fail",
        PolicyEvaluationLog.evaluated_at >= cutoff
    ).count()

    if not latest_score:
        return {
            "status": "no_data",
            "message": "No continuous score available yet.",
            "assets_count": assets_count,
            "recent_violations_24h": recent_violations,
        }

    return {
        "status": "active",
        "current_score": latest_score.overall_score,
        "ghi_grade": latest_score.ghi_grade,
        "confidence": latest_score.confidence_score,
        "assets_count": assets_count,
        "recent_violations_24h": recent_violations,
        "last_updated": latest_score.created_at.isoformat(),
        "domain_scores": latest_score.domain_scores,
    }


@router.get(
    "/score/{org_id}",
    summary="Live score + trend sparkline",
    description="Returns the current score and historical data points for rendering a sparkline.",
)
async def get_mobile_score_trend(
    org_id: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(mobile_member),
):
    """Return historical scores for sparkline rendering."""
    get_org_or_404(db, org_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.org_id == org_id,
        ScoreSnapshot.created_at >= cutoff
    ).order_by(ScoreSnapshot.created_at).all()

    sparkline = [
        {
            "date": s.created_at.isoformat(),
            "score": s.overall_score,
        }
        for s in snapshots
    ]

    latest = snapshots[-1] if snapshots else None

    return {
        "current_score": latest.overall_score if latest else None,
        "ghi_grade": latest.ghi_grade if latest else None,
        "trend_days": days,
        "sparkline": sparkline,
    }


@router.get(
    "/simulations/{org_id}",
    summary="Latest simulation summary",
    description="Returns recent threat simulation results.",
)
async def get_mobile_simulations(
    org_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(mobile_member),
):
    """Return the most recent threat simulation runs."""
    get_org_or_404(db, org_id)

    sims = db.query(SimulationResult).filter(
        SimulationResult.org_id == org_id
    ).order_by(desc(SimulationResult.executed_at)).limit(limit).all()

    return {
        "recent_simulations": [
            {
                "id": s.id,
                "category": s.category.value if hasattr(s.category, "value") else s.category,
                "blast_radius_score": s.blast_radius_score,
                "readiness_degradation_pct": s.readiness_degradation_pct,
                "executed_at": s.executed_at.isoformat(),
                "status": "critical" if s.blast_radius_score > 75 else "warning" if s.blast_radius_score > 40 else "stable",
            }
            for s in sims
        ]
    }


@router.get(
    "/alerts/{org_id}",
    summary="Critical drift alerts",
    description="Returns recent policy violations and critical alerts.",
)
async def get_mobile_alerts(
    org_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(mobile_member),
):
    """Return recent policy violations as mobile alerts."""
    get_org_or_404(db, org_id)

    violations = db.query(PolicyEvaluationLog).filter(
        PolicyEvaluationLog.org_id == org_id,
        PolicyEvaluationLog.result.in_(["fail", "warn"])
    ).order_by(desc(PolicyEvaluationLog.evaluated_at)).limit(limit).all()

    return {
        "alerts": [
            {
                "id": v.id,
                "type": "policy_violation",
                "severity": "high" if v.result == "fail" else "medium",
                "title": f"Policy {v.result.upper()} — ID: {v.policy_id}",
                "created_at": v.evaluated_at.isoformat(),
            }
            for v in violations
        ],
        "total": len(violations),
    }
