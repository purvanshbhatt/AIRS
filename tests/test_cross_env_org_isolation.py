"""Organizations written by another environment's key are skipped, not shown as 'Key Missing'."""
from unittest.mock import patch

from app.core.security.encryption import EncryptionService, generate_encryption_key
from app.db import firestore as fs
# Bind the real functions at import time: an autouse fixture replaces the
# module attributes with no-op mocks for the rest of the suite.
from app.db.firestore import firestore_get_all_orgs as real_get_all_orgs
from app.db.firestore import firestore_get_org as real_get_org


class _Doc:
    def __init__(self, data):
        self._data, self.exists = data, True

    def to_dict(self):
        return dict(self._data)


class _Query:
    def __init__(self, docs):
        self.docs = docs

    def where(self, *a, **k):
        return self

    def stream(self):
        return [_Doc(d) for d in self.docs]

    def document(self, org_id):
        match = [d for d in self.docs if d.get("id") == org_id]
        outer = self

        class _Ref:
            def get(self_inner):
                return _Doc(match[0]) if match else type("X", (), {"exists": False})()
        return _Ref()


class _Client:
    def __init__(self, docs):
        self.docs = docs

    def collection(self, name):
        return _Query(self.docs)


def test_foreign_environment_orgs_are_skipped():
    mine = EncryptionService(secret_b64=generate_encryption_key())
    other = EncryptionService(secret_b64=generate_encryption_key())
    own_doc = mine.encrypt_fields({"id": "org-mine", "owner_uid": "u1", "name": "My Clinic", "contact_email": "a@b.test"})
    foreign_doc = other.encrypt_fields({"id": "org-other", "owner_uid": "u1", "name": "Staging Org", "contact_email": "x@y.test"})
    plain_doc = {"id": "org-plain", "owner_uid": "u1", "name": "Legacy Plain"}
    client = _Client([own_doc, foreign_doc, plain_doc])

    with patch.object(fs, "is_firestore_available", return_value=True), \
         patch.object(fs, "get_firestore_client", return_value=client), \
         patch("app.core.security.encryption.get_encryption_service", return_value=mine):
        orgs = real_get_all_orgs(owner_uid="u1")
        ids = sorted(o["id"] for o in orgs)
        assert ids == ["org-mine", "org-plain"]
        assert all(fs.UNREADABLE_ORG_MARKER not in o for o in orgs)
        assert all("Key Missing" not in (o.get("name") or "") for o in orgs)
        assert real_get_org("org-other") is None
        assert real_get_org("org-mine")["contact_email"] == "a@b.test"
