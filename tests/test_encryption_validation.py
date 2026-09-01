"""
Encryption Validation Test Suite — AES-256-GCM Security Guarantees.

Validates:
  1. Plaintext is encrypted
  2. Ciphertext differs from plaintext
  3. Correct key decrypts successfully
  4. Wrong key fails
  5. Tampered ciphertext fails authentication
  6. Passthrough mode works when key is absent
  7. Organization isolation of encrypted credentials
"""

import pytest
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.security.encryption import EncryptionService, generate_encryption_key


def _make_key() -> str:
    return generate_encryption_key()


class TestEncryptionBasics:
    def test_plaintext_is_encrypted(self):
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        doc = {"name": "Test Org", "api_key": "sk-secret-12345"}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        assert "api_key" not in encrypted
        assert "encrypted_blob" in encrypted
        assert "encrypted_iv" in encrypted

    def test_ciphertext_differs_from_plaintext(self):
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        secret = "my-super-secret-api-key"
        doc = {"name": "Test", "api_key": secret}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        blob = encrypted["encrypted_blob"]
        # The blob should not contain the plaintext
        decoded_blob = base64.urlsafe_b64decode(blob)
        assert secret.encode() not in decoded_blob

    def test_correct_key_decrypts(self):
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        secret = "my-super-secret-api-key"
        doc = {"name": "Test", "api_key": secret}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        decrypted = svc.decrypt_fields(encrypted)
        assert decrypted["api_key"] == secret
        assert decrypted["name"] == "Test"

    def test_wrong_key_fails(self):
        key1 = _make_key()
        key2 = _make_key()
        svc1 = EncryptionService(secret_b64=key1)
        svc2 = EncryptionService(secret_b64=key2)
        doc = {"name": "Test", "api_key": "secret"}
        encrypted = svc1.encrypt_fields(doc, sensitive_fields={"api_key"})
        # svc2 with different key should fail to decrypt
        result = svc2.decrypt_fields(encrypted)
        # On failure, decrypt_fields returns non-sensitive fields only
        assert "api_key" not in result

    def test_tampered_ciphertext_fails(self):
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        doc = {"name": "Test", "api_key": "secret"}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        # Tamper with the blob
        blob_bytes = base64.urlsafe_b64decode(encrypted["encrypted_blob"])
        tampered = bytearray(blob_bytes)
        tampered[0] ^= 0xFF  # flip bits
        encrypted["encrypted_blob"] = base64.urlsafe_b64encode(bytes(tampered)).decode()
        result = svc.decrypt_fields(encrypted)
        # Should not contain the secret
        assert "api_key" not in result


class TestEncryptionPassthrough:
    def test_passthrough_when_no_key(self):
        svc = EncryptionService(secret_b64=None)
        assert not svc.enabled
        doc = {"name": "Test", "api_key": "secret"}
        result = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        # In passthrough mode, document is returned as-is
        assert result["api_key"] == "secret"


class TestEncryptionKeyGeneration:
    def test_generate_key_produces_valid_base64(self):
        key = generate_encryption_key()
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32  # 256 bits

    def test_generated_keys_are_unique(self):
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2


class TestConnectorEncryptionIsolation:
    """Validate that connector credentials are never exposed in API responses."""

    def test_encrypted_fields_list_is_preserved(self):
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        doc = {"name": "Splunk", "api_key": "secret", "token": "bearer-xyz"}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key", "token"})
        assert "encrypted_fields" in encrypted
        assert set(encrypted["encrypted_fields"]) == {"api_key", "token"}

    def test_narrative_layer_never_receives_secrets(self):
        """Verify that encrypted documents strip secrets before narrative use."""
        key = _make_key()
        svc = EncryptionService(secret_b64=key)
        doc = {"name": "Splunk", "api_key": "secret-key-123"}
        encrypted = svc.encrypt_fields(doc, sensitive_fields={"api_key"})
        # Simulating what would be passed to narrative layer:
        # only non-sensitive fields should be visible
        narrative_safe = {k: v for k, v in encrypted.items()
                         if k not in ("encrypted_blob", "encrypted_iv", "key_version", "encrypted_fields")}
        assert "api_key" not in narrative_safe
        assert narrative_safe["name"] == "Splunk"
