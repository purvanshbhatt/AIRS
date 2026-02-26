"""
Cloud Firestore persistence layer.

Provides a Firestore client and sync utilities so that organization data
survives Cloud Run cold starts (SQLite is wiped on each new instance).

Strategy:
  - On startup, sync Firestore → SQLite so existing SQLAlchemy queries work.
  - On every org create/update/delete, dual-write to both SQLite and Firestore.
  - Firestore is the *source of truth* for data that must persist.

Collections:
  organizations/{org_id}      — full org document
  assessments/{assessment_id} — assessment metadata
  audit_events/{event_id}     — audit trail
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("airs.firestore")

# Firestore client — lazy-initialized
_firestore_client = None
_firestore_available = False


def _init_firestore():
    """Initialize Firestore client using Firebase Admin SDK (already init in main.py)."""
    global _firestore_client, _firestore_available
    if _firestore_client is not None:
        return _firestore_available

    try:
        from firebase_admin import firestore as fb_firestore
        _firestore_client = fb_firestore.client()
        _firestore_available = True
        logger.info("Firestore client initialized successfully")
    except Exception as exc:
        _firestore_available = False
        logger.warning("Firestore unavailable (will use SQLite only): %s", exc)

    return _firestore_available


def is_firestore_available() -> bool:
    """Check if Firestore is available."""
    return _init_firestore()


def get_firestore_client():
    """Get the Firestore client, or None if unavailable."""
    _init_firestore()
    return _firestore_client


# ═══════════════════════════════════════════════════════════════════════
# Organization Persistence
# ═══════════════════════════════════════════════════════════════════════

def _org_to_doc(org) -> Dict[str, Any]:
    """Convert a SQLAlchemy Organization to a Firestore document dict."""
    return {
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


def firestore_save_org(org) -> bool:
    """Save/update an organization to Firestore. Returns True on success."""
    if not is_firestore_available():
        return False
    try:
        client = get_firestore_client()
        doc_ref = client.collection("organizations").document(org.id)
        doc_ref.set(_org_to_doc(org))
        logger.debug("Firestore: saved org %s", org.id)
        return True
    except Exception as exc:
        logger.warning("Firestore save_org failed: %s", exc)
        return False


def firestore_delete_org(org_id: str) -> bool:
    """Delete an organization from Firestore."""
    if not is_firestore_available():
        return False
    try:
        client = get_firestore_client()
        client.collection("organizations").document(org_id).delete()
        logger.debug("Firestore: deleted org %s", org_id)
        return True
    except Exception as exc:
        logger.warning("Firestore delete_org failed: %s", exc)
        return False


def firestore_get_all_orgs(owner_uid: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all organizations from Firestore, optionally filtered by owner."""
    if not is_firestore_available():
        return []
    try:
        client = get_firestore_client()
        query = client.collection("organizations")
        if owner_uid:
            query = query.where("owner_uid", "==", owner_uid)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as exc:
        logger.warning("Firestore get_all_orgs failed: %s", exc)
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
