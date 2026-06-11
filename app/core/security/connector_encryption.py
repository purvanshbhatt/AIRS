"""
Connector Credential Encryption — AES-256-GCM with Secret Manager Key.

Dedicated encryption utilities for connector credentials. Uses a separate
key (CONNECTOR_ENCRYPTION_KEY) from the main org-data encryption key to
maintain security domain separation.

Key Hierarchy:
  LOCAL   → CONNECTOR_ENCRYPTION_KEY env var
  STAGING → GCP Secret Manager (projects/<project>/secrets/connector-encryption-key)
  PROD    → GCP Secret Manager

Design: Leverages the existing EncryptionService from app.core.security.encryption
with a connector-specific key to avoid cross-domain key reuse.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

logger = logging.getLogger("airs.security.connector_encryption")


def _load_key_from_secret_manager() -> Optional[str]:
    """Attempt to load CONNECTOR_ENCRYPTION_KEY from GCP Secret Manager.

    Falls back to environment variable if Secret Manager is unavailable.
    """
    # 1. Check environment first (local dev, CI)
    env_key = os.environ.get("CONNECTOR_ENCRYPTION_KEY")
    if env_key:
        logger.info("Connector encryption key loaded from environment variable")
        return env_key

    # 2. Try GCP Secret Manager
    try:
        from google.cloud import secretmanager

        project_id = os.environ.get("GCP_PROJECT_ID", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
        if not project_id:
            logger.warning("No GCP_PROJECT_ID set — skipping Secret Manager")
            return None

        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{project_id}/secrets/connector-encryption-key/versions/latest"

        response = client.access_secret_version(request={"name": secret_name})
        key_value = response.payload.data.decode("utf-8").strip()
        logger.info("Connector encryption key loaded from Secret Manager")
        return key_value

    except ImportError:
        logger.debug("google-cloud-secret-manager not installed — key unavailable")
    except Exception as exc:
        logger.warning("Secret Manager key load failed: %s", exc)

    return None


@lru_cache(maxsize=1)
def _get_connector_encryption_service():
    """Return a dedicated EncryptionService for connector credentials."""
    from app.core.security.encryption import EncryptionService

    key_b64 = _load_key_from_secret_manager()
    svc = EncryptionService(secret_b64=key_b64)

    if not svc.enabled:
        logger.warning(
            "Connector encryption DISABLED — credentials stored as plaintext. "
            "Set CONNECTOR_ENCRYPTION_KEY or provision via Secret Manager."
        )
    return svc


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value (typically JSON credentials).

    Returns a base64-encoded ciphertext string suitable for database storage.
    Falls through to plaintext if encryption is disabled.
    """
    svc = _get_connector_encryption_service()
    if not svc.enabled:
        return plaintext

    payload = {"value": plaintext}
    encrypted = svc.encrypt_fields(payload, sensitive_fields={"value"})
    return json.dumps(encrypted)


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a previously-encrypted credential string.

    Returns the original plaintext. Falls through if input is not encrypted.
    """
    svc = _get_connector_encryption_service()

    try:
        doc = json.loads(ciphertext)
    except (json.JSONDecodeError, TypeError):
        return ciphertext  # Not encrypted — return as-is

    if not isinstance(doc, dict) or "encrypted_blob" not in doc:
        # Plaintext JSON or legacy format
        return doc.get("value", ciphertext) if isinstance(doc, dict) else ciphertext

    if not svc.enabled:
        logger.warning("Cannot decrypt: connector encryption disabled")
        return ciphertext

    decrypted = svc.decrypt_fields(doc)
    return decrypted.get("value", ciphertext)
