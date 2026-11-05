"""
Connector secret hygiene helpers.

Connector forms post both ``credentials`` (encrypted at rest) and ``config``
(plain JSON). These helpers make sure secret-looking keys never land in, or
are returned from, the plaintext ``config`` column.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# Exact keys that are always secrets.
_SECRET_KEYS = frozenset({
    "api_key",
    "apikey",
    "hec_token",
    "client_secret",
    "secret_key",
    "aws_secret_access_key",
    "aws_access_key_id",
    "webhook_secret",
    "credentials",
    "private_key",
})

# Substrings that mark a key as secret-bearing.
_SECRET_MARKERS = ("secret", "password", "passwd", "token", "private_key", "passphrase")


def is_secret_key(key: str) -> bool:
    """True when a config key name denotes a credential."""
    if not isinstance(key, str):
        return False
    lowered = key.strip().lower()
    if lowered in _SECRET_KEYS:
        return True
    return any(marker in lowered for marker in _SECRET_MARKERS)


def scrub_secrets(config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a copy of ``config`` without secret-bearing keys.

    Nested dicts are scrubbed recursively. Non-dict input is returned as-is.
    """
    if not isinstance(config, dict):
        return config
    cleaned: Dict[str, Any] = {}
    for key, value in config.items():
        if is_secret_key(key):
            continue
        cleaned[key] = scrub_secrets(value) if isinstance(value, dict) else value
    return cleaned
