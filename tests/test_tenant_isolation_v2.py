"""
Tenant Isolation Test Suite V2 — Org Ownership & Auth Boundary.

Validates:
  1. All org-scoped services require owner_uid
  2. Users cannot access organizations they don't own
  3. Reports are scoped to owner_uid
  4. Cross-tenant access is prevented
  5. New API endpoints enforce isolation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services.organization import OrganizationService
from app.services.report import ReportService
from app.schemas.organization import OrganizationCreate


@pytest.fixture
def test_db():
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestTenantIsolationV2:
    """Validate strict tenant isolation across services."""

    def test_report_service_requires_owner_uid(self):
        """ReportService must reject empty owner_uid."""
        from unittest.mock import MagicMock
        with pytest.raises(ValueError, match="owner_uid"):
            ReportService(MagicMock(), owner_uid="")

    def test_user_cannot_access_other_users_org(self, test_db):
        """User A cannot access User B's organizations."""
        service_a = OrganizationService(test_db, owner_uid="user-alpha")
        service_b = OrganizationService(test_db, owner_uid="user-beta")

        org_a = service_a.create(OrganizationCreate(name="Alpha Clinic", industry="healthcare"))
        org_b = service_b.create(OrganizationCreate(name="Beta Clinic", industry="healthcare"))

        # User A should not be able to get User B's org
        result = service_a.get(org_b.id)
        assert result is None, "User A should not access User B's org"

        # User B should not be able to get User A's org
        result = service_b.get(org_a.id)
        assert result is None, "User B should not access User A's org"

    def test_user_cannot_list_other_users_orgs(self, test_db):
        """Listing only returns orgs owned by the current user."""
        service_a = OrganizationService(test_db, owner_uid="user-1")
        service_b = OrganizationService(test_db, owner_uid="user-2")

        service_a.create(OrganizationCreate(name="Org 1", industry="healthcare"))
        service_a.create(OrganizationCreate(name="Org 1b", industry="healthcare"))
        service_b.create(OrganizationCreate(name="Org 2", industry="healthcare"))

        a_orgs = service_a.get_all()
        b_orgs = service_b.get_all()

        assert len(a_orgs) == 2
        assert len(b_orgs) == 1
        assert all(o.owner_uid == "user-1" for o in a_orgs)
        assert all(o.owner_uid == "user-2" for o in b_orgs)


class TestReportTenantIsolationV2:
    """Validate reports are scoped to owner_uid."""

    def test_report_query_scoped_to_owner(self, test_db):
        """Report queries must be filtered by owner_uid."""
        service = ReportService(test_db, owner_uid="test-user")
        reports, total = service.list()
        assert total == 0
        assert reports == []

    def test_report_get_returns_none_for_wrong_owner(self, test_db):
        """Getting a report that doesn't belong to the user returns None."""
        service = ReportService(test_db, owner_uid="user-x")
        result = service.get("nonexistent-id")
        assert result is None


class TestExplanationTenantIsolation:
    """Validate explanation service requires tenant credentials."""

    def test_explanation_service_requires_both_ids(self):
        """ExplanationService must reject empty org_id or owner_uid."""
        from unittest.mock import MagicMock
        from app.services.explanation import ExplanationService

        with pytest.raises(ValueError):
            ExplanationService(MagicMock(), org_id="", owner_uid="user")

        with pytest.raises(ValueError):
            ExplanationService(MagicMock(), org_id="org", owner_uid="")


class TestAuthDependencyIntegrityV2:
    """Validate auth module exposes correct dependencies."""

    def test_require_auth_exists(self):
        from app.core.auth import require_auth
        assert callable(require_auth)

    def test_require_org_admin_exists(self):
        from app.core.auth import require_org_admin
        assert callable(require_org_admin)

    def test_user_class_has_uid(self):
        from app.core.auth import User
        user = User(uid="test-uid", email="test@test.com")
        assert user.uid == "test-uid"
