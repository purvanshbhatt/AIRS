"""
CRUD service for Technology Discovery.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.discovery import (
    TechnologyInventory,
    HostAsset,
    InstalledProduct,
    EvidenceSource
)

class TechnologyDiscoveryService:
    """Service layer for managing Technology Discovery models."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def get_latest_inventory(self) -> Optional[TechnologyInventory]:
        """Gets the most recently discovered inventory for the organization."""
        return (
            self.db.query(TechnologyInventory)
            .filter(TechnologyInventory.org_id == self.org_id)
            .order_by(TechnologyInventory.last_discovered_at.desc())
            .first()
        )

    def create_inventory(self, source: str, confidence_score: float = 1.0) -> TechnologyInventory:
        """Creates a new inventory snapshot."""
        inv = TechnologyInventory(
            org_id=self.org_id,
            discovery_source=source,
            confidence_score=confidence_score
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def add_asset(
        self,
        inventory_id: str,
        asset_type: str,
        hostname: Optional[str] = None,
        operating_system: Optional[str] = None,
        ip_address: Optional[str] = None,
        cloud_provider: Optional[str] = None
    ) -> HostAsset:
        asset = HostAsset(
            org_id=self.org_id,
            inventory_id=inventory_id,
            asset_type=asset_type,
            hostname=hostname,
            operating_system=operating_system,
            ip_address=ip_address,
            cloud_provider=cloud_provider
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def add_installed_product(
        self,
        asset_id: str,
        product_name: str,
        vendor: Optional[str] = None,
        version: Optional[str] = None,
        installation_source: Optional[str] = None,
        eol_status: Optional[str] = None
    ) -> InstalledProduct:
        product = InstalledProduct(
            asset_id=asset_id,
            product_name=product_name,
            vendor=vendor,
            version=version,
            installation_source=installation_source,
            eol_status=eol_status
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def add_evidence_source(
        self,
        product_id: str,
        source_type: str,
        connector_name: Optional[str] = None,
        raw_evidence_hash: Optional[str] = None
    ) -> EvidenceSource:
        evidence = EvidenceSource(
            product_id=product_id,
            source_type=source_type,
            connector_name=connector_name,
            raw_evidence_hash=raw_evidence_hash
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence


# ---------------------------------------------------------------------------
# Shared discovery helpers (demo gating, per-source status, async bridging)
# ---------------------------------------------------------------------------

import asyncio
import threading
from dataclasses import dataclass, field
from typing import Any, Dict


class DiscoveryStatus:
    """Per-source outcome of a discovery run. Persisted in the inventory summary."""
    OK = "ok"
    PARTIAL = "partial"            # some API calls denied, rows still real
    NOT_CONNECTED = "not_connected"  # no connector registered for this source
    AUTH_FAILED = "auth_failed"
    PERMISSION_MISSING = "permission_missing"
    ERROR = "error"
    DEMO = "demo"                  # synthetic rows, demo org only
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class SourceDiscoveryResult:
    """What a single discovery source did. Never contains fabricated rows for real orgs."""
    source: str
    status: str = DiscoveryStatus.NOT_CONNECTED
    assets_created: int = 0
    products_created: int = 0
    connectors_used: List[str] = field(default_factory=list)
    denied_apis: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    detail: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        parts = [f"{self.source}={self.status}"]
        if self.assets_created:
            parts.append(f"assets={self.assets_created}")
        if self.denied_apis:
            parts.append("denied=" + "|".join(self.denied_apis))
        return ";".join(parts)


def is_demo_org(db: Session, org_id: str) -> bool:
    """True only for demo tenants. Real (pilot/production) orgs never get synthetic data.

    Demo is established by ``org_mode == demo`` via PilotService, or by the
    ``demo-`` org id prefix used by the sandbox tenants.
    """
    if org_id and str(org_id).startswith("demo-"):
        return True
    from app.services.clinic_engine.v2.pilot import PilotService
    try:
        return PilotService(db).is_demo(org_id)
    except Exception:
        # Unknown mode is treated as real (PilotService invariant).
        return False


def run_coroutine_sync(coro):
    """Run a coroutine from sync code, even when an event loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Dict[str, Any] = {}

    def _runner():
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:  # propagate to caller thread
            result["error"] = exc

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")
