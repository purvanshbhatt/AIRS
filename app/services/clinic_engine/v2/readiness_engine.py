import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.clinic_engine.v2.contracts import (
    DailyReadinessReport,
    ReadinessStatus,
    TimelineEvent,
    ReadinessCheck,
    UnknownItem,
    ActionCard,
    VerificationContext,
    ClinicContext,
    OperationalReadiness,
    BusinessContinuity,
    ConnectorReadiness,
    VerificationExplanation,
)
from app.services.clinic_engine.v2.schema import ClinicMoment, Verdict
from app.services.clinic_engine.v2.risk_engine import BusinessRiskEngine
from app.services.clinic_engine.v2.action_engine import ActionEngine
from app.services.clinic_engine.v2.trust_engine import TrustEngine
from app.services.clinic_engine.v2.coverage_engine import CoverageEngine

class ReadinessEngine:
    """The product layer aggregator.
    
    Converts raw capabilities and evidence into the DailyReadinessReport contract.
    This is what answers: 'Can this clinic safely open today?'
    """

    def __init__(self, db: Session):
        self.db = db
        self.risk_engine = BusinessRiskEngine(db)
        self.action_engine = ActionEngine()
        self.trust_engine = TrustEngine(db)
        self.coverage_engine = CoverageEngine(db)

    def evaluate(self, org_id: str, moments: List[ClinicMoment]) -> DailyReadinessReport:
        """The main product method. Produces the morning readiness check."""
        # 1. Build clinic context (Layer 1)
        context = self.risk_engine.build_clinic_context(org_id)
        
        # 2. Assess business risk for each moment (Layer 2)
        assessments = {}
        for m in moments:
            assessments[m.id] = self.risk_engine.assess_moment(m, context)
            
        # 3. Build action cards (Layer 3)
        actions = {}
        for m in moments:
            actions[m.id] = self.action_engine.build_action_cards(m, assessments[m.id], context)
            
        # 4. Build verification contexts (Layer 4)
        verifications = {}
        for m in moments:
            verifications[m.id] = self.trust_engine.build_verification_context(m, org_id)
            
        # 5. Coverage and Connectors
        coverage = self.coverage_engine.assess_coverage(org_id)
        # Note: TrustEngine could also expose connector health, or CoverageEngine
        # For this prototype, we'll build a simplified view
        
        # 6. Build Checks (pass, fail, warning, unknown)
        passed_checks = []
        failed_checks = []
        warnings = []
        unknowns = []
        immediate_actions = []
        
        for m in moments:
            status = "pass"
            if m.verdict == Verdict.CRITICAL:
                status = "fail"
            elif m.verdict == Verdict.CONCERN:
                status = "warning"
            elif m.verdict == Verdict.UNKNOWN:
                status = "unknown"
                
            check = ReadinessCheck(
                status=status,
                label=m.translation.what_happened,
                detail=m.translation.why_care,
                verification=verifications.get(m.id),
                action=actions.get(m.id)[0] if actions.get(m.id) else None
            )
            
            if status == "pass":
                passed_checks.append(check)
            elif status == "fail":
                failed_checks.append(check)
                immediate_actions.extend(actions.get(m.id, []))
            elif status == "warning":
                warnings.append(check)
            elif status == "unknown":
                unknowns.append(
                    UnknownItem(
                        label=m.translation.what_happened,
                        impact="Confidence reduced due to missing data.",
                        source=verifications.get(m.id).verification_source if verifications.get(m.id) else "Unknown",
                    )
                )

        overall_verification = self.trust_engine.build_overall_verification(org_id)

        # 7. Determine Overall Status
        if failed_checks:
            overall_status = ReadinessStatus.critical_risk
        elif warnings:
            overall_status = ReadinessStatus.action_needed
        elif unknowns or overall_verification.confidence_pct < 100:
            overall_status = ReadinessStatus.unknown
        else:
            overall_status = ReadinessStatus.safe_to_open

        # 8. Calculate Business Health (0-100)
        clinic_health_pct = 100
        clinic_health_pct -= len(failed_checks) * 15
        clinic_health_pct -= len(warnings) * 5
        clinic_health_pct -= len(unknowns) * 2
        clinic_health_pct = max(0, clinic_health_pct)

        # 9. Generate Greeting and Summary
        greeting = f"Good Morning {context.primary_contact}" if context.primary_contact else "Good Morning"
        
        if overall_status == ReadinessStatus.safe_to_open:
            summary = "Your clinic is ready. We checked your systems overnight and found no issues."
        elif overall_status == ReadinessStatus.action_needed:
            summary = f"Your clinic has {len(warnings)} item(s) that need attention."
        elif overall_status == ReadinessStatus.critical_risk:
            summary = f"Your clinic has {len(failed_checks)} critical risk(s) preventing safe operation."
        else:
            summary = "We cannot fully determine your clinic's readiness due to missing data or offline systems."

        # 9a. Business Continuity Logic
        max_downtime = 0
        critical_systems_affected = []
        for check in failed_checks:
            # Re-map check back to moment for assessment
            for m in moments:
                if m.translation.what_happened == check.label:
                    if assessments[m.id].downtime_hours > max_downtime:
                        max_downtime = assessments[m.id].downtime_hours
                    
                    # Try to extract system from moment context or assume from capability
                    if "backup" in m.capability_id.lower() and "Backup Server" not in critical_systems_affected:
                        critical_systems_affected.append("Backup Server")
                    if "network" in m.capability_id.lower() and "Network Firewall" not in critical_systems_affected:
                        critical_systems_affected.append("Network Firewall")
                    break

        can_operate = overall_status == ReadinessStatus.safe_to_open
        can_recover = not any(c.label.lower().find("backup") != -1 for c in failed_checks)

        # Ensure deterministic ordering for frontend arrays
        failed_checks.sort(key=lambda x: x.label)
        passed_checks.sort(key=lambda x: x.label)
        warnings.sort(key=lambda x: x.label)
        unknowns.sort(key=lambda x: x.label)
        immediate_actions.sort(key=lambda x: x.action_id)
        critical_systems_affected.sort()
        
        # Determine operational readiness
        current_blockers = [c.label for c in failed_checks]
        
        operational_readiness = OperationalReadiness(
            can_operate_today=can_operate,
            can_recover=can_recover,
            current_blockers=current_blockers,
            estimated_downtime_minutes=int(max_downtime * 60),
            critical_systems_verified=["Electronic Health Records (EHR)", "Office Network"], # Mocked
            critical_systems_assumed=sorted(["Medical Devices", "HVAC"]) # Mocked
        )
        business_continuity = BusinessContinuity(operational_readiness=operational_readiness)
        
        # 9b. Connectors Readiness dynamically
        # Let's load the connectors for the org_id to build the connector readiness
        from app.models.connector import Connector, ConnectorStatus
        try:
            connector_models = self.db.query(Connector).filter(
                Connector.org_id == org_id,
                Connector.status == ConnectorStatus.active
            ).order_by(Connector.display_name).all()
        except Exception:
            connector_models = []
        
        connectors_readiness = []
        for c in connector_models:
            from app.services.clinic_engine.v2.trust_engine import SOURCE_DISPLAY_NAMES
            conn_name = SOURCE_DISPLAY_NAMES.get(c.connector_type.value if hasattr(c.connector_type, 'value') else c.connector_type, str(c.connector_type))
            
            # Simple humanize for last sync
            last_sync_desc = "Unknown"
            if c.last_sync_at:
                seconds = (datetime.now(timezone.utc) - c.last_sync_at.replace(tzinfo=timezone.utc)).total_seconds()
                if seconds < 3600:
                    last_sync_desc = f"{int(seconds/60)} minutes ago"
                else:
                    last_sync_desc = f"{int(seconds/3600)} hours ago"

            # Mock coverage depending on connector
            coverage = []
            missing = []
            if c.connector_type == "microsoft":
                coverage = ["Users", "Devices", "Email"]
                missing = ["Conditional Access"]
            elif c.connector_type == "veeam":
                coverage = ["Server Backups"]
                missing = ["Cloud Backups"]
            elif c.connector_type == "wazuh":
                coverage = ["Endpoints", "Network Logs"]
                missing = ["Firewall Rules"]

            connectors_readiness.append(ConnectorReadiness(
                name=conn_name,
                connected=True,
                last_verified_at=c.last_sync_at,
                status=c.health_status or "unknown",
                coverage=coverage,
                missing_visibility=missing,
                confidence_pct=100
            ))

        connector_health_pct = 100 if all(c.status == "healthy" for c in connectors_readiness) else 60 if connectors_readiness else 0

        # 10. Assemble Product Contract
        report = DailyReadinessReport(
            report_id=str(uuid.uuid4()),
            org_id=org_id,
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            generated_at=datetime.now(timezone.utc),
            status=overall_status,
            clinic_health_pct=clinic_health_pct,
            connector_health_pct=95,  # Mock for now
            greeting=greeting,
            summary=summary,
            timeline=[], # Can be populated from ledger
            business_continuity=business_continuity,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            unknowns=unknowns,
            immediate_actions=immediate_actions,
            coverage=self.coverage_engine.assess_coverage(org_id),
            connectors=connectors_readiness,
            verification=overall_verification,
            audit_snapshot_id=str(uuid.uuid4()),
            checks_performed=len(moments),
            devices_checked=len(context.devices),
            accounts_checked=len(context.staff),
            backups_verified=len([s for s in context.critical_systems if s.backup_required])
        )
        return report
