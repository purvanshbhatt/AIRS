"""
ReadinessLedgerEntry — Immutable Point-in-Time Audit Ledger.

Per ADR-008, every score recalculation must produce exactly one row here, and
rows are write-once (UPDATE/DELETE rejected at the service layer).

Idempotency: insert with the same (org_id, timestamp, new_score) is a no-op.

This ledger is read-only via API (see app/api/v1/readiness.py).
"""

import uuid

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import validates

from app.db.database import Base


class ReadinessLedgerEntry(Base):
    """Immutable readiness score-change ledger.

    Design Rationale:
      - previous_score / new_score capture the score pair that defines the delta.
      - delta is pre-computed (caller-supplied) to match calculate_readiness_delta().
      - driver_type is a structural category (e.g. "kev", "eol", "coverage_gap").
        It is intentionally NOT scored here — drivers are produced by
        readiness_drivers.py from scoring.py output.

    """

    __tablename__ = "readiness_ledger_entries"

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
        comment="FK to the organization this ledger entry belongs to.",
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the score recalculation occurred.",
    )
    previous_score = Column(
        Float,
        nullable=False,
        comment="Score before recalculation (0-100).",
    )
    new_score = Column(
        Float,
        nullable=False,
        comment="Score after recalculation (0-100).",
    )
    delta = Column(
        Float,
        nullable=False,
        comment="new_score - previous_score.",
    )
    driver_type = Column(
        String(64),
        nullable=True,
        comment="Structural category that triggered this delta (kev|eol|coverage_gap|...).",
    )
    driver_item = Column(
        String(255),
        nullable=True,
        comment="Identifier (asset id, finding id) of the driver, if applicable.",
    )
    impact = Column(
        Float,
        nullable=True,
        comment="Signed impact contribution from this driver to the delta.",
    )
    evidence_source = Column(
        String(128),
        nullable=True,
        comment="Evidence origin (splunk|wazuh|aws|questionnaire|...).",
    )
    created_by = Column(
        String(128),
        nullable=True,
        comment="Originator of the row (system actor or user id).",
    )

    __table_args__ = (
        Index(
            "ix_readiness_ledger_org_timestamp",
            "org_id",
            "timestamp",
        ),
        Index(
            "ix_readiness_ledger_idempotency",
            "org_id",
            "timestamp",
            "new_score",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ReadinessLedgerEntry(id={self.id}, org={self.org_id}, "
            f"prev={self.previous_score}, new={self.new_score}, delta={self.delta})>"
        )

    @validates("previous_score", "new_score")
    def _validate_score_range(self, key: str, value: float) -> float:
        if value is None:
            return value
        if value < 0.0 or value > 100.0:
            raise ValueError(
                f"{key} must be within 0-100 inclusive; got {value}"
            )
        return value
