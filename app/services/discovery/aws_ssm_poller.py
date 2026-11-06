"""
AWS Systems Manager software inventory poller.

ssm:DescribeInstanceInformation lists managed nodes; ssm:ListInventoryEntries
(AWS:Application) lists the software on each. AccessDenied is recorded per
API in ``poller.result.denied_apis``. There is NO synthetic fallback for real
tenants: missing credentials or errors yield an empty list and a status.
Synthetic rows exist only behind ``is_demo=True``.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from app.services.discovery.discovery import DiscoveryStatus
from .direct_connectors import DirectDiscoveryPoller, SoftwareInventoryRecord

logger = logging.getLogger("airs.discovery.aws_ssm")


class AWSConfigPoller(DirectDiscoveryPoller):
    """Poller for AWS Systems Manager Inventory (SSM)."""

    SOURCE = "AWS_SSM"

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
            API_SSM_DESCRIBE_INSTANCE_INFORMATION,
            API_SSM_LIST_INVENTORY_ENTRIES,
            _is_access_denied,
            _paginate,
            build_boto3_session,
        )

        logger.info("Polling AWS SSM Inventory...")
        factory = self._session_factory or build_boto3_session
        try:
            session = factory(self._credentials, {}, "ssm-poller")
            ssm = session.client("ssm")
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
            infos = _paginate(ssm.describe_instance_information, "InstanceInformationList")
        except Exception as exc:
            if _is_access_denied(exc):
                self.result.denied_apis.append(API_SSM_DESCRIBE_INSTANCE_INFORMATION)
            else:
                self.result.status = DiscoveryStatus.ERROR
                self.result.errors.append(f"{API_SSM_DESCRIBE_INSTANCE_INFORMATION}: {exc}")
            return self._finish(records)

        for info in infos:
            instance_id = info.get("InstanceId")
            if not instance_id:
                continue
            try:
                entries = _paginate(
                    ssm.list_inventory_entries, "Entries",
                    InstanceId=instance_id, TypeName="AWS:Application",
                )
            except Exception as exc:
                if _is_access_denied(exc):
                    if API_SSM_LIST_INVENTORY_ENTRIES not in self.result.denied_apis:
                        self.result.denied_apis.append(API_SSM_LIST_INVENTORY_ENTRIES)
                    break
                self.result.errors.append(f"{API_SSM_LIST_INVENTORY_ENTRIES}[{instance_id}]: {exc}")
                continue
            for entry in entries:
                name = entry.get("Name")
                if not name:
                    continue
                records.append(
                    SoftwareInventoryRecord(
                        software_name=str(name),
                        version=str(entry.get("Version") or "unknown"),
                        component_type="application",
                        source=self.SOURCE,
                        host_id=instance_id,
                        raw_evidence={
                            "source": API_SSM_LIST_INVENTORY_ENTRIES,
                            "ApplicationName": name,
                            "ApplicationVersion": entry.get("Version"),
                            "Publisher": entry.get("Publisher"),
                            "PlatformName": info.get("PlatformName"),
                        },
                    )
                )
        return self._finish(records)

    def _demo_records(self) -> List[SoftwareInventoryRecord]:
        return [
            SoftwareInventoryRecord(
                software_name="Python", version="3.8", component_type="language",
                source=self.SOURCE, host_id="i-0abcd1234efgh5678",
                raw_evidence={"source": "demo", "ApplicationName": "Python", "ApplicationVersion": "3.8", "mock": True},
            ),
            SoftwareInventoryRecord(
                software_name="PostgreSQL", version="11", component_type="database",
                source=self.SOURCE, host_id="i-09876gfedcba4321",
                raw_evidence={"source": "demo", "ApplicationName": "PostgreSQL", "ApplicationVersion": "11", "mock": True},
            ),
        ]
