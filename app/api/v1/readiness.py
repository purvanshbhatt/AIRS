"""
Readiness Intelligence API (Sprint 1.8 Feature A).

Endpoints:
  GET /api/v1/readiness/drivers?org_id=<id>
  GET /api/v1/readiness/actions?org_id=<id>
  GET /api/v1/readiness/ledger?org_id=<id>
  GET /api/v1/readiness/timeline?org_id=<id>

Source data:
  - Drivers / actions : ``app.services.readiness_drivers.extract_*``.
    These consume ``calculate_readiness_delta()`` deterministically.
  - Ledger / timeline : ``app.models.readiness_ledger.ReadinessLedgerEntry``.

The endpoints are org-scoped via optional org-id query parameters. In
production these are gated by ``require_auth``; the test harness leaves
auth optional (AUTH_REQUIRED=false).
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.models import Organization, ReadinessLedgerEntry
from app.schemas.readiness import (
    ExecutiveAction,
    ExecutiveActionsResponse,
    ReadinessDriversResponse,
    ReadinessDriver,
    ReadinessLedgerEntryResponse,
    ReadinessLedgerResponse,
    ReadinessTimelinePoint,
    ReadinessTimelineResponse,
)
from app.services.readiness_drivers import (
    extract_action_items,
    extract_drivers,
)


logger = logging.getLogger("airs.api.readiness")


router = APIRouter(prefix="/readiness", tags=["readiness"])


def _resolve_org(db: Session, org_id: str) -> Organization:
    """Returns the Organization or raises 404.

    Note: the spec requires 404 for unknown orgs. This method intentionally
    uses the SQLAlchemy session's transaction visibility.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        raise HTTPException(status_code=404, detail=f"Unknown org_id: {org_id}")
    return org


def _placeholder_scoring_inputs(org_id: str) -> dict:
    """Build a minimal deterministic scoring inputs payload.

    For now (Phase A), the driver / actions endpoints are surfaced as
    empty when no actual scoring inputs have been recorded for the org.
    The scoring engine itself remains the single source of numbers
    (ADR-007); this function exists only to feed the read-only consumer
    in readiness_drivers.
    """
    return {
        "assessment_score": 0.0,
        "verified_controls": [],
        "verified_coverages": [],
        "lifecycle_risks": [],
        "exposure_risks": [],
    }


def _entry_to_response(entry: ReadinessLedgerEntry) -> ReadinessLedgerEntryResponse:
    return ReadinessLedgerEntryResponse(
        id=entry.id,
        org_id=entry.org_id,
        timestamp=entry.timestamp,
        previous_score=entry.previous_score,
        new_score=entry.new_score,
        delta=entry.delta,
        driver_type=entry.driver_type,
        driver_item=entry.driver_item,
        impact=entry.impact,
        evidence_source=entry.evidence_source,
        created_by=entry.created_by,
    )


@router.get(
    "/drivers",
    response_model=ReadinessDriversResponse,
    summary="Top readiness drivers (positive + negative)",
    description="Returns the top-5 positive and top-5 negative readiness impact drivers per ADR-007.",
)
async def get_readiness_drivers(
    org_id: str = Query(..., description="Organization ID."),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    _resolve_org(db, org_id)
    inputs = _placeholder_scoring_inputs(org_id)
    result = extract_drivers(**inputs)
    return ReadinessDriversResponse(
        org_id=org_id,
        positive_drivers=[ReadinessDriver(**d) for d in result["positive_drivers"]],
        negative_drivers=[ReadinessDriver(**d) for d in result["negative_drivers"]],
    )


@router.get(
    "/actions",
    response_model=ExecutiveActionsResponse,
    summary="Executive Action panel (Monday morning list)",
    description="Returns deterministic action items derived from negative readiness drivers.",
)
async def get_readiness_actions(
    org_id: str = Query(..., description="Organization ID."),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    top_n: int = Query(5, ge=1, le=20),
):
    _resolve_org(db, org_id)
    inputs = _placeholder_scoring_inputs(org_id)
    items = extract_action_items(**inputs, top_n=top_n)
    return ExecutiveActionsResponse(
        org_id=org_id,
        actions=[ExecutiveAction(**i) for i in items],
    )


@router.get(
    "/ledger",
    response_model=ReadinessLedgerResponse,
    summary="Readiness score-change ledger (read-only)",
    description="Returns immutable ledger entries ordered by timestamp. Read-only per ADR-008.",
)
async def get_readiness_ledger(
    org_id: str = Query(..., description="Organization ID."),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    _resolve_org(db, org_id)
    rows: List[ReadinessLedgerEntry] = (
        db.query(ReadinessLedgerEntry)
        .filter(ReadinessLedgerEntry.org_id == org_id)
        .order_by(ReadinessLedgerEntry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return ReadinessLedgerResponse(
        org_id=org_id,
        entries=[_entry_to_response(r) for r in rows],
        count=len(rows),
    )


@router.get(
    "/timeline",
    response_model=ReadinessTimelineResponse,
    summary="Readiness timeline (time-series)",
    description="Returns readiness score history as time-series points for the dashboard timeline.",
)
async def get_readiness_timeline(
    org_id: str = Query(..., description="Organization ID."),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
):
    _resolve_org(db, org_id)
    rows = (
        db.query(ReadinessLedgerEntry)
        .filter(ReadinessLedgerEntry.org_id == org_id)
        .order_by(ReadinessLedgerEntry.timestamp.asc())
        .limit(limit)
        .all()
    )
    points = [
        ReadinessTimelinePoint(
            timestamp=r.timestamp,
            new_score=r.new_score,
            delta=r.delta,
            driver_type=r.driver_type,
        )
        for r in rows
    ]
    return ReadinessTimelineResponse(
        org_id=org_id,
        points=points,
        count=len(points),
    )
