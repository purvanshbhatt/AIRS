"""
Connector — External Integration Management.

Manages connections to external security, identity, and AI platforms.
Each connector belongs to an organization and tracks sync state,
authentication method, and health status.

ConnectorSyncLog provides an append-only audit trail of every sync
attempt, recording events ingested, errors, and duration.
"""

import uuid
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Index,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base
from app.db.types import EncryptedString


class ConnectorType(str, enum.Enum):
    """Supported external connector platforms."""
    github = "github"
    gitlab = "gitlab"
    okta = "okta"
    aws_security_hub = "aws_security_hub"
    gcp_scc = "gcp_scc"
    azure_security_center = "azure_security_center"
    splunk = "splunk"
    wazuh = "wazuh"
    crowdstrike = "crowdstrike"
    vertex_ai = "vertex_ai"
    aws_bedrock = "aws_bedrock"
    azure_openai = "azure_openai"
    microsoft = "microsoft"
    veeam = "veeam"


class ConnectorAuthMethod(str, enum.Enum):
    """Authentication methods supported by connectors."""
    oauth = "oauth"
    api_key = "api_key"
    webhook = "webhook"
    iam_role = "iam_role"


class ConnectorStatus(str, enum.Enum):
    """Lifecycle status of a connector."""
    active = "active"
    inactive = "inactive"
    error = "error"
    syncing = "syncing"
    pending_auth = "pending_auth"


class Connector(Base):
    """External integration connector belonging to an organization.

    Design Rationale:
      - Each org can have multiple connectors of the same type.
      - Credentials are stored encrypted (application-layer encryption).
      - config holds platform-specific JSON (e.g. webhook URLs, scopes).
      - health_status and error_message enable at-a-glance monitoring.
    """

    __tablename__ = "connectors"

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
    connector_type = Column(
        SQLEnum(ConnectorType),
        nullable=False,
        comment="Platform type of this connector.",
    )
    display_name = Column(
        String(255),
        nullable=False,
        comment="Human-readable display name for the connector.",
    )
    auth_method = Column(
        SQLEnum(ConnectorAuthMethod),
        nullable=False,
        comment="Authentication method used by this connector.",
    )
    status = Column(
        SQLEnum(ConnectorStatus),
        nullable=False,
        default=ConnectorStatus.pending_auth,
        comment="Current lifecycle status of the connector.",
    )
    encrypted_credentials = Column(
        EncryptedString,
        nullable=True,
        comment="Application-layer encrypted credentials blob.",
    )
    config = Column(
        JSON,
        nullable=True,
        comment="Platform-specific configuration (scopes, endpoints, etc.).",
    )
    last_sync_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the last successful sync.",
    )
    sync_interval_minutes = Column(
        Integer,
        nullable=False,
        default=60,
        comment="Interval in minutes between automatic syncs.",
    )
    health_status = Column(
        String(50),
        nullable=True,
        comment="Current health status string (healthy, degraded, down).",
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Latest error message if the connector is in error state.",
    )
    permissions_validated = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether required permissions have been validated.",
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
        comment="UID of the actor who created this connector.",
    )

    __table_args__ = (
        Index("ix_connector_org_type", "org_id", "connector_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Connector(id={self.id}, org={self.org_id}, "
            f"type={self.connector_type}, status={self.status})>"
        )


class ConnectorSyncLog(Base):
    """Append-only log of connector sync attempts.

    Design Rationale:
      - One row per sync attempt, regardless of outcome.
      - events_ingested and errors_count enable throughput monitoring.
      - duration_ms supports SLA tracking for integrations.
    """

    __tablename__ = "connector_sync_logs"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    connector_id = Column(
        CHAR(36),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the connector that was synced.",
    )
    sync_started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the sync started.",
    )
    sync_completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when the sync completed (null if still running).",
    )
    status = Column(
        String(50),
        nullable=False,
        comment="Sync outcome status (success, partial, failed).",
    )
    events_ingested = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of events successfully ingested during this sync.",
    )
    errors_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of errors encountered during this sync.",
    )
    duration_ms = Column(
        Integer,
        nullable=True,
        comment="Total sync duration in milliseconds.",
    )
    error_details = Column(
        Text,
        nullable=True,
        comment="Detailed error information if the sync encountered failures.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )

    __table_args__ = (
        Index("ix_sync_log_connector_created", "connector_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConnectorSyncLog(id={self.id}, connector={self.connector_id}, "
            f"status={self.status}, ingested={self.events_ingested})>"
        )
