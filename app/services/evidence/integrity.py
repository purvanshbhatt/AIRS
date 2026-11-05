"""
ResilAI Authoritative Evidence Integrity Verification Module.

Enforces cryptographic integrity (SHA-256) on all structured telemetry payloads
before deterministic evaluation and ledger persistence.

Product Invariants:
- SHA-256 must be calculated from canonicalized authoritative evidence payload.
- Any tampering, truncation, or modification of payload MUST fail closed.
- Presentation fields or mutable display metadata are NEVER included in the hash.
- LLMs NEVER calculate or influence hashes or scores.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("airs.evidence.integrity")


def canonicalize_payload(payload: Any) -> str:
    """Canonicalize a telemetry payload into a deterministic string representation.

    Rules:
    - Dict keys are sorted alphabetically.
    - Floating point numbers and dates are formatted predictably.
    - Whitespace formatting is normalized (no indentation, consistent separators).
    """
    if payload is None:
        return "{}"
    if not isinstance(payload, dict):
        payload = {"raw": payload}

    return json.dumps(payload, sort_keys=True, default=str)


def compute_evidence_hash(
    source_connector: str,
    timestamp_iso: str,
    payload: Dict[str, Any],
) -> str:
    """Compute the authoritative SHA-256 evidence hash.

    The hash binds:
      source_connector | timestamp_iso | canonicalized_payload
    """
    canonical_payload = canonicalize_payload(payload)
    base_string = f"{source_connector}|{timestamp_iso}|{canonical_payload}"
    return hashlib.sha256(base_string.encode("utf-8")).hexdigest()


def verify_evidence_hash(
    source_connector: str,
    timestamp_iso: str,
    payload: Dict[str, Any],
    claimed_hash: str,
) -> bool:
    """Verify that a claimed evidence hash matches the recomputed authoritative hash.

    Fails closed if claimed_hash is empty, None, or doesn't match.
    """
    if not claimed_hash or not isinstance(claimed_hash, str):
        return False

    expected_hash = compute_evidence_hash(source_connector, timestamp_iso, payload)
    is_valid = (claimed_hash.strip().lower() == expected_hash.strip().lower())
    if not is_valid:
        logger.warning(
            "Evidence integrity violation: claimed_hash=%s does not match expected_hash=%s for connector=%s",
            claimed_hash,
            expected_hash,
            source_connector,
        )
    return is_valid
