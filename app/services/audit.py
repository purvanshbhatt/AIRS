"""Helpers for writing audit events without breaking request flow."""

import logging

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent

logger = logging.getLogger("airs.audit")


def record_audit_event(db: Session, org_id: str, action: str, actor: str) -> None:
    """Persist an audit event. Fail closed (log only) to avoid user-facing breakage."""
    if not org_id:
        return

    try:
        event = AuditEvent(org_id=org_id, action=action, actor=actor or "system")
        db.add(event)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to write audit event: %s", exc)

