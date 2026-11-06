"""
AWS Discovery Service.

Real organizations: inventory is read from the org's registered AWS
connectors (``aws`` / ``aws_security_hub``) via boto3:

  - ec2:DescribeInstances            -> HostAsset (CLOUD_SERVICE, cloud_provider=AWS)
  - rds:DescribeDBInstances          -> HostAsset + InstalledProduct (engine/version)
  - ssm:DescribeInstanceInformation  -> which EC2 hosts have an SSM agent
  - ssm:ListInventoryEntries         -> InstalledProduct rows (AWS:Application)

AccessDenied on any single API is swallowed and recorded in
``SourceDiscoveryResult.denied_apis``; the other APIs still run.

Demo organizations only (``is_demo_org``) get the synthetic inventory in
``_execute_demo_aws_discovery``. A real org with no AWS connector gets zero
rows and status ``not_connected`` -- never invented resources.
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
)

logger = logging.getLogger("airs.discovery.aws")

AWS_CONNECTOR_TYPES = ("aws", "aws_security_hub")

API_EC2_DESCRIBE_INSTANCES = "ec2:DescribeInstances"
API_RDS_DESCRIBE_DB_INSTANCES = "rds:DescribeDBInstances"
API_SSM_DESCRIBE_INSTANCE_INFORMATION = "ssm:DescribeInstanceInformation"
API_SSM_LIST_INVENTORY_ENTRIES = "ssm:ListInventoryEntries"

_ACCESS_DENIED_CODES = {
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedOperation",
    "UnauthorizedException",
    "InvalidInstanceId",  # SSM returns this when the instance is not an SSM managed node
}

# Type of the injectable boto3 session factory: (credentials, config, connector_id) -> session
SessionFactory = Callable[[Dict[str, Any], Dict[str, Any], str], Any]


def build_boto3_session(credentials: Dict[str, Any], config: Optional[Dict[str, Any]], connector_id: str):
    """Build a boto3 Session from connector credentials.

    Mirrors ``AWSSecurityHubConnector.authenticate``: static access keys,
    optional session token, optional ``role_arn`` assumed through STS with
    ``external_id``. Raises ImportError when boto3 is unavailable.
    """
    import boto3  # imported lazily so the module loads without boto3

    config = config or {}
    region = credentials.get("aws_region") or config.get("aws_region") or "us-east-1"
    access_key = credentials.get("aws_access_key_id", "")
    secret_key = credentials.get("aws_secret_access_key", "")
    session_token = credentials.get("aws_session_token")
    role_arn = credentials.get("role_arn") or config.get("role_arn")

    base_kwargs: Dict[str, Any] = {"region_name": region}
    if access_key and secret_key:
        base_kwargs["aws_access_key_id"] = access_key
        base_kwargs["aws_secret_access_key"] = secret_key
        if session_token:
            base_kwargs["aws_session_token"] = session_token

    if not role_arn:
        return boto3.Session(**base_kwargs)

    sts = boto3.client("sts", **base_kwargs)
    assume_params: Dict[str, Any] = {
        "RoleArn": role_arn,
        "RoleSessionName": f"resilai-discovery-{str(connector_id)[:8]}",
        "DurationSeconds": 3600,
    }
    external_id = credentials.get("external_id") or config.get("external_id")
    if external_id:
        assume_params["ExternalId"] = external_id
    assumed = sts.assume_role(**assume_params)["Credentials"]
    return boto3.Session(
        aws_access_key_id=assumed["AccessKeyId"],
        aws_secret_access_key=assumed["SecretAccessKey"],
        aws_session_token=assumed["SessionToken"],
        region_name=region,
    )


def _client_error_code(exc: BaseException) -> Optional[str]:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        return (response.get("Error") or {}).get("Code")
    return None


def _is_access_denied(exc: BaseException) -> bool:
    return _client_error_code(exc) in _ACCESS_DENIED_CODES


def _paginate(call: Callable[..., Dict[str, Any]], result_key: str, **kwargs) -> List[Dict[str, Any]]:
    """Manual NextToken/Marker pagination so stubbed clients need no paginator."""
    items: List[Dict[str, Any]] = []
    token: Optional[str] = None
    token_key = "Marker" if result_key == "DBInstances" else "NextToken"
    for _ in range(100):  # hard cap: 100 pages
        params = dict(kwargs)
        if token:
            params[token_key] = token
        response = call(**params) or {}
        if not isinstance(response, dict):
            break
        page = response.get(result_key) or []
        items.extend(page)
        token = response.get(token_key)
        if not token:
            break
    return items


def _name_tag(instance: Dict[str, Any]) -> Optional[str]:
    for tag in instance.get("Tags") or []:
        if tag.get("Key") == "Name" and tag.get("Value"):
            return tag["Value"]
    return None


def _evidence_hash(*parts: Any) -> str:
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()


class AWSDiscoveryService:
    """Service to discover technology assets via AWS APIs."""

    def __init__(
        self,
        db: Session,
        org_id: str,
        session_factory: Optional[SessionFactory] = None,
        is_demo: Optional[bool] = None,
    ):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)
        self._session_factory: SessionFactory = session_factory or build_boto3_session
        self._is_demo = is_demo
        self.last_result: Optional[SourceDiscoveryResult] = None

    # ------------------------------------------------------------------
    # Gating
    # ------------------------------------------------------------------

    def is_demo(self) -> bool:
        if self._is_demo is None:
            self._is_demo = is_demo_org(self.db, self.org_id)
        return self._is_demo

    # ------------------------------------------------------------------
    # Connector loading
    # ------------------------------------------------------------------

    def _load_aws_connectors(self) -> List[Dict[str, Any]]:
        """Return [{id, display_name, type, credentials, config}] for active AWS connectors."""
        from app.models.connector import ConnectorStatus
        from app.services.connector_manager import ConnectorManager

        manager = ConnectorManager(self.db, self.org_id)
        loaded: List[Dict[str, Any]] = []
        for ctype in AWS_CONNECTOR_TYPES:
            for connector in manager.list_connectors(connector_type=ctype):
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
                    "display_name": connector.display_name or ctype,
                    "type": ctype,
                    "credentials": credentials,
                    "config": cfg,
                })
        return loaded

    # ------------------------------------------------------------------
    # Real discovery
    # ------------------------------------------------------------------

    def fetch_aws_resources(self, session: Any, result: SourceDiscoveryResult) -> List[Dict[str, Any]]:
        """Call EC2/RDS/SSM and return normalized resource dicts. No persistence.

        Each resource: {external_id, name, asset_type, os, ip, public_ip, state,
        instance_type, launch_time, software: [{name, vendor, version, source}],
        source: "<api path>", raw: {...}}.
        """
        resources: List[Dict[str, Any]] = []

        # -- EC2 ----------------------------------------------------------
        ec2_by_id: Dict[str, Dict[str, Any]] = {}
        try:
            ec2 = session.client("ec2")
            reservations = _paginate(ec2.describe_instances, "Reservations")
            for reservation in reservations:
                for inst in reservation.get("Instances") or []:
                    state = ((inst.get("State") or {}).get("Name")) or "unknown"
                    if state not in ("running", "stopped"):
                        continue
                    instance_id = inst.get("InstanceId")
                    if not instance_id:
                        continue
                    launch = inst.get("LaunchTime")
                    resource = {
                        "external_id": instance_id,
                        "name": _name_tag(inst) or instance_id,
                        "asset_type": AssetType.CLOUD_SERVICE.value,
                        "os": inst.get("PlatformDetails") or inst.get("Platform") or None,
                        "ip": inst.get("PrivateIpAddress"),
                        "public_ip": inst.get("PublicIpAddress"),
                        "state": state,
                        "instance_type": inst.get("InstanceType"),
                        "launch_time": launch.isoformat() if hasattr(launch, "isoformat") else launch,
                        "software": [],
                        "source": API_EC2_DESCRIBE_INSTANCES,
                        "raw": {
                            "InstanceId": instance_id,
                            "InstanceType": inst.get("InstanceType"),
                            "State": state,
                            "PlatformDetails": inst.get("PlatformDetails"),
                        },
                    }
                    ec2_by_id[instance_id] = resource
                    resources.append(resource)
            result.detail["ec2_instances"] = len(ec2_by_id)
        except Exception as exc:
            if _is_access_denied(exc):
                result.denied_apis.append(API_EC2_DESCRIBE_INSTANCES)
            else:
                result.errors.append(f"{API_EC2_DESCRIBE_INSTANCES}: {exc}")
                logger.warning("EC2 describe_instances failed for org %s: %s", self.org_id, exc)

        # -- RDS ----------------------------------------------------------
        try:
            rds = session.client("rds")
            db_instances = _paginate(rds.describe_db_instances, "DBInstances")
            for dbi in db_instances:
                identifier = dbi.get("DBInstanceIdentifier")
                if not identifier:
                    continue
                engine = dbi.get("Engine") or "unknown"
                version = dbi.get("EngineVersion")
                endpoint = (dbi.get("Endpoint") or {}).get("Address")
                resources.append({
                    "external_id": identifier,
                    "name": identifier,
                    "asset_type": AssetType.CLOUD_SERVICE.value,
                    "os": None,
                    "ip": endpoint,
                    "public_ip": endpoint if dbi.get("PubliclyAccessible") else None,
                    "state": dbi.get("DBInstanceStatus"),
                    "instance_type": dbi.get("DBInstanceClass"),
                    "launch_time": None,
                    "software": [{
                        "name": engine,
                        "vendor": None,
                        "version": version,
                        "source": API_RDS_DESCRIBE_DB_INSTANCES,
                    }],
                    "source": API_RDS_DESCRIBE_DB_INSTANCES,
                    "raw": {
                        "DBInstanceIdentifier": identifier,
                        "Engine": engine,
                        "EngineVersion": version,
                        "StorageEncrypted": bool(dbi.get("StorageEncrypted")),
                        "PubliclyAccessible": bool(dbi.get("PubliclyAccessible")),
                        "MultiAZ": bool(dbi.get("MultiAZ")),
                    },
                })
            result.detail["rds_instances"] = len(db_instances)
        except Exception as exc:
            if _is_access_denied(exc):
                result.denied_apis.append(API_RDS_DESCRIBE_DB_INSTANCES)
            else:
                result.errors.append(f"{API_RDS_DESCRIBE_DB_INSTANCES}: {exc}")
                logger.warning("RDS describe_db_instances failed for org %s: %s", self.org_id, exc)

        # -- SSM software inventory ---------------------------------------
        if ec2_by_id:
            managed_ids: List[str] = []
            try:
                ssm = session.client("ssm")
                infos = _paginate(ssm.describe_instance_information, "InstanceInformationList")
                managed_ids = [i.get("InstanceId") for i in infos if i.get("InstanceId") in ec2_by_id]
                result.detail["ssm_managed_instances"] = len(managed_ids)
            except Exception as exc:
                ssm = None
                if _is_access_denied(exc):
                    result.denied_apis.append(API_SSM_DESCRIBE_INSTANCE_INFORMATION)
                else:
                    result.errors.append(f"{API_SSM_DESCRIBE_INSTANCE_INFORMATION}: {exc}")

            inventory_denied = False
            for instance_id in managed_ids:
                if inventory_denied or ssm is None:
                    break
                try:
                    entries = _paginate(
                        ssm.list_inventory_entries,
                        "Entries",
                        InstanceId=instance_id,
                        TypeName="AWS:Application",
                    )
                except Exception as exc:
                    if _is_access_denied(exc):
                        if API_SSM_LIST_INVENTORY_ENTRIES not in result.denied_apis:
                            result.denied_apis.append(API_SSM_LIST_INVENTORY_ENTRIES)
                        inventory_denied = True
                    else:
                        result.errors.append(f"{API_SSM_LIST_INVENTORY_ENTRIES}[{instance_id}]: {exc}")
                    continue
                for entry in entries:
                    name = entry.get("Name")
                    if not name:
                        continue
                    ec2_by_id[instance_id]["software"].append({
                        "name": name,
                        "vendor": entry.get("Publisher"),
                        "version": entry.get("Version"),
                        "source": API_SSM_LIST_INVENTORY_ENTRIES,
                    })

        return resources

    def _persist_resources(
        self,
        inventory_id: str,
        resources: List[Dict[str, Any]],
        connector_name: str,
        result: SourceDiscoveryResult,
    ) -> int:
        assets_created = 0
        for res in resources:
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=res["asset_type"],
                hostname=res.get("name"),
                operating_system=res.get("os"),
                ip_address=res.get("ip"),
                cloud_provider="AWS",
            )
            assets_created += 1

            for sw in res.get("software") or []:
                installation_source = (
                    "aws_rds" if sw.get("source") == API_RDS_DESCRIBE_DB_INSTANCES
                    else "aws_systems_manager"
                )
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=sw["name"],
                    vendor=sw.get("vendor"),
                    version=sw.get("version"),
                    installation_source=installation_source,
                )
                result.products_created += 1
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="aws",
                    connector_name=connector_name,
                    raw_evidence_hash=_evidence_hash(
                        sw.get("source"), res["external_id"], sw["name"], sw.get("version")
                    ),
                )
        return assets_created

    def _execute_real_aws_discovery(self, inventory_id: str) -> SourceDiscoveryResult:
        result = SourceDiscoveryResult(source="aws")
        connectors = self._load_aws_connectors()
        if not connectors:
            result.status = DiscoveryStatus.NOT_CONNECTED
            logger.info("AWS discovery skipped for org %s: no AWS connector registered", self.org_id)
            return result

        for connector in connectors:
            result.connectors_used.append(connector["id"])
            try:
                session = self._session_factory(
                    connector["credentials"], connector["config"], connector["id"]
                )
            except ImportError:
                result.errors.append("boto3 not installed")
                result.status = DiscoveryStatus.ERROR
                continue
            except Exception as exc:
                result.errors.append(f"session[{connector['id']}]: {exc}")
                result.status = DiscoveryStatus.AUTH_FAILED
                logger.warning("AWS session build failed for connector %s: %s", connector["id"], exc)
                continue

            resources = self.fetch_aws_resources(session, result)
            result.assets_created += self._persist_resources(
                inventory_id, resources, connector["display_name"], result
            )

        if result.status not in (DiscoveryStatus.AUTH_FAILED, DiscoveryStatus.ERROR):
            if result.denied_apis and not result.assets_created:
                result.status = DiscoveryStatus.PERMISSION_MISSING
            elif result.denied_apis or result.errors:
                result.status = DiscoveryStatus.PARTIAL
            else:
                result.status = DiscoveryStatus.OK
        return result

    # ------------------------------------------------------------------
    # Demo-only synthetic inventory
    # ------------------------------------------------------------------

    def _execute_demo_aws_discovery(self, inventory_id: str) -> int:
        """Synthetic EC2/RDS inventory. Reached ONLY when ``is_demo()`` is True."""
        resources = [
            {
                "id": "i-0abcd1234efgh5678",
                "type": AssetType.CLOUD_SERVICE.value,
                "name": "EKS-Worker-Node-1",
                "os": "Amazon Linux 2023",
                "ip": "10.0.10.5",
                "software": [
                    {"name": "docker", "vendor": "Docker Inc.", "version": "27.4.1"},
                    {"name": "kubernetes", "vendor": "Cloud Native Computing Foundation", "version": "1.30"},
                    {"name": "aws-cli", "vendor": "Amazon", "version": "2.15.0"},
                ],
            },
            {
                "id": "db-abc123def456ghi",
                "type": AssetType.CLOUD_SERVICE.value,
                "name": "production-postgres-rds",
                "os": None,
                "ip": "10.0.20.10",
                "software": [
                    {"name": "postgresql", "vendor": "PostgreSQL Global Development Group", "version": "16.4"}
                ],
            },
        ]

        assets_created = 0
        for res in resources:
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=res["type"],
                hostname=res["name"],
                operating_system=res.get("os"),
                ip_address=res.get("ip"),
                cloud_provider="AWS",
            )
            assets_created += 1
            for sw in res["software"]:
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=sw["name"],
                    vendor=sw.get("vendor"),
                    version=sw.get("version"),
                    installation_source="aws_systems_manager",
                )
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="aws",
                    connector_name="Demo AWS (synthetic)",
                    raw_evidence_hash=_evidence_hash("demo", res["id"], sw["name"], sw.get("version")),
                )
        return assets_created

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def discover_from_aws(self, inventory_id: str) -> int:
        """Runs discovery against AWS to populate inventory. Returns assets created.

        ``self.last_result`` holds the per-source status after the call.
        """
        if self.is_demo():
            count = self._execute_demo_aws_discovery(inventory_id)
            self.last_result = SourceDiscoveryResult(
                source="aws", status=DiscoveryStatus.DEMO, assets_created=count
            )
            return count

        self.last_result = self._execute_real_aws_discovery(inventory_id)
        return self.last_result.assets_created
