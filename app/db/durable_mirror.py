"""
Durable mirror — keeps selected SQLAlchemy tables in Firestore.

Why: on Cloud Run the SQL database is an in-memory SQLite cache that is
rebuilt on every cold start. Only organizations and assessments were synced
from Firestore, so connectors, the telemetry they ingested, generated reports
and other operational rows silently disappeared whenever the instance
restarted. This module mirrors every committed insert/update/delete of the
registered tables to Firestore and restores them at startup.

Design:
  * Collections are namespaced per environment: ``<env>_mirror_<table>``
    (staging and production never read each other's rows).
  * Writes happen in ``after_commit`` (never inside the transaction) and never
    raise into the request path; a failed mirror write is logged.
  * Restore uses per-row savepoints, an optional age window and a row cap so a
    large table cannot stall startup.
  * Secret columns are only mirrored as ciphertext.

Long term the right fix is a managed SQL database (Cloud SQL); this keeps the
pilot durable until then. Keep Cloud Run at a single instance while the SQL
cache is per-instance.
"""
from __future__ import annotations

import enum
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

logger = logging.getLogger("airs.db.durable_mirror")

_SUPPRESS_KEY = "_durable_mirror_suppress"
_OPS_KEY = "_durable_mirror_ops"
_BATCH_SIZE = 400


@dataclass
class MirrorSpec:
    table: str
    max_restore: int = 5000
    restore_window_days: Optional[int] = None
    timestamp_column: str = "created_at"
    ciphertext_columns: Tuple[str, ...] = field(default_factory=tuple)


# Tables that must survive a restart. Order matters for restore (parents first).
MIRROR_SPECS: List[MirrorSpec] = [
    MirrorSpec("connectors", ciphertext_columns=("encrypted_credentials",)),
    MirrorSpec("telemetry_events", max_restore=20000, restore_window_days=30),
    MirrorSpec("reports", max_restore=2000),
    MirrorSpec("msp_relationships"),
    # Registered when the vulnerability-intelligence models exist.
    MirrorSpec("tech_web_assets"),
    MirrorSpec("web_assets"),
]

_registered = False
_client_factory: Optional[Callable[[], Any]] = None  # injectable for tests


def _env_prefix() -> str:
    try:
        from app.core.config import settings
        env = getattr(settings.ENV, "value", str(settings.ENV))
    except Exception:
        env = "local"
    return f"{env}_mirror_"


def collection_name(table: str) -> str:
    return f"{_env_prefix()}{table}"


def _get_client():
    if _client_factory is not None:
        return _client_factory()
    from app.db.firestore import get_firestore_client, is_firestore_available
    if not is_firestore_available():
        return None
    return get_firestore_client()


def _spec_for(table: str) -> Optional[MirrorSpec]:
    for spec in MIRROR_SPECS:
        if spec.table == table:
            return spec
    return None


def _to_firestore(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, datetime)):
        return value
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, (dict, list)):
        # Round-trip through JSON so nested datetimes/enums cannot break the write.
        return json.loads(json.dumps(value, default=str))
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _protect_ciphertext(value: Any, table: str, column: str) -> Any:
    """Only ciphertext may leave the process for secret columns."""
    if value in (None, ""):
        return value
    text = value if isinstance(value, str) else str(value)
    try:
        doc = json.loads(text)
        if isinstance(doc, dict) and "encrypted_blob" in doc:
            return text  # already an AES-GCM envelope
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        from app.core.security.encryption import get_encryption_service
        svc = get_encryption_service()
        if svc.enabled:
            return json.dumps(svc.encrypt_fields({"value": text}, sensitive_fields={"value"}))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Mirror encryption failed for %s.%s: %s", table, column, exc)
    logger.warning("Refusing to mirror plaintext %s.%s (no encryption key); row stored without it", table, column)
    return None


def _row_payload(obj: Any, spec: MirrorSpec) -> Tuple[str, Dict[str, Any]]:
    mapper = inspect(obj).mapper
    payload: Dict[str, Any] = {}
    for attr in mapper.column_attrs:
        value = getattr(obj, attr.key, None)
        if attr.key in spec.ciphertext_columns:
            value = _protect_ciphertext(value, spec.table, attr.key)
        payload[attr.key] = _to_firestore(value)
    pk = "|".join(str(v) for v in mapper.primary_key_from_instance(obj))
    return pk, payload


# ── Session hooks ────────────────────────────────────────────────────

def _after_flush(session: Session, flush_context) -> None:
    if session.info.get(_SUPPRESS_KEY):
        return
    ops = session.info.setdefault(_OPS_KEY, [])
    for obj in list(session.new) + [o for o in session.dirty if session.is_modified(o)]:
        table = getattr(obj, "__tablename__", None)
        spec = _spec_for(table) if table else None
        if not spec:
            continue
        try:
            pk, payload = _row_payload(obj, spec)
            ops.append(("set", table, pk, payload))
        except Exception as exc:
            logger.warning("Mirror serialisation failed for %s: %s", table, exc)
    for obj in session.deleted:
        table = getattr(obj, "__tablename__", None)
        spec = _spec_for(table) if table else None
        if not spec:
            continue
        try:
            pk = "|".join(str(v) for v in inspect(obj).mapper.primary_key_from_instance(obj))
            ops.append(("delete", table, pk, None))
        except Exception as exc:
            logger.warning("Mirror delete serialisation failed for %s: %s", table, exc)


def _after_commit(session: Session) -> None:
    ops = session.info.pop(_OPS_KEY, None)
    if not ops:
        return
    try:
        client = _get_client()
    except Exception as exc:
        logger.warning("Durable mirror unavailable: %s", exc)
        return
    if client is None:
        return
    # Last write per document wins inside one commit.
    latest: Dict[Tuple[str, str], Tuple[str, Optional[Dict[str, Any]]]] = {}
    for op, table, pk, payload in ops:
        latest[(table, pk)] = (op, payload)
    items = list(latest.items())
    try:
        for start in range(0, len(items), _BATCH_SIZE):
            batch = client.batch()
            for (table, pk), (op, payload) in items[start:start + _BATCH_SIZE]:
                ref = client.collection(collection_name(table)).document(pk)
                if op == "delete":
                    batch.delete(ref)
                else:
                    batch.set(ref, payload)
            batch.commit()
    except Exception as exc:
        logger.error("Durable mirror write failed (%d rows): %s", len(items), exc)


def _after_rollback(session: Session) -> None:
    session.info.pop(_OPS_KEY, None)


def register_durable_mirror() -> None:
    """Attach the mirror hooks to every Session (idempotent)."""
    global _registered
    if _registered:
        return
    event.listen(Session, "after_flush", _after_flush)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    _registered = True
    logger.info("Durable mirror registered for tables: %s", ", ".join(s.table for s in MIRROR_SPECS))


# ── Startup restore ──────────────────────────────────────────────────

def _model_for_table(table: str):
    from app.db.database import Base
    for mapper in Base.registry.mappers:
        if getattr(mapper.class_, "__tablename__", None) == table:
            return mapper.class_
    return None


def restore_from_mirror(db: Session) -> Dict[str, int]:
    """Load mirrored rows back into the SQL cache. Returns rows restored per table."""
    restored: Dict[str, int] = {}
    try:
        client = _get_client()
    except Exception as exc:
        logger.warning("Durable mirror restore skipped: %s", exc)
        return restored
    if client is None:
        return restored

    db.info[_SUPPRESS_KEY] = True
    try:
        for spec in MIRROR_SPECS:
            model = _model_for_table(spec.table)
            if model is None:
                continue
            columns = {attr.key for attr in inspect(model).mapper.column_attrs}
            cutoff = None
            if spec.restore_window_days:
                cutoff = datetime.now(timezone.utc) - timedelta(days=spec.restore_window_days)
            count = 0
            try:
                docs = client.collection(collection_name(spec.table)).limit(spec.max_restore).stream()
                for doc in docs:
                    data = doc.to_dict() or {}
                    ts = data.get(spec.timestamp_column)
                    if cutoff and isinstance(ts, datetime):
                        ts_aware = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
                        if ts_aware < cutoff:
                            continue
                    row = {k: v for k, v in data.items() if k in columns}
                    try:
                        with db.begin_nested():
                            db.merge(model(**row))
                        count += 1
                    except Exception as row_exc:
                        logger.warning("Mirror restore skipped a %s row: %s", spec.table, row_exc)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Mirror restore failed for %s: %s", spec.table, exc)
            if count:
                restored[spec.table] = count
    finally:
        db.info.pop(_SUPPRESS_KEY, None)
    if restored:
        logger.info("Durable mirror restored: %s", restored)
    return restored
