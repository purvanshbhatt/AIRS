"""
Technology Stack Discovery Models.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class AssetType(str, enum.Enum):
    HOST = "HOST"
    CLOUD_SERVICE = "CLOUD_SERVICE"
    IAM = "IAM"
    CONTAINER = "CONTAINER"
    NETWORK_DEVICE = "NETWORK_DEVICE"


class TechnologyInventory(Base):
    """Snapshot of the technology inventory for an organization."""
    __tablename__ = "technology_inventory"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    last_discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    discovery_source = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    
    # Relationships
    organization = relationship("Organization", back_populates="technology_inventories")
    discovered_assets = relationship("DiscoveredAsset", back_populates="inventory", cascade="all, delete-orphan")


class DiscoveredAsset(Base):
    """An individual host, device, or cloud service."""
    __tablename__ = "discovered_assets"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(CHAR(36), ForeignKey("technology_inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    
    hostname = Column(String(255), nullable=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, default=AssetType.HOST)
    operating_system = Column(String(255), nullable=True)
    ip_address = Column(String(100), nullable=True)
    cloud_provider = Column(String(100), nullable=True)
    
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="discovered_assets")
    inventory = relationship("TechnologyInventory", back_populates="discovered_assets")
    installed_products = relationship("InstalledProduct", back_populates="asset", cascade="all, delete-orphan")


class InstalledProduct(Base):
    """Software product installed on a specific asset."""
    __tablename__ = "installed_products"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(CHAR(36), ForeignKey("discovered_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    product_name = Column(String(255), nullable=False)
    vendor = Column(String(255), nullable=True)
    version = Column(String(100), nullable=True)
    installation_source = Column(String(255), nullable=True)
    eol_status = Column(String(50), nullable=True)  # lts, active, deprecated, eol
    
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    asset = relationship("DiscoveredAsset", back_populates="installed_products")
    evidence_sources = relationship("EvidenceSource", back_populates="product", cascade="all, delete-orphan")


class EvidenceSource(Base):
    """The raw telemetry source proving the existence of an installed product."""
    __tablename__ = "evidence_sources"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(CHAR(36), ForeignKey("installed_products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_type = Column(String(100), nullable=False) # e.g., 'splunk', 'wazuh', 'graph'
    connector_name = Column(String(255), nullable=True)
    raw_evidence_hash = Column(String(64), nullable=True)
    
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("InstalledProduct", back_populates="evidence_sources")
