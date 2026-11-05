import enum
import uuid
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.db.database import Base

class ClinicRole(str, enum.Enum):
    physician = "physician"
    nurse = "nurse"
    receptionist = "receptionist"
    billing_specialist = "billing_specialist"
    office_manager = "office_manager"
    it_admin = "it_admin"
    lab_technician = "lab_technician"
    medical_assistant = "medical_assistant"
    other = "other"

class ClinicDepartment(str, enum.Enum):
    clinical = "clinical"
    front_desk = "front_desk"
    billing = "billing"
    administration = "administration"
    it = "it"
    laboratory = "laboratory"
    other = "other"

class EmploymentStatus(str, enum.Enum):
    active = "active"
    terminated = "terminated"
    on_leave = "on_leave"
    contractor = "contractor"

class ClinicStaff(Base):
    """Clinic staff model for tracking users and employment."""
    __tablename__ = "clinic_staff"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(SQLEnum(ClinicRole), nullable=False)
    department = Column(SQLEnum(ClinicDepartment), nullable=False)
    employment_status = Column(SQLEnum(EmploymentStatus), nullable=False, default=EmploymentStatus.active)
    access_systems = Column(JSON, nullable=False, default=list)  # ["emr", "billing", "email"]
    business_impact_level = Column(String(20), nullable=False, default="medium")  # high, medium, low
    external_identity_id = Column(String(255), nullable=True, index=True)  # Links to connector user ID
    hire_date = Column(DateTime(timezone=True), nullable=True)
    termination_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
