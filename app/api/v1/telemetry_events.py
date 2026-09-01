"""
Telemetry Events API — Batch ingestion, querying, and statistics.

Provides the event ingestion pipeline endpoint for connectors and manual
event submission, plus querying/statistics for the governance dashboard.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth, get_user_org_id
from app.db.database import get_db
from app.models.telemetry_event import TelemetryEvent
from app.schemas.telemetry_event import (
    TelemetryBatchIngestRequest,
    TelemetryBatchIngestResponse,
    TelemetryEventListResponse,
    TelemetryEventResponse,
    TelemetryStatsResponse,
)

logger = logging.getLogger("airs.api.telemetry_events")

router = APIRouter(prefix="/telemetry-events", tags=["telemetry-events"])


def _get_org_id(user: User, db: Session) -> str:
    return get_user_org_id(user, db)


# =============================================================================
# Batch Ingestion
# =============================================================================

@router.post(
    "/events",
    response_model=TelemetryBatchIngestResponse,
    status_code=201,
    summary="Batch ingest telemetry events",
    description="Ingest multiple telemetry events with idempotent deduplication by (org_id, source_system, source_event_id).",
)
async def batch_ingest(
    body: TelemetryBatchIngestRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db)
    ingested = 0
    duplicates = 0
    errors = 0

    for event in body.events:
        try:
            # Idempotency check
            existing = (
                db.query(TelemetryEvent.id)
                .filter(
                    TelemetryEvent.org_id == org_id,
                    TelemetryEvent.source_system == event.source_system,
                    TelemetryEvent.source_event_id == event.source_event_id,
                )
                .first()
            )
            if existing:
                duplicates += 1
                continue

            # Compute payload hash for tamper detection
            canonical = json.dumps(event.payload, sort_keys=True, default=str)
            payload_hash = hashlib.sha256(canonical.encode()).hexdigest()

            record = TelemetryEvent(
                org_id=org_id,
                event_type=event.event_type,
                source_system=event.source_system,
                source_event_id=event.source_event_id,
                payload_hash=payload_hash,
                payload=event.payload,
                severity=event.severity,
            )
            db.add(record)
            ingested += 1
        except Exception as exc:
            logger.warning("Event ingestion error: %s", exc)
            errors += 1

    if ingested > 0:
        db.commit()
        from app.core.websocket_manager import telemetry_ws_manager
        import asyncio
        # We spawn a background task so we don't block the ingestion response
        asyncio.create_task(telemetry_ws_manager.broadcast_org_update(org_id))

    return TelemetryBatchIngestResponse(
        ingested=ingested, duplicates_skipped=duplicates, errors=errors,
    )


# =============================================================================
# Querying
# =============================================================================

@router.get(
    "/events",
    response_model=TelemetryEventListResponse,
    summary="Query telemetry events",
    description="Paginated event listing with filtering by type, source, severity, and date range.",
)
async def list_events(
    event_type: Optional[str] = Query(None),
    source_system: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    query = db.query(TelemetryEvent).filter(TelemetryEvent.org_id == org_id)

    if event_type:
        query = query.filter(TelemetryEvent.event_type == event_type)
    if source_system:
        query = query.filter(TelemetryEvent.source_system == source_system)
    if severity:
        query = query.filter(TelemetryEvent.severity == severity)

    total = query.count()
    events = query.order_by(TelemetryEvent.created_at.desc()).offset(skip).limit(limit).all()

    return TelemetryEventListResponse(
        events=[TelemetryEventResponse.model_validate(e) for e in events],
        total=total,
    )


@router.get(
    "/events/{event_id}",
    response_model=TelemetryEventResponse,
    summary="Get single event",
)
async def get_event(
    event_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    event = (
        db.query(TelemetryEvent)
        .filter(TelemetryEvent.id == event_id, TelemetryEvent.org_id == org_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return TelemetryEventResponse.model_validate(event)


# =============================================================================
# Statistics
# =============================================================================

@router.get(
    "/stats",
    response_model=TelemetryStatsResponse,
    summary="Telemetry statistics",
    description="Aggregated event counts by source, type, and severity.",
)
async def get_stats(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    now = datetime.now(timezone.utc)

    total = db.query(sa_func.count(TelemetryEvent.id)).filter(
        TelemetryEvent.org_id == org_id
    ).scalar() or 0

    events_24h = db.query(sa_func.count(TelemetryEvent.id)).filter(
        TelemetryEvent.org_id == org_id,
        TelemetryEvent.created_at >= now - timedelta(hours=24),
    ).scalar() or 0

    events_7d = db.query(sa_func.count(TelemetryEvent.id)).filter(
        TelemetryEvent.org_id == org_id,
        TelemetryEvent.created_at >= now - timedelta(days=7),
    ).scalar() or 0

    # Group by source
    by_source = {}
    source_rows = (
        db.query(TelemetryEvent.source_system, sa_func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.org_id == org_id)
        .group_by(TelemetryEvent.source_system)
        .all()
    )
    for source, count in source_rows:
        by_source[source] = count

    # Group by type
    by_type = {}
    type_rows = (
        db.query(TelemetryEvent.event_type, sa_func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.org_id == org_id)
        .group_by(TelemetryEvent.event_type)
        .all()
    )
    for etype, count in type_rows:
        by_type[etype] = count

    # Group by severity
    by_severity = {}
    sev_rows = (
        db.query(TelemetryEvent.severity, sa_func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.org_id == org_id, TelemetryEvent.severity.isnot(None))
        .group_by(TelemetryEvent.severity)
        .all()
    )
    for sev, count in sev_rows:
        by_severity[sev] = count

    return TelemetryStatsResponse(
        total_events=total,
        events_24h=events_24h,
        events_7d=events_7d,
        by_source=by_source,
        by_type=by_type,
        by_severity=by_severity,
    )
