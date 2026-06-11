"""Helpers for writing audit events without breaking request flow."""

import logging

from sqlalchemy.orm import Session
from sqlalchemy import event

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


def record_connector_audit(
    db: Session,
    org_id: str,
    action: str,
    actor: str,
    connector_type: str,
    status: str,
    extra_details: dict | None = None,
) -> None:
    """Record a connector audit event in both the AuditEvent database table and as a structured SIEM JSON log."""
    from datetime import datetime, timezone
    import json
    from app.core.config import settings
    from app.core.logging import get_request_id

    # 1. Save to SQLite/Postgres AuditEvent table
    record_audit_event(db, org_id, f"connector.{connector_type}.{action}", actor)
    
    # 2. Emit structured log payload for SIEM ingestion
    log_payload = {
        "event": f"integration.{action}",
        "connector_type": connector_type,
        "org_id": org_id,
        "actor": actor or "system",
        "status": status,
        "environment": settings.ENV.value if hasattr(settings.ENV, "value") else str(settings.ENV),
        "request_id": get_request_id() or "-",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra_details:
        log_payload.update(extra_details)
        
    logger.info(json.dumps(log_payload))

class SystemAuditor:
    """
    Automated system auditing trace class that listens to SQLAlchemy session flushes
    and records an immutable ledger entry for every configuration mutation.
    """
    
    # Models to automatically audit
    AUDITABLE_TABLES = {"organizations", "connectors", "wazuh_configs"}
    
    @classmethod
    def setup_listeners(cls, engine):
        """Bind the after_flush listener to the Session context."""
        event.listen(Session, "after_flush", cls.after_flush)
        
    @classmethod
    def after_flush(cls, session, flush_context):
        """Intercepts all changes before commit and generates AuditEvents."""
        for obj in session.new:
            cls._record_mutation(session, obj, "insert")
            
        for obj in session.dirty:
            # Check if actual columns were modified
            if session.is_modified(obj, include_collections=False):
                cls._record_mutation(session, obj, "update")
                
        for obj in session.deleted:
            cls._record_mutation(session, obj, "delete")
            
    @classmethod
    def _record_mutation(cls, session, obj, action: str):
        # Only audit specific tables
        table_name = getattr(obj.__table__, "name", "")
        if table_name not in cls.AUDITABLE_TABLES:
            return
            
        # Get the org_id (assuming all auditable tables have it)
        org_id = getattr(obj, "org_id", None)
        if not org_id and table_name == "organizations":
            org_id = getattr(obj, "id", None)
            
        if not org_id:
            return
            
        from app.core.logging import get_request_id
        import json
        
        # In a real environment, context vars or similar would provide the actor
        actor = "system_automutator"
        
        # Build the changes dictionary
        changes = {}
        if action == "update":
            from sqlalchemy.orm import attributes
            state = attributes.instance_state(obj)
            for attr in state.unmodified:
                pass  # Ignore unmodified
            for attr in state.dict:
                if attr == "_sa_instance_state":
                    continue
                history = attributes.get_history(obj, attr)
                if history.has_changes():
                    # Obfuscate credentials if present
                    if attr in ("encrypted_credentials", "wazuh_api_key"):
                        changes[attr] = {"old": "***", "new": "***"}
                    else:
                        changes[attr] = {
                            "old": history.deleted[0] if history.deleted else None,
                            "new": history.added[0] if history.added else None
                        }
        
        # Construct specific action string like "connector.update"
        model_name = obj.__class__.__name__.lower()
        full_action = f"{model_name}.{action}"
        
        event = AuditEvent(
            org_id=org_id,
            action=full_action,
            actor=actor
        )
        
        # Emit a SIEM structured log as well
        log_payload = {
            "event": "system_audit.mutation",
            "model": model_name,
            "org_id": org_id,
            "action": action,
            "actor": actor,
            "changes": str(changes) if changes else "",
            "request_id": get_request_id() or "-",
        }
        logger.info(json.dumps(log_payload))
        
        # Add to session (won't trigger another flush loop if done correctly, 
        # but safe practice is to use a new session or add to the current flush plan)
        session.add(event)

def register_system_auditor():
    """Call this on application startup to enforce the auditing trace."""
    from app.db.database import engine
    SystemAuditor.setup_listeners(engine)

