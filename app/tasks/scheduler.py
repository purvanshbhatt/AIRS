"""
Lightweight asynchronous task scheduler for AIRS.

Designed for Cloud Run single-container execution environments.
Handles periodic syncs, snapshot creation, and evidence freshness checks
without relying on external message queues (like Celery/Redis) to maintain
simplicity in staging.
"""
import asyncio
import gc
import logging
import os
import tempfile
from typing import Callable, Coroutine, Dict, Any
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.continuous_scoring import ContinuousScoringEngine
from app.core.config import settings

logger = logging.getLogger("airs.scheduler")


class TaskScheduler:
    def __init__(self, lock_path: str | None = None):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        self._lock_path = lock_path or os.environ.get(
            "SCHEDULER_LOCK_FILE", os.path.join(tempfile.gettempdir(), "resilai-scheduler.lock")
        )
        self._lock_handle = None

    def _acquire_leadership(self) -> bool:
        """Only one worker process in the container may run the background tasks.

        The API runs several gunicorn workers. Without this, every worker ran
        its own connector sweep at the same moment: each connector was synced
        twice, and two copies of the AWS SDK's service models pushed the
        container over its memory limit, which restarted it in a loop.

        An exclusive, non-blocking lock on a file decides the leader. The lock
        dies with the process, so a replacement worker takes over at start-up.
        """
        try:
            import fcntl
        except ImportError:  # Windows development machines: single process anyway
            return True
        handle = None
        try:
            handle = open(self._lock_path, "w")
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            if handle is not None:
                handle.close()
            return False
        self._lock_handle = handle
        return True

    def _release_leadership(self) -> None:
        if self._lock_handle is None:
            return
        try:
            self._lock_handle.close()  # closing the file releases the lock
        except OSError:
            pass
        self._lock_handle = None

    def start(self):
        """Start the background task scheduler."""
        if self.running:
            return

        if not self._acquire_leadership():
            logger.info("Background tasks already run in another worker; this worker will not schedule them.")
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

        # Daily vulnerability-intelligence refresh for organizations with inventory
        self.tasks["vuln_intel_refresh"] = asyncio.create_task(
            self._run_periodic(
                name="VulnIntelRefresh",
                interval_seconds=86400,  # 24 hours
                coro_func=self._refresh_vuln_intel,
                initial_delay_seconds=300
            )
        )

    def stop(self):
        """Stop all background tasks."""
        self.running = False
        for name, task in self.tasks.items():
            logger.info(f"Cancelling background task: {name}")
            task.cancel()
        self.tasks = {}
        self._release_leadership()
            
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
                    # Cloud SDK clients hold large service models; hand that
                    # memory back before the next connector starts.
                    gc.collect()
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


    async def _refresh_vuln_intel(self):
        """Re-check each organization's software against the public vulnerability feeds.

        Bounded per run (see app.services.vuln_intel.jobs). Runs in a worker
        thread because the lookups and the database work are synchronous.
        """
        from app.services.vuln_intel.jobs import run_daily_refresh

        logger.info("Vulnerability intelligence refresh executing...")
        totals = await asyncio.to_thread(run_daily_refresh)
        logger.info("Vulnerability intelligence refresh executed: %s", totals)


# Global instance
scheduler = TaskScheduler()
