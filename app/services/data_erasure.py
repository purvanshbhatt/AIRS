"""
Data erasure: removing a connection or an organization really removes it.

Two entry points:

``erase_connector``
    The connection record with its encrypted keys, its sync history, the
    events it ingested and the evidence records built from them.

``erase_organization``
    The organization and every row in every table that belongs to it.

Both erase the SQL rows and the Firestore copies (the durable mirror, and for
an organization its assessment and configuration documents). The durable copy
goes first: if Firestore cannot be reached nothing is deleted from SQL and the
caller gets an ``ErasureError``, so "deleted" is never reported while a copy is
still stored. An erasure marker (identifier and time only) stops a row written
by an in-flight sync from being restored after a restart.

Which tables belong to an organization is worked out from the schema: a table
that has a column pointing at ``organizations`` (or a plain ``org_id`` /
``organization_id`` column), and any table that hangs off one of those through
a foreign key. A table added later is covered without touching this module.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

logger = logging.getLogger("airs.services.data_erasure")

_ORG_COLUMN_NAMES = ("org_id", "organization_id", "owner_org_id")


class ErasureError(RuntimeError):
    """The erasure did not complete. Nothing may be reported as deleted."""


def _metadata():
    import app.models  # noqa: F401  (register every mapped table)
    from app.db.database import Base
    return Base.metadata


def _scopes(seed: Dict[str, Any], org_id: Optional[str] = None) -> Dict[str, Any]:
    """Map table name -> WHERE clause selecting the rows to erase.

    ``seed`` gives the starting tables. With ``org_id`` every table that has
    an organization column is selected by it; every other table is selected
    through its foreign keys to a table already in scope.
    """
    scopes: Dict[str, Any] = dict(seed)
    for table in _metadata().sorted_tables:  # parents before children
        if table.name in scopes or table.name == "organizations":
            continue
        clauses = []
        if org_id is not None:
            for column in table.columns:
                points_at_org = any(fk.column.table.name == "organizations" for fk in column.foreign_keys)
                if points_at_org or (column.name in _ORG_COLUMN_NAMES and not column.foreign_keys):
                    clauses.append(column == org_id)
        if not clauses:
            for column in table.columns:
                for fk in column.foreign_keys:
                    parent = fk.column.table
                    if parent is not table and parent.name in scopes:
                        clauses.append(column.in_(select(fk.column).where(scopes[parent.name])))
        if clauses:
            scopes[table.name] = or_(*clauses)
    return scopes


def _delete_scoped(db: Session, scopes: Dict[str, Any]) -> Dict[str, int]:
    """Delete children before parents. Returns rows removed per table."""
    removed: Dict[str, int] = {}
    for table in reversed(_metadata().sorted_tables):
        clause = scopes.get(table.name)
        if clause is None:
            continue
        count = db.execute(table.delete().where(clause)).rowcount or 0
        if count:
            removed[table.name] = count
    return removed


def erase_connector(db: Session, org_id: str, connector_id: str) -> Dict[str, int]:
    """Erase one connection of an organization. Returns rows removed per table.

    Raises ``LookupError`` when the organization has no such connection.
    """
    from app.db import durable_mirror as mirror
    from app.models.connector import Connector

    connectors = Connector.__table__
    exists = db.execute(
        select(connectors.c.id).where(connectors.c.id == connector_id, connectors.c.org_id == org_id)
    ).first()
    if not exists:
        raise LookupError(f"Connector {connector_id} not found for org {org_id}")

    try:
        mirror.record_tombstone("connector", connector_id)
        mirror.purge_mirror_rows("telemetry_events", "connector_id", connector_id)
        mirror.purge_mirror_rows("connectors", "id", connector_id, document_id=connector_id)
    except mirror.MirrorPurgeError as exc:
        raise ErasureError(str(exc)) from exc

    scopes = _scopes({"connectors": (connectors.c.id == connector_id) & (connectors.c.org_id == org_id)})
    try:
        removed = _delete_scoped(db, scopes)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise ErasureError(f"Could not erase connector {connector_id}: {exc}") from exc
    db.expire_all()
    logger.info("Connector erased: %s (org=%s) rows=%s", connector_id, org_id, removed)
    return removed


def erase_organization(db: Session, org_id: str) -> Dict[str, int]:
    """Erase an organization and everything that belongs to it.

    The caller is responsible for checking that the signed-in person owns it.
    """
    from app.db import durable_mirror as mirror
    from app.db import firestore
    from app.models.organization import Organization

    organizations = Organization.__table__

    try:
        mirror.record_tombstone("org", org_id)
        for spec in mirror.MIRROR_SPECS:
            column = mirror.org_column_for(spec.table)
            if column:
                mirror.purge_mirror_rows(spec.table, column, org_id)
        firestore.firestore_purge_org_documents(org_id)
    except (mirror.MirrorPurgeError, firestore.FirestoreUnavailableError) as exc:
        raise ErasureError(str(exc)) from exc

    scopes = _scopes({}, org_id=org_id)
    try:
        removed = _delete_scoped(db, scopes)
        # Other organizations that pointed at this one keep working without it.
        for column in (organizations.c.managed_by_msp_id, organizations.c.source_org_id):
            db.execute(organizations.update().where(column == org_id).values({column.name: None}))
        removed["organizations"] = db.execute(
            organizations.delete().where(organizations.c.id == org_id)
        ).rowcount or 0
        db.commit()
    except Exception as exc:
        db.rollback()
        raise ErasureError(f"Could not erase organization {org_id}: {exc}") from exc
    db.expire_all()
    logger.info("Organization erased: %s rows=%s", org_id, removed)
    return removed
