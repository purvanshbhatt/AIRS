"""
Technology Discovery Orchestrator.
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.services.discovery.discovery import TechnologyDiscoveryService
from app.services.discovery.wazuh_discovery import WazuhDiscoveryService
from app.services.discovery.graph_discovery import GraphDiscoveryService
from app.services.discovery.aws_discovery import AWSDiscoveryService

from app.models.discovery import TechnologyInventory, HostAsset, InstalledProduct
from app.models.tech_stack import TechStackItem, LtsStatus
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding, Severity, FindingStatus
from app.services.governance.lifecycle_analysis import LifecycleAnalysisService

logger = logging.getLogger(__name__)

class TechnologyDiscoveryOrchestrator:
    """Orchestrates technology discovery across all configured sources."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)

    def run_discovery_cycle(self) -> TechnologyInventory:
        """Runs discovery across all sources and returns the resulting inventory."""
        
        # 1. Create new inventory snapshot
        inventory = self.discovery_service.create_inventory(source="orchestrator", confidence_score=0.95)
        
        logger.info(f"Starting discovery cycle for org {self.org_id}. Inventory ID: {inventory.id}")
        
        # 2. Run discovery from all sources
        total_assets = 0

        # Wazuh
        try:
            wazuh_svc = WazuhDiscoveryService(self.db, self.org_id)
            total_assets += wazuh_svc.discover_from_wazuh(inventory.id)
        except Exception as e:
            logger.error(f"Wazuh discovery failed: {e}")
            
        # Graph
        try:
            graph_svc = GraphDiscoveryService(self.db, self.org_id)
            total_assets += graph_svc.discover_from_graph(inventory.id)
        except Exception as e:
            logger.error(f"Graph discovery failed: {e}")
            
        # AWS
        try:
            aws_svc = AWSDiscoveryService(self.db, self.org_id)
            total_assets += aws_svc.discover_from_aws(inventory.id)
        except Exception as e:
            logger.error(f"AWS discovery failed: {e}")
            
        logger.info(f"Discovery complete. Discovered {total_assets} assets.")
        
        # 3. Merge duplicate assets (Optional / Future enhancement, right now we just store all)
        self._deduplicate_assets(inventory.id)
        
        # 4. Sync to TechStack registry and SoftwareCatalog for backwards compatibility
        self._sync_to_legacy_tables(inventory.id)
        
        return inventory

    def _deduplicate_assets(self, inventory_id: str):
        """Merges duplicate assets within the same inventory based on hostname/ip."""
        # A simple implementation to deduplicate by hostname
        assets = self.db.query(HostAsset).filter(HostAsset.inventory_id == inventory_id).all()
        
        seen_hosts = {}
        for asset in assets:
            if not asset.hostname:
                continue
            
            host_key = asset.hostname.lower()
            if host_key in seen_hosts:
                # Merge logic: Move installed products to the first seen asset
                first_asset = seen_hosts[host_key]
                
                # Move products
                products = self.db.query(InstalledProduct).filter(InstalledProduct.asset_id == asset.id).all()
                for prod in products:
                    prod.asset_id = first_asset.id
                
                # Delete duplicate asset
                self.db.delete(asset)
            else:
                seen_hosts[host_key] = asset
                
        self.db.commit()

    def _sync_to_legacy_tables(self, inventory_id: str):
        """Syncs the new deterministic discovery data to the existing tech_stack tables and generates findings."""
        
        # Clear existing tech stack items to ensure clean state
        self.db.query(TechStackItem).filter(TechStackItem.org_id == self.org_id).delete()
        self.db.commit()
        
        # Get all installed products in this inventory
        products = (
            self.db.query(InstalledProduct)
            .join(HostAsset)
            .filter(HostAsset.inventory_id == inventory_id)
            .all()
        )
        
        # We need to deduplicate products globally for the tech stack view
        unique_products = {}
        for p in products:
            key = f"{p.product_name}-{p.version}"
            if key not in unique_products:
                unique_products[key] = p
                
        lifecycle_service = LifecycleAnalysisService(self.db)
        
        # Find active assessment for Findings
        active_assessment = (
            self.db.query(Assessment)
            .filter(
                Assessment.organization_id == self.org_id,
                Assessment.status.in_([AssessmentStatus.IN_PROGRESS, AssessmentStatus.COMPLETED])
            )
            .order_by(Assessment.created_at.desc())
            .first()
        )

        for key, p in unique_products.items():
            # Resolve version intelligence from deterministic lifecycle service
            analysis = lifecycle_service.analyze_lifecycle(p.product_name, p.version or "")
            
            # Map analysis status to lts_val
            analysis_status = analysis.get("status", "Supported")
            if analysis_status == "EOL":
                lts_val = "eol"
            elif analysis_status == "Expiring":
                lts_val = "deprecated"
            else:
                lts_val = "active"
                
            major_behind = 0
            # If the user wants to keep a simplistic major_behind for the UI:
            if analysis.get("latest_supported") and p.version:
                try:
                    latest_major = int(analysis["latest_supported"].split(".")[0])
                    current_major = int(p.version.split(".")[0])
                    if latest_major > current_major:
                        major_behind = latest_major - current_major
                except Exception:
                    pass
            
            category = "Other"
            # Map standard category
            prod_lower = p.product_name.lower()
            if prod_lower in ("python", "python3", "java", "go"):
                category = "Language Runtime"
            elif prod_lower in ("node", "node.js"):
                category = "Language Runtime"
            elif prod_lower in ("react", "angular", "django", "fastapi", "spring-boot", "express", "flask"):
                category = "Framework"
            elif prod_lower in ("postgresql", "postgresql-16", "mysql", "redis", "mongodb"):
                category = "Database"
            elif prod_lower in ("nginx", "apache-httpd"):
                category = "Web Server"
            elif prod_lower in ("kubernetes", "docker"):
                category = "Container Runtime"
            elif "windows" in prod_lower or "mac" in prod_lower or "ubuntu" in prod_lower or "linux" in prod_lower:
                category = "Operating System"
            elif prod_lower in ("terraform", "aws-cli"):
                category = "CI/CD"
            elif prod_lower in ("openssl", "log4j"):
                category = "Library"

            # Sync to TechStackItem
            tech_item = TechStackItem(
                org_id=self.org_id,
                component_name=p.product_name,
                version=p.version,
                lts_status=LtsStatus(lts_val),
                major_versions_behind=major_behind,
                category=category,
                notes=f"Auto-discovered from {p.installation_source}",
            )
            self.db.add(tech_item)
            
            # Generate Findings if EOL or Expiring and we have an active assessment
            if active_assessment and analysis_status in ("EOL", "Expiring"):
                severity = Severity.CRITICAL if analysis_status == "EOL" else Severity.HIGH
                finding = Finding(
                    assessment_id=active_assessment.id,
                    title=f"{p.product_name} {p.version} Is {analysis_status}",
                    description=f"Deterministic lifecycle analysis detected {p.product_name} version {p.version} is {analysis_status}. Please upgrade to a supported version immediately.",
                    severity=severity,
                    status=FindingStatus.OPEN,
                    domain_id="infrastructure",
                    domain_name="Infrastructure Security",
                    evidence=f"Detected {p.product_name} {p.version} which is {analysis_status}. (Asset: {p.asset_id})",
                    recommendation=f"Upgrade {p.product_name} to a supported version or decommission the asset. Ensure compliance with end-of-life policies.",
                    priority="High",
                    nist_category="ID.AM",
                    nist_function="identify"
                )
                self.db.add(finding)

        self.db.commit()
