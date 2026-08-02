"""Shared evidence status / result dataclasses.

These three types used to live alongside ``app/services/splunk.py``
(SplunkService.delete 2026-07-19 — Sprint 2.2 consolidation).
They are still consumed by:

  - ``app/services/elastic.py`` (Elastic SIEM verify_* returns an
    ``EvidenceResult`` and ``LoggingHealthResult``);
  - the Evidence Adapter layer (vendor-neutral canonical evidence
    adaptations).

They live here as a small house-keeping module so the Splunk path
can delete its old facade and yet keep these vendor-neutral types
available to other SIEMs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceStatus(str, Enum):
    """Vendor-neutral status of an evidence verification check."""

    VERIFIED = "verified"
    PARTIAL = "partial"
    NOT_VERIFIED = "not_verified"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


class EvidenceResult:
    """Vendor-neutral result of a single evidence verification check."""

    def __init__(
        self,
        control: str,
        status: EvidenceStatus,
        event_count: int = 0,
        sample_events: Optional[List[Dict[str, Any]]] = None,
        message: str = "",
        query_used: str = "",
        verified_at: Optional[str] = None,
    ):
        self.control = control
        self.status = status
        self.event_count = event_count
        self.sample_events = sample_events or []
        self.message = message
        self.query_used = query_used
        self.verified_at = verified_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "control": self.control,
            "status": self.status.value,
            "event_count": self.event_count,
            "sample_events": self.sample_events[:5],
            "message": self.message,
            "query_used": self.query_used,
            "verified_at": self.verified_at,
        }


class LoggingHealthResult(EvidenceResult):
    """Vendor-neutral structured logging-health result used by the UI."""

    def __init__(
        self,
        logging_enabled: bool,
        last_event_time: Optional[str],
        event_count_24h: int,
        event_count_7d: int,
        sourcetypes_active: Optional[List[str]] = None,
        indexes_active: Optional[List[str]] = None,
        message: str = "",
        query_used: str = "",
        verified_at: Optional[str] = None,
    ):
        super().__init__(
            control="Centralized Logging",
            status=EvidenceStatus.VERIFIED if logging_enabled else EvidenceStatus.NOT_VERIFIED,
            event_count=event_count_24h,
            sample_events=[],
            message=message,
            query_used=query_used,
            verified_at=verified_at,
        )
        self.logging_enabled = logging_enabled
        self.last_event_time = last_event_time
        self.event_count_24h = event_count_24h
        self.event_count_7d = event_count_7d
        self.sourcetypes_active = sourcetypes_active or []
        self.indexes_active = indexes_active or []

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "logging_enabled": self.logging_enabled,
                "last_event_time": self.last_event_time,
                "event_count_24h": self.event_count_24h,
                "event_count_7d": self.event_count_7d,
                "sourcetypes_active": self.sourcetypes_active,
                "indexes_active": self.indexes_active,
            }
        )
        return base
