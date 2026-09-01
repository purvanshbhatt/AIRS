"""
EvidenceAdapter base class — vendor-agnostic telemetry ingestion.

Per ADR-009, every third-party evidence source (Splunk, Wazuh, AWS,
Microsoft Sentinel, SentinelOne, CrowdStrike, Okta, etc.) implements
this ABC and registers via ``app.services.evidence.registry.EvidenceRegistry``.
The Verification Engine never imports vendor-specific modules.

Contract:
  - ``connector_name`` (str): stable identifier used by the registry.
  - ``fetch_evidence()`` (coroutine or sync): retrieves fresh evidence
    from the third-party. Returns a list of ``EvidenceRecord``.
  - ``normalize()``: converts vendor-specific records into the canonical
    ``EvidenceRecord`` shape (already used by
    ``app.models.verification.ControlEvidence``).
  - ``health()`` (coroutine): returns ``AdapterHealth`` so the
    Evidence Confidence engine can compute its per-adapter score.

This module never imports AI/LLM modules (ADR-007). It also MUST NOT
import vendor-specific modules — those live in ``adapters/``.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceRecord:
    """Vendor-neutral canonical evidence shape.

    Onward consumers (Verification Engine, Score Audit) only ever see
    ``EvidenceRecord`` instances — never vendor-specific payloads.
    """

    connector_name: str
    external_id: str
    control_id: Optional[str] = None
    finding_kind: str = "telemetry"
    raw_payload: Optional[Dict[str, Any]] = None
    observed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connector_name": self.connector_name,
            "external_id": self.external_id,
            "control_id": self.control_id,
            "finding_kind": self.finding_kind,
            "observed_at": (
                self.observed_at.isoformat()
                if self.observed_at is not None else None
            ),
            "metadata": self.metadata,
            "raw_payload": self.raw_payload,
        }


@dataclass
class AdapterHealth:
    """Health snapshot used by Evidence Confidence (ADR-010)."""

    healthy: bool
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    detail: Optional[str] = None

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "last_success_at": (
                self.last_success_at.isoformat()
                if self.last_success_at else None
            ),
            "last_failure_at": (
                self.last_failure_at.isoformat()
                if self.last_failure_at else None
            ),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "detail": self.detail,
        }


class EvidenceAdapter(abc.ABC):
    """Base class for vendor-agnostic telemetry adapters.

    Subclasses MUST override all three abstract methods plus
    ``connector_name``.
    """

    @property
    @abc.abstractmethod
    def connector_name(self) -> str:
        """Stable identifier (e.g. 'splunk', 'wazuh', 'aws_ssminventory')."""

    @abc.abstractmethod
    async def fetch_evidence(self, *, since: Optional[datetime] = None) -> List[EvidenceRecord]:
        """Fetch evidence from the underlying vendor.

        Implementations must return canonical ``EvidenceRecord`` objects
        — vendor-specific payload decoding happens inside this method,
        but the result must already be canonical.
        """

    @abc.abstractmethod
    def normalize(self, vendor_payload: Any) -> List[EvidenceRecord]:
        """Translate vendor-specific payloads to canonical records.

        Used by tests and offline pipelines.
        """

    @abc.abstractmethod
    async def health(self) -> AdapterHealth:
        """Report live adapter health for the Evidence Confidence engine."""


class WebhookEvidenceAdapter(EvidenceAdapter):
    """Conceptual interface for ingesting generic JSON webhooks.
    
    Allows the pipeline to ingest arbitrary JSON webhooks (e.g., from custom
    internal tools or unsupported vendors) and normalize them into 
    EvidenceRecord without requiring a dedicated direct connector.
    """

    @property
    @abc.abstractmethod
    def expected_schema(self) -> Dict[str, Any]:
        """JSON Schema definition of the expected webhook payload."""

    @abc.abstractmethod
    async def process_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> List[EvidenceRecord]:
        """Validate and normalize an incoming webhook payload into EvidenceRecords."""


class ManualUploadAdapter(EvidenceAdapter):
    """Conceptual interface for manual evidence uploads.
    
    Supports the ingestion of static evidence files (e.g., PDF audit reports,
    CSV exports) uploaded by users when automated API telemetry is unavailable.
    """

    @property
    @abc.abstractmethod
    def supported_mime_types(self) -> List[str]:
        """List of MIME types this adapter can process (e.g. 'application/pdf', 'text/csv')."""

    @abc.abstractmethod
    async def process_upload(self, file_content: bytes, filename: str, mime_type: str, uploader_id: str) -> List[EvidenceRecord]:
        """Process an uploaded file and extract canonical EvidenceRecords."""
