import enum
import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.db.database import Base

class MSPContractType(str, enum.Enum):
    fully_managed = "fully_managed"
    co_managed = "co_managed"
    break_fix = "break_fix"
    none = "none"

class MSPRelationship(Base):
    """MSP relationship model."""
    __tablename__ = "msp_relationships"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    msp_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contract_type = Column(SQLEnum(MSPContractType), nullable=False)
    escalation_email = Column(String(255), nullable=True)
    response_sla_hours = Column(Integer, default=4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
