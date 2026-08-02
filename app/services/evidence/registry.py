"""
EvidenceRegistry — vendor-agnostic connector resolution.

Adapters register themselves by ``connector_name``; the Verification
Engine looks them up via :func:`get_adapter` rather than holding a
direct import to a vendor module.

Per ADR-009:
  - Switching vendors (e.g. Splunk ↔ SentinelOne) requires no change
    to scoring, verification, or confidence code. Only the
    corresponding ``adapters/<vendor>.py`` implementation differs.
  - The registry holds no vendor-specific imports.
  - Lookup failures return ``None``; the verification engine treats
    missing evidence as a clean confidence-0 state.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, Iterable, List, Optional

from .base_adapter import EvidenceAdapter


logger = logging.getLogger("airs.adapters")


class EvidenceRegistry:
    """In-memory registry of ``EvidenceAdapter`` instances.

    Singleton-style access via ``get_instance()``. The base service
    uses an instance-per-process model; tests can construct a fresh
    registry for isolation.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, EvidenceAdapter] = {}
        self._lock = threading.RLock()

    def register(self, adapter: EvidenceAdapter) -> None:
        if not isinstance(adapter, EvidenceAdapter):
            raise TypeError(
                f"EvidenceRegistry expects EvidenceAdapter instances; got {type(adapter)}"
            )
        name = adapter.connector_name
        with self._lock:
            if name in self._adapters:
                logger.info("Replacing existing adapter for connector %s", name)
            self._adapters[name] = adapter

    def unregister(self, connector_name: str) -> bool:
        with self._lock:
            return self._adapters.pop(connector_name, None) is not None

    def get_adapter(self, connector_name: str) -> Optional[EvidenceAdapter]:
        with self._lock:
            return self._adapters.get(connector_name)

    def list_connectors(self) -> List[str]:
        with self._lock:
            return sorted(self._adapters.keys())

    def adapters(self) -> Iterable[EvidenceAdapter]:
        with self._lock:
            return list(self._adapters.values())

    def is_registered(self, connector_name: str) -> bool:
        with self._lock:
            return connector_name in self._adapters


# ── Module-level singleton ──────────────────────────────────────────

_instance: Optional[EvidenceRegistry] = None
_instance_lock = threading.Lock()


def get_instance() -> EvidenceRegistry:
    """Return the process-wide ``EvidenceRegistry`` singleton."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = EvidenceRegistry()
    return _instance


def reset_instance() -> None:
    """Discard the singleton (used by tests)."""
    global _instance
    with _instance_lock:
        _instance = None
