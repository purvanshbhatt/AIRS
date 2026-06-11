"""
Deterministic Tech Stack Lifecycle Analysis Engine.
"""

import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from app.models.lifecycle_catalog import GlobalSoftwareCatalog, SoftwareVersion

class LifecycleAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_lifecycle(self, product_name: str, version: str) -> Dict[str, Any]:
        """
        Deterministically evaluates the lifecycle status of a specific product version.
        
        Returns a dictionary with:
        - status: 'Supported', 'Expiring', or 'EOL'
        - severity: 'critical' (EOL), 'high' (Expiring), or 'low' (Supported)
        - is_known: bool
        """
        # Attempt to find the product in the global catalog
        catalog = (
            self.db.query(GlobalSoftwareCatalog)
            .filter(GlobalSoftwareCatalog.product_name == product_name)
            .first()
        )

        # Default fallback if unknown
        default_result = {
            "is_known": False,
            "status": "Supported",  # Assume supported if unknown to avoid false positives
            "severity": "low",
            "days_until_eol": None,
            "eol_date": None,
            "latest_supported": catalog.current_lts_version if catalog else None,
        }

        if not catalog:
            return default_result

        # Find the specific version or best match
        # Version string matching can be complex; we look for exact prefix matches.
        # For simplicity in this engine, we do a basic prefix match.
        version_entry = None
        for v in catalog.versions:
            if version.startswith(v.version_name):
                version_entry = v
                break

        if not version_entry:
            default_result["is_known"] = True
            return default_result

        today = datetime.date.today()
        
        # 1. Check strict EOL
        if version_entry.support_status.upper() == "EOL":
            status = "EOL"
            severity = "critical"
        elif version_entry.eol_date and version_entry.eol_date <= today:
            status = "EOL"
            severity = "critical"
        # 2. Check Expiring (within 365 days of EOL, or explicitly marked Expiring/EOS)
        elif version_entry.support_status.upper() == "EXPIRING":
            status = "Expiring"
            severity = "high"
        elif version_entry.eos_date and version_entry.eos_date <= today:
            status = "Expiring"
            severity = "high"
        elif version_entry.eol_date and (version_entry.eol_date - today).days <= 365:
            status = "Expiring"
            severity = "high"
        # 3. Otherwise Supported
        else:
            status = "Supported"
            severity = "low"

        days_until_eol = None
        if version_entry.eol_date:
            days_until_eol = (version_entry.eol_date - today).days

        return {
            "is_known": True,
            "status": status,
            "severity": severity,
            "days_until_eol": days_until_eol,
            "eol_date": version_entry.eol_date.isoformat() if version_entry.eol_date else None,
            "latest_supported": catalog.current_lts_version,
        }
