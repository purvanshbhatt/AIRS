"""
Organization model.
"""

import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Organization(Base):
    """Organization entity."""
    
    __tablename__ = "organizations"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_uid = Column(String(128), nullable=True, index=True)  # Firebase user UID for tenant isolation
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # e.g., "1-50", "51-200", "201-1000", "1000+"
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    region_state = Column(String(100), nullable=True)
    regulatory_profile = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    integration_status = Column(Text, nullable=False, default="{}")
    timezone = Column(String(50), nullable=False, default="UTC")
    deployment_mode = Column(String(20), nullable=False, default="production") # "sandbox", "production"
    managed_by_msp_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    # Governance & Analytics Control (Phase 5) — if False, telemetry is suppressed
    analytics_enabled = Column(sa.Boolean, nullable=False, default=True, server_default="1")

    # ── Governance Profile (Phase 8) ────────────────────────────────────
    revenue_band = Column(String(50), nullable=True)       # e.g. "<10M", "10M-100M", "100M-1B", "1B+"
    employee_count = Column(Integer, nullable=True)
    geo_regions = Column(Text, nullable=True)               # JSON array: ["US", "EU", "APAC"]
    processes_pii = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    processes_phi = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    processes_cardholder_data = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    handles_dod_data = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    uses_ai_in_production = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    government_contractor = Column(sa.Boolean, nullable=False, default=False, server_default="0")
    financial_services = Column(sa.Boolean, nullable=False, default=False, server_default="0")

    # ── Uptime Tier (Phase 8) ───────────────────────────────────────────
    application_tier = Column(String(20), nullable=True)    # "tier_1" (99.9%), "tier_2" (98%), "tier_3" (95%)
    sla_target = Column(Float, nullable=True)               # User-specified SLA target percentage

    # ── Clinic Specific (Product Layer) ─────────────────────────────────
    org_mode = Column(String(20), default="pilot")  # "demo", "pilot", "production"
    clinic_name = Column(String(255), nullable=True)
    clinic_type = Column(String(50), nullable=True)  # "dental", "medical", "optometry", etc.
    patient_volume_daily = Column(Integer, nullable=True)
    operating_hours_start = Column(String(5), nullable=True)  # "08:00"
    operating_hours_end = Column(String(5), nullable=True)    # "17:00"
    primary_contact_name = Column(String(255), nullable=True)
    primary_contact_role = Column(String(100), nullable=True)  # "Dr. Smith", "Office Manager"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ── Sprint 2.5 (Digital Twin / Decision Engine) ─────────────────────
    is_clone = Column(sa.Boolean, nullable=False, default=False, server_default="0", comment="True if org is a simulation clone.")
    source_org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, comment="If is_clone=True, the original org id.")

    
    # Relationships
    assessments = relationship("Assessment", back_populates="organization", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    external_findings = relationship("ExternalFinding", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")
    audit_calendar_entries = relationship("AuditCalendarEntry", back_populates="organization", cascade="all, delete-orphan")
    tech_stack_items = relationship("TechStackItem", back_populates="organization", cascade="all, delete-orphan")
    software_catalog_items = relationship("SoftwareCatalog", back_populates="organization", cascade="all, delete-orphan")
    discovered_assets = relationship("DiscoveredAsset", back_populates="organization", cascade="all, delete-orphan")
    host_assets = relationship("HostAsset", back_populates="organization", cascade="all, delete-orphan")
    technology_inventories = relationship("TechnologyInventory", back_populates="organization", cascade="all, delete-orphan")
    
    # ── Clinic Specific Relationships ───────────────────────────────────
    clinic_staff = relationship("ClinicStaff", cascade="all, delete-orphan")
    clinic_devices = relationship("ClinicDevice", cascade="all, delete-orphan")
    critical_systems = relationship("CriticalSystem", cascade="all, delete-orphan")
    msp_relationship = relationship("MSPRelationship", uselist=False, cascade="all, delete-orphan")
    value_metrics = relationship("ClinicValueMetric", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, owner={self.owner_uid})>"
