"""
AIAsset — AI Asset Inventory & Lifecycle Management.

Tracks all AI-related assets within an organization: models, agents,
RAG pipelines, vector databases, prompt systems, datasets, and
inference endpoints. Each asset carries business criticality,
exposure level, and lifecycle stage metadata.

AIAssetVersion provides an append-only version history with full
JSON snapshots for audit trail reconstruction.

AIAssetRelationship captures directed dependency edges between
assets (feeds_into, depends_on, monitors) to model the AI supply chain.
"""

import uuid
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Index,
    ForeignKey, Enum as SQLEnum, Float, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class AIAssetType(str, enum.Enum):
    """Classification of AI asset types."""
    model = "model"
    agent = "agent"
    rag_pipeline = "rag_pipeline"
    vector_db = "vector_db"
    prompt_system = "prompt_system"
    dataset = "dataset"
    inference_endpoint = "inference_endpoint"
    fine_tuned_model = "fine_tuned_model"
    external_vendor = "external_vendor"

    # Added in Sprint 1.8 (Task S1.8-B5): non-traditional AI assets.
    mcp_server = "mcp_server"
    mcp_client = "mcp_client"
    agent_framework = "agent_framework"
    embedding_pipeline = "embedding_pipeline"
    rag_corpus = "rag_corpus"
    training_dataset = "training_dataset"
    evaluation_pipeline = "evaluation_pipeline"
    prompt_library = "prompt_library"


class BusinessCriticality(str, enum.Enum):
    """Business impact tier of an AI asset."""
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ExposureLevel(str, enum.Enum):
    """Data exposure classification."""
    public = "public"
    internal = "internal"
    restricted = "restricted"
    confidential = "confidential"


class LifecycleStage(str, enum.Enum):
    """Deployment lifecycle stage of an AI asset."""
    development = "development"
    testing = "testing"
    staging = "staging"
    production = "production"
    deprecated = "deprecated"
    retired = "retired"


class AIAsset(Base):
    """Registered AI asset within an organization.

    Design Rationale:
      - risk_tags and associated_controls are JSON arrays enabling flexible
        tagging without join tables.
      - version is an optimistic-locking counter incremented on each update.
      - metadata_extra is a schemaless JSON bucket for platform-specific data.
      - last_validated_at tracks when the asset was last governance-reviewed.
    """

    __tablename__ = "ai_assets"

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
    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable name of the AI asset.",
    )
    asset_type = Column(
        SQLEnum(AIAssetType),
        nullable=False,
        comment="Classification of this AI asset.",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the asset's purpose and scope.",
    )
    owner = Column(
        String(255),
        nullable=True,
        comment="Owner or responsible team for this asset.",
    )
    business_criticality = Column(
        SQLEnum(BusinessCriticality),
        nullable=False,
        comment="Business impact tier (critical, high, medium, low).",
    )
    exposure_level = Column(
        SQLEnum(ExposureLevel),
        nullable=False,
        comment="Data exposure classification.",
    )
    deployment_environment = Column(
        String(100),
        nullable=True,
        comment="Deployment target environment (e.g. us-east-1, on-prem).",
    )
    lifecycle_stage = Column(
        SQLEnum(LifecycleStage),
        nullable=False,
        comment="Current lifecycle stage of the asset.",
    )
    risk_tags = Column(
        JSON,
        nullable=False,
        default=list,
        comment="JSON array of risk tags associated with this asset.",
    )
    associated_controls = Column(
        JSON,
        nullable=False,
        default=list,
        comment="JSON array of control IDs mapped to this asset.",
    )
    last_validated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of last governance validation.",
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Optimistic-locking version counter.",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag. Inactive assets are excluded from scoring.",
    )
    metadata_extra = Column(
        JSON,
        nullable=True,
        comment="Schemaless JSON bucket for platform-specific metadata.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Row last-update timestamp.",
    )
    created_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor who registered this asset.",
    )

    __table_args__ = (
        Index("ix_ai_asset_org_type", "org_id", "asset_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIAsset(id={self.id}, name={self.name!r}, "
            f"type={self.asset_type}, stage={self.lifecycle_stage})>"
        )


class AIAssetVersion(Base):
    """Append-only version history for an AI asset.

    Design Rationale:
      - snapshot stores the full JSON representation of the asset at that
        version, enabling point-in-time audit reconstruction.
      - change_summary is a human-readable description of what changed.
    """

    __tablename__ = "ai_asset_versions"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    asset_id = Column(
        CHAR(36),
        ForeignKey("ai_assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the AI asset being versioned.",
    )
    version_number = Column(
        Integer,
        nullable=False,
        comment="Sequential version number for this asset.",
    )
    change_summary = Column(
        Text,
        nullable=True,
        comment="Human-readable summary of changes in this version.",
    )
    changed_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor who created this version.",
    )
    snapshot = Column(
        JSON,
        nullable=True,
        comment="Full JSON snapshot of the asset at this version.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )

    __table_args__ = (
        Index("ix_ai_asset_version_asset_ver", "asset_id", "version_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIAssetVersion(id={self.id}, asset={self.asset_id}, "
            f"v={self.version_number})>"
        )


class AIAssetRelationship(Base):
    """Directed dependency edge between two AI assets.

    Design Rationale:
      - Models the AI supply chain graph: feeds_into, depends_on, monitors.
      - source_asset_id -> target_asset_id is the directed edge.
      - metadata_extra can carry edge weight, confidence, or annotations.
    """

    __tablename__ = "ai_asset_relationships"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    source_asset_id = Column(
        CHAR(36),
        ForeignKey("ai_assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the source AI asset (edge origin).",
    )
    target_asset_id = Column(
        CHAR(36),
        ForeignKey("ai_assets.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the target AI asset (edge destination).",
    )
    relationship_type = Column(
        String(100),
        nullable=False,
        comment="Type of relationship (feeds_into, depends_on, monitors).",
    )
    metadata_extra = Column(
        JSON,
        nullable=True,
        comment="Optional JSON metadata for the relationship edge.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )

    def __repr__(self) -> str:
        return (
            f"<AIAssetRelationship(src={self.source_asset_id}, "
            f"tgt={self.target_asset_id}, type={self.relationship_type!r})>"
        )
