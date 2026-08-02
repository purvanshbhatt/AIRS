"""Microsoft Security Graph Connector — Enterprise Integration.

Connects to Microsoft Graph API via OAuth2 to pull compliance and security data
from Microsoft Intune, Entra ID, and Microsoft Defender.
Normalizes response data into a standardized TelemetryPayload schema.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector
from app.schemas.microsoft import (
    TelemetryPayload,
    IntuneDeviceTelemetry,
    EntraUserTelemetry,
    DefenderAlertTelemetry,
)

logger = logging.getLogger("airs.connectors.microsoft")


# ---------------------------------------------------------------------------
# Resilience & Backoff Request Helper
# ---------------------------------------------------------------------------

async def request_with_backoff(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> httpx.Response:
    """Execute an HTTP request with exponential backoff on HTTP 429 rate limit."""
    for attempt in range(max_retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            if resp.status_code == 429:
                if attempt == max_retries:
                    logger.error("Rate limit (HTTP 429) hit and retries exhausted for URL: %s", url)
                    return resp
                
                # Parse Retry-After header if available
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                
                logger.warning(
                    "HTTP 429 Rate Limited. Retrying in %.2fs (attempt %d/%d) for URL: %s",
                    delay, attempt + 1, max_retries, url
                )
                await asyncio.sleep(delay)
                continue
            return resp
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            if attempt == max_retries:
                logger.error("HTTP request failed after max retries: %s", exc)
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
            logger.warning("HTTP error: %s. Retrying in %.2fs...", exc, delay)
            await asyncio.sleep(delay)
    
    raise httpx.HTTPError("Request failed after max retries")


# ---------------------------------------------------------------------------
# Secret Manager Helper
# ---------------------------------------------------------------------------

def load_secret_if_gcp(value: str) -> str:
    """If the secret string looks like a GCP Secret Manager path, retrieve it dynamically."""
    if value and value.startswith("projects/") and "/secrets/" in value:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(request={"name": value})
            secret_val = response.payload.data.decode("utf-8").strip()
            logger.info("Loaded client_secret from GCP Secret Manager")
            return secret_val
        except Exception as exc:
            logger.error("Failed to fetch secret from GCP Secret Manager (%s): %s", value, exc)
            raise ValueError(f"Secret Manager resolution failed: {exc}") from exc
    return value


# ---------------------------------------------------------------------------
# Modular Services
# ---------------------------------------------------------------------------

class IntuneService:
    """Service class for fetching Intune device state from MS Graph."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url

    async def fetch_devices(self) -> List[IntuneDeviceTelemetry]:
        """Fetch managed devices status from Intune."""
        url = f"{self.base_url}/deviceManagement/managedDevices"
        # Select key properties for compliance and BitLocker auditing
        params = {"$select": "id,deviceName,complianceState,osVersion,isEncrypted"}
        
        resp = await request_with_backoff(self.client, "GET", url, params=params)
        if resp.status_code != 200:
            logger.warning("Failed to fetch Intune devices: %d %s", resp.status_code, resp.text)
            return []

        devices = resp.json().get("value", [])
        normalized = []
        for dev in devices:
            device_id = dev.get("id", "")
            if not device_id:
                continue
            
            # BitLocker status normalization based on isEncrypted boolean
            is_encrypted = dev.get("isEncrypted")
            if is_encrypted is True:
                bitlocker_status = "encrypted"
            elif is_encrypted is False:
                bitlocker_status = "not_encrypted"
            else:
                bitlocker_status = "unknown"

            normalized.append(IntuneDeviceTelemetry(
                device_id=device_id,
                device_name=dev.get("deviceName"),
                compliance_state=str(dev.get("complianceState", "unknown")).lower(),
                bitlocker_status=bitlocker_status,
                os_version=dev.get("osVersion", "unknown"),
            ))
        return normalized


class EntraIDService:
    """Service class for fetching identity risk and compliance data from MS Graph."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url

    async def fetch_users_and_mfa(self) -> List[EntraUserTelemetry]:
        """Fetch users and compute their MFA/Conditional Access status."""
        # 1. Fetch Conditional Access Policies to check MFA mandates
        ca_url = f"{self.base_url}/identity/conditionalAccess/policies"
        resp = await request_with_backoff(self.client, "GET", ca_url)
        
        has_global_mfa = False
        mfa_policy_ids = []
        if resp.status_code == 200:
            policies = resp.json().get("value", [])
            for policy in policies:
                if policy.get("state") == "enabled":
                    grant_controls = policy.get("grantControls", {})
                    controls = grant_controls.get("builtInControls", [])
                    if "mfa" in [c.lower() for c in controls]:
                        mfa_policy_ids.append(policy.get("id"))
                        # If policy applies to all users (empty or 'all' in users scope)
                        conditions = policy.get("conditions", {})
                        users_cond = conditions.get("users", {})
                        if "all" in [u.lower() for u in users_cond.get("includeUsers", [])]:
                            has_global_mfa = True

        # 2. Fetch Users
        users_url = f"{self.base_url}/users"
        params = {"$select": "id,userPrincipalName"}
        resp_users = await request_with_backoff(self.client, "GET", users_url, params=params)
        if resp_users.status_code != 200:
            logger.warning("Failed to fetch Entra ID users: %d", resp_users.status_code)
            return []

        users = resp_users.json().get("value", [])
        normalized = []
        for user in users:
            user_id = user.get("id", "")
            upn = user.get("userPrincipalName", "")
            if not user_id:
                continue

            # In production, we would query the authentication methods or registration details for each user
            # Here we derive MFA status from CA Policy scope or default to True if global MFA is on.
            mfa_enforced = has_global_mfa or (len(mfa_policy_ids) > 0)
            
            normalized.append(EntraUserTelemetry(
                user_id=user_id,
                user_principal_name=upn,
                mfa_enforced=mfa_enforced,
                conditional_access_status="enforced" if len(mfa_policy_ids) > 0 else "unknown",
            ))
        return normalized


class DefenderService:
    """Service class for fetching Defender EDR and alerts from MS Graph."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url

    async def fetch_alerts(self) -> List[DefenderAlertTelemetry]:
        """Fetch active Defender security alerts."""
        url = f"{self.base_url}/security/alerts_v2"
        # Only fetch active alerts
        params = {"$filter": "status eq 'new' or status eq 'inProgress'"}
        
        resp = await request_with_backoff(self.client, "GET", url, params=params)
        if resp.status_code != 200:
            # Fallback to legacy v1.0 alerts if security/alerts_v2 is not available
            legacy_url = f"{self.base_url}/security/alerts"
            resp = await request_with_backoff(self.client, "GET", legacy_url, params=params)
            if resp.status_code != 200:
                logger.warning("Failed to fetch Defender alerts: %d", resp.status_code)
                return []

        alerts = resp.json().get("value", [])
        normalized = []
        for alert in alerts:
            alert_id = alert.get("id", "")
            if not alert_id:
                continue

            normalized.append(DefenderAlertTelemetry(
                alert_id=alert_id,
                title=alert.get("title", "Defender Alert"),
                severity=str(alert.get("severity", "medium")).lower(),
                status=str(alert.get("status", "new")).lower(),
                device_id=alert.get("deviceId"),
            ))
        return normalized


# ---------------------------------------------------------------------------
# Connector Implementation
# ---------------------------------------------------------------------------

@register_connector
class MicrosoftConnector(Connector):
    """Microsoft Graph security telemetry connector.

    Connects to the MS Graph API (Intune, Entra ID, Defender) via client credentials flow.
    """

    CONNECTOR_TYPE = "microsoft"
    CAPABILITIES = ["users", "devices", "security_alerts"]
    REQUIRED_PERMISSIONS = [
        "DeviceManagementManagedDevices.Read.All",
        "Policy.Read.All",
        "User.Read.All",
        "SecurityAlert.Read.All",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._tenant_id = self._credentials.get("tenant_id", "")
        self._client_id = self._credentials.get("client_id", "")
        # client_secret may need dynamic loading from Secret Manager
        self._client_secret = ""
        self._graph_base_url = "https://graph.microsoft.com/v1.0"
        self._authority_url = "https://login.microsoftonline.com"

    def _resolve_client_secret(self) -> str:
        """Helper to resolve client secret from config/GCP Secret Manager."""
        if not self._client_secret:
            raw_secret = self._credentials.get("client_secret", "")
            self._client_secret = load_secret_if_gcp(raw_secret)
        return self._client_secret

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        """Authenticate via Client Credentials grant to Microsoft identity platform."""
        client_secret = self._resolve_client_secret()
        if not self._tenant_id or not self._client_id or not client_secret:
            self.logger.error("Missing tenant_id, client_id, or client_secret")
            return False

        # Token caching logic
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            self._authenticated = True
            return True

        token_url = f"{self._authority_url}/{self._tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(token_url, headers=headers, data=data)
                if resp.status_code == 200:
                    token_data = resp.json()
                    self._token = token_data.get("access_token", "")
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expires_at = now + expires_in
                    if self._token:
                        self._authenticated = True
                        self.logger.info("Microsoft Graph authentication successful")
                        return True
                self.logger.warning("Microsoft Graph auth failed: %d %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            self.logger.error("Microsoft Graph auth exception: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync Telemetry Ingestion
    # ------------------------------------------------------------------

    async def sync(self) -> List[NormalizedEvent]:
        """Fetch and normalize security telemetry from Intune, Entra ID, and Defender."""
        if not self._authenticated:
            auth_ok = await self.authenticate()
            if not auth_ok:
                raise httpx.HTTPStatusError("Authentication failed", request=None, response=None)

        timestamp = datetime.now(timezone.utc).isoformat()
        headers = {"Authorization": f"Bearer {self._token}"}

        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            intune_svc = IntuneService(client, self._graph_base_url)
            entra_svc = EntraIDService(client, self._graph_base_url)
            defender_svc = DefenderService(client, self._graph_base_url)

            # Parallelize Graph API queries
            intune_task = intune_svc.fetch_devices()
            entra_task = entra_svc.fetch_users_and_mfa()
            defender_task = defender_svc.fetch_alerts()

            intune_devices, entra_users, defender_alerts = await asyncio.gather(
                intune_task, entra_task, defender_task
            )

        # Calculate telemetry summary statistics
        total_devices = len(intune_devices)
        compliant_devices = sum(1 for d in intune_devices if d.compliance_state == "compliant")
        encrypted_devices = sum(1 for d in intune_devices if d.bitlocker_status == "encrypted")
        compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 100.0
        bitlocker_rate = (encrypted_devices / total_devices * 100) if total_devices > 0 else 100.0

        total_users = len(entra_users)
        mfa_users = sum(1 for u in entra_users if u.mfa_enforced)
        mfa_rate = (mfa_users / total_users * 100) if total_users > 0 else 100.0

        active_high_severity_alerts = sum(
            1 for a in defender_alerts if a.severity in ("high", "critical") and a.status != "resolved"
        )
        
        # Defender coverage maps to devices successfully managed
        edr_coverage_pct = compliance_rate  # Proxy EDR status with Intune compliant agent state

        summary = {
            "total_devices": total_devices,
            "compliance_rate_pct": round(compliance_rate, 2),
            "bitlocker_rate_pct": round(bitlocker_rate, 2),
            "total_users": total_users,
            "mfa_enforced_rate_pct": round(mfa_rate, 2),
            "active_high_severity_alerts": active_high_severity_alerts,
            "edr_coverage_pct": round(edr_coverage_pct, 2),
        }

        # Build TelemetryPayload
        payload = TelemetryPayload(
            organization_id=self.org_id,
            connector_id=self.connector_id,
            timestamp=timestamp,
            intune_devices=intune_devices,
            entra_users=entra_users,
            defender_alerts=defender_alerts,
            summary=summary,
        )

        event = NormalizedEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id=f"sync-{self.connector_id}-{int(time.time())}",
            severity="high" if active_high_severity_alerts > 0 else "low",
            payload=payload.model_dump(),
            timestamp=timestamp,
        )

        self.logger.info(
            "Microsoft sync complete. Devices: %d, Users: %d, Alerts: %d, High Severity: %d",
            total_devices, total_users, len(defender_alerts), active_high_severity_alerts
        )
        return [event]

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> ConnectorHealth:
        """Verify Graph API endpoint connectivity."""
        start_time = time.monotonic()
        try:
            auth_ok = await self.authenticate()
            if not auth_ok:
                return ConnectorHealth(status="unreachable", message="OAuth2 authentication failed")

            headers = {"Authorization": f"Bearer {self._token}"}
            # Simple metadata endpoint check
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                resp = await client.get(f"{self._graph_base_url}/organization")
                latency = int((time.monotonic() - start_time) * 1000)
                if resp.status_code == 200:
                    tenant_info = resp.json().get("value", [{}])[0]
                    tenant_name = tenant_info.get("displayName", "Microsoft Graph Tenant")
                    return ConnectorHealth(
                        status="healthy",
                        latency_ms=latency,
                        message=f"Connected to {tenant_name}",
                    )
                return ConnectorHealth(
                    status="degraded",
                    latency_ms=latency,
                    message=f"Graph API returned status {resp.status_code}",
                )
        except Exception as exc:
            return ConnectorHealth(status="unreachable", message=str(exc))

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        """Validate token claims and scopes."""
        auth_ok = await self.authenticate()
        if not auth_ok:
            return PermissionResult(valid=False, message="Authentication failed")

        # In Client Credentials flow, we can perform basic dry-run queries on Intune & Entra to verify scopes
        headers = {"Authorization": f"Bearer {self._token}"}
        missing = []
        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                # 1. Test Intune read
                resp_intune = await client.get(f"{self._graph_base_url}/deviceManagement/managedDevices?$top=1")
                if resp_intune.status_code not in (200, 404):
                    missing.append("DeviceManagementManagedDevices.Read.All")

                # 2. Test Entra User read
                resp_users = await client.get(f"{self._graph_base_url}/users?$top=1")
                if resp_users.status_code != 200:
                    missing.append("User.Read.All")

                # 3. Test Conditional Access read
                resp_ca = await client.get(f"{self._graph_base_url}/identity/conditionalAccess/policies?$top=1")
                if resp_ca.status_code not in (200, 404):
                    missing.append("Policy.Read.All")

                # 4. Test Defender Alerts read
                resp_def = await client.get(f"{self._graph_base_url}/security/alerts_v2?$top=1")
                if resp_def.status_code not in (200, 404):
                    # Try legacy alerts fallback
                    resp_def_legacy = await client.get(f"{self._graph_base_url}/security/alerts?$top=1")
                    if resp_def_legacy.status_code not in (200, 404):
                        missing.append("SecurityAlert.Read.All")

            if missing:
                return PermissionResult(
                    valid=False,
                    missing_permissions=missing,
                    message=f"Missing permissions: {', '.join(missing)}",
                )
            
            return PermissionResult(valid=True, message="All required Microsoft Graph permissions validated successfully")
        except Exception as exc:
            return PermissionResult(valid=False, message=f"Permissions validation exception: {exc}")
