import enum
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.db.database import Base

class SystemType(str, enum.Enum):
    emr = "emr"
    billing = "billing"
    email = "email"
    backup = "backup"
    imaging = "imaging"
    scheduling = "scheduling"
    phone_system = "phone_system"
    network = "network"
    security_camera = "security_camera"
    lab_system = "lab_system"
    other = "other"

class HostingType(str, enum.Enum):
    on_premise = "on_premise"
    cloud = "cloud"
    hybrid = "hybrid"

class CriticalSystem(Base):
    """Clinic critical system model."""
    __tablename__ = "critical_systems"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_name = Column(String(255), nullable=False)
    system_type = Column(SQLEnum(SystemType), nullable=False)
    vendor_name = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True)
    hosting = Column(SQLEnum(HostingType), nullable=False)
    backup_required = Column(Boolean, default=True)
    hipaa_relevant = Column(Boolean, default=False)
    downtime_tolerance_hours = Column(Integer, default=24)
    recovery_objective_hours = Column(Integer, default=4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
