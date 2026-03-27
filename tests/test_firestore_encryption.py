from types import SimpleNamespace

from app.core.security.encryption import generate_encryption_key, get_encryption_service
from app.db.firestore import (
    ASSESSMENT_SENSITIVE_FIELDS,
    FINDING_TRACKING_SENSITIVE_FIELDS,
    _assessment_to_doc,
    _decrypt_assessment_doc,
    _decrypt_doc_fields,
    _encrypt_doc_fields,
)


def _dummy_assessment():
    return SimpleNamespace(
        id="a1",
        organization_id="org1",
        owner_uid="owner1",
        version="1.0.0",
        status="in_progress",
        title="Q1 Security Assessment",
        schema_version=1,
        overall_score=72.5,
        maturity_level=3,
        maturity_name="Managed",
        created_at=None,
        updated_at=None,
        completed_at=None,
        answers=[SimpleNamespace(id="ans1", question_id="q1", value="yes", notes="sensitive", created_at=None, updated_at=None)],
        scores=[SimpleNamespace(id="s1", domain_id="d1", domain_name="Domain", score=2.0, max_score=5.0, weight=1.0, weighted_score=2.0, raw_points=2, max_raw_points=5, created_at=None)],
        findings=[SimpleNamespace(id="f1", title="Missing policy", description="desc", severity="medium", status="open", domain_id="d1", domain_name="Domain", question_id="q1", evidence="ev", recommendation="fix", priority="medium", nist_function=None, nist_category=None, nist_subcategory=None, soc2_controls=None, created_at=None, updated_at=None)],
    )


def test_assessment_firestore_payload_is_encrypted_when_secret_present(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_SECRET", generate_encryption_key())
    get_encryption_service.cache_clear()

    doc = _assessment_to_doc(_dummy_assessment())

    assert "encrypted_blob" in doc
    assert "encrypted_fields" in doc
    assert "title" not in doc
    assert "answers" not in doc
    assert "owner_uid" in doc
    assert "title" in doc["encrypted_fields"]


def test_assessment_firestore_payload_round_trips_after_decrypt(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_SECRET", generate_encryption_key())
    get_encryption_service.cache_clear()

    encrypted_doc = _assessment_to_doc(_dummy_assessment())
    plain_doc = _decrypt_assessment_doc(encrypted_doc)

    assert plain_doc["title"] == "Q1 Security Assessment"
    assert isinstance(plain_doc["answers"], list)
    assert plain_doc["owner_uid"] == "owner1"


def test_finding_tracking_encryption_round_trip(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_SECRET", generate_encryption_key())
    get_encryption_service.cache_clear()

    source = {
        "owner": "alice",
        "due_date": "2026-03-30",
        "control_id": "PR.AC-1",
        "framework_tag": "NIST",
        "status": "open",
        "updated_at": "2026-03-27T00:00:00+00:00",
    }

    encrypted = _encrypt_doc_fields(source, FINDING_TRACKING_SENSITIVE_FIELDS)
    decrypted = _decrypt_doc_fields(encrypted)

    assert "encrypted_blob" in encrypted
    assert "owner" not in encrypted
    assert decrypted["owner"] == "alice"
    assert decrypted["status"] == "open"


def test_assessment_sensitive_fields_configuration_is_non_empty():
    assert "findings" in ASSESSMENT_SENSITIVE_FIELDS
    assert "answers" in ASSESSMENT_SENSITIVE_FIELDS
