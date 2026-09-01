"""
Pilot Service — Organization Mode Management.

Supports Demo, Pilot, and Production organization modes.
Connectors and engines become mode-aware without changing their implementations.

In demo mode, seed_demo_clinic() creates a realistic synthetic clinic
that exercises every engine pathway.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.clinic_engine.v2.pilot")


class OrgMode:
    """Organization operating modes."""
    DEMO = "demo"
    PILOT = "pilot"
    PRODUCTION = "production"


class PilotService:
    """Organization mode management and demo data seeding."""

    def __init__(self, db: Session):
        self.db = db

    def get_mode(self, org_id: str) -> str:
        """Get the operating mode for an organization.

        Returns one of OrgMode.DEMO, OrgMode.PILOT, or OrgMode.PRODUCTION.

        INVARIANT: A missing org, null org_mode, or unrecognized org_mode
        is treated as PILOT (not demo). This prevents demo data from ever
        contaminating real customer tenants.
        """
        from app.models.organization import Organization
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return OrgMode.PILOT
        mode = getattr(org, "org_mode", None)
        if mode in (OrgMode.DEMO, OrgMode.PILOT, OrgMode.PRODUCTION):
            return mode
        # Unknown or null mode — treat as pilot (real), NEVER as demo
        return OrgMode.PILOT

    def is_demo(self, org_id: str) -> bool:
        return self.get_mode(org_id) == OrgMode.DEMO

    def is_pilot(self, org_id: str) -> bool:
        return self.get_mode(org_id) == OrgMode.PILOT

    def is_production(self, org_id: str) -> bool:
        return self.get_mode(org_id) == OrgMode.PRODUCTION

    def seed_demo_clinic(self, org_id: str) -> None:
        """Seed a complete synthetic clinic for demo/pilot.

        Creates 'Sunshine Dental Clinic' with realistic:
        - 8 staff members across roles
        - 12 devices across locations
        - 6 critical systems
        - 1 MSP relationship
        """
        from app.models.organization import Organization
        from app.models.clinic.staff import ClinicStaff, ClinicRole, ClinicDepartment, EmploymentStatus
        from app.models.clinic.device import ClinicDevice, DeviceType
        from app.models.clinic.critical_system import CriticalSystem, SystemType, HostingType
        from app.models.clinic.msp import MSPRelationship, MSPContractType
        from app.models.connector import Connector, ConnectorType, ConnectorAuthMethod, ConnectorStatus

        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            logger.warning("Cannot seed demo clinic: org %s not found", org_id)
            return

        # Idempotency check
        if self.db.query(MSPRelationship).filter_by(org_id=org_id).first():
            return

        # Update org with clinic metadata
        org.clinic_name = "Sunshine Dental Clinic"
        org.clinic_type = "dental"
        org.org_mode = OrgMode.DEMO
        org.patient_volume_daily = 35
        org.operating_hours_start = "08:00"
        org.operating_hours_end = "17:00"
        org.primary_contact_name = "Dr. Sarah Smith"
        org.primary_contact_role = "Owner / Lead Dentist"
        org.processes_phi = True
        org.industry = "healthcare"

        now = datetime.now(timezone.utc)

        # ── Staff ────────────────────────────────────────────────────────
        staff_data = [
            ("Dr. Sarah Smith", "dr.smith@sunshinedental.com", ClinicRole.physician,
             ClinicDepartment.clinical, EmploymentStatus.active,
             ["emr", "email", "scheduling", "imaging"], "high", "u-001"),
            ("Dr. Michael Chen", "dr.chen@sunshinedental.com", ClinicRole.physician,
             ClinicDepartment.clinical, EmploymentStatus.active,
             ["emr", "email", "scheduling", "imaging"], "high", "u-003"),
            ("Lisa Rodriguez", "lisa@sunshinedental.com", ClinicRole.nurse,
             ClinicDepartment.clinical, EmploymentStatus.active,
             ["emr", "email", "scheduling"], "high", "u-004"),
            ("Amy Park", "amy@sunshinedental.com", ClinicRole.nurse,
             ClinicDepartment.clinical, EmploymentStatus.active,
             ["emr", "email"], "high", "u-005"),
            ("Jessica Williams", "jessica@sunshinedental.com", ClinicRole.receptionist,
             ClinicDepartment.front_desk, EmploymentStatus.active,
             ["emr", "billing", "email", "scheduling"], "high", "u-006"),
            ("Jane Doe", "former.nurse@sunshinedental.com", ClinicRole.nurse,
             ClinicDepartment.clinical, EmploymentStatus.terminated,
             ["emr", "billing", "email"], "high", "u-002"),
            ("Robert Kim", "robert@sunshinedental.com", ClinicRole.billing_specialist,
             ClinicDepartment.billing, EmploymentStatus.active,
             ["billing", "email"], "medium", "u-007"),
            ("Patricia Moore", "patricia@sunshinedental.com", ClinicRole.office_manager,
             ClinicDepartment.administration, EmploymentStatus.active,
             ["emr", "billing", "email", "scheduling"], "high", "u-008"),
        ]

        for (name, email, role, dept, status, systems, impact, ext_id) in staff_data:
            staff = ClinicStaff(
                org_id=org_id,
                display_name=name,
                email=email,
                role=role,
                department=dept,
                employment_status=status,
                access_systems=systems,
                business_impact_level=impact,
                external_identity_id=ext_id,
                hire_date=now - timedelta(days=365),
                termination_date=(now - timedelta(days=45)) if status == EmploymentStatus.terminated else None,
            )
            self.db.add(staff)

        # ── Critical Systems ─────────────────────────────────────────────
        systems_data = [
            ("Dentrix", SystemType.emr, "Henry Schein", "G7.8", HostingType.on_premise, True, True, 0, 2),
            ("QuickBooks", SystemType.billing, "Intuit", "2026", HostingType.cloud, True, True, 4, 4),
            ("Microsoft 365", SystemType.email, "Microsoft", "E3", HostingType.cloud, False, True, 1, 1),
            ("Veeam Backup", SystemType.backup, "Veeam", "12.1", HostingType.on_premise, True, True, 0, 1),
            ("Dexis Imaging", SystemType.imaging, "Dexis", "11.0", HostingType.on_premise, False, True, 8, 8),
            ("Dentrix Ascend", SystemType.scheduling, "Henry Schein", "Cloud", HostingType.cloud, False, False, 4, 4),
        ]

        system_ids = {}
        for (name, stype, vendor, ver, hosting, backup_req, hipaa, dt_hours, rto) in systems_data:
            sys = CriticalSystem(
                org_id=org_id,
                system_name=name,
                system_type=stype,
                vendor_name=vendor,
                version=ver,
                hosting=hosting,
                backup_required=backup_req,
                hipaa_relevant=hipaa,
                downtime_tolerance_hours=dt_hours,
                recovery_objective_hours=rto,
            )
            self.db.add(sys)
            self.db.flush()
            system_ids[stype.value] = sys.id

        # ── Devices ──────────────────────────────────────────────────────
        devices_data = [
            ("FRONT-DESK-PC", DeviceType.workstation, "Front Desk", "Windows", "11", "d-001", "high", "emr"),
            ("BILLING-PC", DeviceType.workstation, "Billing Office", "Windows", "11", "d-002", "medium", "billing"),
            ("OPERATORY-1-PC", DeviceType.workstation, "Operatory 1", "Windows", "11", "d-003", "high", "emr"),
            ("OPERATORY-2-PC", DeviceType.workstation, "Operatory 2", "Windows", "11", "d-004", "high", "emr"),
            ("CLINIC-SERVER", DeviceType.server, "Server Room", "Windows Server", "2022", "d-005", "high", "backup"),
            ("DR-SMITH-LAPTOP", DeviceType.laptop, "Mobile", "Windows", "11", "d-006", "high", None),
            ("DR-CHEN-LAPTOP", DeviceType.laptop, "Mobile", "Windows", "11", "d-007", "high", None),
            ("XRAY-TABLET", DeviceType.tablet, "Operatory 1", "Android", "14", "d-008", "medium", "imaging"),
            ("RECEPTION-TABLET", DeviceType.tablet, "Front Desk", "iPad", "17", "d-009", "medium", None),
            ("OFFICE-PRINTER", DeviceType.printer, "Administration", None, None, "d-010", "low", None),
            ("PANORAMIC-XRAY", DeviceType.medical_device, "Imaging Room", None, None, "d-011", "high", "imaging"),
            ("STERILIZATION-MONITOR", DeviceType.medical_device, "Sterilization", None, None, "d-012", "medium", None),
        ]

        for (name, dtype, location, os_type, os_ver, ext_id, impact, sys_key) in devices_data:
            dev = ClinicDevice(
                org_id=org_id,
                device_name=name,
                device_type=dtype,
                location=location,
                os_type=os_type,
                os_version=os_ver,
                external_device_id=ext_id,
                business_impact_level=impact,
                critical_system_id=system_ids.get(sys_key),
            )
            self.db.add(dev)

        # ── MSP ──────────────────────────────────────────────────────────
        msp = MSPRelationship(
            org_id=org_id,
            msp_name="Pinnacle IT Solutions",
            contact_email="support@pinnacleit.com",
            contact_phone="555-0199",
            contract_type=MSPContractType.co_managed,
            escalation_email="urgent@pinnacleit.com",
            response_sla_hours=4,
        )
        self.db.add(msp)

        # ── Connectors ──
        connectors_data = [
            (ConnectorType.microsoft, "Microsoft 365", ConnectorAuthMethod.oauth, ConnectorStatus.active),
            (ConnectorType.wazuh, "Wazuh Security", ConnectorAuthMethod.api_key, ConnectorStatus.active),
            (ConnectorType.veeam, "Veeam Backup", ConnectorAuthMethod.api_key, ConnectorStatus.active),
        ]
        for (ctype, cname, auth, status) in connectors_data:
            conn = Connector(
                org_id=org_id,
                connector_type=ctype,
                display_name=cname,
                auth_method=auth,
                status=status,
                health_status="healthy",
                last_sync_at=now,
            )
            self.db.add(conn)

        self.db.commit()
        logger.info("Demo clinic seeded for org %s: 8 staff, 12 devices, 6 systems, 1 MSP, 3 Connectors", org_id)
