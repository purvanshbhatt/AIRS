"""
Daily vulnerability-intelligence refresh (called by ``app.tasks.scheduler``).

Re-queries the public feeds for the software each organization runs so a
newly published CVE or a newly passed end-of-life date shows up without
anyone pressing refresh. Bounded per run; anything left over is picked up
by the next run or the next page load. Does not touch the readiness score.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.vuln_intel.jobs")

DEMO_ORG_IDS = ("demo-northstar-health", "demo-northstar-cole")
MAX_ORGS_PER_RUN = 25
ORG_BUDGET_SECONDS = 20.0
ORG_MAX_LOOKUPS = 200
REFRESH_OLDER_THAN = timedelta(hours=20)
NVD_WINDOW_PAUSE_SECONDS = 31.0     # NVD's rolling rate-limit window, plus a second
NVD_WAIT_BUDGET_SECONDS = 600.0     # total time one run may spend waiting for NVD
MAX_PASSES_PER_ORG = 4


def orgs_with_inventory(db: Session) -> List[str]:
    from app.models.discovered_asset import DiscoveredAsset
    from app.models.discovery import TechnologyInventory
    from app.models.tech_stack import TechStackItem
    from app.models.vuln_intel import WebAsset

    org_ids = set()
    for model in (TechnologyInventory, DiscoveredAsset, TechStackItem, WebAsset):
        try:
            org_ids.update(row[0] for row in db.query(model.org_id).distinct().all() if row[0])
        except Exception as exc:
            db.rollback()
            logger.debug("Inventory scan of %s failed: %s", model.__tablename__, exc)
    return sorted(o for o in org_ids if not str(o).startswith("demo-"))


def run_daily_refresh(
    db: Optional[Session] = None,
    clients: Any = None,
    max_orgs: int = MAX_ORGS_PER_RUN,
    now: Optional[datetime] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Dict[str, int]:
    """Refresh intelligence for demo stacks and for up to ``max_orgs`` organizations."""
    from app.services.discovery.discovery import is_demo_org
    from app.services.vuln_intel.service import build_summary, run_intel

    own_session = db is None
    if own_session:
        from app.db.database import SessionLocal
        db = SessionLocal()
    now = now or datetime.now(timezone.utc)
    totals = {"orgs": 0, "looked_up": 0, "queued": 0, "vulnerable_items": 0,
              "confirmed_advisories": 0, "failed": 0, "skipped": 0}
    waited = 0.0
    try:
        # Demo stacks share cache keys with real organizations: warm them first.
        for demo_id in DEMO_ORG_IDS:
            try:
                result, _ = run_intel(db, demo_id, True, clients=clients, max_age=REFRESH_OLDER_THAN,
                                      budget_seconds=ORG_BUDGET_SECONDS, max_lookups=ORG_MAX_LOOKUPS)
                totals["looked_up"] += result.looked_up
            except Exception as exc:
                db.rollback()
                logger.warning("Demo intel warm-up failed for %s: %s", demo_id, exc)

        org_ids = orgs_with_inventory(db)
        if len(org_ids) > max_orgs:
            # Rotate so every organization is reached within a few days.
            offset = (now.timetuple().tm_yday * max_orgs) % len(org_ids)
            rotated = org_ids[offset:] + org_ids[:offset]
            totals["skipped"] = len(org_ids) - max_orgs
            org_ids = rotated[:max_orgs]

        for org_id in org_ids:
            try:
                if is_demo_org(db, org_id):
                    continue
                result, _ = run_intel(db, org_id, False, clients=clients, max_age=REFRESH_OLDER_THAN,
                                      budget_seconds=ORG_BUDGET_SECONDS, max_lookups=ORG_MAX_LOOKUPS)
                looked_up = result.looked_up
                # NVD allows a handful of requests per 30 s: wait for the window and carry on
                # instead of leaving this organization half checked.
                passes = 1
                while (result.feeds["nvd"].get("queued") and passes < MAX_PASSES_PER_ORG
                       and waited + NVD_WINDOW_PAUSE_SECONDS <= NVD_WAIT_BUDGET_SECONDS):
                    sleep(NVD_WINDOW_PAUSE_SECONDS)
                    waited += NVD_WINDOW_PAUSE_SECONDS
                    passes += 1
                    result, _ = run_intel(db, org_id, False, clients=clients, max_age=REFRESH_OLDER_THAN,
                                          budget_seconds=ORG_BUDGET_SECONDS, max_lookups=ORG_MAX_LOOKUPS)
                    looked_up += result.looked_up
                summary = build_summary(result)
                totals["orgs"] += 1
                totals["looked_up"] += looked_up
                totals["queued"] += result.queued
                totals["vulnerable_items"] += summary["vulnerable"]
                totals["confirmed_advisories"] += summary["confirmed_advisories"]
                if result.failing_feeds:
                    logger.warning("Vuln intel for org %s: feeds failing: %s", org_id, result.failing_feeds)
            except Exception as exc:
                db.rollback()
                totals["failed"] += 1
                logger.error("Vuln intel refresh failed for org %s: %s", org_id, exc, exc_info=True)
        logger.info(
            "Vuln intel daily refresh: orgs=%(orgs)d looked_up=%(looked_up)d queued=%(queued)d "
            "vulnerable_items=%(vulnerable_items)d confirmed_advisories=%(confirmed_advisories)d "
            "failed=%(failed)d skipped=%(skipped)d", totals,
        )
        return totals
    finally:
        if own_session:
            db.close()
