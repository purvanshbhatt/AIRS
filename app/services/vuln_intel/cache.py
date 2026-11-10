"""
DB-backed cache for public intelligence lookups (24 h TTL by default).

Expired rows are never deleted by a read: when the network is down the
caller serves them as stale data and says so, instead of returning nothing.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.vuln_intel import VulnIntelCache

logger = logging.getLogger("airs.vuln_intel.cache")

DEFAULT_TTL = timedelta(hours=24)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class CacheEntry:
    key: str
    payload: Any
    fetched_at: datetime
    expires_at: datetime

    def is_fresh(self, now: datetime, max_age: Optional[timedelta] = None) -> bool:
        if now >= self.expires_at:
            return False
        if max_age is not None and now - self.fetched_at > max_age:
            return False
        return True


class IntelCache:
    def __init__(self, db: Session, ttl: timedelta = DEFAULT_TTL):
        self.db = db
        self.ttl = ttl

    def get(self, key: str) -> Optional[CacheEntry]:
        try:
            row = self.db.query(VulnIntelCache).filter(VulnIntelCache.cache_key == key).first()
        except Exception as exc:  # table missing in an old database: behave as a cold cache
            logger.debug("Intel cache read failed for %s: %s", key, exc)
            self.db.rollback()
            return None
        if row is None:
            return None
        try:
            payload = json.loads(row.payload)
        except (TypeError, ValueError):
            return None
        fetched = _aware(row.fetched_at) or datetime.now(timezone.utc)
        return CacheEntry(key=key, payload=payload, fetched_at=fetched,
                          expires_at=_aware(row.expires_at) or fetched)

    def set(self, key: str, source: str, payload: Any, now: Optional[datetime] = None,
            ttl: Optional[timedelta] = None) -> Optional[CacheEntry]:
        now = now or datetime.now(timezone.utc)
        expires = now + (ttl or self.ttl)
        try:
            row = self.db.query(VulnIntelCache).filter(VulnIntelCache.cache_key == key).first()
            body = json.dumps(payload, separators=(",", ":"), default=str)
            if row is None:
                row = VulnIntelCache(cache_key=key, source=source, payload=body,
                                     fetched_at=now, expires_at=expires)
                self.db.add(row)
            else:
                row.payload = body
                row.source = source
                row.fetched_at = now
                row.expires_at = expires
            self.db.commit()
        except Exception as exc:
            logger.warning("Intel cache write failed for %s: %s", key, exc)
            self.db.rollback()
            return None
        return CacheEntry(key=key, payload=payload, fetched_at=now, expires_at=expires)
