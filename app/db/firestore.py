"""
Cloud Firestore persistence layer.

Provides a Firestore client and sync utilities so that organization data
survives Cloud Run cold starts (SQLite is wiped on each new instance).

Strategy:
  - On startup, sync Firestore → SQLite so existing SQLAlchemy queries work.
  - On every org create/update/delete, dual-write to both SQLite and Firestore.
  - Firestore is the *source of truth* for data that must persist.
  - FAIL FAST: If Firestore is unavailable, raise an error instead of silently falling back.
  - LOCAL/TEST: When FIRESTORE_EMULATOR_HOST is set, connects to the emulator
    with a demo project ID (no GCP credentials required).

Collections:
  organizations/{org_id}      — full org document
  assessments/{assessment_id} — assessment metadata
  audit_events/{event_id}     — audit trail
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("airs.firestore")


ASSESSMENT_SENSITIVE_FIELDS = {
    "title",
    "answers",
    "scores",
    "findings",
    "maturity_name",
    "completed_at",
}

FINDING_TRACKING_SENSITIVE_FIELDS = {
    "owner",
    "due_date",
    "control_id",
    "framework_tag",
}

# Firestore client — lazy-initialized
_firestore_client = None
_firestore_available = False
_firestore_init_attempted = False


class FirestoreUnavailableError(Exception):
    """Raised when Firestore is required but not available."""
    pass


def _init_firestore():
    """
    Initialize Firestore client.

    Order of preference:
      1. Emulator — if FIRESTORE_EMULATOR_HOST is set, use it (no creds needed).
      2. Firebase Admin SDK — production / Cloud Run path.
    """
    global _firestore_client, _firestore_available, _firestore_init_attempted

    if _firestore_init_attempted:
        return _firestore_available

    _firestore_init_attempted = True

    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")

    if emulator_host:
        try:
            from google.cloud import firestore as gc_firestore  # type: ignore
            # The emulator doesn't require auth — use a dummy project id.
            os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host
            _firestore_client = gc_firestore.Client(project="demo-airs-local")
            _firestore_available = True
            logger.info(
                "Firestore emulator connected at %s (project=demo-airs-local)",
                emulator_host,
            )
        except Exception as exc:
            _firestore_available = False
            logger.error("Firestore emulator init failed: %s", exc)
        return _firestore_available

    try:
        from firebase_admin import firestore as fb_firestore
        _firestore_client = fb_firestore.client()
        _firestore_available = True
        logger.info("Firestore client initialized successfully")
    except Exception as exc:
        _firestore_available = False
        logger.error("CRITICAL: Firestore initialization failed: %s", exc)
        logger.error("Data persistence will NOT work. Check Firebase Admin SDK configuration.")

    return _firestore_available


def reset_firestore_state():
    """
    Reset the module-level Firestore state so that the next call to
    ``_init_firestore()`` re-initialises the client from scratch.

    Used by the test harness to inject mocks between test runs.
    """
    global _firestore_client, _firestore_available, _firestore_init_attempted
    _firestore_client = None
    _firestore_available = False
    _firestore_init_attempted = False


def is_firestore_available() -> bool:
    """Check if Firestore is available."""
    return _init_firestore()


def require_firestore() -> bool:
    """
    Require Firestore to be available. Raises FirestoreUnavailableError if not.
    Call this before any write operation to ensure data persistence.
    """
    if not is_firestore_available():
        raise FirestoreUnavailableError(
            "Firestore is not available. Data cannot be persisted. "
            "Check Firebase Admin SDK configuration and GCP credentials."
        )
    return True


def get_firestore_client():
    """Get the Firestore client. Raises error if unavailable."""
    _init_firestore()
    if _firestore_client is None:
        raise FirestoreUnavailableError("Firestore client not initialized")
    return _firestore_client


# ═══════════════════════════════════════════════════════════════════════
# Organization Persistence
# ═══════════════════════════════════════════════════════════════════════

def _org_to_doc(org) -> Dict[str, Any]:
    """Convert a SQLAlchemy Organization to a Firestore document dict.

    When the ``EncryptionService`` is enabled, sensitive fields
    (name, contact_email, etc.) are encrypted into a single
    ``encrypted_blob`` before storage.  Non-sensitive fields remain
    plaintext for Firestore queries / indexing.
    """
    doc = {
        "id": org.id,
        "owner_uid": org.owner_uid,
        "name": org.name,
        "industry": org.industry,
        "size": org.size,
        "contact_email": org.contact_email,
        "contact_name": org.contact_name,
        "notes": org.notes,
        "integration_status": org.integration_status or "{}",
        "analytics_enabled": bool(org.analytics_enabled),
        "revenue_band": org.revenue_band,
        "employee_count": org.employee_count,
        "geo_regions": org.geo_regions,  # stored as JSON string
        "processes_pii": bool(org.processes_pii),
        "processes_phi": bool(org.processes_phi),
        "processes_cardholder_data": bool(org.processes_cardholder_data),
        "handles_dod_data": bool(org.handles_dod_data),
        "uses_ai_in_production": bool(org.uses_ai_in_production),
        "government_contractor": bool(org.government_contractor),
        "financial_services": bool(org.financial_services),
        "application_tier": org.application_tier,
        "sla_target": org.sla_target,
        "created_at": org.created_at.isoformat() if org.created_at else datetime.now(timezone.utc).isoformat(),
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }

    # ── Field-level encryption ────────────────────────────────────────
    try:
        from app.core.security.encryption import get_encryption_service
        svc = get_encryption_service()
        if svc.enabled:
            doc = svc.encrypt_fields(doc)
    except Exception as exc:
        logger.warning("Encryption skipped for org %s: %s", org.id, exc)

    return doc


def _decrypt_org_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt a Firestore org document if it contains an encrypted blob."""
    if "encrypted_blob" not in doc:
        return doc
    try:
        from app.core.security.encryption import get_encryption_service
        svc = get_encryption_service()
        return svc.decrypt_fields(doc)
    except Exception as exc:
        logger.warning("Decryption failed for org %s: %s", doc.get("id"), exc)
        return doc


def _encrypt_doc_fields(doc: Dict[str, Any], sensitive_fields: set[str]) -> Dict[str, Any]:
    """Encrypt selected fields in a Firestore document when encryption is enabled."""
    try:
        from app.core.security.encryption import get_encryption_service

        svc = get_encryption_service()
        if not svc.enabled:
            return doc
        return svc.encrypt_fields(doc, sensitive_fields=sensitive_fields)
    except Exception as exc:
        logger.warning("Encryption skipped for Firestore document: %s", exc)
        return doc


def _decrypt_doc_fields(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt a Firestore document if it contains encrypted field metadata."""
    if "encrypted_blob" not in doc:
        return doc
    try:
        from app.core.security.encryption import get_encryption_service

        svc = get_encryption_service()
        return svc.decrypt_fields(doc)
    except Exception as exc:
        logger.warning("Decryption failed for Firestore document: %s", exc)
        return doc


def firestore_save_org(org) -> bool:
    """
    Save/update an organization to Firestore.
    
    IMPORTANT: This function MUST succeed for data persistence.
    Raises FirestoreUnavailableError if Firestore is not available.
    """
    require_firestore()
    try:
        client = get_firestore_client()
        doc_ref = client.collection("organizations").document(org.id)
        doc_ref.set(_org_to_doc(org))
        logger.info("Firestore: saved org %s (%s)", org.id, org.name)
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error("CRITICAL: Firestore save_org failed for %s: %s", org.id, exc)
        raise FirestoreUnavailableError(f"Failed to save organization to Firestore: {exc}")


def firestore_delete_org(org_id: str) -> bool:
    """
    Delete an organization from Firestore.
    
    IMPORTANT: This function MUST succeed for data consistency.
    Raises FirestoreUnavailableError if Firestore is not available.
    """
    require_firestore()
    try:
        client = get_firestore_client()
        client.collection("organizations").document(org_id).delete()
        logger.info("Firestore: deleted org %s", org_id)
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error("CRITICAL: Firestore delete_org failed for %s: %s", org_id, exc)
        raise FirestoreUnavailableError(f"Failed to delete organization from Firestore: {exc}")


def firestore_get_all_orgs(owner_uid: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all organizations from Firestore, optionally filtered by owner.
    
    Returns empty list if Firestore is unavailable (startup sync gracefully handles this).
    """
    if not is_firestore_available():
        logger.warning("Firestore not available for get_all_orgs — returning empty list")
        return []
    try:
        client = get_firestore_client()
        query = client.collection("organizations")
        if owner_uid:
            query = query.where("owner_uid", "==", owner_uid)
        docs = query.stream()
        return [_decrypt_org_doc(doc.to_dict()) for doc in docs]
    except Exception as exc:
        logger.error("Firestore get_all_orgs failed: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════════════════
# Startup Sync: Firestore → SQLite
# ═══════════════════════════════════════════════════════════════════════

def sync_orgs_from_firestore(db_session) -> int:
    """
    On startup, pull all orgs from Firestore into SQLite so that
    SQLAlchemy queries work seamlessly.

    Returns the number of orgs synced.
    """
    if not is_firestore_available():
        return 0

    from app.models.organization import Organization
    from datetime import datetime

    try:
        docs = firestore_get_all_orgs()
        count = 0
        for doc in docs:
            org_id = doc.get("id")
            if not org_id:
                continue

            existing = db_session.query(Organization).filter(Organization.id == org_id).first()
            if existing:
                # Update in-place
                for key, value in doc.items():
                    if key in ("created_at", "updated_at"):
                        if value:
                            try:
                                value = datetime.fromisoformat(value)
                            except (ValueError, TypeError):
                                continue
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Insert new
                org = Organization(id=org_id)
                for key, value in doc.items():
                    if key in ("created_at", "updated_at"):
                        if value:
                            try:
                                value = datetime.fromisoformat(value)
                            except (ValueError, TypeError):
                                continue
                        else:
                            continue
                    if hasattr(org, key) and key != "id":
                        setattr(org, key, value)
                db_session.add(org)
            count += 1

        db_session.commit()
        logger.info("Firestore sync: %d organizations loaded into SQLite", count)
        return count
    except Exception as exc:
        db_session.rollback()
        logger.warning("Firestore sync failed: %s", exc)
        return 0


# ═══════════════════════════════════════════════════════════════════════
# Assessment Persistence
# ═══════════════════════════════════════════════════════════════════════

def _dt_to_iso(value) -> Optional[str]:
    """Convert datetime-like value to ISO string."""
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return None


def _iso_to_dt(value: Optional[str]):
    """Parse ISO timestamp safely."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _assessment_to_doc(assessment, answers: Optional[List[Any]] = None,
                       scores: Optional[List[Any]] = None,
                       findings: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Convert a SQLAlchemy Assessment + related records to Firestore doc."""
    answers = answers if answers is not None else list(getattr(assessment, "answers", []) or [])
    scores = scores if scores is not None else list(getattr(assessment, "scores", []) or [])
    findings = findings if findings is not None else list(getattr(assessment, "findings", []) or [])

    doc = {
        "id": assessment.id,
        "organization_id": assessment.organization_id,
        "owner_uid": assessment.owner_uid,
        "version": assessment.version,
        "status": getattr(assessment.status, "value", assessment.status),
        "title": assessment.title,
        "schema_version": getattr(assessment, "schema_version", 1),
        "overall_score": assessment.overall_score,
        "maturity_level": assessment.maturity_level,
        "maturity_name": assessment.maturity_name,
        "created_at": _dt_to_iso(assessment.created_at) or datetime.now(timezone.utc).isoformat(),
        "updated_at": _dt_to_iso(assessment.updated_at),
        "completed_at": _dt_to_iso(assessment.completed_at),
        "answers": [
            {
                "id": a.id,
                "question_id": a.question_id,
                "value": a.value,
                "notes": a.notes,
                "created_at": _dt_to_iso(a.created_at),
                "updated_at": _dt_to_iso(a.updated_at),
            }
            for a in answers
        ],
        "scores": [
            {
                "id": s.id,
                "domain_id": s.domain_id,
                "domain_name": s.domain_name,
                "score": s.score,
                "max_score": s.max_score,
                "weight": s.weight,
                "weighted_score": s.weighted_score,
                "raw_points": s.raw_points,
                "max_raw_points": s.max_raw_points,
                "created_at": _dt_to_iso(s.created_at),
            }
            for s in scores
        ],
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "severity": getattr(f.severity, "value", f.severity),
                "status": getattr(f.status, "value", f.status),
                "domain_id": f.domain_id,
                "domain_name": f.domain_name,
                "question_id": f.question_id,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "priority": f.priority,
                "nist_function": f.nist_function,
                "nist_category": f.nist_category,
                "nist_subcategory": f.nist_subcategory,
                "soc2_controls": f.soc2_controls,
                "created_at": _dt_to_iso(f.created_at),
                "updated_at": _dt_to_iso(f.updated_at),
            }
            for f in findings
        ],
    }

    return _encrypt_doc_fields(doc, ASSESSMENT_SENSITIVE_FIELDS)


def _decrypt_assessment_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt Firestore assessment payload if encrypted."""
    return _decrypt_doc_fields(doc)


def firestore_save_assessment(assessment, answers: Optional[List[Any]] = None,
                              scores: Optional[List[Any]] = None,
                              findings: Optional[List[Any]] = None) -> bool:
    """
    Save/update an assessment payload to Firestore.

    Stores assessment metadata plus answers/scores/findings so Cloud Run
    instance restarts do not lose completed assessment state.
    """
    require_firestore()
    try:
        client = get_firestore_client()
        payload = _assessment_to_doc(assessment, answers=answers, scores=scores, findings=findings)
        client.collection("assessments").document(assessment.id).set(payload)
        logger.info("Firestore: saved assessment %s (org=%s)", assessment.id, assessment.organization_id)
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error("CRITICAL: Firestore save_assessment failed for %s: %s", assessment.id, exc)
        raise FirestoreUnavailableError(f"Failed to save assessment to Firestore: {exc}")


def firestore_delete_assessment(assessment_id: str) -> bool:
    """Delete an assessment from Firestore."""
    require_firestore()
    try:
        client = get_firestore_client()
        client.collection("assessments").document(assessment_id).delete()
        logger.info("Firestore: deleted assessment %s", assessment_id)
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error("CRITICAL: Firestore delete_assessment failed for %s: %s", assessment_id, exc)
        raise FirestoreUnavailableError(f"Failed to delete assessment from Firestore: {exc}")


def firestore_get_all_assessments(owner_uid: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all persisted assessments from Firestore."""
    if not is_firestore_available():
        logger.warning("Firestore not available for get_all_assessments — returning empty list")
        return []
    try:
        client = get_firestore_client()
        query = client.collection("assessments")
        if owner_uid:
            query = query.where("owner_uid", "==", owner_uid)
        return [_decrypt_assessment_doc(doc.to_dict() or {}) for doc in query.stream()]
    except Exception as exc:
        logger.error("Firestore get_all_assessments failed: %s", exc)
        return []


def sync_assessments_from_firestore(db_session) -> int:
    """
    Restore assessments (+ answers/scores/findings) from Firestore into SQLite.

    This prevents assessment loss after Cloud Run cold starts where SQLite
    is recreated from scratch.
    """
    if not is_firestore_available():
        return 0

    from app.models.organization import Organization
    from app.models.assessment import Assessment, AssessmentStatus
    from app.models.answer import Answer
    from app.models.score import Score
    from app.models.finding import Finding, Severity, FindingStatus

    docs = firestore_get_all_assessments()
    restored = 0

    try:
        for doc in docs:
            assessment_id = doc.get("id")
            org_id = doc.get("organization_id")
            if not assessment_id or not org_id:
                continue

            org_exists = db_session.query(Organization).filter(Organization.id == org_id).first()
            if not org_exists:
                logger.warning(
                    "Skipping Firestore assessment %s because org %s is missing in SQLite",
                    assessment_id,
                    org_id,
                )
                continue

            existing = db_session.query(Assessment).filter(Assessment.id == assessment_id).first()
            if existing:
                assessment = existing
            else:
                assessment = Assessment(id=assessment_id, organization_id=org_id)
                db_session.add(assessment)

            status_raw = doc.get("status") or AssessmentStatus.DRAFT.value
            try:
                assessment.status = AssessmentStatus(status_raw)
            except Exception:
                assessment.status = AssessmentStatus.DRAFT

            assessment.organization_id = org_id
            assessment.owner_uid = doc.get("owner_uid")
            assessment.version = doc.get("version") or "1.0.0"
            assessment.title = doc.get("title")
            assessment.schema_version = int(doc.get("schema_version") or 1)
            assessment.overall_score = doc.get("overall_score")
            assessment.maturity_level = doc.get("maturity_level")
            assessment.maturity_name = doc.get("maturity_name")
            assessment.created_at = _iso_to_dt(doc.get("created_at"))
            assessment.updated_at = _iso_to_dt(doc.get("updated_at"))
            assessment.completed_at = _iso_to_dt(doc.get("completed_at"))

            db_session.query(Answer).filter(Answer.assessment_id == assessment_id).delete()
            db_session.query(Score).filter(Score.assessment_id == assessment_id).delete()
            db_session.query(Finding).filter(Finding.assessment_id == assessment_id).delete()

            for a in doc.get("answers", []):
                value_raw = a.get("value")
                answer = Answer(
                    assessment_id=assessment_id,
                    question_id=a.get("question_id") or "",
                    value="" if value_raw is None else str(value_raw),
                    notes=a.get("notes"),
                )
                if a.get("id"):
                    answer.id = a.get("id")
                answer.created_at = _iso_to_dt(a.get("created_at"))
                answer.updated_at = _iso_to_dt(a.get("updated_at"))
                db_session.add(answer)

            for s in doc.get("scores", []):
                score = Score(
                    assessment_id=assessment_id,
                    domain_id=s.get("domain_id") or "",
                    domain_name=s.get("domain_name") or "",
                    score=float(s.get("score") or 0),
                    max_score=float(s.get("max_score") or 5.0),
                    weight=float(s.get("weight") or 0),
                    weighted_score=float(s.get("weighted_score") or 0),
                    raw_points=s.get("raw_points"),
                    max_raw_points=s.get("max_raw_points"),
                )
                if s.get("id"):
                    score.id = s.get("id")
                score.created_at = _iso_to_dt(s.get("created_at"))
                db_session.add(score)

            for f in doc.get("findings", []):
                severity_raw = (f.get("severity") or "medium").lower()
                status_raw = (f.get("status") or "open").lower()

                try:
                    severity = Severity(severity_raw)
                except Exception:
                    severity = Severity.MEDIUM

                try:
                    finding_status = FindingStatus(status_raw)
                except Exception:
                    finding_status = FindingStatus.OPEN

                finding = Finding(
                    assessment_id=assessment_id,
                    title=f.get("title") or "Untitled finding",
                    description=f.get("description"),
                    severity=severity,
                    status=finding_status,
                    domain_id=f.get("domain_id"),
                    domain_name=f.get("domain_name"),
                    question_id=f.get("question_id"),
                    evidence=f.get("evidence"),
                    recommendation=f.get("recommendation"),
                    priority=f.get("priority"),
                    nist_function=f.get("nist_function"),
                    nist_category=f.get("nist_category"),
                    nist_subcategory=f.get("nist_subcategory"),
                    soc2_controls=f.get("soc2_controls"),
                )
                if f.get("id"):
                    finding.id = f.get("id")
                finding.created_at = _iso_to_dt(f.get("created_at"))
                finding.updated_at = _iso_to_dt(f.get("updated_at"))
                db_session.add(finding)

            restored += 1

        db_session.commit()
        logger.info("Firestore sync: %d assessments loaded into SQLite", restored)
        return restored
    except Exception as exc:
        db_session.rollback()
        logger.warning("Firestore assessment sync failed: %s", exc)
        return 0


# ═══════════════════════════════════════════════════════════════════════
# Intelligence Packet Persistence
# ═══════════════════════════════════════════════════════════════════════

def firestore_upsert_remediation_ledger(
    *,
    org_id: str,
    workspace_id: str,
    audit_id: str,
    owner_uid: str,
    packet: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Persist a strict Gemini intelligence packet under:

      organizations/{org_id}/workspaces/{workspace_id}/audits/{audit_id}

    and upsert remediation items under:

      .../remediation_ledger/{task_id}
    """
    require_firestore()
    try:
        client = get_firestore_client()
        now_iso = datetime.now(timezone.utc).isoformat()

        org_ref = client.collection("organizations").document(org_id)
        workspace_ref = org_ref.collection("workspaces").document(workspace_id)
        audit_ref = workspace_ref.collection("audits").document(audit_id)

        simulation = packet.get("simulation", {})
        remediation_ledger = packet.get("remediation_ledger", [])

        # Keep a normalized audit snapshot for the Attack Lab and monitoring screens.
        audit_ref.set(
            {
                "id": audit_id,
                "org_id": org_id,
                "workspace_id": workspace_id,
                "owner_uid": owner_uid,
                "updated_at": now_iso,
                "last_simulation": simulation,
                "remediation_task_count": len(remediation_ledger),
            },
            merge=True,
        )

        # Store the full latest packet for replay/debug and drift checks.
        audit_ref.collection("intelligence_packets").document("latest").set(
            {
                "received_at": now_iso,
                "owner_uid": owner_uid,
                "packet": packet,
            },
            merge=True,
        )

        ledger_collection = audit_ref.collection("remediation_ledger")
        batch = client.batch()
        for item in remediation_ledger:
            task_id = str(item["task_id"])
            task_ref = ledger_collection.document(task_id)
            batch.set(
                task_ref,
                {
                    "task_id": task_id,
                    "action": item["action"],
                    "priority": item["priority"],
                    "ghi_impact": item["ghi_impact"],
                    "automation_potential": item["automation_potential"],
                    "org_id": org_id,
                    "workspace_id": workspace_id,
                    "audit_id": audit_id,
                    "owner_uid": owner_uid,
                    "updated_at": now_iso,
                },
                merge=True,
            )

        if remediation_ledger:
            batch.commit()

        collection_path = (
            f"organizations/{org_id}/workspaces/{workspace_id}/"
            f"audits/{audit_id}/remediation_ledger"
        )
        logger.info(
            "Firestore: upserted %d remediation tasks at %s",
            len(remediation_ledger),
            collection_path,
        )
        return {
            "tasks_upserted": len(remediation_ledger),
            "ledger_collection_path": collection_path,
        }
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error(
            "CRITICAL: Firestore remediation ledger upsert failed for org=%s workspace=%s audit=%s: %s",
            org_id,
            workspace_id,
            audit_id,
            exc,
        )
        raise FirestoreUnavailableError(f"Failed to upsert remediation ledger: {exc}")


# ═══════════════════════════════════════════════════════════════════════
# Cloud Metadata Persistence (No SQL migration required)
# ═══════════════════════════════════════════════════════════════════════

def firestore_set_assessment_lifecycle(
    assessment_id: str,
    status: str,
    *,
    submitted_at: Optional[str] = None,
    scored_at: Optional[str] = None,
) -> bool:
    """Persist cloud lifecycle status for an assessment in Firestore metadata."""
    require_firestore()
    try:
        client = get_firestore_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload: Dict[str, Any] = {
            "status": status,
            "updated_at": now_iso,
        }
        if submitted_at:
            payload["submitted_at"] = submitted_at
        if scored_at:
            payload["scored_at"] = scored_at

        client.collection("assessments").document(assessment_id).collection("cloud_meta").document("lifecycle").set(payload, merge=True)
        logger.info("Firestore: saved lifecycle metadata for assessment %s", assessment_id)
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error("CRITICAL: Firestore set_assessment_lifecycle failed for %s: %s", assessment_id, exc)
        raise FirestoreUnavailableError(f"Failed to persist assessment lifecycle metadata: {exc}")


def firestore_get_assessment_lifecycle(assessment_id: str) -> Dict[str, Any]:
    """Fetch cloud lifecycle metadata for an assessment."""
    if not is_firestore_available():
        return {}
    try:
        client = get_firestore_client()
        doc = client.collection("assessments").document(assessment_id).collection("cloud_meta").document("lifecycle").get()
        if not doc.exists:
            return {}
        return doc.to_dict() or {}
    except Exception as exc:
        logger.warning("Firestore get_assessment_lifecycle failed for %s: %s", assessment_id, exc)
        return {}


def firestore_save_finding_tracking(
    assessment_id: str,
    finding_id: str,
    tracking: Dict[str, Any],
) -> bool:
    """Persist finding lifecycle tracking metadata in Firestore."""
    require_firestore()
    try:
        client = get_firestore_client()
        payload = dict(tracking)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        payload = _encrypt_doc_fields(payload, FINDING_TRACKING_SENSITIVE_FIELDS)
        client.collection("assessments").document(assessment_id).collection("finding_tracking").document(finding_id).set(payload, merge=True)
        logger.info(
            "Firestore: saved finding tracking metadata for assessment %s finding %s",
            assessment_id,
            finding_id,
        )
        return True
    except FirestoreUnavailableError:
        raise
    except Exception as exc:
        logger.error(
            "CRITICAL: Firestore save_finding_tracking failed for assessment=%s finding=%s: %s",
            assessment_id,
            finding_id,
            exc,
        )
        raise FirestoreUnavailableError(f"Failed to persist finding tracking metadata: {exc}")


def firestore_get_finding_tracking_map(assessment_id: str) -> Dict[str, Dict[str, Any]]:
    """Return finding_id -> tracking metadata map for an assessment."""
    if not is_firestore_available():
        return {}
    try:
        client = get_firestore_client()
        docs = (
            client.collection("assessments")
            .document(assessment_id)
            .collection("finding_tracking")
            .stream()
        )
        result: Dict[str, Dict[str, Any]] = {}
        for doc in docs:
            raw_doc = doc.to_dict() or {}
            result[doc.id] = _decrypt_doc_fields(raw_doc)
        return result
    except Exception as exc:
        logger.warning("Firestore get_finding_tracking_map failed for %s: %s", assessment_id, exc)
        return {}
