"""
Auditor View Service – shareable read-only access for external auditors.

Generates time-limited tokens that let an outside auditor view an
organization's governance posture without a platform account.

Storage: when a database session is passed, links are kept in the
``auditor_links`` table (copied to Firestore by the durable mirror), so a link
keeps working after a restart and a revocation holds on every instance. Only
the SHA-256 hash of a token is stored. Without a session the process-local
store is used; that path exists for unit tests.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Process-local store: token_hash -> metadata. Used only when no session is passed.
_auditor_tokens: Dict[str, dict] = {}

# Token validity duration
TOKEN_TTL_HOURS = 72  # 3 days default


def _hash_token(token: str) -> str:
    """SHA-256 hash for storage (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _aware(value: datetime) -> datetime:
    """SQLite returns naive datetimes; every stored time is UTC."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _row(db: Optional[Session], token_hash: str):
    if db is None:
        return None
    from app.models.auditor_link import AuditorLink

    return db.get(AuditorLink, token_hash)


def create_auditor_link(
    org_id: str,
    org_name: str,
    created_by: str,
    ttl_hours: int = TOKEN_TTL_HOURS,
    db: Optional[Session] = None,
) -> dict:
    """
    Generate a time-limited auditor access token.

    Returns dict with token, expires_at, and link metadata.
    """
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)

    if db is not None:
        from app.models.auditor_link import AuditorLink

        db.add(AuditorLink(
            token_hash=token_hash,
            org_id=org_id,
            org_name=org_name,
            created_by=created_by,
            created_at=now,
            expires_at=expires_at,
            revoked=False,
            access_count=0,
        ))
        db.commit()
    else:
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


def validate_token(token: str, db: Optional[Session] = None) -> Optional[dict]:
    """
    Validate an auditor token. Returns metadata if valid, None otherwise.
    Increments access counter on success.
    """
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)

    row = _row(db, token_hash)
    if row is not None:
        if row.revoked:
            logger.warning("Auditor token revoked for org %s", row.org_id)
            return None
        expires_at = _aware(row.expires_at)
        if now > expires_at:
            logger.warning("Auditor token expired for org %s", row.org_id)
            return None
        row.access_count = (row.access_count or 0) + 1
        db.commit()
        return {
            "org_id": row.org_id,
            "org_name": row.org_name,
            "expires_at": expires_at.isoformat(),
            "access_count": row.access_count,
        }

    meta = _auditor_tokens.get(token_hash)

    if not meta:
        logger.warning("Auditor token not found")
        return None

    if meta["revoked"]:
        logger.warning("Auditor token revoked for org %s", meta["org_id"])
        return None

    expires_at = datetime.fromisoformat(meta["expires_at"])
    if now > expires_at:
        logger.warning("Auditor token expired for org %s", meta["org_id"])
        return None

    meta["access_count"] += 1
    return {
        "org_id": meta["org_id"],
        "org_name": meta["org_name"],
        "expires_at": meta["expires_at"],
        "access_count": meta["access_count"],
    }


def revoke_token(token: str, org_id: Optional[str] = None, db: Optional[Session] = None) -> bool:
    """Revoke an auditor token. Returns True if found and revoked.

    When ``org_id`` is given, a token issued for another organisation is
    treated as not found.
    """
    token_hash = _hash_token(token)

    row = _row(db, token_hash)
    if row is not None:
        if org_id is not None and row.org_id != org_id:
            return False
        row.revoked = True
        db.commit()
        logger.info("Auditor token revoked for org %s", row.org_id)
        return True

    meta = _auditor_tokens.get(token_hash)
    if meta and org_id is not None and meta["org_id"] != org_id:
        return False
    if meta:
        meta["revoked"] = True
        logger.info("Auditor token revoked for org %s", meta["org_id"])
        return True
    return False


def list_active_tokens(org_id: str, db: Optional[Session] = None) -> list:
    """List non-expired, non-revoked tokens for an org (metadata only)."""
    now = datetime.now(timezone.utc)
    results = []

    if db is not None:
        from app.models.auditor_link import AuditorLink

        rows = (
            db.query(AuditorLink)
            .filter(AuditorLink.org_id == org_id, AuditorLink.revoked.is_(False))
            .order_by(AuditorLink.created_at)
            .all()
        )
        for row in rows:
            if now > _aware(row.expires_at):
                continue
            results.append({
                "created_by": row.created_by,
                "created_at": _aware(row.created_at).isoformat(),
                "expires_at": _aware(row.expires_at).isoformat(),
                "access_count": row.access_count or 0,
            })

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
