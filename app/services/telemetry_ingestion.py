"""
TelemetryIngestionService — Event Processing & Evidence Freshness Tracking.

Processes raw telemetry events from connectors and manual ingest,
computes evidence freshness scores, and maintains the processed/unprocessed
event queue for the continuous scoring engine.

Architectural Invariant:
  - This service NEVER modifies scores or findings directly.
  - It ingests, deduplicates, hashes, and marks events as processed.
  - The ContinuousScoringEngine (Phase 2) consumes processed events.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models.telemetry_event import TelemetryEvent

logger = logging.getLogger("airs.services.telemetry_ingestion")


class TelemetryIngestionService:
    """Organization-scoped telemetry event processing pipeline.

    Responsibilities:
      1. Ingest & deduplicate events from connectors
      2. Compute SHA-256 payload hashes for tamper evidence
      3. Track evidence freshness per source system
      4. Provide unprocessed event queues for the scoring engine
    """

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_events(
        self,
        events: List[Dict[str, Any]],
        connector_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Batch-ingest telemetry events with idempotent deduplication.

        Args:
            events: List of event dicts with keys:
                event_type, source_system, source_event_id, payload, severity
            connector_id: Optional FK to the source connector.

        Returns:
            Dict with counts: {ingested, duplicates_skipped, errors}
        """
        ingested = 0
        duplicates = 0
        errors = 0

        for event_data in events:
            try:
                source_system = event_data.get("source_system", "unknown")
                source_event_id = event_data.get("source_event_id", "")

                # Idempotency: check composite unique key
                existing = (
                    self.db.query(TelemetryEvent.id)
                    .filter(
                        TelemetryEvent.org_id == self.org_id,
                        TelemetryEvent.source_system == source_system,
                        TelemetryEvent.source_event_id == source_event_id,
                    )
                    .first()
                )
                if existing:
                    duplicates += 1
                    continue

                # Compute content-addressable hash
                payload = event_data.get("payload", {})
                canonical = json.dumps(payload, sort_keys=True, default=str)
                payload_hash = hashlib.sha256(canonical.encode()).hexdigest()

                record = TelemetryEvent(
                    org_id=self.org_id,
                    connector_id=connector_id,
                    event_type=event_data.get("event_type", "unknown"),
                    source_system=source_system,
                    source_event_id=source_event_id,
                    payload_hash=payload_hash,
                    payload=payload,
                    severity=event_data.get("severity"),
                )
                self.db.add(record)
                ingested += 1

            except Exception as exc:
                logger.warning("Event ingestion error: %s", exc)
                errors += 1

        if ingested > 0:
            self.db.commit()
            logger.info(
                "Ingested %d events (org=%s, dupes=%d, errors=%d)",
                ingested, self.org_id, duplicates, errors,
            )

        return {
            "ingested": ingested,
            "duplicates_skipped": duplicates,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Event Queue (for Scoring Engine)
    # ------------------------------------------------------------------

    def get_unprocessed_events(
        self, limit: int = 500
    ) -> List[TelemetryEvent]:
        """Fetch unprocessed events for consumption by the scoring engine.

        Args:
            limit: Maximum events to return per batch.

        Returns:
            List of TelemetryEvent ORM instances.
        """
        return (
            self.db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.org_id == self.org_id,
                TelemetryEvent.processed == False,
            )
            .order_by(TelemetryEvent.created_at.asc())
            .limit(limit)
            .all()
        )

    def mark_events_processed(self, event_ids: List[str]) -> int:
        """Mark events as processed after consumption by the scoring engine.

        Returns:
            Number of events marked.
        """
        if not event_ids:
            return 0

        now = datetime.now(timezone.utc)
        count = (
            self.db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.id.in_(event_ids),
                TelemetryEvent.org_id == self.org_id,
            )
            .update(
                {"processed": True, "processed_at": now},
                synchronize_session="fetch",
            )
        )
        self.db.commit()
        return count

    # ------------------------------------------------------------------
    # Evidence Freshness
    # ------------------------------------------------------------------

    def compute_evidence_freshness(self) -> Dict[str, Any]:
        """Compute evidence freshness metrics across all source systems.

        Freshness is measured as the time since the most recent event from
        each source system. A higher freshness score indicates more recent
        telemetry coverage.

        Returns:
            Dict with:
              - overall_freshness: float (0.0-1.0)
              - by_source: Dict[source_system, {last_event, age_hours, freshness}]
              - stale_sources: List of sources with no events in 24h
        """
        now = datetime.now(timezone.utc)
        freshness_window = timedelta(hours=24)

        # Get latest event per source system
        latest_by_source = (
            self.db.query(
                TelemetryEvent.source_system,
                sa_func.max(TelemetryEvent.created_at).label("last_event"),
                sa_func.count(TelemetryEvent.id).label("event_count"),
            )
            .filter(TelemetryEvent.org_id == self.org_id)
            .group_by(TelemetryEvent.source_system)
            .all()
        )

        if not latest_by_source:
            return {
                "overall_freshness": 0.0,
                "by_source": {},
                "stale_sources": [],
            }

        by_source = {}
        stale_sources = []
        total_freshness = 0.0

        for source, last_event, count in latest_by_source:
            if last_event is None:
                age_hours = float("inf")
                freshness = 0.0
            else:
                # Ensure timezone-aware comparison
                if last_event.tzinfo is None:
                    age = now.replace(tzinfo=None) - last_event
                else:
                    age = now - last_event
                age_hours = age.total_seconds() / 3600

                # Freshness decays linearly over the window
                freshness = max(0.0, 1.0 - (age_hours / freshness_window.total_seconds() * 3600))
                freshness = min(1.0, freshness)

            by_source[source] = {
                "last_event": last_event.isoformat() if last_event else None,
                "age_hours": round(age_hours, 1),
                "freshness": round(freshness, 3),
                "event_count": count,
            }

            if age_hours > 24:
                stale_sources.append(source)

            total_freshness += freshness

        overall = total_freshness / len(latest_by_source) if latest_by_source else 0.0

        return {
            "overall_freshness": round(overall, 3),
            "by_source": by_source,
            "stale_sources": stale_sources,
        }

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated telemetry statistics for this organization.

        Returns:
            Dict with total, 24h, 7d counts and breakdowns by source/type/severity.
        """
        now = datetime.now(timezone.utc)

        total = (
            self.db.query(sa_func.count(TelemetryEvent.id))
            .filter(TelemetryEvent.org_id == self.org_id)
            .scalar()
        ) or 0

        events_24h = (
            self.db.query(sa_func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.org_id == self.org_id,
                TelemetryEvent.created_at >= now - timedelta(hours=24),
            )
            .scalar()
        ) or 0

        events_7d = (
            self.db.query(sa_func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.org_id == self.org_id,
                TelemetryEvent.created_at >= now - timedelta(days=7),
            )
            .scalar()
        ) or 0

        unprocessed = (
            self.db.query(sa_func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.org_id == self.org_id,
                TelemetryEvent.processed == False,
            )
            .scalar()
        ) or 0

        return {
            "total_events": total,
            "events_24h": events_24h,
            "events_7d": events_7d,
            "unprocessed": unprocessed,
            "evidence_freshness": self.compute_evidence_freshness(),
        }
