import enum
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.db.database import Base

class DeviceType(str, enum.Enum):
    workstation = "workstation"
    server = "server"
    laptop = "laptop"
    tablet = "tablet"
    mobile = "mobile"
    network_device = "network_device"
    printer = "printer"
    medical_device = "medical_device"

class ClinicDevice(Base):
    """Clinic device model for hardware tracking."""
    __tablename__ = "clinic_devices"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    location = Column(String(255), nullable=True)  # "Front Desk", "Exam Room 1"
    assigned_staff_id = Column(CHAR(36), ForeignKey("clinic_staff.id", ondelete="SET NULL"), nullable=True)
    critical_system_id = Column(CHAR(36), ForeignKey("critical_systems.id", ondelete="SET NULL"), nullable=True)
    os_type = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    external_device_id = Column(String(255), nullable=True, index=True)  # Links to Intune/Wazuh device
    business_impact_level = Column(String(20), nullable=False, default="medium")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
