"""
Lightweight asynchronous task scheduler for AIRS.

Designed for Cloud Run single-container execution environments.
Handles periodic syncs, snapshot creation, and evidence freshness checks
without relying on external message queues (like Celery/Redis) to maintain
simplicity in staging.
"""
import asyncio
import logging
from typing import Callable, Coroutine, Dict, Any
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.continuous_scoring import ContinuousScoringEngine
from app.core.config import settings

logger = logging.getLogger("airs.scheduler")


class TaskScheduler:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        
    def start(self):
        """Start the background task scheduler."""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting background task scheduler...")
        
        # Schedule the connector sync sweep
        self.tasks["connector_sync"] = asyncio.create_task(
            self._run_periodic(
                name="ConnectorSync",
                interval_seconds=3600,  # 1 hour
                coro_func=self._sync_connectors,
                initial_delay_seconds=60
            )
        )
        
        # Schedule health monitoring
        self.tasks["connector_health"] = asyncio.create_task(
            self._run_periodic(
                name="ConnectorHealth",
                interval_seconds=600,  # 10 minutes
                coro_func=self._monitor_health,
                initial_delay_seconds=30
            )
        )

    def stop(self):
        """Stop all background tasks."""
        self.running = False
        for name, task in self.tasks.items():
            logger.info(f"Cancelling background task: {name}")
            task.cancel()
            
    async def _run_periodic(
        self, 
        name: str, 
        interval_seconds: int, 
        coro_func: Callable[[], Coroutine[Any, Any, None]],
        initial_delay_seconds: int = 0
    ):
        """Run a coroutine periodically."""
        if initial_delay_seconds > 0:
            await asyncio.sleep(initial_delay_seconds)
            
        while self.running:
            start_time = datetime.now(timezone.utc)
            logger.info(f"Task '{name}' started at {start_time.isoformat()}")
            
            try:
                await coro_func()
            except asyncio.CancelledError:
                logger.info(f"Task '{name}' cancelled.")
                break
            except Exception as e:
                logger.error(f"Task '{name}' failed with error: {e}", exc_info=True)
                
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            sleep_time = max(0, interval_seconds - elapsed)
            
            logger.info(f"Task '{name}' finished in {elapsed:.2f}s. Sleeping for {sleep_time:.2f}s.")
            await asyncio.sleep(sleep_time)

    async def _sync_connectors(self):
        """Trigger syncs for active connectors. (Implementation matches Phase 1 stub behavior)"""
        from app.models.connector import Connector, ConnectorStatus
        from app.services.connector_manager import ConnectorManager

        logger.info("Connector sync sweep executing...")
        db = SessionLocal()
        try:
            # Fetch active or syncing connectors
            connectors = db.query(Connector).filter(
                Connector.status.in_([ConnectorStatus.active.value, ConnectorStatus.syncing.value, ConnectorStatus.error.value])
            ).all()

            for connector in connectors:
                try:
                    # Minimal rate limit / interval check could be added here based on connector.sync_interval_minutes and connector.last_sync_at
                    if connector.last_sync_at and connector.sync_interval_minutes:
                        elapsed = (datetime.now(timezone.utc) - connector.last_sync_at.replace(tzinfo=timezone.utc)).total_seconds()
                        if elapsed < (connector.sync_interval_minutes * 60):
                            continue # Skip, not yet time to sync

                    mgr = ConnectorManager(db, org_id=connector.org_id)
                    await mgr.sync_connector(connector.id)
                except Exception as e:
                    logger.error(f"Error syncing connector {connector.id}: {e}", exc_info=True)
        finally:
            db.close()
        logger.info("Connector sync sweep executed.")

    async def _monitor_health(self):
        """Check the health of active connectors periodically."""
        from app.models.connector import Connector, ConnectorStatus
        from app.services.connector_manager import ConnectorManager

        logger.info("Connector health monitoring executing...")
        db = SessionLocal()
        try:
            connectors = db.query(Connector).filter(
                Connector.status.in_([ConnectorStatus.active.value, ConnectorStatus.error.value])
            ).all()

            for connector in connectors:
                try:
                    mgr = ConnectorManager(db, org_id=connector.org_id)
                    await mgr.health_check(connector.id)
                except Exception as e:
                    logger.error(f"Error checking health for connector {connector.id}: {e}", exc_info=True)
        finally:
            db.close()
        logger.info("Connector health monitoring executed.")


# Global instance
scheduler = TaskScheduler()
