"""
ScoreSnapshot — Point-in-Time Governance Health Index.

Captures a complete governance readiness snapshot for an organization
at a specific moment. Each snapshot records the overall score, GHI grade,
per-domain breakdowns, framework coverage, and confidence/staleness
adjustments.

Snapshots are triggered by scheduled jobs, manual recalculations,
incoming events, or completed assessments.
"""

import uuid
import enum

from sqlalchemy import (
    Column, String, Float, DateTime, Index,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class SnapshotTrigger(str, enum.Enum):
    """What triggered the score snapshot."""
    scheduled = "scheduled"
    manual = "manual"
    event_triggered = "event_triggered"
    assessment_completed = "assessment_completed"


class ScoreSnapshot(Base):
    """Point-in-time governance readiness snapshot.

    Design Rationale:
      - overall_score is the composite governance readiness score (0-100).
      - ghi_score and ghi_grade provide the Governance Health Index metric.
      - domain_scores is a JSON map of domain -> score for drill-down.
      - telemetry_weight and stale_penalty_applied track scoring adjustments.
      - confidence_score indicates data completeness of the snapshot.
    """

    __tablename__ = "score_snapshots"

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
        comment="FK to the organization this snapshot belongs to.",
    )
    snapshot_trigger = Column(
        SQLEnum(SnapshotTrigger),
        nullable=False,
        comment="What triggered this snapshot (scheduled, manual, event, assessment).",
    )
    overall_score = Column(
        Float,
        nullable=False,
        comment="Composite governance readiness score (0-100).",
    )
    ghi_score = Column(
        Float,
        nullable=False,
        comment="Governance Health Index score.",
    )
    ghi_grade = Column(
        String(2),
        nullable=False,
        comment="Letter grade derived from GHI score (A+, A, B, etc.).",
    )
    domain_scores = Column(
        JSON,
        nullable=False,
        comment="JSON map of domain name -> score for per-domain breakdown.",
    )
    framework_coverage = Column(
        JSON,
        nullable=True,
        comment="JSON map of framework -> coverage percentage.",
    )
    evidence_freshness_score = Column(
        Float,
        nullable=True,
        comment="Score reflecting how recent the underlying evidence is.",
    )
    confidence_score = Column(
        Float,
        nullable=True,
        comment="Data completeness / confidence indicator (0.0-1.0).",
    )
    telemetry_weight = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Weight of telemetry-derived evidence in the score.",
    )
    stale_penalty_applied = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Penalty applied for stale or expired evidence.",
    )
    triggered_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor or system that triggered this snapshot.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )

    __table_args__ = (
        Index("ix_score_snapshot_org_created", "org_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScoreSnapshot(id={self.id}, org={self.org_id}, "
            f"score={self.overall_score}, grade={self.ghi_grade!r})>"
        )
