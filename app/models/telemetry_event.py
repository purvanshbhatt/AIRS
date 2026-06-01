"""
TelemetryEvent — Raw Event Ingestion & Deduplication.

Stores raw telemetry events ingested from external connectors.
Each event carries a payload_hash for content-addressable deduplication
and a composite unique constraint on (org_id, source_system, source_event_id)
to prevent duplicate ingestion from the same source.

Events are processed asynchronously by the governance engine; the
'processed' flag and 'processed_at' timestamp track consumption state.
"""

import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Index, UniqueConstraint,
    ForeignKey, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class TelemetryEvent(Base):
    """Raw telemetry event ingested from an external connector.

    Design Rationale:
      - payload_hash (SHA-256) enables content-addressable deduplication.
      - source_event_id is the upstream system's native event ID.
      - Composite unique constraint prevents double-ingestion.
      - payload stores the full raw JSON for reprocessing capability.
      - connector_id is nullable to support manually-injected events.
    """

    __tablename__ = "telemetry_events"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    org_id = Column(
        CHAR(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the owning organization.",
    )
    connector_id = Column(
        CHAR(36),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=True,
        comment="FK to the connector that ingested this event (nullable for manual events).",
    )
    event_type = Column(
        String(255),
        nullable=False,
        comment="Classification of the event (e.g. alert, audit_log, config_change).",
    )
    source_system = Column(
        String(255),
        nullable=False,
        comment="Name of the upstream source system (e.g. wazuh, splunk, github).",
    )
    source_event_id = Column(
        String(255),
        nullable=False,
        comment="Native event ID from the source system for traceability.",
    )
    payload_hash = Column(
        String(64),
        nullable=False,
        comment="SHA-256 hex digest of the raw event payload for deduplication.",
    )
    payload = Column(
        JSON,
        nullable=True,
        comment="Full raw JSON payload of the ingested event.",
    )
    severity = Column(
        String(50),
        nullable=True,
        comment="Severity level assigned by the source system.",
    )
    processed = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this event has been consumed by the governance engine.",
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of when the event was processed.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )

    __table_args__ = (
        UniqueConstraint(
            "org_id",
            "source_system",
            "source_event_id",
            name="uq_telemetry_org_source_event",
        ),
        Index("ix_telemetry_org_created", "org_id", "created_at"),
        Index("ix_telemetry_org_event_type", "org_id", "event_type"),
        Index("ix_telemetry_processed", "processed"),
    )

    def __repr__(self) -> str:
        return (
            f"<TelemetryEvent(id={self.id}, type={self.event_type!r}, "
            f"source={self.source_system!r}, processed={self.processed})>"
        )
