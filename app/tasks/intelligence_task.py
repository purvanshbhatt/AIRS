"""
Intelligence Task Scheduler — runs software version drift checks on a periodic interval.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.intelligence import IntelligenceService

logger = logging.getLogger("airs.tasks.intelligence")

# Global APScheduler instance
intelligence_scheduler = AsyncIOScheduler()


async def run_intelligence_sync_sweep():
    """Job to query all organizations and run the version drift check."""
    logger.info("Starting background intelligence version drift sweep...")
    db = SessionLocal()
    try:
        orgs = db.query(Organization).all()
        for org in orgs:
            try:
                service = IntelligenceService(db, org.id)
                drift_count = await service.sync_intelligence_and_detect_drift()
                logger.info("Drift audit completed for org %s. Drift count: %d", org.id, drift_count)
            except Exception as org_err:
                logger.error("Failed running version drift check for org %s: %s", org.id, org_err, exc_info=True)
    finally:
        db.close()
    logger.info("Background intelligence version drift sweep completed.")


def start_intelligence_scheduler():
    """Initialize and start the background scheduler."""
    if not intelligence_scheduler.running:
        logger.info("Initializing intelligence task scheduler...")
        # Schedule to run every 12 hours
        intelligence_scheduler.add_job(
            run_intelligence_sync_sweep,
            "interval",
            hours=12,
            id="intelligence_version_drift_sync",
            replace_existing=True,
        )
        intelligence_scheduler.start()
        logger.info("Intelligence task scheduler started.")


def stop_intelligence_scheduler():
    """Stop the background scheduler."""
    if intelligence_scheduler.running:
        logger.info("Stopping intelligence task scheduler...")
        intelligence_scheduler.shutdown()
        logger.info("Intelligence task scheduler stopped.")
