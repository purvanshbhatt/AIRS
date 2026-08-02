"""
AIRS CVE Enrichment Engine.

Maps normalized software and versions to known vulnerabilities using NVD and CISA KEV data.

In staging, this returns deterministic mock data for specific known combinations
(e.g., Python 3.8, PostgreSQL 11) to simulate the enrichment process without
hitting live API rate limits.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.cve")


@dataclass
class VulnerabilitySignal:
    """A single vulnerability mapped to a software product."""
    cve_id: str
    severity: str  # critical, high, medium, low
    cvss_score: float
    description: str
    is_kev: bool   # True if present in CISA Known Exploited Vulnerabilities catalog


@dataclass
class EnrichmentResult:
    """The result of enriching a specific software product/version."""
    vendor: str
    product_name: str
    version: str
    critical_cves: int = 0
    high_cves: int = 0
    kev_count: int = 0
    vulnerabilities: List[VulnerabilitySignal] = field(default_factory=list)
    evidence_hash: str = ""
    
    def compute_evidence_hash(self) -> str:
        """Compute SHA-256 hash of the enrichment result for the evidence log."""
        payload = {
            "vendor": self.vendor,
            "product": self.product_name,
            "version": self.version,
            "cves": [v.cve_id for v in self.vulnerabilities],
            "kev_count": self.kev_count
        }
        payload_str = json.dumps(payload, sort_keys=True)
        self.evidence_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        return self.evidence_hash


class CVEEnrichmentService:
    """
    Enriches software inventory with CVE data.
    
    NOTE: In Sprint 1, we DO NOT create findings automatically or alter scores.
    We only map the data, count the severities, and generate the evidence trace.
    """

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        
        # Staging mock database for deterministic testing
        import os
        cache_path = os.path.join(os.path.dirname(__file__), "nvd_staging_cache.json")
        try:
            with open(cache_path, "r") as f:
                raw_cache = json.load(f)
            
            self._staging_db = {}
            for key, vulns in raw_cache.items():
                parts = key.split("|")
                if len(parts) == 3:
                    vendor, product, version = parts
                    self._staging_db[(vendor, product, version)] = [
                        VulnerabilitySignal(**v) for v in vulns
                    ]
        except Exception as e:
            logger.error(f"Failed to load staging CVE cache: {e}")
            self._staging_db = {}

    async def enrich_software(self, vendor: str, product_name: str, version: str) -> EnrichmentResult:
        """
        Enrich a single software product with CVE data.
        
        In production, this would query the local CVECatalog (synced from NVD/KEV).
        For staging, we use the deterministic mock DB.
        """
        logger.info(f"Enriching {vendor} {product_name} {version}")
        
        result = EnrichmentResult(
            vendor=vendor,
            product_name=product_name,
            version=version
        )
        
        # Mock lookup
        key = (vendor, product_name, version)
        vulns = self._staging_db.get(key, [])
        
        # If specific version isn't found, try matching major version
        if not vulns and version:
            major_version = version.split(".")[0]
            key_major = (vendor, product_name, major_version)
            vulns = self._staging_db.get(key_major, [])
            
        result.vulnerabilities = vulns
        
        # Aggregate counts
        for v in vulns:
            if v.severity.lower() == "critical":
                result.critical_cves += 1
            elif v.severity.lower() == "high":
                result.high_cves += 1
                
            if v.is_kev:
                result.kev_count += 1
                
        # Generate tamper-evident hash
        result.compute_evidence_hash()
        
        # Log evidence (In a future sprint, this writes to the Evidence store)
        logger.debug(f"Evidence Hash for {product_name} {version}: {result.evidence_hash}")
        
        return result
        
    async def bulk_enrich(self, inventory_items: List[Dict[str, str]]) -> List[EnrichmentResult]:
        """
        Enrich a batch of normalized software records.
        
        Args:
            inventory_items: List of dicts with 'vendor', 'product', 'version' keys.
        """
        results = []
        for item in inventory_items:
            res = await self.enrich_software(
                vendor=item.get("vendor", ""),
                product_name=item.get("product", ""),
                version=item.get("version", "")
            )
            results.append(res)
        return results
