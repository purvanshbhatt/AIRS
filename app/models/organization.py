"""
Organization model.
"""

import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, Text, Integer, Float
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
    notes = Column(Text, nullable=True)
    integration_status = Column(Text, nullable=False, default="{}")
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessments = relationship("Assessment", back_populates="organization", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    external_findings = relationship("ExternalFinding", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")
    audit_calendar_entries = relationship("AuditCalendarEntry", back_populates="organization", cascade="all, delete-orphan")
    tech_stack_items = relationship("TechStackItem", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, owner={self.owner_uid})>"
