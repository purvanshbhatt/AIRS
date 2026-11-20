"""
Regression proofs for the security gaps left open after the pilot pass.

* The sentinel routes and the board-story PDF only answer the owner of the
  organisation asked about.
* An auditor link is stored (hash only), so it survives a restart, and a
  revocation is read back from storage.
* Connector credentials saved before a key rotation still decrypt, and a
  hosted environment refuses to store a credential without a key.
"""
import base64
import os

import pytest

from app.core.config import Settings
from app.core.security import connector_encryption
from app.db.durable_mirror import MIRROR_SPECS
from app.models.auditor_link import AuditorLink
from app.models.organization import Organization
from app.services import auditor_view

OWN_ORG = "test-org-123"  # provisioned by the client_with_org fixture
OTHER_ORG = "someone-elses-org"


def _other_org(db_session):
    db_session.add(Organization(id=OTHER_ORG, name="Other Practice", owner_uid="another-user"))
    db_session.commit()


def _key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


# ---------------------------------------------------------------------------
# Owner checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["status", "telemetry", "evidence", "simulations"])
def test_sentinel_routes_refuse_another_organisation(db_session, client_with_org, path):
    _other_org(db_session)

    resp = client_with_org.get(f"/api/sentinel/{path}", params={"org_id": OTHER_ORG})

    assert resp.status_code == 404, resp.text


def test_sentinel_routes_need_an_organisation_id(client_with_org):
    # The old code answered for one hard-coded organisation with no id at all.
    assert client_with_org.get("/api/sentinel/telemetry").status_code == 422


def test_sentinel_telemetry_answers_the_owner(client_with_org):
    resp = client_with_org.get("/api/sentinel/telemetry", params={"org_id": OWN_ORG})

    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_board_story_pdf_refuses_another_organisation(db_session, client_with_org):
    _other_org(db_session)

    resp = client_with_org.get("/api/v1/reports/board-story.pdf", params={"org_id": OTHER_ORG})

    assert resp.status_code == 404, resp.text


def test_board_story_pdf_is_served_to_the_owner(client_with_org):
    resp = client_with_org.get("/api/v1/reports/board-story.pdf", params={"org_id": OWN_ORG})

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Auditor links are stored
# ---------------------------------------------------------------------------

def test_auditor_link_survives_a_restart_and_stores_only_the_hash(db_session):
    link = auditor_view.create_auditor_link("org-a", "Org A", "user-a", db=db_session)

    # A restart empties process memory; the table is what remains.
    auditor_view._auditor_tokens.clear()
    db_session.expire_all()

    meta = auditor_view.validate_token(link["token"], db=db_session)
    assert meta is not None
    assert meta["org_id"] == "org-a"
    assert meta["access_count"] == 1

    rows = db_session.query(AuditorLink).all()
    assert len(rows) == 1
    assert rows[0].token_hash != link["token"]
    assert len(rows[0].token_hash) == 64
    assert link["token"] not in repr(rows[0].__dict__)


def test_stored_auditor_link_can_be_revoked_only_by_its_organisation(db_session):
    link = auditor_view.create_auditor_link("org-a", "Org A", "user-a", db=db_session)

    assert auditor_view.revoke_token(link["token"], org_id="org-b", db=db_session) is False
    assert auditor_view.validate_token(link["token"], db=db_session) is not None

    assert auditor_view.revoke_token(link["token"], org_id="org-a", db=db_session) is True
    assert auditor_view.validate_token(link["token"], db=db_session) is None
    assert auditor_view.list_active_tokens("org-a", db=db_session) == []


def test_auditor_link_endpoints_use_storage(db_session, client_with_org):
    created = client_with_org.post(f"/api/governance/orgs/{OWN_ORG}/auditor-link")
    assert created.status_code in (200, 201), created.text
    token = created.json()["token"]

    assert db_session.query(AuditorLink).filter(AuditorLink.org_id == OWN_ORG).count() == 1
    auditor_view._auditor_tokens.clear()

    listed = client_with_org.get(f"/api/governance/orgs/{OWN_ORG}/auditor-links")
    assert listed.status_code == 200, listed.text
    assert listed.json()["count"] == 1

    revoked = client_with_org.delete(f"/api/governance/orgs/{OWN_ORG}/auditor-link", params={"token": token})
    assert revoked.status_code == 200, revoked.text
    assert auditor_view.validate_token(token, db=db_session) is None


def test_auditor_links_are_copied_to_durable_storage():
    assert "auditor_links" in {spec.table for spec in MIRROR_SPECS}


# ---------------------------------------------------------------------------
# Connector credential encryption
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_key_env(monkeypatch):
    for name in (
        "CONNECTOR_ENCRYPTION_KEY",
        "CONNECTOR_ENCRYPTION_KEY_PREVIOUS",
        "ENCRYPTION_SECRET",
        "ENCRYPTION_SECRET_PREVIOUS",
        "GCP_PROJECT_ID",
        "GOOGLE_CLOUD_PROJECT",
    ):
        monkeypatch.delenv(name, raising=False)
    connector_encryption._get_connector_encryption_service.cache_clear()
    yield monkeypatch
    connector_encryption._get_connector_encryption_service.cache_clear()


def test_connector_credentials_are_not_readable_in_storage(clean_key_env):
    clean_key_env.setenv("ENCRYPTION_SECRET", _key())
    secret = '{"secret_access_key": "SENTINEL-not-a-real-key"}'

    stored = connector_encryption.encrypt_value(secret)

    assert "SENTINEL-not-a-real-key" not in stored
    assert "encrypted_blob" in stored
    assert connector_encryption.decrypt_value(stored) == secret


def test_connector_credentials_saved_before_a_key_rotation_still_decrypt(clean_key_env):
    old_key, new_key = _key(), _key()
    secret = '{"client_secret": "SENTINEL-rotation"}'

    clean_key_env.setenv("ENCRYPTION_SECRET", old_key)
    stored_under_old_key = connector_encryption.encrypt_value(secret)

    # Rotate: the old key moves to ENCRYPTION_SECRET_PREVIOUS.
    clean_key_env.setenv("ENCRYPTION_SECRET", new_key)
    clean_key_env.setenv("ENCRYPTION_SECRET_PREVIOUS", old_key)
    connector_encryption._get_connector_encryption_service.cache_clear()

    assert connector_encryption.decrypt_value(stored_under_old_key) == secret
    # New writes use the new key and round-trip.
    restored = connector_encryption.encrypt_value(secret)
    assert restored != stored_under_old_key
    assert connector_encryption.decrypt_value(restored) == secret


def test_wrong_key_does_not_return_the_secret(clean_key_env):
    clean_key_env.setenv("ENCRYPTION_SECRET", _key())
    stored = connector_encryption.encrypt_value('{"token": "SENTINEL-wrong-key"}')

    clean_key_env.setenv("ENCRYPTION_SECRET", _key())
    connector_encryption._get_connector_encryption_service.cache_clear()

    assert "SENTINEL-wrong-key" not in connector_encryption.decrypt_value(stored)


def test_hosted_environment_refuses_to_store_a_credential_without_a_key(clean_key_env):
    clean_key_env.setattr(connector_encryption, "_must_encrypt", lambda: True)

    with pytest.raises(RuntimeError, match="not saved"):
        connector_encryption.encrypt_value('{"token": "SENTINEL-plaintext"}')


def test_developer_machine_without_a_key_still_works(clean_key_env):
    clean_key_env.setattr(connector_encryption, "_must_encrypt", lambda: False)

    assert connector_encryption.encrypt_value('{"a": 1}') == '{"a": 1}'


def test_a_malformed_key_stops_startup_in_a_hosted_environment():
    with pytest.raises(ValueError, match="32 bytes"):
        Settings(ENV="staging", ENCRYPTION_SECRET="not-a-real-key")


def test_a_well_formed_key_passes_the_key_check():
    try:
        Settings(ENV="staging", ENCRYPTION_SECRET=_key())
    except ValueError as exc:  # other staging settings may be missing in a test run
        assert "32 bytes" not in str(exc)
