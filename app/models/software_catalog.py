"""
Software Catalog model — tracks latest versions, advisories, and version drift.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class SoftwareCatalog(Base):
    """Software Catalog — maps global software intelligence against client versions."""

    __tablename__ = "software_catalog"

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
    current_version = Column(
        String(50),
        nullable=True,
        comment="Current version running in the client's environment.",
    )
    latest_version = Column(
        String(50),
        nullable=True,
        comment="Latest available version retrieved from intelligence sources.",
    )
    latest_release_date = Column(
        String(100),
        nullable=True,
        comment="Release date of the latest available version.",
    )
    advisory_url = Column(
        String(1024),
        nullable=True,
        comment="URL pointing to release notes or security advisory.",
    )
    source = Column(
        String(100),
        nullable=True,
        comment="Source of the intelligence data (e.g. github, cisa, nvd).",
    )
    severity = Column(
        String(50),
        nullable=True,
        comment="Severity classification if a security advisory is present.",
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

    # Relationships
    organization = relationship("Organization", back_populates="software_catalog_items")

    __table_args__ = (
        Index("ix_software_catalog_org_product", "org_id", "product"),
    )

    def __repr__(self) -> str:
        return (
            f"<SoftwareCatalog(id={self.id}, product={self.product!r}, "
            f"current={self.current_version!r}, latest={self.latest_version!r})>"
        )
