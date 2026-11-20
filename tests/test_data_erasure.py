"""Removing a connection or an organization erases it: SQL rows and Firestore copies."""
import base64
import json
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db import durable_mirror as dm
from app.models.assessment import Assessment
from app.models.connector import Connector, ConnectorSyncLog
from app.models.evidence import EvidenceLedger, NormalizedEvidenceRecord
from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent
from app.services import data_erasure
from app.services.connector_manager import (
    ConnectorManager,
    ConnectorNotFoundError,
    encrypt_plaintext_credentials,
)
from app.services.data_erasure import ErasureError, erase_connector, erase_organization
from tests.conftest import USER_WITH_ORG


# ── In-memory Firestore stand-in ─────────────────────────────────────

class _Ref:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def set(self, payload):
        self.store[self.key] = payload

    def delete(self):
        self.store.pop(self.key, None)


class _Doc:
    def __init__(self, store, key):
        self.store, self.key = store, key
        self.reference = _Ref(store, key)

    def to_dict(self):
        return dict(self.store[self.key])


class _Query:
    def __init__(self, store, predicate=None):
        self.store, self.predicate = store, predicate

    def limit(self, n):
        return self

    def stream(self):
        return [
            _Doc(self.store, k) for k in list(self.store)
            if self.predicate is None or self.predicate(self.store[k])
        ]


class _Collection(_Query):
    def document(self, key):
        return _Ref(self.store, key)

    def where(self, field=None, op=None, value=None, filter=None):
        if filter is not None:
            field, value = filter.field_path, filter.value
        return _Query(self.store, lambda row: row.get(field) == value)


class _Batch:
    def __init__(self):
        self.ops = []

    def set(self, ref, payload):
        self.ops.append(("set", ref, payload))

    def delete(self, ref):
        self.ops.append(("delete", ref, None))

    def commit(self):
        for op, ref, payload in self.ops:
            if op == "set":
                ref.store[ref.key] = payload
            else:
                ref.store.pop(ref.key, None)


class FakeFirestore:
    def __init__(self):
        self.collections = {}
        self.fail = False

    def collection(self, name):
        if self.fail:
            raise RuntimeError("firestore is down")
        return _Collection(self.collections.setdefault(name, {}))

    def batch(self):
        return _Batch()

    def rows(self, table):
        return self.collections.get(dm.collection_name(table), {})


@pytest.fixture
def mirror(db_session):
    fake = FakeFirestore()
    dm._client_factory = lambda: fake
    event.listen(Session, "after_flush", dm._after_flush)
    event.listen(Session, "after_commit", dm._after_commit)
    event.listen(Session, "after_rollback", dm._after_rollback)
    yield fake
    event.remove(Session, "after_flush", dm._after_flush)
    event.remove(Session, "after_commit", dm._after_commit)
    event.remove(Session, "after_rollback", dm._after_rollback)
    dm._client_factory = None


# ── Builders ─────────────────────────────────────────────────────────

def _org(db, org_id, owner="u1", **extra):
    org = Organization(id=org_id, name=f"Org {org_id}", owner_uid=owner, **extra)
    db.add(org)
    db.commit()
    return org


def _connector(db, org_id, name="AWS"):
    connector = Connector(
        org_id=org_id, connector_type="aws", display_name=name, auth_method="api_key", status="active",
        encrypted_credentials=json.dumps({"aws_secret_access_key": "TOPSECRET"}),
    )
    db.add(connector)
    db.commit()
    return connector


def _evidence(db, org_id, connector_id, tag):
    """One telemetry event, one sync log, one ledger entry and its normalized record."""
    db.add(TelemetryEvent(
        org_id=org_id, connector_id=connector_id, event_type="finding", source_system="aws",
        source_event_id=f"evt-{tag}", payload_hash=f"hash-{tag}", payload={"detail": tag}, severity="high",
    ))
    db.add(ConnectorSyncLog(
        connector_id=connector_id, sync_started_at=datetime.now(timezone.utc), status="success",
    ))
    db.add(EvidenceLedger(
        org_id=org_id, connector_id=connector_id, evidence_hash=f"ledger-{tag}",
        source_name="aws", event_type="finding", raw_payload={"detail": tag},
    ))
    db.add(NormalizedEvidenceRecord(org_id=org_id, evidence_hash=f"ledger-{tag}", severity="high"))
    db.commit()


def _count(db, model, **filters):
    return db.query(model).filter_by(**filters).count()


# ── Connector erasure ────────────────────────────────────────────────

def test_removing_a_connector_erases_its_keys_events_and_evidence(db_session, mirror):
    _org(db_session, "org-a")
    keep, gone = _connector(db_session, "org-a", "Keep"), _connector(db_session, "org-a", "Gone")
    keep_id, gone_id = keep.id, gone.id
    _evidence(db_session, "org-a", keep_id, "keep")
    _evidence(db_session, "org-a", gone_id, "gone")
    assert gone_id in mirror.rows("connectors")
    assert any(r["connector_id"] == gone_id for r in mirror.rows("telemetry_events").values())

    removed = erase_connector(db_session, "org-a", gone_id)

    assert removed["connectors"] == 1 and removed["telemetry_events"] == 1
    # SQL: nothing of the removed connector is left, credentials included.
    assert _count(db_session, Connector, id=gone_id) == 0
    assert _count(db_session, TelemetryEvent, connector_id=gone_id) == 0
    assert _count(db_session, ConnectorSyncLog, connector_id=gone_id) == 0
    assert _count(db_session, EvidenceLedger, connector_id=gone_id) == 0
    assert _count(db_session, NormalizedEvidenceRecord, evidence_hash="ledger-gone") == 0
    # The other connector is untouched.
    assert _count(db_session, Connector, id=keep_id) == 1
    assert _count(db_session, TelemetryEvent, connector_id=keep_id) == 1
    assert _count(db_session, ConnectorSyncLog, connector_id=keep_id) == 1
    assert _count(db_session, NormalizedEvidenceRecord, evidence_hash="ledger-keep") == 1
    # Firestore: the mirrored copies are gone too.
    assert gone_id not in mirror.rows("connectors") and keep_id in mirror.rows("connectors")
    assert not any(r["connector_id"] == gone_id for r in mirror.rows("telemetry_events").values())
    assert any(r["connector_id"] == keep_id for r in mirror.rows("telemetry_events").values())
    assert "TOPSECRET" not in json.dumps(mirror.collections, default=str)


def test_connector_of_another_organization_cannot_be_erased(db_session, mirror):
    _org(db_session, "org-a")
    _org(db_session, "org-b", owner="u2")
    theirs = _connector(db_session, "org-b")
    _evidence(db_session, "org-b", theirs.id, "theirs")

    with pytest.raises(LookupError):
        erase_connector(db_session, "org-a", theirs.id)
    with pytest.raises(ConnectorNotFoundError):
        ConnectorManager(db_session, "org-a").delete_connector(theirs.id)

    assert _count(db_session, Connector, id=theirs.id) == 1
    assert _count(db_session, TelemetryEvent, connector_id=theirs.id) == 1
    assert theirs.id in mirror.rows("connectors")


def test_nothing_is_deleted_when_the_durable_copy_cannot_be_erased(db_session, mirror):
    _org(db_session, "org-a")
    connector = _connector(db_session, "org-a")
    _evidence(db_session, "org-a", connector.id, "x")

    mirror.fail = True
    with pytest.raises(ErasureError):
        erase_connector(db_session, "org-a", connector.id)
    with pytest.raises(ErasureError):
        erase_organization(db_session, "org-a")
    mirror.fail = False

    assert _count(db_session, Connector, id=connector.id) == 1
    assert _count(db_session, TelemetryEvent, connector_id=connector.id) == 1
    assert _count(db_session, Organization, id="org-a") == 1


def test_erased_rows_do_not_come_back_after_a_restart(db_session, mirror):
    _org(db_session, "org-a")
    connector = _connector(db_session, "org-a")
    connector_id = connector.id
    erase_connector(db_session, "org-a", connector_id)

    # A sync that was still running writes one more event into the mirror.
    mirror.collection(dm.collection_name("telemetry_events")).document("late").set({
        "id": "late", "org_id": "org-a", "connector_id": connector_id, "event_type": "finding",
        "source_system": "aws", "source_event_id": "late", "payload_hash": "late", "severity": "low",
        "processed": False, "created_at": datetime.now(timezone.utc),
    })

    restored = dm.restore_from_mirror(db_session)

    assert "telemetry_events" not in restored
    assert _count(db_session, TelemetryEvent, connector_id=connector_id) == 0
    assert "late" not in mirror.rows("telemetry_events")


# ── Organization erasure ─────────────────────────────────────────────

def test_deleting_an_organization_erases_everything_it_owns(db_session, mirror):
    _org(db_session, "org-a")
    _org(db_session, "org-b", owner="u2")
    _org(db_session, "client-of-a", owner="u3", managed_by_msp_id="org-a")
    mine, theirs = _connector(db_session, "org-a"), _connector(db_session, "org-b")
    mine_id, theirs_id = mine.id, theirs.id
    _evidence(db_session, "org-a", mine_id, "mine")
    _evidence(db_session, "org-b", theirs_id, "theirs")
    db_session.add(Assessment(organization_id="org-a", owner_uid="u1", title="Mine"))
    db_session.add(Assessment(organization_id="org-b", owner_uid="u2", title="Theirs"))
    db_session.commit()

    removed = erase_organization(db_session, "org-a")

    assert removed["organizations"] == 1 and removed["connectors"] == 1
    for model, column in (
        (Connector, "org_id"), (TelemetryEvent, "org_id"), (EvidenceLedger, "org_id"),
        (NormalizedEvidenceRecord, "org_id"), (Assessment, "organization_id"),
    ):
        assert _count(db_session, model, **{column: "org-a"}) == 0, model.__tablename__
        assert _count(db_session, model, **{column: "org-b"}) == 1, model.__tablename__
    assert _count(db_session, ConnectorSyncLog, connector_id=mine_id) == 0
    assert _count(db_session, ConnectorSyncLog, connector_id=theirs_id) == 1
    assert _count(db_session, Organization, id="org-a") == 0
    # An organization that was managed by the deleted one survives, unlinked.
    client = db_session.query(Organization).filter_by(id="client-of-a").one()
    assert client.managed_by_msp_id is None
    # Firestore mirror: only the other organization's rows remain.
    assert set(mirror.rows("connectors")) == {theirs_id}
    assert {r["org_id"] for r in mirror.rows("telemetry_events").values()} == {"org-b"}


def test_every_table_that_points_at_an_organization_is_in_scope():
    """A table added later with an organization column must be erased too."""
    scopes = data_erasure._scopes({}, org_id="x")
    for table in data_erasure._metadata().sorted_tables:
        if table.name == "organizations":
            continue
        org_linked = any(
            fk.column.table.name == "organizations" for column in table.columns for fk in column.foreign_keys
        ) or any(column.name in ("org_id", "organization_id") for column in table.columns)
        if org_linked:
            assert table.name in scopes, table.name
    # Reached through a parent rather than an organization column.
    for name in ("connector_sync_logs", "answers", "findings", "control_evidence", "installed_products"):
        assert name in scopes, name
    # Shared reference data is never in scope.
    for name in ("global_software_catalog", "framework_registry", "vuln_intel_cache", "question_metadata"):
        assert name not in scopes, name


# ── API ──────────────────────────────────────────────────────────────

def test_delete_connector_endpoint_erases_the_row(client_with_org, db_session):
    connector = _connector(db_session, "test-org-123")
    connector_id = connector.id
    _evidence(db_session, "test-org-123", connector_id, "api")

    response = client_with_org.delete(f"/api/v1/connectors/{connector_id}?org_id=test-org-123")

    assert response.status_code == 204, response.text
    db_session.expire_all()
    assert _count(db_session, Connector, id=connector_id) == 0
    assert _count(db_session, TelemetryEvent, connector_id=connector_id) == 0
    assert client_with_org.delete(f"/api/v1/connectors/{connector_id}?org_id=test-org-123").status_code == 404


def test_delete_organization_endpoint_erases_connectors_and_events(client_with_org, db_session):
    connector = _connector(db_session, "test-org-123")
    _evidence(db_session, "test-org-123", connector.id, "org-api")

    response = client_with_org.delete("/api/orgs/test-org-123")

    assert response.status_code == 204, response.text
    db_session.expire_all()
    assert _count(db_session, Organization, id="test-org-123") == 0
    assert _count(db_session, Connector, org_id="test-org-123") == 0
    assert _count(db_session, TelemetryEvent, org_id="test-org-123") == 0
    assert _count(db_session, EvidenceLedger, org_id="test-org-123") == 0


def test_splunk_config_of_another_owner_cannot_be_read_or_removed(client_with_org, db_session):
    _org(db_session, "someone-else", owner="other-user")
    theirs = Connector(
        org_id="someone-else", connector_type="splunk", display_name="Splunk", auth_method="api_key",
        status="active", encrypted_credentials="{}", config={"base_url": "https://splunk.example"},
    )
    db_session.add(theirs)
    db_session.commit()

    assert client_with_org.get("/api/orgs/someone-else/splunk-config").status_code == 404
    assert client_with_org.delete("/api/orgs/someone-else/splunk-config").status_code == 404
    db_session.expire_all()
    assert _count(db_session, Connector, org_id="someone-else") == 1


# ── Stored credentials ───────────────────────────────────────────────

@pytest.fixture
def encryption_key(monkeypatch):
    from app.core.security.connector_encryption import _get_connector_encryption_service

    monkeypatch.setenv("CONNECTOR_ENCRYPTION_KEY", base64.b64encode(os.urandom(32)).decode())
    _get_connector_encryption_service.cache_clear()
    yield
    _get_connector_encryption_service.cache_clear()


def test_unencrypted_credentials_are_encrypted_on_upgrade(db_session, encryption_key):
    _org(db_session, "org-a")
    bare = Connector(org_id="org-a", connector_type="splunk", display_name="Bare token",
                     auth_method="api_key", status="active", encrypted_credentials="hec-token-PLAINTEXT")
    plain_json = Connector(org_id="org-a", connector_type="splunk", display_name="Plain JSON",
                           auth_method="api_key", status="active",
                           encrypted_credentials=json.dumps({"api_key": "key-PLAINTEXT"}))
    db_session.add_all([bare, plain_json])
    db_session.commit()

    assert encrypt_plaintext_credentials(db_session) == 2
    assert encrypt_plaintext_credentials(db_session) == 0  # already encrypted: nothing to do

    db_session.expire_all()
    manager = ConnectorManager(db_session, "org-a")
    for connector, expected in ((bare, {"hec_token": "hec-token-PLAINTEXT"}), (plain_json, {"api_key": "key-PLAINTEXT"})):
        assert "PLAINTEXT" not in connector.encrypted_credentials
        assert "encrypted_blob" in json.loads(connector.encrypted_credentials)
        assert manager._decrypt_credentials(connector.encrypted_credentials) == expected


def test_splunk_hec_token_is_stored_encrypted(client_with_org, db_session, encryption_key, monkeypatch):
    from app.services.billing.entitlements import EntitlementService

    monkeypatch.setattr(EntitlementService, "has", lambda self, org_id, entitlement: True)
    response = client_with_org.post(
        "/api/orgs/test-org-123/splunk-config",
        json={"base_url": "https://splunk.example:8088", "hec_token": "hec-token-PLAINTEXT"},
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    stored = db_session.query(Connector).filter_by(org_id="test-org-123").one().encrypted_credentials
    assert "PLAINTEXT" not in stored
    assert ConnectorManager(db_session, "test-org-123")._decrypt_credentials(stored) == {
        "hec_token": "hec-token-PLAINTEXT"
    }
