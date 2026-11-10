"""Durable mirror: committed rows of registered tables go to Firestore and come back."""
import json

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db import durable_mirror as dm
from app.models.connector import Connector
from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent


class _Doc:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def to_dict(self):
        return dict(self.store[self.key])


class _Ref:
    def __init__(self, store, key):
        self.store, self.key = store, key


class _Collection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return _Ref(self.store, key)

    def limit(self, n):
        return self

    def stream(self):
        return [_Doc(self.store, k) for k in list(self.store)]


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

    def collection(self, name):
        return _Collection(self.collections.setdefault(name, {}))

    def batch(self):
        return _Batch()


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


def _org(db):
    org = Organization(id="mirror-org", name="Mirror Org", owner_uid="u1")
    db.add(org)
    db.commit()
    return org


def test_commit_mirrors_connector_without_plaintext_secret(db_session, mirror):
    _org(db_session)
    c = Connector(org_id="mirror-org", connector_type="aws", display_name="AWS", auth_method="api_key",
                  status="pending_auth", encrypted_credentials=json.dumps({"aws_secret_access_key": "TOPSECRET"}),
                  config={"aws_region": "us-east-1"})
    db_session.add(c)
    db_session.commit()

    rows = mirror.collections[dm.collection_name("connectors")]
    assert c.id in rows
    stored = rows[c.id]
    assert stored["connector_type"] == "aws" and stored["config"] == {"aws_region": "us-east-1"}
    # No encryption key in tests: the secret must not leave the process in clear text.
    assert "TOPSECRET" not in json.dumps(stored, default=str)
    # Organizations are not a mirrored table.
    assert dm.collection_name("organizations") not in mirror.collections


def test_update_and_rollback(db_session, mirror):
    _org(db_session)
    c = Connector(org_id="mirror-org", connector_type="webhook", display_name="Hook", auth_method="webhook",
                  status="pending_auth", encrypted_credentials="{}")
    db_session.add(c)
    db_session.commit()
    c.status = "active"
    db_session.commit()
    assert mirror.collections[dm.collection_name("connectors")][c.id]["status"] == "active"

    c.status = "error"
    db_session.flush()
    db_session.rollback()
    assert mirror.collections[dm.collection_name("connectors")][c.id]["status"] == "active"


def test_restore_brings_rows_back_and_does_not_remirror(db_session, mirror):
    _org(db_session)
    c = Connector(org_id="mirror-org", connector_type="webhook", display_name="Hook", auth_method="webhook",
                  status="active", encrypted_credentials="{}")
    ev = TelemetryEvent(org_id="mirror-org", connector_id=None, event_type="msp.backup", source_system="webhook",
                        source_event_id="e1", payload_hash="h", payload="{}", severity="low")
    db_session.add_all([c, ev])
    db_session.commit()
    cid, eid = c.id, ev.id

    # Simulate a cold start: the SQL cache is empty, Firestore still has the rows.
    db_session.query(TelemetryEvent).delete()
    db_session.query(Connector).delete()
    db_session.info[dm._SUPPRESS_KEY] = True
    db_session.commit()
    db_session.info.pop(dm._SUPPRESS_KEY, None)
    assert db_session.query(Connector).count() == 0

    def snapshot():
        return json.dumps({k: v for k, v in mirror.collections.items() if v}, default=str, sort_keys=True)

    writes_before = snapshot()
    restored = dm.restore_from_mirror(db_session)
    assert restored.get("connectors") == 1 and restored.get("telemetry_events") == 1
    assert db_session.query(Connector).get(cid).status == "active"
    assert db_session.query(TelemetryEvent).get(eid).source_event_id == "e1"
    assert snapshot() == writes_before


def test_collections_are_namespaced_per_environment():
    name = dm.collection_name("connectors")
    assert name.endswith("_mirror_connectors") and name != "connectors"
