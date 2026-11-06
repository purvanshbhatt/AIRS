"""
Microsoft Graph Discovery Service.

Real organizations: devices are read from the org's registered ``microsoft``
connector via Microsoft Graph:

  - GET /v1.0/deviceManagement/managedDevices  -> HostAsset (HOST) per Intune device
  - GET /v1.0/security/alerts_v2?$top=50       -> recorded in result.detail (no rows)

A 403 is recorded as ``permission_missing`` for that endpoint; rows are never
invented. Token acquisition reuses ``MicrosoftConnector.authenticate`` (client
credentials flow); HTTP goes through an injectable httpx client factory so
tests can stub the network.

Demo organizations only (``is_demo_org``) get the synthetic Intune/Defender
inventory in ``_execute_demo_graph_discovery``.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.discovery import AssetType
from app.services.discovery.discovery import (
    DiscoveryStatus,
    SourceDiscoveryResult,
    TechnologyDiscoveryService,
    is_demo_org,
    run_coroutine_sync,
)

logger = logging.getLogger("airs.discovery.ms_graph")

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_MANAGED_DEVICES = "/deviceManagement/managedDevices"
GRAPH_SECURITY_ALERTS = "/security/alerts_v2"
MANAGED_DEVICE_FIELDS = (
    "id,deviceName,operatingSystem,osVersion,complianceState,isEncrypted,lastSyncDateTime"
)

# (headers) -> client with .get(url) returning an object with .status_code / .json() / .text
HttpClientFactory = Callable[[Dict[str, str]], Any]
# (credentials, config, connector_id) -> bearer token or None
TokenProvider = Callable[[Dict[str, Any], Dict[str, Any], str], Optional[str]]


def default_http_client_factory(headers: Dict[str, str]):
    import httpx
    return httpx.Client(headers=headers, timeout=30.0)


def default_token_provider(credentials: Dict[str, Any], config: Dict[str, Any], connector_id: str) -> Optional[str]:
    """Obtain a Graph token through the existing MicrosoftConnector client-credentials flow."""
    from app.connectors.microsoft import MicrosoftConnector

    impl = MicrosoftConnector(connector_id=connector_id, credentials=credentials, config=config)
    ok = run_coroutine_sync(impl.authenticate())
    return impl._token if ok else None


def _evidence_hash(*parts: Any) -> str:
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()


def fetch_managed_devices(client: Any, result: SourceDiscoveryResult, base_url: str = GRAPH_BASE_URL) -> List[Dict[str, Any]]:
    """Page through managedDevices. Records 403 as permission missing. Returns normalized devices."""
    devices: List[Dict[str, Any]] = []
    url: Optional[str] = f"{base_url}{GRAPH_MANAGED_DEVICES}?$select={MANAGED_DEVICE_FIELDS}&$top=100"
    pages = 0
    while url and pages < 100:
        pages += 1
        resp = client.get(url)
        status = getattr(resp, "status_code", 0)
        if status == 403:
            result.denied_apis.append(GRAPH_MANAGED_DEVICES)
            logger.warning("Graph managedDevices denied (403) for org %s: permission missing", result.detail.get("org_id"))
            return devices
        if status == 401:
            result.errors.append(f"{GRAPH_MANAGED_DEVICES}: 401 unauthorized")
            return devices
        if status != 200:
            result.errors.append(f"{GRAPH_MANAGED_DEVICES}: HTTP {status}")
            return devices
        try:
            payload = resp.json() or {}
        except Exception as exc:
            result.errors.append(f"{GRAPH_MANAGED_DEVICES}: invalid JSON ({exc})")
            return devices
        for d in payload.get("value") or []:
            if not d.get("id"):
                continue
            devices.append({
                "external_id": d["id"],
                "name": d.get("deviceName") or d["id"],
                "os": d.get("operatingSystem"),
                "os_version": d.get("osVersion"),
                "compliance_state": d.get("complianceState"),
                "is_encrypted": d.get("isEncrypted"),
                "last_sync": d.get("lastSyncDateTime"),
                "source": GRAPH_MANAGED_DEVICES,
            })
        url = payload.get("@odata.nextLink")
    return devices


def fetch_security_alerts(client: Any, result: SourceDiscoveryResult, base_url: str = GRAPH_BASE_URL) -> List[Dict[str, Any]]:
    """GET /security/alerts_v2?$top=50 if permitted. Alerts are recorded in result.detail only."""
    try:
        resp = client.get(f"{base_url}{GRAPH_SECURITY_ALERTS}?$top=50")
    except Exception as exc:
        result.errors.append(f"{GRAPH_SECURITY_ALERTS}: {exc}")
        return []
    status = getattr(resp, "status_code", 0)
    if status == 403:
        result.denied_apis.append(GRAPH_SECURITY_ALERTS)
        return []
    if status != 200:
        result.errors.append(f"{GRAPH_SECURITY_ALERTS}: HTTP {status}")
        return []
    try:
        alerts = (resp.json() or {}).get("value") or []
    except Exception:
        return []
    result.detail["security_alerts"] = len(alerts)
    return alerts


class GraphDiscoveryService:
    """Service to discover technology assets via Microsoft Graph."""

    def __init__(
        self,
        db: Session,
        org_id: str,
        http_client_factory: Optional[HttpClientFactory] = None,
        token_provider: Optional[TokenProvider] = None,
        is_demo: Optional[bool] = None,
    ):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)
        self._http_client_factory = http_client_factory or default_http_client_factory
        self._token_provider = token_provider or default_token_provider
        self._is_demo = is_demo
        self.last_result: Optional[SourceDiscoveryResult] = None

    def is_demo(self) -> bool:
        if self._is_demo is None:
            self._is_demo = is_demo_org(self.db, self.org_id)
        return self._is_demo

    # ------------------------------------------------------------------
    # Connector loading
    # ------------------------------------------------------------------

    def _load_microsoft_connectors(self) -> List[Dict[str, Any]]:
        from app.models.connector import ConnectorStatus
        from app.services.connector_manager import ConnectorManager

        manager = ConnectorManager(self.db, self.org_id)
        loaded: List[Dict[str, Any]] = []
        for connector in manager.list_connectors(connector_type="microsoft"):
            if connector.status == ConnectorStatus.inactive.value:
                continue
            credentials = manager._decrypt_credentials(connector.encrypted_credentials)
            cfg_raw = connector.config
            if isinstance(cfg_raw, str):
                try:
                    cfg = json.loads(cfg_raw) if cfg_raw else {}
                except json.JSONDecodeError:
                    cfg = {}
            else:
                cfg = cfg_raw or {}
            loaded.append({
                "id": connector.id,
                "display_name": connector.display_name or "Microsoft Graph",
                "credentials": credentials,
                "config": cfg,
            })
        return loaded

    # ------------------------------------------------------------------
    # Real discovery
    # ------------------------------------------------------------------

    def _persist_devices(
        self,
        inventory_id: str,
        devices: List[Dict[str, Any]],
        connector_name: str,
        result: SourceDiscoveryResult,
    ) -> int:
        created = 0
        for device in devices:
            os_string = f"{device.get('os') or ''} {device.get('os_version') or ''}".strip() or None
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=AssetType.HOST.value,
                hostname=device.get("name"),
                operating_system=os_string,
                ip_address=None,  # managedDevices does not expose a reliable IP
            )
            created += 1
            # The OS itself is the one product Intune attests to per device.
            if device.get("os"):
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=str(device["os"]).lower(),
                    vendor="Microsoft" if "windows" in str(device["os"]).lower() else None,
                    version=device.get("os_version"),
                    installation_source="microsoft_intune",
                )
                result.products_created += 1
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="ms_graph",
                    connector_name=connector_name,
                    raw_evidence_hash=_evidence_hash(
                        GRAPH_MANAGED_DEVICES, device["external_id"], device.get("os"), device.get("os_version"),
                        device.get("compliance_state"), device.get("is_encrypted"), device.get("last_sync"),
                    ),
                )
        return created

    def _execute_real_graph_discovery(self, inventory_id: str) -> SourceDiscoveryResult:
        result = SourceDiscoveryResult(source="ms_graph")
        result.detail["org_id"] = self.org_id
        connectors = self._load_microsoft_connectors()
        if not connectors:
            result.status = DiscoveryStatus.NOT_CONNECTED
            logger.info("Graph discovery skipped for org %s: no microsoft connector registered", self.org_id)
            return result

        for connector in connectors:
            result.connectors_used.append(connector["id"])
            try:
                token = self._token_provider(connector["credentials"], connector["config"], connector["id"])
            except Exception as exc:
                token = None
                result.errors.append(f"token[{connector['id']}]: {exc}")
            if not token:
                result.status = DiscoveryStatus.AUTH_FAILED
                result.errors.append(f"token[{connector['id']}]: authentication failed")
                continue

            client = self._http_client_factory({"Authorization": f"Bearer {token}"})
            try:
                devices = fetch_managed_devices(client, result)
                fetch_security_alerts(client, result)
            except Exception as exc:
                result.errors.append(f"graph[{connector['id']}]: {exc}")
                logger.warning("Graph discovery request failed for org %s: %s", self.org_id, exc)
                devices = []
            finally:
                close = getattr(client, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass

            result.assets_created += self._persist_devices(
                inventory_id, devices, connector["display_name"], result
            )

        if result.status != DiscoveryStatus.AUTH_FAILED:
            if GRAPH_MANAGED_DEVICES in result.denied_apis and not result.assets_created:
                result.status = DiscoveryStatus.PERMISSION_MISSING
            elif result.denied_apis or result.errors:
                result.status = DiscoveryStatus.PARTIAL
            else:
                result.status = DiscoveryStatus.OK
        return result

    # ------------------------------------------------------------------
    # Demo-only synthetic inventory
    # ------------------------------------------------------------------

    def _execute_demo_graph_discovery(self, inventory_id: str) -> int:
        """Synthetic Intune/Defender inventory. Reached ONLY when ``is_demo()`` is True."""
        devices = [
            {"id": "device-101", "deviceName": "desktop-sales-01", "operatingSystem": "Windows",
             "osVersion": "10.0.22631", "ipAddress": "192.168.1.50"},
            {"id": "device-102", "deviceName": "laptop-eng-04", "operatingSystem": "macOS",
             "osVersion": "14.2.1", "ipAddress": "192.168.1.65"},
        ]
        software_inventory = {
            "device-101": [
                {"name": "chrome", "vendor": "Google", "version": "121.0"},
                {"name": "windows-11-client", "vendor": "Microsoft", "version": "10.0.22631"},
            ],
            "device-102": [
                {"name": "firefox", "vendor": "Mozilla", "version": "122.0"},
                {"name": "node.js", "vendor": "Node.js Foundation", "version": "22"},
                {"name": "python", "vendor": "Python Software Foundation", "version": "3.11"},
            ],
        }

        assets_created = 0
        for device in devices:
            device_id = device["id"]
            os_string = f"{device.get('operatingSystem', '')} {device.get('osVersion', '')}".strip()
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=AssetType.HOST.value,
                hostname=device.get("deviceName"),
                operating_system=os_string,
                ip_address=device.get("ipAddress"),
            )
            assets_created += 1
            for sw in software_inventory.get(device_id, []):
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=sw["name"],
                    vendor=sw.get("vendor"),
                    version=sw.get("version"),
                    installation_source="microsoft_defender",
                )
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="ms_graph",
                    connector_name="Demo Microsoft Intune (synthetic)",
                    raw_evidence_hash=_evidence_hash("demo", device_id, sw["name"], sw.get("version")),
                )
        return assets_created

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def discover_from_graph(self, inventory_id: str) -> int:
        """Runs discovery against Microsoft Graph to populate inventory. Returns assets created."""
        if self.is_demo():
            count = self._execute_demo_graph_discovery(inventory_id)
            self.last_result = SourceDiscoveryResult(
                source="ms_graph", status=DiscoveryStatus.DEMO, assets_created=count
            )
            return count

        self.last_result = self._execute_real_graph_discovery(inventory_id)
        return self.last_result.assets_created
