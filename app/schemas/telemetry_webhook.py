"""
Telemetry Webhook Schemas — Pydantic V2 type-safe contracts for SIEM ingestion.

Defines the canonical input/output shapes for the
POST /api/v1/telemetry/webhook/event endpoint.

Architectural Invariants:
  - raw_telemetry_dump must not be empty (validated by field_validator).
  - organization_id is mandatory for multi-tenant isolation.
  - source_integration is a closed enum: only 'wazuh' or 'splunk'.
  - LLMs have zero involvement in schema validation or hash computation.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class SIEMEventWebhookPayload(BaseModel):
    """Inbound webhook payload from a Wazuh or Splunk SIEM integration.

    This is the canonical M2M contract for automated telemetry ingestion.
    The evidence_hash is computed server-side from raw_telemetry_dump —
    never trust a client-supplied hash without re-verification.
    """

    alert_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique alert/event ID from the source SIEM.",
        examples=["wazuh-2026-001234", "splunk-SID-7890"],
    )
    rule_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "ResilAI finding rule ID for direct control resolution "
            "(e.g. 'DC-001', 'IV-002'). Must match an active ControlRuleRegistry entry."
        ),
        examples=["DC-001", "IV-002", "TL-001"],
    )
    source_integration: Literal["wazuh", "splunk"] = Field(
        ...,
        description="Source SIEM integration. Must be 'wazuh' or 'splunk'.",
    )
    organization_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Tenant organization UUID. Used for multi-tenant idempotency isolation.",
    )
    raw_telemetry_dump: Dict[str, Any] = Field(
        ...,
        description=(
            "Raw telemetry event payload from the SIEM. "
            "Must not be empty. SHA-256 is computed from sorted keys of this dict."
        ),
    )

    @field_validator("raw_telemetry_dump")
    @classmethod
    def raw_telemetry_dump_must_not_be_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce non-empty telemetry payload.

        An empty dict provides no forensic evidence and would produce a
        trivially-predictable hash — both are security red flags.
        """
        if not v:
            raise ValueError(
                "raw_telemetry_dump must not be empty. "
                "A valid SIEM event payload is required for evidence hashing."
            )
        return v

    @field_validator("alert_id", "rule_id", "organization_id")
    @classmethod
    def strip_and_validate_strings(cls, v: str) -> str:
        """Strip whitespace and reject blank strings."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field must not be blank or whitespace-only.")
        return stripped


class WebhookIngestionResponse(BaseModel):
    """Structured response from the telemetry webhook ingestion endpoint.

    status values:
      - 'verified'       : Finding matched and provenance updated to SOC_VERIFIED.
      - 'already_exists' : Duplicate alert_id+org_id; idempotent no-op.
      - 'no_match'       : No ControlRuleRegistry entry found for the rule_id.
      - 'error'          : Unexpected server-side error.
    """

    status: str = Field(..., description="Processing outcome.")
    finding_id: Optional[str] = Field(None, description="Matched finding UUID.")
    finding_title: Optional[str] = Field(None, description="Human-readable finding title.")
    verification_status: Optional[str] = Field(
        None, description="New ProvenanceStatus after processing."
    )
    evidence_hash: Optional[str] = Field(
        None,
        description="SHA-256 hex digest (64 chars) of the raw_telemetry_dump.",
    )
    siem_alert_id: str = Field(..., description="Echo of the inbound alert_id.")
    organization_id: str = Field(..., description="Echo of the inbound organization_id.")
    message: str = Field("", description="Human-readable summary of the outcome.")
    processed_at: Optional[str] = Field(
        None, description="ISO-8601 UTC timestamp of when this event was processed."
    )
