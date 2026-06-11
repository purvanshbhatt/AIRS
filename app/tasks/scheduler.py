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
                initial_delay_seconds=120
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
        # In a full implementation, this would iterate active connectors and call their sync() method
        logger.info("Connector sync sweep executed.")


# Global instance
scheduler = TaskScheduler()
