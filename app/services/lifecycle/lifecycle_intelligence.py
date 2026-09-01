"""
Lifecycle Intelligence Service.

Deterministic lifecycle status checks against the GlobalSoftwareCatalog.
NO AI involvement — pure data lookups and date-based logic.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.lifecycle")


class LifecycleStatus(str, Enum):
    """Deterministic lifecycle classification."""
    SUPPORTED = "supported"
    EXPIRING = "expiring"      # Within 6 months of EOL
    EOL = "eol"                # Past EOL date
    UNKNOWN = "unknown"        # Not in catalog


class LifecycleSeverity(str, Enum):
    """Severity mapping for lifecycle status. Deterministic — no AI."""
    HEALTHY = "healthy"        # SUPPORTED
    HIGH = "high"              # EXPIRING
    CRITICAL = "critical"      # EOL


@dataclass
class LifecycleCheckResult:
    """Result of a lifecycle status check."""
    product_name: str
    vendor: str
    installed_version: str
    lifecycle_status: LifecycleStatus
    severity: LifecycleSeverity
    current_version: Optional[str] = None
    lts_version: Optional[str] = None
    eol_date: Optional[datetime] = None
    eos_date: Optional[datetime] = None
    days_until_eol: Optional[int] = None
    upgrade_recommendation: Optional[str] = None


EXPIRING_THRESHOLD_DAYS = 180  # 6 months


class LifecycleIntelligenceService:
    """
    Deterministic software lifecycle intelligence.

    Checks installed software versions against the GlobalSoftwareCatalog
    to determine lifecycle status (SUPPORTED, EXPIRING, EOL).

    RULES (deterministic, no AI):
    - EOL (past EOL date) = CRITICAL severity
    - EXPIRING (within 6 months of EOL) = HIGH severity
    - SUPPORTED = HEALTHY
    - UNKNOWN (not in catalog) = reported but not scored
    """

    def __init__(self, db: Session):
        self.db = db

    def check_lifecycle_status(
        self, product_name: str, version: str, vendor: Optional[str] = None
    ) -> LifecycleCheckResult:
        """
        Check lifecycle status for a specific product + version.

        Performs a deterministic lookup against GlobalSoftwareCatalog → SoftwareVersion.
        """
        from app.models.lifecycle_catalog import GlobalSoftwareCatalog, SoftwareVersion

        # Find the product in the global catalog
        query = self.db.query(GlobalSoftwareCatalog).filter(
            GlobalSoftwareCatalog.product_name.ilike(f"%{product_name}%")
        )
        if vendor:
            query = query.filter(
                GlobalSoftwareCatalog.vendor.ilike(f"%{vendor}%")
            )
        catalog_entry = query.first()

        if not catalog_entry:
            logger.debug(
                "Product '%s' (vendor=%s) not found in GlobalSoftwareCatalog",
                product_name, vendor
            )
            return LifecycleCheckResult(
                product_name=product_name,
                vendor=vendor or "Unknown",
                installed_version=version,
                lifecycle_status=LifecycleStatus.UNKNOWN,
                severity=LifecycleSeverity.HEALTHY,
            )

        # Find the specific version
        version_entry = (
            self.db.query(SoftwareVersion)
            .filter(
                SoftwareVersion.catalog_id == catalog_entry.id,
                SoftwareVersion.version_name == version,
            )
            .first()
        )

        # If exact version not found, try prefix match (e.g., "3.6" matches "3.6.9")
        if not version_entry:
            version_entry = (
                self.db.query(SoftwareVersion)
                .filter(
                    SoftwareVersion.catalog_id == catalog_entry.id,
                    SoftwareVersion.version_name.like(f"{version}%"),
                )
                .first()
            )

        if not version_entry:
            logger.debug(
                "Version '%s' of '%s' not found in catalog",
                version, product_name
            )
            return LifecycleCheckResult(
                product_name=product_name,
                vendor=catalog_entry.vendor or vendor or "Unknown",
                installed_version=version,
                lifecycle_status=LifecycleStatus.UNKNOWN,
                severity=LifecycleSeverity.HEALTHY,
                current_version=catalog_entry.current_version,
                lts_version=catalog_entry.current_lts_version,
            )

        # Determine lifecycle status from dates and support_status
        now_dt = datetime.utcnow()
        now_date = now_dt.date()
        status = LifecycleStatus.SUPPORTED
        severity = LifecycleSeverity.HEALTHY
        days_until_eol = None

        # Check explicit support_status field first
        if version_entry.support_status:
            status_lower = version_entry.support_status.lower()
            if status_lower == "eol":
                status = LifecycleStatus.EOL
                severity = LifecycleSeverity.CRITICAL
            elif status_lower == "expiring":
                status = LifecycleStatus.EXPIRING
                severity = LifecycleSeverity.HIGH

        # If support_status isn't set, derive from EOL date
        if status == LifecycleStatus.SUPPORTED and version_entry.eol_date:
            eol_dt = version_entry.eol_date
            if isinstance(eol_dt, str):
                try:
                    eol_dt = datetime.fromisoformat(eol_dt)
                except (ValueError, TypeError):
                    eol_dt = None

            if eol_dt:
                eol_d = eol_dt.date() if isinstance(eol_dt, datetime) else eol_dt
                days_until_eol = (eol_d - now_date).days
                if days_until_eol <= 0:
                    status = LifecycleStatus.EOL
                    severity = LifecycleSeverity.CRITICAL
                elif days_until_eol <= EXPIRING_THRESHOLD_DAYS:
                    status = LifecycleStatus.EXPIRING
                    severity = LifecycleSeverity.HIGH

        # Build upgrade recommendation
        upgrade_rec = None
        if status in (LifecycleStatus.EOL, LifecycleStatus.EXPIRING):
            if catalog_entry.current_lts_version:
                upgrade_rec = f"Upgrade to LTS version {catalog_entry.current_lts_version}"
            elif catalog_entry.current_version:
                upgrade_rec = f"Upgrade to current version {catalog_entry.current_version}"
            else:
                upgrade_rec = "Upgrade to a supported version"

        return LifecycleCheckResult(
            product_name=product_name,
            vendor=catalog_entry.vendor or vendor or "Unknown",
            installed_version=version,
            lifecycle_status=status,
            severity=severity,
            current_version=catalog_entry.current_version,
            lts_version=catalog_entry.current_lts_version,
            eol_date=version_entry.eol_date if version_entry else None,
            eos_date=version_entry.eos_date if version_entry else None,
            days_until_eol=days_until_eol,
            upgrade_recommendation=upgrade_rec,
        )

    def bulk_check(
        self, products: List[Dict[str, str]]
    ) -> List[LifecycleCheckResult]:
        """
        Check lifecycle status for multiple products.

        Args:
            products: List of dicts with keys: product_name, version, vendor (optional)

        Returns:
            List of LifecycleCheckResult
        """
        results = []
        for product in products:
            result = self.check_lifecycle_status(
                product_name=product.get("product_name", ""),
                version=product.get("version", ""),
                vendor=product.get("vendor"),
            )
            results.append(result)
        return results

    def get_eol_timeline(
        self, org_id: str, days_ahead: int = 90
    ) -> List[LifecycleCheckResult]:
        """
        Get products approaching EOL within the specified window.

        Scans InstalledProduct records for the org and checks each against
        the lifecycle catalog.

        Args:
            org_id: Organization ID
            days_ahead: Number of days to look ahead (default 90)

        Returns:
            List of products that are EOL or expiring within the window
        """
        from app.models.discovery import InstalledProduct, HostAsset

        # Get all installed products for the org
        installed = (
            self.db.query(InstalledProduct)
            .join(HostAsset, InstalledProduct.asset_id == HostAsset.id)
            .filter(HostAsset.org_id == org_id)
            .all()
        )

        at_risk = []
        for product in installed:
            result = self.check_lifecycle_status(
                product_name=product.product_name,
                version=product.version or "",
                vendor=product.vendor,
            )
            if result.lifecycle_status in (
                LifecycleStatus.EOL,
                LifecycleStatus.EXPIRING,
            ):
                at_risk.append(result)
            elif (
                result.days_until_eol is not None
                and result.days_until_eol <= days_ahead
            ):
                at_risk.append(result)

        # Sort by severity (CRITICAL first) then days until EOL
        at_risk.sort(
            key=lambda r: (
                0 if r.severity == LifecycleSeverity.CRITICAL else 1,
                r.days_until_eol if r.days_until_eol is not None else 9999,
            )
        )
        return at_risk

    def get_org_lifecycle_summary(self, org_id: str) -> Dict:
        """
        Get a summary of lifecycle health for an organization.

        Returns counts of products by lifecycle status.
        """
        from app.models.discovery import InstalledProduct, HostAsset

        installed = (
            self.db.query(InstalledProduct)
            .join(HostAsset, InstalledProduct.asset_id == HostAsset.id)
            .filter(HostAsset.org_id == org_id)
            .all()
        )

        summary = {
            "total_products": len(installed),
            "supported": 0,
            "expiring": 0,
            "eol": 0,
            "unknown": 0,
            "critical_products": [],
            "expiring_products": [],
        }

        for product in installed:
            result = self.check_lifecycle_status(
                product_name=product.product_name,
                version=product.version or "",
                vendor=product.vendor,
            )
            status_key = result.lifecycle_status.value
            if status_key in summary:
                summary[status_key] += 1

            if result.lifecycle_status == LifecycleStatus.EOL:
                summary["critical_products"].append({
                    "product": result.product_name,
                    "version": result.installed_version,
                    "eol_date": str(result.eol_date) if result.eol_date else None,
                    "recommendation": result.upgrade_recommendation,
                })
            elif result.lifecycle_status == LifecycleStatus.EXPIRING:
                summary["expiring_products"].append({
                    "product": result.product_name,
                    "version": result.installed_version,
                    "days_until_eol": result.days_until_eol,
                    "recommendation": result.upgrade_recommendation,
                })

        return summary
