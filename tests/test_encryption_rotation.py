"""
Key rotation: documents encrypted under a retired key must still decrypt
when that key is supplied via ENCRYPTION_SECRET_PREVIOUS, and new writes
must use the current key.
"""
from app.core.security.encryption import EncryptionService, generate_encryption_key


def test_previous_key_decrypts_old_documents_and_new_writes_use_current_key():
    old_key = generate_encryption_key()
    new_key = generate_encryption_key()

    old_svc = EncryptionService(secret_b64=old_key)
    doc = old_svc.encrypt_fields({"id": "org-1", "name": "Clinic", "contact_email": "a@b.test"})
    assert "encrypted_blob" in doc

    rotated = EncryptionService(secret_b64=new_key, previous_secrets_b64=[old_key])
    assert rotated.has_previous_keys
    plain = rotated.decrypt_fields(doc)
    assert plain.get("contact_email") == "a@b.test"

    rewritten = rotated.encrypt_fields(plain)
    only_new = EncryptionService(secret_b64=new_key)
    assert only_new.decrypt_fields(rewritten).get("contact_email") == "a@b.test"
    # The old key alone can no longer read the rewritten document.
    assert old_svc.decrypt_fields(rewritten).get("contact_email") != "a@b.test"


def test_without_previous_key_old_document_is_unreadable_but_non_fatal():
    old_key = generate_encryption_key()
    new_key = generate_encryption_key()
    doc = EncryptionService(secret_b64=old_key).encrypt_fields({"id": "o", "name": "X", "contact_email": "a@b.test"})
    result = EncryptionService(secret_b64=new_key).decrypt_fields(doc)
    assert result.get("contact_email") != "a@b.test"
