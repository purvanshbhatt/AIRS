"""
Readiness snapshot source for template reports.

Builds the server-side data snapshot every report template renders from.
Nothing here invents numbers: the readiness score, checks, coverage and
connector health come from the same clinic-engine pipeline that serves
``GET /api/clinic/readiness/{org_id}`` (demo orgs use demo telemetry, real
orgs use persisted connector telemetry). Missing data is reported as
"Not yet verified" with a reason, never guessed.

PRODUCT_MOAT: all numbers are deterministic and server-side.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization

logger = logging.getLogger("airs.reports.readiness_source")

SNAPSHOT_SCHEMA_VERSION = 1

# Demo organizations are identified the same way as the readiness endpoint.
_LEGACY_DEMO_ORG_IDS = {"acme-health-systems", "default-org", "sandbox-org"}


def is_demo_org(db: Session, org_id: str) -> bool:
    """Mirror of the readiness endpoint's demo detection."""
    if not org_id:
        return False
    if org_id.startswith("demo-") or org_id in _LEGACY_DEMO_ORG_IDS:
        return True
    try:
        from app.services.clinic_engine.v2.pilot import OrgMode, PilotService
        return PilotService(db).get_mode(org_id) == OrgMode.DEMO
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Demo detection failed for %s: %s", org_id, exc)
        return False


# ──────────────────────────────────────────────────────────────────────────
# Readiness report (reuses the clinic pipeline; no scoring duplicated here)
# ──────────────────────────────────────────────────────────────────────────

def build_readiness_report(db: Session, org_id: str, demo: Optional[bool] = None):
    """Run the clinic readiness pipeline for ``org_id`` and return a
    ``DailyReadinessReport`` plus the telemetry source label.

    This calls the exact service functions used by the readiness endpoint
    (demo telemetry generator, persisted telemetry loader, provider
    extraction, ``ClinicEvaluationEngine`` and ``ReadinessEngine``). Daily
    business-value metrics are read but NOT re-recorded, so generating a
    report never mutates the metrics ledger.
    """
    from app.api.clinic.router import _fetch_persisted_telemetry, get_demo_telemetry
    from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
    from app.services.clinic_engine.v2.metrics_engine import MetricsEngine
    from app.services.clinic_engine.v2.pilot import PilotService
    from app.services.clinic_engine.v2.providers import ProviderRegistry
    from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine

    if demo is None:
        demo = is_demo_org(db, org_id)

    if demo:
        try:
            PilotService(db).seed_demo_clinic(org_id)
        except Exception as exc:
            logger.debug("Demo seeding skipped for %s: %s", org_id, exc)
        events = get_demo_telemetry(org_id)
        source = "demo_telemetry"
    else:
        events = _fetch_persisted_telemetry(db, org_id)
        source = "persisted_telemetry"

    moments = []
    try:
        evidence = []
        for provider_cls in ProviderRegistry.list_all().values():
            evidence.extend(provider_cls.extract(events))
        moments = ClinicEvaluationEngine().evaluate(evidence)
    except Exception as exc:
        logger.warning("Evidence evaluation failed for org %s: %s", org_id, exc)
        moments = []

    report = ReadinessEngine(db).evaluate(org_id, moments)
    try:
        report.value = MetricsEngine(db).get_summary(org_id, days=30)
    except Exception as exc:
        logger.debug("Value summary unavailable for %s: %s", org_id, exc)

    return report, source, len(events)


# ──────────────────────────────────────────────────────────────────────────
# Supporting data: connectors, verification results, MSP, assessment
# ──────────────────────────────────────────────────────────────────────────

def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _enum_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    return getattr(value, "value", str(value))


def collect_connectors(db: Session, org_id: str) -> List[Dict[str, Any]]:
    """Connector inventory via ``ConnectorManager.list_connectors``."""
    try:
        from app.services.connector_manager import ConnectorManager
        rows = ConnectorManager(db, org_id).list_connectors()
    except Exception as exc:
        logger.warning("Connector listing failed for %s: %s", org_id, exc)
        return []
    out = []
    for c in rows:
        out.append({
            "name": c.display_name,
            "type": _enum_value(c.connector_type),
            "status": _enum_value(c.status),
            "health_status": _enum_value(getattr(c, "health_status", None)),
            "last_sync_at": _iso(getattr(c, "last_sync_at", None)),
            "sync_interval_minutes": getattr(c, "sync_interval_minutes", None),
            "error_message": getattr(c, "error_message", None),
            "permissions_validated": bool(getattr(c, "permissions_validated", False)),
        })
    return out


def collect_verification_results(db: Session, org_id: str) -> List[Dict[str, Any]]:
    """Control verification states from the Control Verification Engine."""
    try:
        from app.models.verification import VerificationResult
        rows = (
            db.query(VerificationResult)
            .filter(VerificationResult.organization_id == org_id)
            .order_by(VerificationResult.control_id)
            .all()
        )
    except Exception as exc:
        logger.warning("Verification lookup failed for %s: %s", org_id, exc)
        return []
    out = []
    for r in rows:
        try:
            evidence_count = len(r.evidence or [])
        except Exception:
            evidence_count = 0
        out.append({
            "control_id": r.control_id,
            "state": _enum_value(r.state),
            "confidence": _enum_value(r.confidence_level),
            "last_verified_at": _iso(r.last_verified_at),
            "evidence_count": evidence_count,
        })
    return out


def collect_msp(db: Session, org_id: str) -> Optional[Dict[str, Any]]:
    """MSP relationship, if the clinic has one on file."""
    try:
        from app.models.clinic.msp import MSPRelationship
        row = db.query(MSPRelationship).filter(MSPRelationship.org_id == org_id).first()
    except Exception as exc:
        logger.debug("MSP lookup failed for %s: %s", org_id, exc)
        return None
    if not row:
        return None
    return {
        "msp_name": row.msp_name,
        "contact_email": row.contact_email,
        "contact_phone": row.contact_phone,
        "escalation_email": row.escalation_email,
        "contract_type": _enum_value(row.contract_type),
        "response_sla_hours": row.response_sla_hours,
    }


def collect_assessment(db: Session, owner_uid: Optional[str], org_id: str,
                       assessment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Questionnaire assessment summary (when one exists) via ``AssessmentService``."""
    if not owner_uid:
        return None
    try:
        from app.models.assessment import Assessment
        from app.services.assessment import AssessmentService
        svc = AssessmentService(db, owner_uid=owner_uid)
        if assessment_id:
            assessment = svc.get(assessment_id)
            if assessment and assessment.organization_id != org_id:
                assessment = None
        else:
            assessment = (
                db.query(Assessment)
                .filter(
                    Assessment.organization_id == org_id,
                    Assessment.owner_uid == owner_uid,
                    Assessment.status != "archived",
                )
                .order_by(Assessment.created_at.desc())
                .first()
            )
        if not assessment:
            return None
        summary = svc.get_summary(assessment.id) or {}
    except Exception as exc:
        logger.debug("Assessment summary unavailable for %s: %s", org_id, exc)
        return None

    tier = summary.get("tier") if isinstance(summary.get("tier"), dict) else {}
    return {
        "id": assessment.id,
        "title": assessment.title,
        "status": assessment.status,
        "overall_score": summary.get("overall_score"),
        "tier_label": tier.get("label"),
        "maturity_level": tier.get("maturity_level"),
        "findings_count": summary.get("findings_count", 0),
        "critical_high_count": summary.get("critical_high_count", 0),
        "domain_scores": [
            {
                "domain_name": d.get("domain_name"),
                "score": d.get("score"),
                "score_5": d.get("score_5"),
            }
            for d in (summary.get("domain_scores") or [])
        ],
    }


# ──────────────────────────────────────────────────────────────────────────
# Snapshot assembly
# ──────────────────────────────────────────────────────────────────────────

def _org_block(org: Optional[Organization], org_id: str, demo: bool) -> Dict[str, Any]:
    if org is None:
        label = org_id.replace("demo-", "").replace("-", " ").title() if demo else org_id
        return {
            "id": org_id,
            "name": f"{label} (Demo)" if demo else org_id,
            "clinic_name": None,
            "industry": None,
            "contact_name": None,
            "contact_email": None,
            "org_mode": "demo" if demo else None,
            "is_demo": demo,
        }
    return {
        "id": org.id,
        "name": org.name,
        "clinic_name": getattr(org, "clinic_name", None),
        "industry": org.industry,
        "contact_name": getattr(org, "primary_contact_name", None) or org.contact_name,
        "contact_email": org.contact_email,
        "org_mode": getattr(org, "org_mode", None),
        "is_demo": demo,
    }


def compute_evidence_hash(readiness: Dict[str, Any]) -> str:
    """SHA-256 over the canonical readiness JSON. Deterministic for a snapshot."""
    canonical = json.dumps(readiness, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_template_snapshot(
    db: Session,
    org_id: str,
    template: str,
    fmt: str = "pdf",
    org: Optional[Organization] = None,
    owner_uid: Optional[str] = None,
    assessment_id: Optional[str] = None,
    demo: Optional[bool] = None,
) -> Dict[str, Any]:
    """Assemble the JSON-serialisable snapshot every template renders from."""
    if demo is None:
        demo = is_demo_org(db, org_id)

    readiness_model, source, event_count = build_readiness_report(db, org_id, demo=demo)
    readiness = readiness_model.model_dump(mode="json")

    failed = readiness.get("failed_checks") or []
    warnings = readiness.get("warnings") or []
    unknowns = readiness.get("unknowns") or []
    findings_count = len(failed) + len(warnings) + len(unknowns)

    assessment = collect_assessment(db, owner_uid, org_id, assessment_id)
    overall_score = readiness.get("clinic_health_pct")
    if template == "executive_pdf" and assessment and assessment.get("overall_score") is not None:
        overall_score = assessment["overall_score"]

    snapshot: Dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "template": template,
        "format": fmt,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organization": _org_block(org, org_id, demo),
        "data_source": source,
        "telemetry_event_count": event_count,
        "readiness": readiness,
        "connectors": collect_connectors(db, org_id),
        "verification_results": collect_verification_results(db, org_id),
        "msp": collect_msp(db, org_id),
        "assessment": assessment,
        "overall_score": overall_score,
        "findings_count": findings_count,
    }
    snapshot["evidence_hash"] = compute_evidence_hash(readiness)
    return snapshot
