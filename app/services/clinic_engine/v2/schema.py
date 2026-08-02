"""
Clinic Engine V2 — Core Schema

Question → Capability → Evidence → Evaluation → Moment → Action → Automation

All data types for the question-driven clinic engine.
No business logic. Pure contracts.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Raw Events
# ---------------------------------------------------------------------------

class RawEvent(BaseModel):
    """Phase 7: Raw Events from Connectors before Evidence Providers normalize them."""
    event_type: str
    source_system: str
    source_event_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None
    organization_id: str

# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class ConnectorCapability(str, Enum):
    """Phase 1: Connector Capability Framework. Explicit declarations."""
    USERS = "users"
    DEVICES = "devices"
    IDENTITY = "identity"
    EMAIL = "email"
    BACKUPS = "backups"
    ENDPOINT_PROTECTION = "endpoint_protection"
    NETWORK = "network"
    CLOUD_ASSETS = "cloud_assets"
    PATCH_STATUS = "patch_status"
    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    LOGS = "logs"

class EvidenceKind(str, Enum):
    """What type of evidence is this? Vendor-agnostic."""
    USER_ACCOUNT_STATUS = "user_account_status"
    BACKUP_STATUS = "backup_status"
    DEVICE_SECURITY_STATUS = "device_security_status"
    SECURITY_ALERT = "security_alert"
    VULNERABILITY_SCAN = "vulnerability_scan"
    IDENTITY_CONFIGURATION = "identity_configuration"
    NETWORK_CONFIGURATION = "network_configuration"


class Evidence(BaseModel):
    """A single piece of vendor-agnostic evidence."""
    id: str = Field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()) # Will be overwritten by DB or explicit setting
    kind: EvidenceKind
    source_connector: str       # e.g. "microsoft", "wazuh", "google_workspace"
    source_id: str              # Unique ID from the source system
    organization_id: str
    tenant_id: Optional[str] = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: int = 3600             # Time to live in seconds
    version: str = "1.0"
    payload: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0     # 0.0–1.0

    @property
    def is_expired(self) -> bool:
        """Phase 4: Expired evidence must never generate moments."""
        age = (datetime.now(timezone.utc) - self.collected_at).total_seconds()
        return age > self.ttl

    @property
    def payload_hash(self) -> str:
        canonical = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class Verdict(str, Enum):
    SAFE = "safe"
    CONCERN = "concern"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class EvaluationResult(BaseModel):
    """Output of a capability's deterministic evaluation."""
    verdict: Verdict
    confidence: float = 1.0
    evidence_used: List[str] = Field(default_factory=list, exclude=True)  # Evidence source_ids
    details: Dict[str, Any] = Field(default_factory=dict, exclude=True)


# ---------------------------------------------------------------------------
# Translation & Actions
# ---------------------------------------------------------------------------

class MomentTranslation(BaseModel):
    """Plain-English rendering of an evaluation result."""
    what_happened: str
    why_care: str
    ignore_impact: str


class ActionIntent(BaseModel):
    """What the user can do. Describes intent, not execution."""
    action_id: str
    label: str                  # "Suspend Account", "Email IT Provider"
    can_automate: bool = False
    automation_type: Optional[str] = Field(default=None, exclude=True)   # e.g. "m365_disable_user"
    automation_params: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    estimated_minutes: int = 5


# ---------------------------------------------------------------------------
# Clinic Moment (the final output)
# ---------------------------------------------------------------------------

class ClinicMoment(BaseModel):
    """The complete output: what happened, why, and what to do."""
    id: str
    question_id: str
    capability_id: str
    verdict: Verdict
    confidence: float = Field(default=1.0, exclude=True)
    translation: MomentTranslation
    actions: List[ActionIntent] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list, exclude=True)
    severity: str = "medium"    # "high", "medium", "low"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
