"""
Asset Discovery Service — automatically discovers software assets from external sources
and syncs them to discovered_assets, software_catalog, and tech_stack_registry.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.discovered_asset import DiscoveredAsset
from app.models.software_catalog import SoftwareCatalog
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.lifecycle_engine import get_version_status, get_technology_versions
from app.services.discovery.discovery import DiscoveryStatus, SourceDiscoveryResult, is_demo_org

logger = logging.getLogger("airs.services.asset_discovery")

SOURCE_AWS_EC2 = "AWS EC2"
SOURCE_AWS_RDS = "AWS RDS"
SOURCE_AWS_SSM = "AWS Systems Manager"
SOURCE_INTUNE = "Microsoft Intune"


class AssetDiscoveryService:
    """Service to discover software assets and update catalog and tech stack tables.

    Real organizations: ``discovered_assets`` is filled from the org's registered
    connectors (AWS via EC2/RDS/SSM, Microsoft via Graph managedDevices). No
    connector of a type means nothing from that source and a ``not_connected``
    status in ``last_results``. Demo organizations keep the synthetic 47-row seed.
    """

    def __init__(
        self,
        db: Session,
        org_id: str,
        is_demo: Optional[bool] = None,
        session_factory=None,
        http_client_factory=None,
        token_provider=None,
    ):
        self.db = db
        self.org_id = org_id
        self._is_demo = is_demo
        self._session_factory = session_factory
        self._http_client_factory = http_client_factory
        self._token_provider = token_provider
        self.last_results: Dict[str, SourceDiscoveryResult] = {}

    def is_demo(self) -> bool:
        if self._is_demo is None:
            self._is_demo = is_demo_org(self.db, self.org_id)
        return self._is_demo

    def discover_assets(self) -> int:
        """
        Orchestrate the discovery pipeline:
        1. Discover assets from registered connectors (real org) or seed the
           synthetic set (demo org only).
        2. Sync discovered assets to the SoftwareCatalog.
        3. Match versions against Version Intelligence / lifecycle config.
        4. Populate/Sync the TechStackItem registry for technology currency scoring.

        Returns the number of discovered_assets rows for the org.
        """
        logger.info("Running automated asset discovery for org: %s", self.org_id)

        if self.is_demo():
            existing_count = (
                self.db.query(DiscoveredAsset)
                .filter(DiscoveredAsset.org_id == self.org_id)
                .count()
            )
            if existing_count == 0:
                self._seed_demo_discovered_assets()
            self.last_results = {
                "demo": SourceDiscoveryResult(source="demo", status=DiscoveryStatus.DEMO)
            }
        else:
            self._discover_from_connectors()

        # Sync discovered_assets to software_catalog and tech_stack_registry
        self.sync_discovered_to_catalog_and_stack()
        return (
            self.db.query(DiscoveredAsset)
            .filter(DiscoveredAsset.org_id == self.org_id)
            .count()
        )

    # ------------------------------------------------------------------
    # Real organizations: connector-backed discovery
    # ------------------------------------------------------------------

    def _upsert_discovered_asset(self, vendor: Optional[str], product: str, version: Optional[str], source: str) -> bool:
        """Insert or touch a (product, version, source) row. Returns True when inserted."""
        product = (product or "").strip()
        if not product:
            return False
        version = (str(version).strip() if version is not None else None) or None
        existing = (
            self.db.query(DiscoveredAsset)
            .filter(
                DiscoveredAsset.org_id == self.org_id,
                DiscoveredAsset.product == product,
                DiscoveredAsset.version == version,
                DiscoveredAsset.source == source,
            )
            .first()
        )
        if existing:
            existing.last_seen = datetime.now(timezone.utc)
            if vendor and not existing.vendor:
                existing.vendor = vendor
            return False
        self.db.add(DiscoveredAsset(
            org_id=self.org_id, vendor=vendor, product=product, version=version, source=source,
        ))
        return True

    def _discover_from_connectors(self) -> None:
        """Fill discovered_assets from the org's AWS and Microsoft connectors."""
        from app.services.discovery.aws_discovery import (
            API_RDS_DESCRIBE_DB_INSTANCES,
            AWSDiscoveryService,
        )
        from app.services.discovery.graph_discovery import (
            GraphDiscoveryService,
            fetch_managed_devices,
            fetch_security_alerts,
        )

        self.last_results = {}
        inserted = 0

        # -- AWS ------------------------------------------------------------
        aws_result = SourceDiscoveryResult(source="aws")
        aws_svc = AWSDiscoveryService(
            self.db, self.org_id, session_factory=self._session_factory, is_demo=False
        )
        try:
            connectors = aws_svc._load_aws_connectors()
        except Exception as exc:
            connectors = []
            aws_result.status = DiscoveryStatus.ERROR
            aws_result.errors.append(f"connectors: {exc}")
        if not connectors and aws_result.status != DiscoveryStatus.ERROR:
            aws_result.status = DiscoveryStatus.NOT_CONNECTED
        for connector in connectors:
            aws_result.connectors_used.append(connector["id"])
            try:
                session = aws_svc._session_factory(connector["credentials"], connector["config"], connector["id"])
            except Exception as exc:
                aws_result.status = DiscoveryStatus.AUTH_FAILED
                aws_result.errors.append(f"session[{connector['id']}]: {exc}")
                continue
            resources = aws_svc.fetch_aws_resources(session, aws_result)
            for res in resources:
                aws_result.assets_created += 1
                for sw in res.get("software") or []:
                    source = SOURCE_AWS_RDS if sw.get("source") == API_RDS_DESCRIBE_DB_INSTANCES else SOURCE_AWS_SSM
                    if self._upsert_discovered_asset(sw.get("vendor"), sw["name"], sw.get("version"), source):
                        inserted += 1
                        aws_result.products_created += 1
            if aws_result.status == DiscoveryStatus.NOT_CONNECTED:
                aws_result.status = DiscoveryStatus.OK
        if connectors and aws_result.status not in (DiscoveryStatus.AUTH_FAILED, DiscoveryStatus.ERROR):
            if aws_result.denied_apis and not aws_result.assets_created:
                aws_result.status = DiscoveryStatus.PERMISSION_MISSING
            elif aws_result.denied_apis or aws_result.errors:
                aws_result.status = DiscoveryStatus.PARTIAL
            else:
                aws_result.status = DiscoveryStatus.OK
        self.last_results["aws"] = aws_result

        # -- Microsoft Graph ------------------------------------------------
        graph_result = SourceDiscoveryResult(source="ms_graph")
        graph_result.detail["org_id"] = self.org_id
        graph_svc = GraphDiscoveryService(
            self.db, self.org_id,
            http_client_factory=self._http_client_factory,
            token_provider=self._token_provider,
            is_demo=False,
        )
        try:
            ms_connectors = graph_svc._load_microsoft_connectors()
        except Exception as exc:
            ms_connectors = []
            graph_result.status = DiscoveryStatus.ERROR
            graph_result.errors.append(f"connectors: {exc}")
        if not ms_connectors and graph_result.status != DiscoveryStatus.ERROR:
            graph_result.status = DiscoveryStatus.NOT_CONNECTED
        for connector in ms_connectors:
            graph_result.connectors_used.append(connector["id"])
            try:
                token = graph_svc._token_provider(connector["credentials"], connector["config"], connector["id"])
            except Exception as exc:
                token = None
                graph_result.errors.append(f"token[{connector['id']}]: {exc}")
            if not token:
                graph_result.status = DiscoveryStatus.AUTH_FAILED
                continue
            client = graph_svc._http_client_factory({"Authorization": f"Bearer {token}"})
            try:
                devices = fetch_managed_devices(client, graph_result)
                fetch_security_alerts(client, graph_result)
            except Exception as exc:
                graph_result.errors.append(f"graph[{connector['id']}]: {exc}")
                devices = []
            finally:
                close = getattr(client, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
            for device in devices:
                graph_result.assets_created += 1
                if device.get("os"):
                    vendor = "Microsoft" if "windows" in str(device["os"]).lower() else None
                    if self._upsert_discovered_asset(vendor, str(device["os"]).lower(), device.get("os_version"), SOURCE_INTUNE):
                        inserted += 1
                        graph_result.products_created += 1
        if ms_connectors and graph_result.status not in (DiscoveryStatus.AUTH_FAILED, DiscoveryStatus.ERROR):
            if graph_result.denied_apis and not graph_result.assets_created:
                graph_result.status = DiscoveryStatus.PERMISSION_MISSING
            elif graph_result.denied_apis or graph_result.errors:
                graph_result.status = DiscoveryStatus.PARTIAL
            else:
                graph_result.status = DiscoveryStatus.OK
        self.last_results["ms_graph"] = graph_result

        self.db.commit()
        logger.info(
            "Connector discovery for org %s: %d new rows; %s",
            self.org_id, inserted, "; ".join(r.summary() for r in self.last_results.values()),
        )

    # ------------------------------------------------------------------
    # Demo organizations only: synthetic seed
    # ------------------------------------------------------------------

    def _seed_demo_discovered_assets(self):
        """Seed exactly 47 synthetic assets (Intune, Defender, Wazuh, Splunk). DEMO ORGS ONLY."""
        logger.info("Seeding 47 demo software assets for demo org: %s", self.org_id)
        
        assets_data = []

        # ── Wazuh ── (12 assets: 11 Current, 1 Critical)
        # 1 Critical
        assets_data.append({
            "vendor": "PostgreSQL Global Development Group",
            "product": "postgresql",
            "version": "12",
            "source": "Wazuh",
        })
        # 11 Current
        wazuh_current = [
            ("Wazuh Inc.", "wazuh-agent", "4.7.2"),
            ("Oracle Corporation", "java", "21"),
            ("PostgreSQL Global Development Group", "postgresql", "16"),
            ("MySQL AB", "mysql", "8.4"),
            ("F5 Nginx", "nginx", "1.27.3"),
            ("Python Software Foundation", "python", "3.12.3"),
            ("OpenSSL Project", "openssl", "3.4.0"),
            ("Apache Software Foundation", "log4j", "2.24.3"),
            ("Oracle Corporation", "java", "17"),
            ("HashiCorp", "terraform", "1.9.8"),
            ("Google", "go", "1.23.4"),
        ]
        for v, p, ver in wazuh_current:
            assets_data.append({"vendor": v, "product": p, "version": ver, "source": "Wazuh"})

        # ── Microsoft Intune ── (12 assets: 10 Current, 2 Outdated)
        # 2 Outdated
        assets_data.extend([
            {
                "vendor": "Python Software Foundation",
                "product": "python",
                "version": "3.9",
                "source": "Microsoft Intune",
            },
            {
                "vendor": "Node.js Foundation",
                "product": "node.js",
                "version": "18",
                "source": "Microsoft Intune",
            }
        ])
        # 10 Current
        intune_current = [
            ("Microsoft", "windows-11-client", "10.0.22631"),
            ("Adobe", "acrobat-reader", "24.0"),
            ("Google", "chrome", "121.0"),
            ("Mozilla", "firefox", "122.0"),
            ("Node.js Foundation", "node.js", "22"),
            ("Python Software Foundation", "python", "3.11"),
            ("Python Software Foundation", "python", "3.13"),
            ("Microsoft", "powershell-core", "7.4"),
            ("Git", "git-scm", "2.43.0"),
            ("Slack Technologies", "slack-client", "4.36.0"),
        ]
        for v, p, ver in intune_current:
            assets_data.append({"vendor": v, "product": p, "version": ver, "source": "Microsoft Intune"})

        # ── Microsoft Defender ── (11 assets: 10 Current, 1 Outdated)
        # 1 Outdated
        assets_data.append({
            "vendor": "Angular Team",
            "product": "angular",
            "version": "16",
            "source": "Microsoft Defender",
        })
        # 10 Current
        defender_current = [
            ("Microsoft", "defender-endpoint", "10.1.2403"),
            ("Facebook", "react", "19.0.0"),
            ("Facebook", "react", "18.2.0"),
            ("FastAPI", "fastapi", "0.115.6"),
            ("Django Software Foundation", "django", "5.1.4"),
            ("Expressjs", "express", "4.21.1"),
            ("Pallets", "flask", "3.1.0"),
            ("Angular Team", "angular", "18"),
            ("Angular Team", "angular", "17"),
            ("Spring Boot", "spring boot", "3.4.1"),
        ]
        for v, p, ver in defender_current:
            assets_data.append({"vendor": v, "product": p, "version": ver, "source": "Microsoft Defender"})

        # ── Splunk ── (12 assets: 10 Current, 2 Outdated)
        # 2 Outdated
        assets_data.extend([
            {
                "vendor": "Redis Labs",
                "product": "redis",
                "version": "6",
                "source": "Splunk",
            },
            {
                "vendor": "Cloud Native Computing Foundation",
                "product": "kubernetes",
                "version": "1.28",
                "source": "Splunk",
            }
        ])
        # 10 Current
        splunk_current = [
            ("Splunk Inc.", "splunk-forwarder", "9.2.0"),
            ("Redis Labs", "redis", "7"),
            ("Cloud Native Computing Foundation", "kubernetes", "1.31"),
            ("Cloud Native Computing Foundation", "kubernetes", "1.30"),
            ("Docker Inc.", "docker", "27.4.1"),
            ("MongoDB Inc.", "mongodb", "8.0.4"),
            ("MySQL AB", "mysql", "8.0"),
            ("Nginx Inc.", "nginx", "1.26.0"),
            ("Apache Software Foundation", "apache httpd", "2.4.62"),
            ("Amazon", "aws-cli", "2.15.0"),
        ]
        for v, p, ver in splunk_current:
            assets_data.append({"vendor": v, "product": p, "version": ver, "source": "Splunk"})

        # Bulk insert
        for a in assets_data:
            asset = DiscoveredAsset(
                org_id=self.org_id,
                vendor=a["vendor"],
                product=a["product"],
                version=a["version"],
                source=a["source"],
            )
            self.db.add(asset)
        
        self.db.commit()
        logger.info("Successfully seeded 47 assets into discovered_assets table.")

    def sync_discovered_to_catalog_and_stack(self):
        """Sync discovered assets to software_catalog and tech_stack_registry tables."""
        discovered = (
            self.db.query(DiscoveredAsset)
            .filter(DiscoveredAsset.org_id == self.org_id)
            .all()
        )

        # Clear existing tech stack items for staging to ensure clean automated counts
        self.db.query(TechStackItem).filter(TechStackItem.org_id == self.org_id).delete()
        self.db.commit()

        for asset in discovered:
            # 1. Sync to SoftwareCatalog
            catalog_item = (
                self.db.query(SoftwareCatalog)
                .filter(
                    SoftwareCatalog.org_id == self.org_id,
                    SoftwareCatalog.product == asset.product,
                )
                .first()
            )
            if not catalog_item:
                catalog_item = SoftwareCatalog(
                    org_id=self.org_id,
                    product=asset.product,
                    vendor=asset.vendor,
                )
                self.db.add(catalog_item)

            catalog_item.current_version = asset.version
            catalog_item.source = asset.source

            # Resolve version intelligence from lifecycle config
            lifecycle_status = get_version_status(asset.product, asset.version or "")
            
            lts_val = "active"
            major_behind = 0
            category = "Other"

            if lifecycle_status:
                lts_val = lifecycle_status.get("status", "active")
                # Infer category from technology versions structure
                tech_versions = get_technology_versions(asset.product)
                if tech_versions:
                    # Resolve latest version
                    # Sort version strings that are keys of tech_versions
                    keys = [k for k in tech_versions.keys() if k != "_meta"]
                    if keys:
                        # Clean releases & sort
                        latest_release = keys[-1]
                        catalog_item.latest_version = latest_release
                        catalog_item.latest_release_date = lifecycle_status.get("eol_date")
            
            # Map standard category
            prod_lower = asset.product.lower()
            if prod_lower in ("python", "java", "go"):
                category = "Language Runtime"
            elif prod_lower in ("node", "node.js"):
                category = "Language Runtime"
            elif prod_lower in ("react", "angular", "django", "fastapi", "spring-boot", "express", "flask"):
                category = "Framework"
            elif prod_lower in ("postgresql", "mysql", "redis", "mongodb"):
                category = "Database"
            elif prod_lower in ("nginx", "apache-httpd"):
                category = "Web Server"
            elif prod_lower in ("kubernetes", "docker"):
                category = "Container Runtime"
            elif prod_lower in ("windows-11-client"):
                category = "Operating System"
            elif prod_lower in ("terraform"):
                category = "CI/CD"
            elif prod_lower in ("openssl", "log4j"):
                category = "Library"

            # Determine major_versions_behind and override status for mock accuracy.
            # Demo seed only: real orgs keep the lifecycle engine's own answer.
            if not self.is_demo():
                pass
            elif prod_lower == "python" and asset.version == "3.9":
                lts_val = "active"
                major_behind = 2  # Outdated
            elif prod_lower in ("node", "node.js") and asset.version == "18":
                lts_val = "active"
                major_behind = 2  # Outdated
            elif prod_lower == "redis" and asset.version == "6":
                lts_val = "active"
                major_behind = 2  # Outdated
            elif prod_lower == "angular" and asset.version == "16":
                lts_val = "active"
                major_behind = 2  # Outdated
            elif prod_lower == "kubernetes" and asset.version == "1.28":
                lts_val = "active"
                major_behind = 2  # Outdated
            elif prod_lower == "postgresql" and asset.version == "12":
                lts_val = "eol"
                major_behind = 0  # EOL/Critical only

            # 2. Sync to TechStackItem
            tech_item = TechStackItem(
                org_id=self.org_id,
                component_name=asset.product,
                version=asset.version,
                lts_status=LtsStatus(lts_val),
                major_versions_behind=major_behind,
                category=category,
                notes=f"Auto-discovered from {asset.source}",
            )
            self.db.add(tech_item)
            
            # Enrich SoftwareCatalog severity based on lifecycle status
            if lts_val == "eol":
                catalog_item.severity = "critical"
            elif lts_val == "deprecated" or major_behind >= 3:
                catalog_item.severity = "high"
            elif major_behind >= 1:
                catalog_item.severity = "medium"
            else:
                catalog_item.severity = "low"

        self.db.commit()
        logger.info("Successfully synced discovered assets to SoftwareCatalog and TechStackItem tables.")
