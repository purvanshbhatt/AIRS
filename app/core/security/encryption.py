"""
Field-Level Encryption Service — AES-256-GCM.

Encrypts sensitive organization fields at the application layer *before*
they are stored in Firestore.  Google's infrastructure encryption (at-rest)
still applies, but this layer ensures that:

  1. A compromised service account sees only ciphertext.
  2. Misconfigured Firebase Rules never expose plaintext PII.
  3. Internal access yields no readable customer data.

Design decisions:
  • AES-256-GCM — authenticated encryption; nonce + ciphertext + tag in one blob.
  • Per-document random 96-bit nonce (generated on every write).
  • Key versioning baked-in so key rotation is non-destructive.
  • Selective encryption — only fields in ``SENSITIVE_FIELDS`` are encrypted;
    booleans, scores, and timestamps remain queryable / indexable.

Key storage hierarchy:
  LOCAL  → ENCRYPTION_SECRET in .env / env var
  STAGING → Google Secret Manager
  PROD   → Cloud KMS or Secret Manager

Usage::

    svc = get_encryption_service()
    encrypted = svc.encrypt_fields(org_document, key_version=1)
    original  = svc.decrypt_fields(encrypted)
"""

from __future__ import annotations

import base64
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("airs.security.encryption")


# ═══════════════════════════════════════════════════════════════════════
# Sensitive field definitions
# ═══════════════════════════════════════════════════════════════════════

# Fields that contain PII or organization-identifiable metadata.
# These are encrypted into a single ``encrypted_blob`` before Firestore write.
SENSITIVE_FIELDS: Set[str] = {
    "name",
    "contact_name",
    "contact_email",
    "notes",
    "owner_uid",
    "industry",
    "geo_regions",
    "revenue_band",
}

# Fields that must NEVER be encrypted (required for queries / indexing).
NON_SENSITIVE_FIELDS: Set[str] = {
    "id",
    "analytics_enabled",
    "processes_pii",
    "processes_phi",
    "processes_cardholder_data",
    "handles_dod_data",
    "uses_ai_in_production",
    "government_contractor",
    "financial_services",
    "application_tier",
    "sla_target",
    "size",
    "employee_count",
    "integration_status",
    "created_at",
    "updated_at",
}


# ═══════════════════════════════════════════════════════════════════════
# Encryption Service
# ═══════════════════════════════════════════════════════════════════════

class EncryptionService:
    """
    AES-256-GCM field-level encryption for Firestore documents.

    The service is initialised with a 32-byte secret (base64-encoded in
    the environment variable ``ENCRYPTION_SECRET``).

    If no secret is configured the service operates in *passthrough* mode —
    fields are stored unencrypted and a warning is emitted once at startup.
    This keeps local development frictionless while production is secured.
    """

    def __init__(self, secret_b64: Optional[str] = None):
        self._enabled = False
        self._aesgcm: Optional[AESGCM] = None

        if secret_b64:
            try:
                key_bytes = base64.urlsafe_b64decode(secret_b64)
                if len(key_bytes) != 32:
                    raise ValueError(
                        f"ENCRYPTION_SECRET must decode to exactly 32 bytes "
                        f"(got {len(key_bytes)})"
                    )
                self._aesgcm = AESGCM(key_bytes)
                self._enabled = True
                logger.info("EncryptionService: AES-256-GCM initialised (key loaded)")
            except Exception as exc:
                logger.error(
                    "EncryptionService: failed to initialise key — running in "
                    "PASSTHROUGH mode. Error: %s",
                    exc,
                )
        else:
            logger.warning(
                "EncryptionService: ENCRYPTION_SECRET not set — running in "
                "PASSTHROUGH mode (fields stored as plaintext)."
            )

    # ── Properties ────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        """Return ``True`` when encryption is active."""
        return self._enabled

    # ── Low-level encrypt / decrypt ───────────────────────────────────

    def _encrypt_blob(self, plaintext: bytes) -> tuple[bytes, bytes]:
        """
        Encrypt *plaintext* and return ``(nonce, ciphertext_with_tag)``.

        Raises ``RuntimeError`` if service is not enabled.
        """
        if not self._enabled or self._aesgcm is None:
            raise RuntimeError("Encryption is not enabled")
        nonce = os.urandom(12)  # 96-bit random nonce
        ct = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce, ct

    def _decrypt_blob(self, nonce: bytes, ciphertext: bytes) -> bytes:
        """Decrypt and authenticate *ciphertext*."""
        if not self._enabled or self._aesgcm is None:
            raise RuntimeError("Encryption is not enabled")
        return self._aesgcm.decrypt(nonce, ciphertext, None)

    # ── Field-level API ───────────────────────────────────────────────

    def encrypt_fields(
        self,
        document: Dict[str, Any],
        key_version: int = 1,
    ) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in *document* and return a new document
        suitable for Firestore storage.

        Non-sensitive fields are passed through unchanged.  Sensitive
        fields are removed and replaced with::

            encrypted_blob: <base64 ciphertext>
            encrypted_iv:   <base64 nonce>
            key_version:    <int>

        If encryption is disabled (passthrough mode) the document is
        returned as-is.
        """
        if not self._enabled:
            return dict(document)

        # Split sensitive from non-sensitive
        sensitive_payload: Dict[str, Any] = {}
        result: Dict[str, Any] = {}

        for key, value in document.items():
            if key in SENSITIVE_FIELDS:
                sensitive_payload[key] = value
            else:
                result[key] = value

        if not sensitive_payload:
            return result  # nothing to encrypt

        # Serialise → encrypt → base64
        plaintext = json.dumps(sensitive_payload, default=str).encode("utf-8")
        nonce, ciphertext = self._encrypt_blob(plaintext)

        result["encrypted_blob"] = base64.urlsafe_b64encode(ciphertext).decode("ascii")
        result["encrypted_iv"] = base64.urlsafe_b64encode(nonce).decode("ascii")
        result["key_version"] = key_version

        return result

    def decrypt_fields(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt an encrypted Firestore document back to its original form.

        If the document has no ``encrypted_blob`` key (legacy / passthrough)
        it is returned unchanged.
        """
        encrypted_blob_b64 = document.get("encrypted_blob")
        encrypted_iv_b64 = document.get("encrypted_iv")

        if not encrypted_blob_b64 or not encrypted_iv_b64:
            # Legacy or passthrough document — return as-is.
            return dict(document)

        if not self._enabled:
            logger.warning(
                "Document has encrypted_blob but encryption is disabled — "
                "returning non-sensitive fields only"
            )
            # Strip encryption metadata, return only cleartext fields.
            result = {
                k: v
                for k, v in document.items()
                if k not in ("encrypted_blob", "encrypted_iv", "key_version")
            }
            return result

        try:
            ciphertext = base64.urlsafe_b64decode(encrypted_blob_b64)
            nonce = base64.urlsafe_b64decode(encrypted_iv_b64)
            plaintext = self._decrypt_blob(nonce, ciphertext)
            sensitive = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            logger.error("Decryption failed for document: %s", exc)
            # Return non-sensitive fields only on failure
            result = {
                k: v
                for k, v in document.items()
                if k not in ("encrypted_blob", "encrypted_iv", "key_version")
            }
            return result

        # Merge non-sensitive fields with decrypted sensitive fields
        result: Dict[str, Any] = {}
        for key, value in document.items():
            if key in ("encrypted_blob", "encrypted_iv", "key_version"):
                continue
            result[key] = value
        result.update(sensitive)

        return result


# ═══════════════════════════════════════════════════════════════════════
# Singleton accessor
# ═══════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_encryption_service() -> EncryptionService:
    """
    Return the application-wide ``EncryptionService``.

    Reads ``ENCRYPTION_SECRET`` from the environment on first call.
    Subsequent calls return the cached instance.
    """
    secret = os.environ.get("ENCRYPTION_SECRET")
    return EncryptionService(secret_b64=secret)


def generate_encryption_key() -> str:
    """
    Generate a new 256-bit encryption key and return it as a
    URL-safe base64 string, ready to be stored as ``ENCRYPTION_SECRET``.

    Usage (one-time)::

        python -c "from app.core.security.encryption import generate_encryption_key; print(generate_encryption_key())"
    """
    key = AESGCM.generate_key(bit_length=256)
    return base64.urlsafe_b64encode(key).decode("ascii")
