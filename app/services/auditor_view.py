"""
Auditor View Service – shareable read-only access for external auditors.

Generates time-limited tokens that allow Big-4 auditors to view an
organization's Governance Health Index, compliance posture, and evidence
without requiring platform authentication.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory token store: token_hash -> metadata
# Production would use Firestore or Redis
_auditor_tokens: Dict[str, dict] = {}

# Token validity duration
TOKEN_TTL_HOURS = 72  # 3 days default


def _hash_token(token: str) -> str:
    """SHA-256 hash for storage (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_auditor_link(
    org_id: str,
    org_name: str,
    created_by: str,
    ttl_hours: int = TOKEN_TTL_HOURS,
) -> dict:
    """
    Generate a time-limited auditor access token.

    Returns dict with token, expires_at, and link metadata.
    """
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)

    _auditor_tokens[token_hash] = {
        "org_id": org_id,
        "org_name": org_name,
        "created_by": created_by,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "revoked": False,
        "access_count": 0,
    }

    logger.info("Auditor link created for org %s, expires %s", org_id, expires_at.isoformat())

    return {
        "token": token,
        "org_id": org_id,
        "org_name": org_name,
        "expires_at": expires_at.isoformat(),
        "ttl_hours": ttl_hours,
    }


def validate_token(token: str) -> Optional[dict]:
    """
    Validate an auditor token. Returns metadata if valid, None otherwise.
    Increments access counter on success.
    """
    token_hash = _hash_token(token)
    meta = _auditor_tokens.get(token_hash)

    if not meta:
        logger.warning("Auditor token not found")
        return None

    if meta["revoked"]:
        logger.warning("Auditor token revoked for org %s", meta["org_id"])
        return None

    expires_at = datetime.fromisoformat(meta["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        logger.warning("Auditor token expired for org %s", meta["org_id"])
        return None

    meta["access_count"] += 1
    return {
        "org_id": meta["org_id"],
        "org_name": meta["org_name"],
        "expires_at": meta["expires_at"],
        "access_count": meta["access_count"],
    }


def revoke_token(token: str) -> bool:
    """Revoke an auditor token. Returns True if found and revoked."""
    token_hash = _hash_token(token)
    meta = _auditor_tokens.get(token_hash)
    if meta:
        meta["revoked"] = True
        logger.info("Auditor token revoked for org %s", meta["org_id"])
        return True
    return False


def list_active_tokens(org_id: str) -> list:
    """List non-expired, non-revoked tokens for an org (metadata only)."""
    now = datetime.now(timezone.utc)
    results = []
    for _hash, meta in _auditor_tokens.items():
        if meta["org_id"] != org_id:
            continue
        if meta["revoked"]:
            continue
        expires_at = datetime.fromisoformat(meta["expires_at"])
        if now > expires_at:
            continue
        results.append({
            "created_by": meta["created_by"],
            "created_at": meta["created_at"],
            "expires_at": meta["expires_at"],
            "access_count": meta["access_count"],
        })
    return results
