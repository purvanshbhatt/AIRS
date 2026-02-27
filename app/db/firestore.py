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
