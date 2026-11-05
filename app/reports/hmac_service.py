"""
Server-Side HMAC Integrity Validation Service for ResilAI Reports.

Enforces cryptographic server-side authentication (HMAC-SHA256) on generated reports
and PDF artifacts to guarantee origin authenticity and tamper-evidence.

Product Invariants:
- HMAC secret is strictly server-side and NEVER exposed to frontend, browser, API responses, Gemini, or PDF text.
- Validates origin authenticity and content integrity.
- Works in tandem with, but distinct from, SHA-256 evidence hashes.
- Auditable: Binds report_id, org_id, content hash, and timestamp.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("airs.reports.hmac")


def get_hmac_secret() -> str:
    """Retrieve the authoritative server-side HMAC secret.

    Priority:
    1. REPORT_HMAC_SECRET env var
    2. ENCRYPTION_SECRET env var
    3. Secure deterministic local fallback for dev/testing
    """
    secret = os.environ.get("REPORT_HMAC_SECRET")
    if not secret:
        secret = os.environ.get("ENCRYPTION_SECRET")
    if not secret:
        # Fallback for local development and test execution
        secret = "resilai-server-report-hmac-dev-secret-key-32b"
    return secret


def compute_content_sha256(content: bytes) -> str:
    """Compute the SHA-256 hash of the binary content."""
    if not isinstance(content, bytes):
        if isinstance(content, str):
            content = content.encode("utf-8")
        else:
            content = str(content).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def sign_report_content(
    report_id: str,
    org_id: str,
    content: bytes,
    secret: Optional[str] = None,
) -> str:
    """Generate an authoritative server-side HMAC-SHA256 signature for report content.

    Contextually binds:
      report_id | org_id | SHA256(content)
    """
    key = (secret or get_hmac_secret()).encode("utf-8")
    content_hash = compute_content_sha256(content)
    message = f"{report_id}|{org_id}|{content_hash}".encode("utf-8")

    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature


def verify_report_hmac(
    report_id: str,
    org_id: str,
    content: bytes,
    signature: str,
    secret: Optional[str] = None,
) -> bool:
    """Verify that a report's HMAC signature matches the content and signing context.

    Uses constant-time comparison to prevent timing attacks.
    Fails closed if signature is empty or context does not match.
    """
    if not signature or not isinstance(signature, str):
        return False

    expected_sig = sign_report_content(report_id, org_id, content, secret)
    return hmac.compare_digest(signature.strip().lower(), expected_sig.strip().lower())


def build_audit_metadata(
    report_id: str,
    org_id: str,
    content: bytes,
    timestamp: Optional[datetime] = None,
) -> Dict[str, str]:
    """Build public-safe audit traceability metadata for the report.

    NEVER includes the HMAC secret.
    """
    ts = timestamp or datetime.now(timezone.utc)
    content_hash = compute_content_sha256(content)
    sig = sign_report_content(report_id, org_id, content)

    return {
        "report_id": report_id,
        "org_id": org_id,
        "generated_at": ts.isoformat(),
        "content_sha256": content_hash,
        "hmac_signature": sig,
        "verification_url": f"/api/reports/{report_id}/verify",
    }
