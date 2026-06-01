"""
Intelligence Service — fetches software version advisories and detects environmental drift.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.models.drift_event import DriftEvent
from app.models.software_catalog import SoftwareCatalog
from app.models.telemetry_event import TelemetryEvent
from app.models.tech_stack import TechStackItem

logger = logging.getLogger("airs.services.intelligence")


class IntelligenceService:
    """Service to ingest global version intelligence and run version drift audits."""

    # Default common enterprise repositories to monitor
    MONITORED_REPOS = {
        "python": "python/cpython",
        "kubernetes": "kubernetes/kubernetes",
        "postgresql": "postgres/postgres",
    }

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    # ------------------------------------------------------------------
    # Intelligence Fetchers
    # ------------------------------------------------------------------

    async def fetch_github_latest_release(self, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch latest release tag name, url, and date from GitHub Releases API."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        headers = {"User-Agent": "ResilAI-Intelligence-Client/1.0"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "tag_name": data.get("tag_name"),
                        "html_url": data.get("html_url"),
                        "published_at": data.get("published_at"),
                    }
                logger.warning("GitHub Releases API returned status %d for %s", resp.status_code, repo)
        except Exception as exc:
            logger.error("Error fetching GitHub Releases for %s: %s", repo, exc)
        return None

    async def fetch_cisa_kev_advisory(self, product: str) -> Optional[Dict[str, Any]]:
        """Scan CISA KEV JSON feed for known exploited vulnerabilities of a product."""
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    vulns = data.get("vulnerabilities", [])
                    # Find first vulnerability matching the product name
                    for vuln in vulns:
                        vuln_product = vuln.get("product", "").lower()
                        if product.lower() in vuln_product:
                            return {
                                "cve_id": vuln.get("cveID"),
                                "short_description": vuln.get("shortDescription"),
                                "advisory_url": vuln.get("notes"),
                                "date_added": vuln.get("dateAdded"),
                            }
        except Exception as exc:
            logger.error("Error fetching CISA KEV advisory for %s: %s", product, exc)
        return None

    async def fetch_nvd_severity(self, product: str) -> Optional[str]:
        """Fetch recent severity score from NVD API. Strict try-except isolations to avoid failures."""
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={product}"
        headers = {"User-Agent": "ResilAI-Intelligence-Client/1.0"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    if vulnerabilities:
                        # Grab the first CVE severity metrics
                        cve_item = vulnerabilities[0].get("cve", {})
                        metrics = cve_item.get("metrics", {})
                        # Try CVSS v3.1 first
                        cvss_v31 = metrics.get("cvssMetricV31", [])
                        if cvss_v31:
                            return cvss_v31[0].get("cvssData", {}).get("baseSeverity", "medium").lower()
                        # Fallback to CVSS v3.0
                        cvss_v30 = metrics.get("cvssMetricV30", [])
                        if cvss_v30:
                            return cvss_v30[0].get("cvssData", {}).get("baseSeverity", "medium").lower()
                        # Fallback to CVSS v2
                        cvss_v2 = metrics.get("cvssMetricV2", [])
                        if cvss_v2:
                            return cvss_v2[0].get("baseSeverity", "medium").lower()
        except Exception as exc:
            # Strict isolation: logging only, do not propagate failure
            logger.warning("NVD API fetch failed for %s (isolated): %s", product, exc)
        return None

    # ------------------------------------------------------------------
    # Version Comparison Engine
    # ------------------------------------------------------------------

    @staticmethod
    def is_version_older(current: str, latest: str) -> bool:
        """Check if current version is older than latest available version."""
        if not current or not latest:
            return False

        def clean_version(v: str) -> List[int]:
            # Strip leading 'v' or 'V'
            v_clean = re.sub(r'^[vV]', '', v.strip())
            # Capture only the starting numeric parts
            match = re.match(r'^(\d+(?:\.\d+)*)', v_clean)
            if match:
                parts = match.group(1).split('.')
                return [int(x) for x in parts]
            return []

        try:
            curr_parts = clean_version(current)
            late_parts = clean_version(latest)
            for c, l in zip(curr_parts, late_parts):
                if c < l:
                    return True
                elif c > l:
                    return False
            return len(curr_parts) < len(late_parts)
        except Exception as exc:
            logger.debug("Failed parsing version compare for %s and %s: %s", current, latest, exc)
            return current.strip() != latest.strip()

    # ------------------------------------------------------------------
    # Drift Core Logic
    # ------------------------------------------------------------------

    async def sync_intelligence_and_detect_drift(self) -> int:
        """Pull software versions, run diff engine, update database, and trigger alerts."""
        logger.info("Starting intelligence sync and version drift audit for org: %s", self.org_id)
        
        # 1. Establish client current versions
        # Look for telemetry events from the Microsoft (Azure Security Center) connector
        asc_events = (
            self.db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.org_id == self.org_id,
                TelemetryEvent.source_system == "azure_security_center",
                TelemetryEvent.event_type == "azure_security_center.software_inventory",
            )
            .all()
        )

        current_inventory: Dict[str, Dict[str, str]] = {}
        for ev in asc_events:
            payload = ev.get_payload() if hasattr(ev, "get_payload") else ev.payload
            if isinstance(payload, str):
                import json
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            if payload:
                prod = payload.get("product", "").lower()
                if prod:
                    current_inventory[prod] = {
                        "vendor": payload.get("vendor", ""),
                        "version": payload.get("version", ""),
                    }

        # Fallback to TechStackItems if Microsoft Connector event telemetry is missing
        if not current_inventory:
            tech_items = (
                self.db.query(TechStackItem)
                .filter(TechStackItem.org_id == self.org_id)
                .all()
            )
            for item in tech_items:
                prod = item.component_name.lower()
                current_inventory[prod] = {
                    "vendor": "",
                    "version": item.version or "0.0.0",
                }

        if not current_inventory:
            logger.info("No current software inventory found for org %s. Skipping drift audit.", self.org_id)
            return 0

        drift_count = 0

        # 2. Iterate monitored systems
        for prod, repo in self.MONITORED_REPOS.items():
            inv = current_inventory.get(prod)
            if not inv:
                continue

            current_ver = inv["version"]
            vendor = inv["vendor"]

            # Fetch latest version from GitHub Releases
            release_info = await self.fetch_github_latest_release(repo)
            if not release_info:
                continue

            latest_ver = release_info["tag_name"]
            release_date = release_info["published_at"]
            advisory_url = release_info["html_url"]

            # Check if client's current version is drifted (older)
            if self.is_version_older(current_ver, latest_ver):
                # Fetch security metadata: CISA KEV and NVD
                severity = "medium"  # default severity
                cisa_advisory = await self.fetch_cisa_kev_advisory(prod)
                if cisa_advisory:
                    severity = "critical"
                    advisory_url = cisa_advisory["advisory_url"] or advisory_url

                nvd_severity = await self.fetch_nvd_severity(prod)
                if nvd_severity:
                    severity = nvd_severity

                # Create/Update Software Catalog Entry
                catalog_entry = (
                    self.db.query(SoftwareCatalog)
                    .filter(
                        SoftwareCatalog.org_id == self.org_id,
                        SoftwareCatalog.product == prod,
                    )
                    .first()
                )

                if not catalog_entry:
                    catalog_entry = SoftwareCatalog(
                        org_id=self.org_id,
                        product=prod,
                    )
                    self.db.add(catalog_entry)

                catalog_entry.vendor = vendor or catalog_entry.vendor or "Unknown"
                catalog_entry.current_version = current_ver
                catalog_entry.latest_version = latest_ver
                catalog_entry.latest_release_date = release_date
                catalog_entry.advisory_url = advisory_url
                catalog_entry.source = "github_releases"
                catalog_entry.severity = severity

                # Trigger Drift Event alert if not already logged
                event_title = f"Software Version Drift: {prod}"
                existing_event = (
                    self.db.query(DriftEvent)
                    .filter(
                        DriftEvent.org_id == self.org_id,
                        DriftEvent.signal_type == "software_drift",
                        DriftEvent.title == event_title,
                        DriftEvent.acknowledged == False,
                    )
                    .first()
                )

                if not existing_event:
                    drift_event = DriftEvent(
                        org_id=self.org_id,
                        signal_type="software_drift",
                        severity=severity,
                        title=event_title,
                        description=(
                            f"Product '{prod}' is running version {current_ver}, "
                            f"but the latest version available is {latest_ver}. "
                            f"Update recommended to resolve environment drift."
                        ),
                        delta=1.0,  # represent version delta flag
                        metadata_extra={
                            "product": prod,
                            "current_version": current_ver,
                            "latest_version": latest_ver,
                            "advisory_url": advisory_url,
                        },
                    )
                    self.db.add(drift_event)

                drift_count += 1

        if drift_count > 0:
            self.db.commit()
            logger.info("Intelligence sync complete. Detected %d drifted packages.", drift_count)

        return drift_count

    def get_latest_versions(self) -> List[SoftwareCatalog]:
        """Retrieve latest version catalog for the organization."""
        return (
            self.db.query(SoftwareCatalog)
            .filter(SoftwareCatalog.org_id == self.org_id)
            .order_by(SoftwareCatalog.product.asc())
            .all()
        )
