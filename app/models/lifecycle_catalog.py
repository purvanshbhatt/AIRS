"""
Global Software Catalog and Lifecycle Intelligence Models.
These models represent a deterministic registry of known software products, versions, and their end-of-life (EOL) status.
Unlike discovery models, these are NOT tied to an organization ID.
"""

import uuid
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class GlobalSoftwareCatalog(Base):
    """A globally recognized software product (e.g. PostgreSQL, Python)."""
    __tablename__ = "global_software_catalog"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=False, unique=True, index=True)
    product_family = Column(String(255), nullable=True)
    current_version = Column(String(100), nullable=True)
    current_lts_version = Column(String(100), nullable=True)
    
    # Relationships
    versions = relationship("SoftwareVersion", back_populates="catalog", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GlobalSoftwareCatalog(product={self.product_name!r})>"


class SoftwareVersion(Base):
    """Specific version lifecycle intelligence for a product."""
    __tablename__ = "software_versions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    catalog_id = Column(CHAR(36), ForeignKey("global_software_catalog.id", ondelete="CASCADE"), nullable=False, index=True)
    
    version_name = Column(String(100), nullable=False)
    support_status = Column(String(50), nullable=False)  # 'Supported', 'Expiring', 'EOL'
    eol_date = Column(Date, nullable=True)
    eos_date = Column(Date, nullable=True)
    
    # Relationships
    catalog = relationship("GlobalSoftwareCatalog", back_populates="versions")
    references = relationship("LifecycleReference", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SoftwareVersion(version={self.version_name!r}, status={self.support_status!r})>"


class LifecycleReference(Base):
    """Source provenance and reference links for the lifecycle intelligence."""
    __tablename__ = "lifecycle_references"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(CHAR(36), ForeignKey("software_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    last_verified_date = Column(DateTime(timezone=True), server_default=func.now())
    source_url = Column(Text, nullable=True)
    
    # Relationships
    version = relationship("SoftwareVersion", back_populates="references")

    def __repr__(self):
        return f"<LifecycleReference(verified={self.last_verified_date})>"
