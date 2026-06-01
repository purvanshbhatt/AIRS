"""Microsoft Telemetry Pydantic Schemas — Data contract for Microsoft Graph evidence normalization."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntuneDeviceTelemetry(BaseModel):
    """Normalized Intune device state."""
    device_id: str = Field(..., description="Unique Intune device UUID.")
    device_name: Optional[str] = Field(None, description="Device hostname/display name.")
    compliance_state: str = Field(..., description="Device compliance status (e.g., compliant, noncompliant).")
    bitlocker_status: str = Field(..., description="BitLocker encryption status (e.g., encrypted, not_encrypted).")
    os_version: str = Field(..., description="OS version string.")


class EntraUserTelemetry(BaseModel):
    """Normalized Entra ID user security state."""
    user_id: str = Field(..., description="Unique Entra user object UUID.")
    user_principal_name: str = Field(..., description="User principal name / email.")
    mfa_enforced: bool = Field(..., description="True if MFA is enforced for this user.")
    conditional_access_status: str = Field(..., description="Applied Conditional Access state.")


class DefenderAlertTelemetry(BaseModel):
    """Normalized Microsoft Defender alert details."""
    alert_id: str = Field(..., description="Unique Defender alert UUID.")
    title: str = Field(..., description="Short alert title or description.")
    severity: str = Field(..., description="Alert severity: critical, high, medium, low, informational.")
    status: str = Field(..., description="Alert status: new, in_progress, resolved.")
    device_id: Optional[str] = Field(None, description="ID of the affected device, if applicable.")


class TelemetryPayload(BaseModel):
    """Standardized top-level telemetry payload for the Microsoft Security Graph connector."""
    organization_id: str = Field(..., description="Tenant organization ID.")
    connector_id: str = Field(..., description="Telemetry connector UUID.")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp of when data was pulled.")
    intune_devices: List[IntuneDeviceTelemetry] = Field(default_factory=list, description="Intune managed devices telemetry.")
    entra_users: List[EntraUserTelemetry] = Field(default_factory=list, description="Entra ID user identity telemetry.")
    defender_alerts: List[DefenderAlertTelemetry] = Field(default_factory=list, description="Microsoft Defender alerts telemetry.")
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pre-computed summary statistics (e.g. compliance_rate, mfa_enforced_rate, active_high_severity_alerts)."
    )
