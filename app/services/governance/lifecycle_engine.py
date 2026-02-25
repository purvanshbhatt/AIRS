"""
Lifecycle Intelligence Engine — static version lifecycle lookups.

Loads lifecycle_config.json and provides governance-only intelligence
about technology version status and EOL dates.

No live scraping. No CVE integration.
"""

import json
import logging
import os
from datetime import datetime, date
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Load lifecycle config once at module level
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "core", "lifecycle_config.json")
_LIFECYCLE_DATA: Dict = {}


def _load_config() -> Dict:
    """Load and cache the lifecycle configuration."""
    global _LIFECYCLE_DATA
    if _LIFECYCLE_DATA:
        return _LIFECYCLE_DATA
    try:
        config_path = os.path.normpath(_CONFIG_PATH)
        with open(config_path, "r") as f:
            _LIFECYCLE_DATA = json.load(f)
        logger.info(f"Lifecycle config loaded: {len(_LIFECYCLE_DATA) - 1} technologies")
    except FileNotFoundError:
        logger.warning("lifecycle_config.json not found — lifecycle lookups disabled")
        _LIFECYCLE_DATA = {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid lifecycle_config.json: {e}")
        _LIFECYCLE_DATA = {}
    return _LIFECYCLE_DATA


def get_version_status(technology: str, version: str) -> Optional[Dict]:
    """
    Look up the lifecycle status of a technology version.

    Args:
        technology: Technology name (case-insensitive, e.g. "python", "node")
        version: Version string (e.g. "3.8", "18")

    Returns:
        Dict with 'status' and 'eol_date', or None if not found.
    """
    config = _load_config()
    tech_key = technology.lower().strip()

    # Normalize common aliases
    aliases = {
        "nodejs": "node",
        "node.js": "node",
        "postgres": "postgresql",
        "pg": "postgresql",
        ".net": "dotnet",
        "dotnet core": "dotnet",
        "k8s": "kubernetes",
    }
    tech_key = aliases.get(tech_key, tech_key)

    tech_data = config.get(tech_key)
    if not tech_data:
        return None

    # Try exact version match
    version_data = tech_data.get(version)
    if version_data:
        return version_data

    # Try major version only (e.g., "3.11.5" → "3.11")
    parts = version.split(".")
    if len(parts) >= 2:
        major_minor = f"{parts[0]}.{parts[1]}"
        version_data = tech_data.get(major_minor)
        if version_data:
            return version_data

    # Try major only (e.g., "18.17.0" → "18")
    if len(parts) >= 1:
        version_data = tech_data.get(parts[0])
        if version_data:
            return version_data

    return None


def is_eol(technology: str, version: str) -> bool:
    """Check if a technology version has reached end-of-life."""
    info = get_version_status(technology, version)
    if not info:
        return False
    return info.get("status") == "eol"


def get_eol_date(technology: str, version: str) -> Optional[str]:
    """Get the EOL date string for a technology version."""
    info = get_version_status(technology, version)
    if not info:
        return None
    return info.get("eol_date")


def days_until_eol(technology: str, version: str) -> Optional[int]:
    """
    Calculate days until EOL for a technology version.

    Returns:
        Positive int = days remaining.
        Negative int = days past EOL.
        None = not found in config.
    """
    eol_str = get_eol_date(technology, version)
    if not eol_str:
        return None
    try:
        eol_date = datetime.strptime(eol_str, "%Y-%m-%d").date()
        return (eol_date - date.today()).days
    except ValueError:
        return None


def get_supported_technologies() -> List[str]:
    """Return list of technologies in the lifecycle config."""
    config = _load_config()
    return [k for k in config.keys() if k != "_meta"]


def get_technology_versions(technology: str) -> Optional[Dict]:
    """Return all version data for a technology."""
    config = _load_config()
    tech_key = technology.lower().strip()
    aliases = {
        "nodejs": "node", "node.js": "node",
        "postgres": "postgresql", "pg": "postgresql",
        ".net": "dotnet", "k8s": "kubernetes",
    }
    tech_key = aliases.get(tech_key, tech_key)
    data = config.get(tech_key)
    if not data or tech_key == "_meta":
        return None
    return data


def reload_config() -> None:
    """Force reload of lifecycle config (for testing)."""
    global _LIFECYCLE_DATA
    _LIFECYCLE_DATA = {}
    _load_config()
