"""
Direct discovery pollers.

Each poller turns one external inventory API into normalized
``SoftwareInventoryRecord`` rows. Network access is injectable so tests stub
it. Synthetic rows exist ONLY behind ``is_demo=True`` (demo tenants); a real
organization with no usable credentials gets an empty list and a status,
never invented rows. ``raw_evidence["source"]`` names the real API path.
"""
from __future__ import annotations

import abc
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.discovery.discovery import DiscoveryStatus, SourceDiscoveryResult

logger = logging.getLogger("airs.discovery.pollers")


class SoftwareInventoryRecord(BaseModel):
    """Normalized software inventory record returned by pollers."""
    software_name: str
    version: str
    component_type: str  # e.g., "language", "database", "server", "runtime"
    source: str          # e.g., "AWSConfig", "Kubernetes", "MicrosoftGraph"
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    host_id: Optional[str] = None
    raw_evidence: Dict[str, Any] = Field(default_factory=dict)


class DirectDiscoveryPoller(abc.ABC):
    """Abstract base class for direct technology discovery pollers."""

    SOURCE = "direct"

    def __init__(self, credentials: Dict[str, Any], is_demo: bool = False):
        """
        Initialize the poller.

        Args:
            credentials: A dictionary containing secrets/keys.
                         Must be isolated and not logged.
            is_demo: True only for demo tenants. Enables synthetic rows.
        """
        self._credentials = credentials or {}
        self._is_demo = bool(is_demo)
        self.result = SourceDiscoveryResult(source=self.SOURCE)

    @property
    def status(self) -> str:
        return self.result.status

    @abc.abstractmethod
    async def poll(self) -> List[SoftwareInventoryRecord]:
        """
        Poll the data source and return a list of discovered software inventory records.
        Returns raw evidence in a normalized, fully auditable format without LLM usage.
        """
        pass

    def _demo_records(self) -> List[SoftwareInventoryRecord]:
        """Synthetic rows for demo tenants. Subclasses override."""
        return []

    def _finish(self, records: List[SoftwareInventoryRecord]) -> List[SoftwareInventoryRecord]:
        r = self.result
        # NOT_CONNECTED is the dataclass default; callers that mean it return before _finish.
        if r.status in (DiscoveryStatus.AUTH_FAILED, DiscoveryStatus.NOT_IMPLEMENTED, DiscoveryStatus.ERROR):
            return records
        if r.denied_apis and not records:
            r.status = DiscoveryStatus.PERMISSION_MISSING
        elif r.denied_apis or r.errors:
            r.status = DiscoveryStatus.PARTIAL
        else:
            r.status = DiscoveryStatus.OK
        r.products_created = len(records)
        return records


class MicrosoftGraphPoller(DirectDiscoveryPoller):
    """Poller for Microsoft Graph managed device inventory (Intune).

    Credentials: tenant_id, client_id, client_secret (client credentials flow),
    or a pre-obtained ``access_token``.
    """

    SOURCE = "MicrosoftGraph"

    def __init__(
        self,
        credentials: Dict[str, Any],
        is_demo: bool = False,
        http_client_factory: Optional[Callable[[Dict[str, str]], Any]] = None,
        token_provider: Optional[Callable[[Dict[str, Any], Dict[str, Any], str], Optional[str]]] = None,
    ):
        super().__init__(credentials, is_demo=is_demo)
        self._http_client_factory = http_client_factory
        self._token_provider = token_provider

    async def poll(self) -> List[SoftwareInventoryRecord]:
        if self._is_demo:
            self.result.status = DiscoveryStatus.DEMO
            return self._demo_records()

        from app.services.discovery.graph_discovery import (
            GRAPH_MANAGED_DEVICES,
            default_http_client_factory,
            default_token_provider,
            fetch_managed_devices,
        )

        if not self._credentials:
            self.result.status = DiscoveryStatus.NOT_CONNECTED
            return []

        token = self._credentials.get("access_token")
        if not token:
            provider = self._token_provider or default_token_provider
            try:
                token = provider(self._credentials, {}, "direct-poller")
            except Exception as exc:
                self.result.errors.append(f"token: {exc}")
                token = None
        if not token:
            self.result.status = DiscoveryStatus.AUTH_FAILED
            return []

        factory = self._http_client_factory or default_http_client_factory
        client = factory({"Authorization": f"Bearer {token}"})
        try:
            devices = fetch_managed_devices(client, self.result)
        except Exception as exc:
            self.result.errors.append(f"{GRAPH_MANAGED_DEVICES}: {exc}")
            devices = []
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

        records = [
            SoftwareInventoryRecord(
                software_name=str(d.get("os") or "unknown"),
                version=str(d.get("os_version") or "unknown"),
                component_type="operating_system",
                source=self.SOURCE,
                host_id=d["external_id"],
                raw_evidence={
                    "source": GRAPH_MANAGED_DEVICES,
                    "endpoint": GRAPH_MANAGED_DEVICES,
                    "deviceName": d.get("name"),
                    "complianceState": d.get("compliance_state"),
                    "isEncrypted": d.get("is_encrypted"),
                    "lastSyncDateTime": d.get("last_sync"),
                },
            )
            for d in devices
        ]
        return self._finish(records)

    def _demo_records(self) -> List[SoftwareInventoryRecord]:
        return [
            SoftwareInventoryRecord(
                software_name="NodeJS", version="18", component_type="runtime",
                source=self.SOURCE, host_id="vm-graph-01",
                raw_evidence={"source": "demo", "endpoint": "/deviceManagement/managedDevices", "mock": True},
            ),
            SoftwareInventoryRecord(
                software_name="Nginx", version="1.20", component_type="server",
                source=self.SOURCE, host_id="vm-graph-02",
                raw_evidence={"source": "demo", "endpoint": "/deviceManagement/managedDevices", "mock": True},
            ),
        ]


class AWSConfigPoller(DirectDiscoveryPoller):
    """Poller for AWS managed database inventory (rds:DescribeDBInstances).

    Credentials: aws_access_key_id / aws_secret_access_key / aws_region,
    optional role_arn + external_id (see ``build_boto3_session``).
    """

    SOURCE = "AWSConfig"

    def __init__(
        self,
        credentials: Dict[str, Any],
        is_demo: bool = False,
        session_factory: Optional[Callable[[Dict[str, Any], Dict[str, Any], str], Any]] = None,
    ):
        super().__init__(credentials, is_demo=is_demo)
        self._session_factory = session_factory

    async def poll(self) -> List[SoftwareInventoryRecord]:
        if self._is_demo:
            self.result.status = DiscoveryStatus.DEMO
            return self._demo_records()

        from app.services.discovery.aws_discovery import (
            API_RDS_DESCRIBE_DB_INSTANCES,
            _is_access_denied,
            _paginate,
            build_boto3_session,
        )

        factory = self._session_factory or build_boto3_session
        try:
            session = factory(self._credentials, {}, "direct-poller")
        except ImportError:
            self.result.status = DiscoveryStatus.ERROR
            self.result.errors.append("boto3 not installed")
            return []
        except Exception as exc:
            self.result.status = DiscoveryStatus.AUTH_FAILED
            self.result.errors.append(f"session: {exc}")
            return []

        records: List[SoftwareInventoryRecord] = []
        try:
            rds = session.client("rds")
            for dbi in _paginate(rds.describe_db_instances, "DBInstances"):
                identifier = dbi.get("DBInstanceIdentifier")
                if not identifier:
                    continue
                records.append(
                    SoftwareInventoryRecord(
                        software_name=str(dbi.get("Engine") or "unknown"),
                        version=str(dbi.get("EngineVersion") or "unknown"),
                        component_type="database",
                        source=self.SOURCE,
                        host_id=identifier,
                        raw_evidence={
                            "source": API_RDS_DESCRIBE_DB_INSTANCES,
                            "resourceType": "AWS::RDS::DBInstance",
                            "StorageEncrypted": bool(dbi.get("StorageEncrypted")),
                            "PubliclyAccessible": bool(dbi.get("PubliclyAccessible")),
                            "MultiAZ": bool(dbi.get("MultiAZ")),
                        },
                    )
                )
        except Exception as exc:
            if _is_access_denied(exc):
                self.result.denied_apis.append(API_RDS_DESCRIBE_DB_INSTANCES)
            else:
                self.result.errors.append(f"{API_RDS_DESCRIBE_DB_INSTANCES}: {exc}")
        return self._finish(records)

    def _demo_records(self) -> List[SoftwareInventoryRecord]:
        return [
            SoftwareInventoryRecord(
                software_name="PostgreSQL", version="11", component_type="database",
                source=self.SOURCE, host_id="rds-postgres-11",
                raw_evidence={"source": "demo", "resourceType": "AWS::RDS::DBInstance", "mock": True},
            )
        ]


class KubernetesInventoryPoller(DirectDiscoveryPoller):
    """Poller for Kubernetes cluster workloads and images.

    No live Kubernetes integration exists yet: real tenants get an empty list
    with status ``not_implemented``; demo tenants get synthetic rows.
    """

    SOURCE = "Kubernetes"

    async def poll(self) -> List[SoftwareInventoryRecord]:
        if self._is_demo:
            self.result.status = DiscoveryStatus.DEMO
            return self._demo_records()
        self.result.status = DiscoveryStatus.NOT_IMPLEMENTED
        return []

    def _demo_records(self) -> List[SoftwareInventoryRecord]:
        return [
            SoftwareInventoryRecord(
                software_name="Python", version="3.8.1", component_type="language",
                source=self.SOURCE, host_id="pod-python-backend",
                raw_evidence={"source": "demo", "apiVersion": "v1", "kind": "Pod", "mock": True},
            )
        ]
