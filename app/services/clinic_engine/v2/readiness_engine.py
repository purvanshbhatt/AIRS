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
    TrustContext,
    ClinicContext,
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
            
        # 4. Build trust contexts (Layer 4)
        trusts = {}
        for m in moments:
            trusts[m.id] = self.trust_engine.build_trust_context(m, org_id)
            
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
                trust=trusts.get(m.id),
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
                        source=trusts.get(m.id).evidence_source if trusts.get(m.id) else "Unknown",
                    )
                )

        overall_trust = self.trust_engine.build_overall_trust(org_id)

        # 7. Determine Overall Status
        if failed_checks:
            overall_status = ReadinessStatus.critical_risk
        elif warnings:
            overall_status = ReadinessStatus.action_needed
        elif unknowns or overall_trust.confidence_pct < 100:
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
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            unknowns=unknowns,
            immediate_actions=immediate_actions,
            coverage=coverage,
            connectors=[],
            trust=overall_trust,
            audit_snapshot_id=str(uuid.uuid4()),
            checks_performed=len(moments),
            devices_checked=len(context.devices),
            accounts_checked=len(context.staff),
            backups_verified=len([s for s in context.critical_systems if s.backup_required])
        )
        return report
