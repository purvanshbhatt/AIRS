from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.organization import Organization

try:
    from app.models.clinic_staff import ClinicStaff
    from app.models.clinic_device import ClinicDevice
    from app.models.critical_system import CriticalSystem
    from app.models.msp_relationship import MSPRelationship
except ImportError:
    pass

from app.services.clinic_engine.v2.contracts import (
    ClinicContext,
    StaffSummary,
    DeviceSummary,
    SystemSummary,
    MSPSummary,
    BusinessRiskAssessment,
    PatientImpact,
    ComplianceExposure,
    Urgency
)
from app.services.clinic_engine.v2.schema import ClinicMoment

class BusinessRiskEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def build_clinic_context(self, org_id: str) -> ClinicContext:
        """Load all clinic domain data into a ClinicContext object.

        If the organization is not yet seeded in the local DB (e.g. fresh Cloud Run
        instance before Firestore sync completes), returns a minimal ClinicContext
        so the ReadinessEngine can continue with graceful degradation instead of
        raising and triggering the Unknown fallback middleware.
        """
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            # Graceful degradation: org may not be seeded yet in ephemeral DB.
            # Return a minimal context so the engine can still produce a report.
            return ClinicContext(
                org_id=org_id,
                clinic_name=org_id,
                clinic_type="medical",
                staff=[],
                devices=[],
                critical_systems=[],
                msp=None
            )
            
        context = ClinicContext(
            org_id=org_id,
            clinic_name=org.name,
            clinic_type="medical",
            staff=[],
            devices=[],
            critical_systems=[],
            msp=None
        )
        
        try:
            from app.models.clinic.staff import ClinicStaff
            staff_records = self.db.query(ClinicStaff).filter(ClinicStaff.org_id == org_id).all()
            for s in staff_records:
                context.staff.append(StaffSummary(
                    id=s.id,
                    display_name=s.display_name,
                    role=s.role,
                    department=s.department,
                    employment_status=s.employment_status,
                    access_systems=s.access_systems or [],
                    business_impact_level=s.business_impact_level or "medium",
                    external_identity_id=s.external_identity_id,
                    email=s.email
                ))
        except ImportError:
            pass

        try:
            from app.models.clinic.device import ClinicDevice
            device_records = self.db.query(ClinicDevice).filter(ClinicDevice.org_id == org_id).all()
            for d in device_records:
                context.devices.append(DeviceSummary(
                    id=d.id,
                    device_name=d.device_name,
                    device_type=d.device_type,
                    location=d.location,
                    assigned_staff_name=None,
                    critical_system_name=d.critical_system_id, # Using ID as placeholder for name temporarily
                    business_impact_level=d.business_impact_level or "medium",
                    external_device_id=d.external_device_id
                ))
        except ImportError:
            pass
            
        try:
            from app.models.clinic.critical_system import CriticalSystem
            system_records = self.db.query(CriticalSystem).filter(CriticalSystem.org_id == org_id).all()
            for sys in system_records:
                context.critical_systems.append(SystemSummary(
                    id=sys.id,
                    system_name=sys.system_name,
                    system_type=sys.system_type,
                    hipaa_relevant=sys.hipaa_relevant,
                    backup_required=sys.backup_required,
                    downtime_tolerance_hours=sys.downtime_tolerance_hours or 24
                ))
        except ImportError:
            pass
            
        try:
            from app.models.clinic.msp import MSPRelationship
            msp = self.db.query(MSPRelationship).filter(MSPRelationship.org_id == org_id).first()
            if msp:
                context.msp = MSPSummary(
                    msp_name=msp.msp_name,
                    contact_email=msp.contact_email,
                    escalation_email=msp.escalation_email,
                    response_sla_hours=msp.response_sla_hours or 4
                )
        except ImportError:
            pass

        return context
        
    def _resolve_staff_context(self, moment: ClinicMoment, context: ClinicContext) -> Optional[StaffSummary]:
        if moment.capability_id in ['unauthorized_access', 'former_employee_access', 'suspicious_login']:
            for evidence_id in moment.evidence_ids:
                for staff in context.staff:
                    if staff.external_identity_id == evidence_id:
                        return staff
        return None

    def _resolve_device_context(self, moment: ClinicMoment, context: ClinicContext) -> Optional[DeviceSummary]:
        if moment.capability_id in ['device_compromise', 'missing_updates', 'av_disabled']:
            for evidence_id in moment.evidence_ids:
                for device in context.devices:
                    if device.external_device_id == evidence_id:
                        return device
        return None

    def assess_moment(self, moment: ClinicMoment, context: ClinicContext) -> BusinessRiskAssessment:
        """Deterministic business risk assessment. AI never decides."""
        staff = self._resolve_staff_context(moment, context)
        device = self._resolve_device_context(moment, context)
        
        assessment = BusinessRiskAssessment(
            patient_impact=PatientImpact.none,
            financial_impact_usd=0,
            downtime_hours=0.0,
            compliance_exposure=ComplianceExposure.none,
            urgency=Urgency.routine,
            overall_priority=0,
            risk_factors=[]
        )
        
        priority_score = 0
        
        # Staff has EMR access + terminated -> patient_impact=critical, compliance=critical, priority +40
        if staff and staff.employment_status == "terminated" and "EMR" in staff.access_systems:
            assessment.patient_impact = PatientImpact.critical
            assessment.compliance_exposure = ComplianceExposure.critical
            priority_score += 40
            assessment.risk_factors.append("Terminated staff retains EMR access")
            assessment.urgency = Urgency.immediate
            
        # Staff has billing access + terminated -> patient_impact=direct, compliance=high, priority +30
        elif staff and staff.employment_status == "terminated" and "billing" in staff.access_systems:
            if assessment.patient_impact != PatientImpact.critical:
                assessment.patient_impact = PatientImpact.direct
            if assessment.compliance_exposure not in [ComplianceExposure.critical]:
                assessment.compliance_exposure = ComplianceExposure.high
            priority_score += 30
            assessment.risk_factors.append("Terminated staff retains billing access")
            if assessment.urgency not in [Urgency.immediate]:
                assessment.urgency = Urgency.urgent

        # Device runs EMR + non-compliant -> patient_impact=critical, compliance=high, priority +35
        if device and device.critical_system_name == "EMR" and moment.capability_id in ['device_compromise', 'av_disabled', 'missing_updates']:
            if assessment.patient_impact != PatientImpact.critical:
                assessment.patient_impact = PatientImpact.critical
            if assessment.compliance_exposure not in [ComplianceExposure.critical]:
                assessment.compliance_exposure = ComplianceExposure.high
            priority_score += 35
            assessment.risk_factors.append("EMR device is non-compliant/compromised")
            assessment.urgency = Urgency.immediate

        # Backup system failed + hipaa_relevant -> patient_impact=direct, compliance=critical, priority +40
        if moment.capability_id == 'recovery_readiness':
            is_hipaa = any(sys.hipaa_relevant for sys in context.critical_systems)
            if is_hipaa:
                if assessment.patient_impact not in [PatientImpact.critical]:
                    assessment.patient_impact = PatientImpact.direct
                assessment.compliance_exposure = ComplianceExposure.critical
                priority_score += 40
                assessment.risk_factors.append("HIPAA-relevant backup failure")
                assessment.urgency = Urgency.immediate

        # Server missing update -> patient_impact=indirect, compliance=moderate, priority +15
        if moment.capability_id == 'missing_updates' and device and device.device_type == 'server':
            if assessment.patient_impact in [PatientImpact.none]:
                assessment.patient_impact = PatientImpact.indirect
            if assessment.compliance_exposure in [ComplianceExposure.none, ComplianceExposure.low]:
                assessment.compliance_exposure = ComplianceExposure.moderate
            priority_score += 15
            assessment.risk_factors.append("Server missing critical updates")

        # Workstation missing update -> patient_impact=none, compliance=low, priority +5
        if moment.capability_id == 'missing_updates' and device and device.device_type == 'workstation':
            if assessment.compliance_exposure in [ComplianceExposure.none]:
                assessment.compliance_exposure = ComplianceExposure.low
            priority_score += 5
            assessment.risk_factors.append("Workstation missing updates")

        # Active security alert on any device -> patient_impact=direct, urgency=immediate, priority +25
        if moment.capability_id == 'device_compromise':
            if assessment.patient_impact in [PatientImpact.none, PatientImpact.indirect]:
                assessment.patient_impact = PatientImpact.direct
            assessment.urgency = Urgency.immediate
            priority_score += 25
            assessment.risk_factors.append("Active security alert on device")
            
        assessment.overall_priority = min(100, priority_score)
        assessment.automation_possible = any(action.can_automate for action in moment.actions)
        
        return assessment
