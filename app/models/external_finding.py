"""External finding model for mock SIEM ingestion demos."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ExternalFinding(Base):
    """Represents an externally ingested finding for an organization."""

    __tablename__ = "external_findings"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)
    source = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(32), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)

    organization = relationship("Organization", back_populates="external_findings")

    def __repr__(self):
        return f"<ExternalFinding(id={self.id}, org={self.org_id}, source={self.source})>"

