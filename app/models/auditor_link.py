"""
Auditor link: a time-limited, read-only share link for an outside auditor.

Only the SHA-256 hash of the token is stored. The token itself is shown once
to the owner who created the link and cannot be recovered from this table.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.database import Base


class AuditorLink(Base):
    __tablename__ = "auditor_links"

    token_hash = Column(String(64), primary_key=True)
    org_id = Column(String(64), nullable=False, index=True)
    org_name = Column(String(255), nullable=False)
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    access_count = Column(Integer, nullable=False, default=0)
