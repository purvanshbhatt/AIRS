"""
Vulnerability intelligence models.

``VulnIntelCache``  shared (not per-org) cache of public intelligence lookups
                    (OSV, NVD, CISA KEV, endoflife.date). Rows are keyed by the
                    exact lookup (source + product + version) and carry a TTL so
                    a request never has to wait on the network twice in a day.
                    Expired rows are kept: they are served as stale data when
                    the network is unavailable.
``WebAsset``        a website / web application the organization asked us to
                    watch, with the last passive scan result.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class VulnIntelCache(Base):
    """One cached public-intelligence lookup."""

    __tablename__ = "vuln_intel_cache"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(512), nullable=False, unique=True, index=True,
                       comment="e.g. nvd:php:php:8.1.2, osv:PyPI:django:3.2.0, kev:catalog, eol:php")
    source = Column(String(50), nullable=False, index=True, comment="osv | nvd | kev | eol | deployments")
    payload = Column(Text, nullable=False, default="null", comment="JSON document returned by the lookup.")
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<VulnIntelCache(key={self.cache_key!r}, fetched_at={self.fetched_at})>"


class WebAsset(Base):
    """A website or web application registered for passive checks."""

    __tablename__ = "web_assets"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    label = Column(String(255), nullable=True)
    last_scan = Column(Text, nullable=True, comment="JSON of the last scan result (API contract shape).")
    last_scan_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_web_assets_org_url", "org_id", "url"),
    )

    def __repr__(self) -> str:
        return f"<WebAsset(id={self.id}, url={self.url!r})>"
