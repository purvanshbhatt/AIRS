"""
Discovered Asset model — tracks automatically discovered software assets.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class DiscoveredAsset(Base):
    """Discovered Asset — stores software discovered from telemetry sources."""

    __tablename__ = "discovered_assets"

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
        index=True,
        comment="FK to the owning organization.",
    )

    vendor = Column(
        String(255),
        nullable=True,
        comment="Software vendor or publisher.",
    )
    product = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Name of the software product.",
    )
    version = Column(
        String(50),
        nullable=True,
        comment="Discovered version of the software.",
    )
    source = Column(
        String(150),
        nullable=False,
        comment="Source of discovery (e.g. intune, defender, wazuh, splunk).",
    )

    first_seen = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this asset was first discovered.",
    )
    last_seen = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="When this asset was last discovered.",
    )

    # Relationships
    organization = relationship("Organization", back_populates="discovered_assets")

    def __repr__(self) -> str:
        return (
            f"<DiscoveredAsset(id={self.id}, product={self.product!r}, "
            f"version={self.version!r}, source={self.source!r})>"
        )
