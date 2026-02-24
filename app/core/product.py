"""Product metadata helpers."""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache
from typing import Dict

from app.core.config import settings


@lru_cache(maxsize=1)
def _resolve_git_sha() -> str | None:
    """Resolve a short git SHA from env or local repository, if available."""
    env_sha = os.getenv("GIT_SHA") or os.getenv("COMMIT_SHA") or settings.APP_VERSION
    if env_sha:
        return str(env_sha)[:12]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        sha = result.stdout.strip()
        return sha or None
    except Exception:
        return None


def get_product_info() -> Dict[str, str | None]:
    """Return product metadata for API responses."""
    return {
        "name": settings.APP_NAME,
        "version": _resolve_git_sha(),
    }

