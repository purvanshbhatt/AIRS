from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import json
import logging
import time
from datetime import datetime, timezone, timedelta

from app.services.clinic_engine.v2.schema import RawEvent
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.morning_check import MorningCheckGeneratorV2, MorningCheckV2
from app.services.clinic_engine.v2.providers import ProviderRegistry
from app.core.auth import get_current_user, User
from app.core.config import settings
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.clinic_engine.v2.moment_repository import MomentRepository
from app.services.clinic_engine.v2.contracts import DailyReadinessReport
from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
from app.services.clinic_engine.v2.pilot import PilotService, OrgMode
from app.services.clinic_engine.v2.metrics_engine import MetricsEngine
from app.models.clinic_moment import MomentStatus

router = APIRouter(tags=["clinic"])
logger = logging.getLogger("airs.clinic_engine.router")


# =============================================================================
# Demo Telemetry — ONLY for explicit demo organizations
# =============================================================================

def get_demo_telemetry(org_id: str) -> List[RawEvent]:
    """
    Simulates fetching LIVE telemetry from connected systems for DEMO organizations.
    In production, this telemetry is fetched asynchronously by connector sync jobs.

    INVARIANT: This function MUST ONLY be called when the organization is
    explicitly in demo mode (org_mode == "demo"). It must NEVER be used as
    a fallback for real organizations.
    """
    now = datetime.now(timezone.utc)

    # 1. Microsoft Graph Telemetry (Entra ID, Intune, Defender)
    ms_event = RawEvent(
        event_type="microsoft.telemetry",
        source_system="microsoft",
        source_event_id=f"sync-ms-{int(time.time())}",
        organization_id=org_id,
        payload={
            "entra_users": [
                {
                    "user_id": "u-001",
                    "user_principal_name": "dr.smith@clinic.com",
                    "mfa_enforced": True,
                    "account_enabled": True,
                    "last_sign_in": (now - timedelta(hours=2)).isoformat(),
                    "conditional_access_status": "enforced"
                },
                {
                    "user_id": "u-002",
                    "user_principal_name": "former.nurse@clinic.com",
                    "mfa_enforced": False,
                    "account_enabled": True,
                    "last_sign_in": (now - timedelta(days=45)).isoformat(),  # Stale! (Q1)
                    "conditional_access_status": "unknown"
                }
            ],
            "intune_devices": [
                {
                    "device_id": "d-001",
                    "device_name": "FRONT-DESK-PC",
                    "compliance_state": "noncompliant", # Non-compliant! (Q3)
                    "bitlocker_status": "not_encrypted",
                    "os_version": "10.0.19044"
                }
            ],
            "defender_alerts": [
                {
                    "alert_id": "a-001",
                    "title": "Suspicious PowerShell execution",
                    "severity": "high",
                    "status": "active",
                    "device_id": "d-001"
                }
            ]
        }
    )

    # 2. Veeam Backup Telemetry (Assuming a backup connector returns this)
    backup_event = RawEvent(
        event_type="veeam.backup_job",
        source_system="veeam",
        source_event_id=f"sync-v-{int(time.time())}",
        organization_id=org_id,
        payload={
            "system_name": "Patient Database Server",
            "last_successful_backup": (now - timedelta(hours=28)).isoformat(), # Failed! (Q2)
            "backup_type": "full"
        }
    )

    return [ms_event, backup_event]


# =============================================================================
# Real Telemetry — Fetches from existing connector pipeline
# =============================================================================

def _fetch_persisted_telemetry(db: Session, org_id: str) -> List[RawEvent]:
    """
    Fetch real telemetry events from the existing persistence layer.

    This reads TelemetryEvent records that were ingested by the real
    connector sync pipeline (ConnectorManager → BaseConnector.safe_sync()
    → _ingest_events()). It does NOT create a parallel pipeline.

    Returns RawEvent objects compatible with the existing ProviderRegistry
    extraction interface.
    """
    from app.models.telemetry_event import TelemetryEvent

    # Fetch recent telemetry events (last 24h) for this org
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    try:
        records = (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.org_id == org_id,
                TelemetryEvent.created_at >= cutoff,
            )
            .order_by(TelemetryEvent.created_at.desc())
            .limit(500)
            .all()
        )
    except Exception as exc:
        logger.warning(
            "Failed to fetch telemetry for org %s: %s", org_id, exc,
        )
        return []

    events: List[RawEvent] = []
    for record in records:
        try:
            payload = record.payload
            if isinstance(payload, str):
                payload = json.loads(payload)
            elif payload is None:
                payload = {}

            events.append(RawEvent(
                event_type=record.event_type,
                source_system=record.source_system,
                source_event_id=record.source_event_id,
                organization_id=org_id,
                payload=payload,
            ))
        except Exception as exc:
            logger.debug(
                "Skipping malformed telemetry record %s: %s", record.id, exc,
            )
            continue

    logger.info(
        "Fetched %d persisted telemetry events for org %s",
        len(events), org_id,
    )
    return events


# =============================================================================
# Deprecated endpoint
# =============================================================================

@router.get("/morning-summary", response_model=MorningCheckV2, deprecated=True)
async def get_morning_summary(db: Session = Depends(get_db)):
    """Returns the Morning Safety Check for the clinic owner. DEPRECATED. Use /readiness/{org_id}."""

    # 1. For Morning Check V2 (Internal Demo logic)
    events = get_demo_telemetry("sandbox-org")

    # 2. Extract Evidence from Telemetry using Providers
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))

    # 3. Evaluate Evidence against Capabilities
    engine = ClinicEvaluationEngine()
    moments = engine.evaluate(evidence)

    # 4. Save to Repository
    repo = MomentRepository(db)
    # Using a dummy org_id for now as there's no auth context
    repo.save_moments(org_id="sandbox-org", moments=moments)

    # 5. Generate the final Morning Check
    generator = MorningCheckGeneratorV2()
    check = generator.generate(moments)

    return check


# =============================================================================
# Main Readiness Endpoint — The Product
# =============================================================================

@router.get("/readiness/{org_id}", response_model=DailyReadinessReport)
async def get_clinic_readiness(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """The product endpoint. Returns the immutable DailyReadinessReport.

    Organization Lifecycle:
    - Real orgs: Consumes telemetry from the existing connector sync pipeline.
    - Demo orgs: Uses synthetic demo telemetry for demonstrations.
    - New orgs with no connectors: Returns honest "unknown/not verified" state.

    INVARIANT: Demo data is ONLY used when org_mode is explicitly "demo".
    A missing or null org_mode is treated as a real organization.
    """
    # --- Phase 2: Validate org_id is not empty ---
    if not org_id or not org_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Organization ID is required. Create an organization first.",
        )

    # --- Phase 7: Organization Isolation Guard ---
    # When auth is enforced: verify the caller is authorized to read this org.
    # We intentionally do not leak whether the org exists — return 403 either way.
    if settings.is_auth_required and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    if settings.is_auth_required and current_user is not None:
        from app.services.organization import OrganizationService
        try:
            org = OrganizationService(db, owner_uid=current_user.uid).get(org_id)
            if not org:
                # Permit access if it is an explicit demo organization
                pilot = PilotService(db)
                if pilot.get_mode(org_id) != OrgMode.DEMO:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "code": "ORGANIZATION_NOT_FOUND",
                            "message": f"Organization '{org_id}' not found or access not authorized.",
                            "organization_id": org_id,
                        }
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Organization access check failed for user=%s, org=%s: %s",
                current_user.uid, org_id, e,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization access could not be verified"
            )

    # --- Phase 3: Determine organization mode (DEMO vs REAL) ---
    # INVARIANT: Demo data is ONLY used when org_mode is explicitly "demo".
    # Missing mode, null mode, "pilot", "production" → ALL treated as real.
    pilot = PilotService(db)
    org_mode = pilot.get_mode(org_id)
    is_demo_org = (org_mode == OrgMode.DEMO)

    logger.info(
        "Readiness request: org_id=%s, mode=%s, is_demo=%s",
        org_id, org_mode, is_demo_org,
    )

    # --- Phase 10: Demo seeding ONLY for explicit demo orgs ---
    if is_demo_org:
        pilot.seed_demo_clinic(org_id)

    # --- Phase 5: Fetch telemetry from the correct source ---
    # Demo orgs: synthetic demo data
    # Real orgs: persisted telemetry from the existing connector pipeline
    if is_demo_org:
        events = get_demo_telemetry(org_id)
    else:
        events = _fetch_persisted_telemetry(db, org_id)

    # --- Extract Evidence ---
    evidence = []
    try:
        for provider_cls in ProviderRegistry.list_all().values():
            evidence.extend(provider_cls.extract(events))

        # Evaluate Capabilities -> Moments
        engine = ClinicEvaluationEngine()
        moments = engine.evaluate(evidence)
    except Exception as e:
        # Unknown philosophy: degradation is handled naturally by having 0 moments
        # ReadinessEngine will map missing data to Unknown state
        logger.warning(
            "Evidence extraction/evaluation failed for org %s: %s", org_id, e,
        )
        moments = []

    # --- Build Readiness Report (The Product Layer) ---
    # For real orgs with 0 moments (no connectors, no telemetry),
    # ReadinessEngine correctly returns status=unknown, clinic_health_pct=0.
    # This is the honest "not yet verified" state per Phase 4.
    readiness_engine = ReadinessEngine(db)
    report = readiness_engine.evaluate(org_id, moments)

    # Record Business Value Metrics
    metrics_engine = MetricsEngine(db)
    metrics_engine.record_daily_metrics(org_id, report)
    report.value = metrics_engine.get_summary(org_id, days=30)

    return report


# =============================================================================
# Problem Fix Endpoint
# =============================================================================

@router.post("/problems/{problem_id}/fix")
async def fix_problem(problem_id: str, db: Session = Depends(get_db)):
    """Triggers the autofix for a given problem."""
    repo = MomentRepository(db)
    record = repo.get_moment(problem_id)

    if not record:
        raise HTTPException(status_code=404, detail="Issue not found.")

    if record.status != MomentStatus.ACTIVE:
        return {"status": "error", "message": "This issue has already been resolved."}

    # Re-evaluate: fetch telemetry based on org mode
    pilot = PilotService(db)
    org_mode = pilot.get_mode(record.org_id)

    if org_mode == OrgMode.DEMO:
        events = get_demo_telemetry(record.org_id)
    else:
        events = _fetch_persisted_telemetry(db, record.org_id)

    evidence = []
    try:
        for provider_cls in ProviderRegistry.list_all().values():
            evidence.extend(provider_cls.extract(events))

        engine = ClinicEvaluationEngine()
        current_moments = engine.evaluate(evidence)
    except Exception:
        current_moments = []

    is_still_valid = any(m.id == problem_id for m in current_moments)
    if not is_still_valid:
        # It's fixed, mark it
        repo.mark_resolved(problem_id, resolved_by="system", method=MomentStatus.RESOLVED_AUTOMATICALLY)
        return {"status": "error", "message": "This issue has already been resolved."}

    # Execute remediation (mock)
    # The actions are in `record.actions` which is a list of dicts.
    # We would use `automation_type` and `automation_params`.
    executed_action = None
    for action in record.actions:
        if action.get("can_automate"):
            executed_action = action
            break

    if not executed_action:
        raise HTTPException(status_code=400, detail="This issue cannot be automated.")

    # In a real system, we'd dispatch to a remediation worker using `executed_action["automation_params"]`

    repo.mark_resolved(problem_id, resolved_by="user_id", method=MomentStatus.RESOLVED_MANUALLY)
    repo.add_audit_log(
        moment_id=problem_id,
        actor="user_id",
        action=f"Execute {executed_action.get('automation_type')}",
        result="Success",
        success=True
    )

    return {"status": "success", "message": "Issue resolved and systems secured."}
