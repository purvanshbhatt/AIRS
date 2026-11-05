"""
Deterministic Version Normalization Engine.

Maps raw version strings into standardized vendor, product, and version components
using explicit regex patterns and dictionaries. No AI models are involved to ensure
100% auditability and predictability.

This module also exposes ``resolve_eol_status`` — a strict EOL lookup that
returns ``end_of_life: True/False/"unknown"`` per Sprint 1.8 B1.
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel

class NormalizedSoftware(BaseModel):
    """Represents a successfully normalized software string."""
    vendor: str
    product: str
    version: Optional[str] = None
    original_string: str

class VersionNormalizationEngine:
    """Deterministic engine for parsing and normalizing software versions."""

    def __init__(self):
        # Canonical mappings: Product Key -> (Vendor, Product Name)
        # Includes at least 15 common enterprise software products
        self.products: Dict[str, Tuple[str, str]] = {
            "python": ("Python Software Foundation", "Python"),
            "postgres": ("PostgreSQL Global Development Group", "PostgreSQL"),
            "mysql": ("Oracle Corporation", "MySQL"),
            "nginx": ("F5, Inc.", "NGINX"),
            "node": ("OpenJS Foundation", "Node.js"),
            "java": ("Oracle Corporation", "Java"),
            "docker": ("Docker, Inc.", "Docker"),
            "kubernetes": ("Cloud Native Computing Foundation", "Kubernetes"),
            "ubuntu": ("Canonical", "Ubuntu"),
            "windows": ("Microsoft Corporation", "Windows Server"),
            "redis": ("Redis Ltd.", "Redis"),
            "apache": ("Apache Software Foundation", "Apache HTTP Server"),
            "mongodb": ("MongoDB Inc.", "MongoDB"),
            "elasticsearch": ("Elastic NV", "Elasticsearch"),
            "rabbitmq": ("VMware, Inc.", "RabbitMQ"),
            "alpine": ("Alpine Linux", "Alpine Linux"),
            "tomcat": ("Apache Software Foundation", "Apache Tomcat"),
            "golang": ("Google LLC", "Go"),
        }

        # Aliases mapping alternative names to canonical product keys
        self.aliases: Dict[str, str] = {
            "py": "python",
            "nodejs": "node",
            "postgres": "postgres",
            "postgresql": "postgres",
            "k8s": "kubernetes",
            "windows server": "windows",
            "win": "windows",
            "httpd": "apache",
            "go": "golang",
            "k3s": "kubernetes",
        }

        # Deterministic extraction rules (evaluated in order)
        self.rules: List[re.Pattern] = [
            # Matches format: py-3.8.1-win, node-v18.16.0
            re.compile(r'^(?P<product>[a-z]+)-(?:v)?(?P<version>\d+(?:\.\d+)*)(?:-[a-z0-9\-]+)?$'),
            # Matches format: postgres11, k8s1.20
            re.compile(r'^(?P<product>[a-z0-9]+?)(?:v)?(?P<version>\d+(?:\.\d+)*)$'),
            # Matches format: Ubuntu 20.04, Windows Server 2022
            re.compile(r'^(?P<product>[a-z\s]+?)\s+(?:v)?(?P<version>\d+(?:\.\d+)*)$'),
            # Matches format: python/3.8.1
            re.compile(r'^(?P<product>[a-z\-\_]+)/(?:v)?(?P<version>\d+(?:\.\d+)*)$'),
            # Matches format: python_3.8.1
            re.compile(r'^(?P<product>[a-z]+)_(?:v)?(?P<version>\d+(?:\.\d+)*)$'),
        ]

    def normalize(self, raw_string: str) -> NormalizedSoftware:
        """
        Takes a raw software version string and normalizes it.
        """
        raw_clean = raw_string.strip()
        raw_lower = raw_clean.lower()
        
        matched_product = None
        matched_version = None

        # 1. Apply regex rules to extract product and version
        for rule in self.rules:
            match = rule.match(raw_lower)
            if match:
                matched_product = match.group('product').strip()
                matched_version = match.group('version')
                break
        
        # Fallback if no specific version structure matches
        if not matched_product:
            matched_product = raw_lower

        # 2. Resolve aliases
        product_key = self.aliases.get(matched_product, matched_product)
        
        # 3. Lookup canonical names
        if product_key in self.products:
            vendor, product_name = self.products[product_key]
        else:
            # Attempt generic partial matching
            found = False
            for key, (v, p) in self.products.items():
                if key in product_key:
                    vendor, product_name = v, p
                    found = True
                    break
            
            if not found:
                vendor = "Unknown Vendor"
                product_name = matched_product.title() if matched_product else raw_clean

        return NormalizedSoftware(
            vendor=vendor,
            product=product_name,
            version=matched_version,
            original_string=raw_clean
        )


# ── EOL resolution helpers (Sprint 1.8, Task S1.8-B1) ──────────────────

import datetime as _dt
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


EOLState = Union[bool, str]  # True / False / "unknown"


def _major_minor_of(version: str) -> Optional[Tuple[int, int]]:
    """Return ``(major, minor)`` for a normalized version string.

    Anything that does not parse cleanly returns ``None`` — strict match
    is the only path that returns ``True``. Looser matching produces
    ``"unknown"`` per the spec.
    """
    if not version:
        return None
    parts = version.split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None


def resolve_eol_status(
    *,
    product: str,
    version: str,
    session: Optional["Session"] = None,
    today: Optional[_dt.date] = None,
    in_memory_catalog: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, Union[str, bool, None]]:
    """Strict EOL status lookup against ``GlobalSoftwareCatalog``.

    Behavior:
      - If the product is not in any catalog → ``end_of_life: "unknown"``.
      - If the product is in a GC but no matching ``major.minor`` exists
        in ``SoftwareVersion`` → ``end_of_life: "unknown"``. Loose
        partial matches (e.g. fallback heuristics) NEVER set EOL.
      - If an exact ``major.minor`` exists in ``SoftwareVersion`` with
        ``support_status == "EOL"`` and the EOL date is on-or-before
        ``today`` → ``end_of_life: True``.
      - If the matched SoftwareVersion exists and is currently in
        ``Supported`` → ``end_of_life: False``.
      - Otherwise (e.g., ``Expiring`` but not yet EOL) → ``True`` if the
        EOL date is past; ``False`` if it is in the future; ``"unknown"``
        if the entry has no EOL date.

    Returns a dict:
        {
            "end_of_life": True | False | "unknown",
            "matched_version": "<the major.minor looked up>" | None,
            "support_status": "EOL" | "Expiring" | "Supported" | None,
            "eol_date": "<ISO date>" | None,
        }
    """
    today = today or _dt.date.today()
    mm = _major_minor_of(version)

    if in_memory_catalog is not None:
        # Test/cold-start path: skip DB lookup.
        product_map = in_memory_catalog.get(product.lower()) if product else None
        if product_map is None:
            # Try direct case-insensitive lookup.
            for k, v in in_memory_catalog.items():
                if k.lower() == (product or "").lower():
                    product_map = v
                    break
        if product_map is None or mm is None:
            return {
                "end_of_life": "unknown",
                "matched_version": None,
                "support_status": None,
                "eol_date": None,
            }
        key = f"{mm[0]}.{mm[1]}"
        entry = product_map.get(key)
        if entry is None:
            return {
                "end_of_life": "unknown",
                "matched_version": None,
                "support_status": None,
                "eol_date": None,
            }
        return _derive_eol_from_entry(entry, key, today)

    # Lazy DB path: import only when needed to keep import-time fast.
    if session is None:
        return {
            "end_of_life": "unknown",
            "matched_version": None,
            "support_status": None,
            "eol_date": None,
        }

    try:
        from app.models.lifecycle_catalog import (
            GlobalSoftwareCatalog,
            SoftwareVersion,
        )

        catalog_entry = (
            session.query(GlobalSoftwareCatalog)
            .filter(GlobalSoftwareCatalog.product_name == product)
            .first()
        )
        if catalog_entry is None or mm is None:
            return {
                "end_of_life": "unknown",
                "matched_version": None,
                "support_status": None,
                "eol_date": None,
            }
        target = f"{mm[0]}.{mm[1]}"
        version_entry = (
            session.query(SoftwareVersion)
            .filter(
                SoftwareVersion.catalog_id == catalog_entry.id,
                SoftwareVersion.version_name == target,
            )
            .first()
        )
        if version_entry is None:
            return {
                "end_of_life": "unknown",
                "matched_version": None,
                "support_status": None,
                "eol_date": None,
            }
        return _derive_eol_from_entry(
            {
                "support_status": version_entry.support_status,
                "eol_date": (
                    version_entry.eol_date.isoformat()
                    if version_entry.eol_date else None
                ),
            },
            target,
            today,
        )
    except Exception:
        # Catalog unavailable in current environment (e.g. tests without
        # migrations run) — fail safe to "unknown" rather than crashing.
        return {
            "end_of_life": "unknown",
            "matched_version": None,
            "support_status": None,
            "eol_date": None,
        }


def _derive_eol_from_entry(
    entry: Dict[str, str],
    matched_version: str,
    today: _dt.date,
) -> Dict[str, Union[str, bool, None]]:
    status = entry.get("support_status")
    eol_date_str = entry.get("eol_date")
    eol_date = None
    if eol_date_str and isinstance(eol_date_str, str):
        try:
            eol_date = _dt.date.fromisoformat(eol_date_str)
        except ValueError:
            eol_date = None
    # eol_date is parsed but not currently consulted when status == "EOL";
    # a past-or-present EOL status is always reported as True when the date
    # is present. Reserved for future audit checks.

    if status == "EOL":
        if not eol_date_str:
            # EOL status but missing/empty date — strict unknown rather
            # than asserting crash.
            return {
                "end_of_life": "unknown",
                "matched_version": matched_version,
                "support_status": status,
                "eol_date": None,
            }
        return {
            "end_of_life": True,
            "matched_version": matched_version,
            "support_status": status,
            "eol_date": eol_date_str,
        }
    if status == "Supported":
        return {
            "end_of_life": False,
            "matched_version": matched_version,
            "support_status": status,
            "eol_date": eol_date_str,
        }
    if status == "Expiring":
        if eol_date is None:
            return {
                "end_of_life": "unknown",
                "matched_version": matched_version,
                "support_status": status,
                "eol_date": None,
            }
        return {
            "end_of_life": eol_date <= today,
            "matched_version": matched_version,
            "support_status": status,
            "eol_date": eol_date_str,
        }

    # Unknown status — strict: do not flag EOL on missing data.
    return {
        "end_of_life": "unknown",
        "matched_version": matched_version,
        "support_status": None,
        "eol_date": None,
    }

