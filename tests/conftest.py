import os
import pytest
from unittest.mock import MagicMock, patch
from contextlib import ExitStack
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force deterministic local test settings regardless of host environment.
os.environ.setdefault("ENV", "local")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("TESTING", "true")
os.environ["DATABASE_URL"] = "sqlite://"

from app.main import app as fastapi_app
from app.db.database import Base, get_db, engine, SessionLocal as TestingSessionLocal
import app.models as app_models  # Force register all models for testing


# ── Firestore mock layer ────────────────────────────────────────────
# When the Firestore emulator is running (FIRESTORE_EMULATOR_HOST set),
# the real emulated client is used automatically by app.db.firestore.
# When it is NOT running, we patch the Firestore layer with an in-memory
# mock so tests that create/update/delete orgs don't crash with
# FirestoreUnavailableError.

def _emulator_available() -> bool:
    """Return True if the Firestore emulator appears to be running."""
    host = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if not host:
        return False
    import socket
    parts = host.split(":")
    hostname = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 8080
    try:
        with socket.create_connection((hostname, port), timeout=0.3):
            return True
    except OSError:
        return False


@pytest.fixture(autouse=True)
def _mock_firestore_if_no_emulator():
    """
    If the Firestore emulator is NOT reachable, patch the save/delete/get
    functions in ``app.db.firestore`` so that they succeed as no-ops.

    This keeps every test green without requiring live GCP credentials or
    a running emulator.  When the emulator IS running, the real (emulated)
    Firestore is exercised instead.
    """
    if _emulator_available():
        yield  # real emulator — nothing to patch
        return

    patchers = [
        patch("app.db.firestore.firestore_save_org", return_value=True),
        patch("app.db.firestore.firestore_delete_org", return_value=True),
        patch("app.db.firestore.firestore_save_assessment", return_value=True),
        patch("app.db.firestore.firestore_delete_assessment", return_value=True),
        patch(
            "app.db.firestore.firestore_upsert_remediation_ledger",
            return_value={
                "tasks_upserted": 0,
                "ledger_collection_path": "organizations/mock/workspaces/mock/audits/mock/remediation_ledger",
            },
        ),
        patch("app.db.firestore.firestore_set_assessment_lifecycle", return_value=True),
        patch("app.db.firestore.firestore_get_assessment_lifecycle", return_value={}),
        patch("app.db.firestore.firestore_save_finding_tracking", return_value=True),
        patch("app.db.firestore.firestore_get_finding_tracking_map", return_value={}),
        patch("app.db.firestore.firestore_get_all_orgs", return_value=[]),
        patch("app.db.firestore.firestore_get_all_assessments", return_value=[]),
        patch("app.db.firestore.require_firestore", return_value=True),
        patch("app.db.firestore.is_firestore_available", return_value=True),
        patch("app.services.organization.firestore_save_org", return_value=True),
        patch("app.services.organization.firestore_delete_org", return_value=True),
        patch("app.services.assessment.firestore_save_assessment", return_value=True),
        patch("app.services.assessment.firestore_delete_assessment", return_value=True),
        patch("app.api.assessments.firestore_set_assessment_lifecycle", return_value=True),
        patch("app.api.assessments.firestore_get_assessment_lifecycle", return_value={}),
        patch("app.api.assessments.firestore_save_finding_tracking", return_value=True),
        patch("app.api.assessments.firestore_get_finding_tracking_map", return_value={}),
        patch("app.api.governance.firestore_save_org", return_value=True),
    ]

    with ExitStack() as stack:
        for patcher in patchers:
            stack.enter_context(patcher)
        yield


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


from app.core.auth import User, require_auth

# Mock users for testing
USER_NO_ORG = User(uid="user-no-org", email="no_org@example.com", name="No Org User")
USER_WITH_ORG = User(uid="user-with-org", email="has_org@example.com", name="Has Org User")
USER_A = User(uid="user-a", email="user_a@example.com", name="User A")
USER_B = User(uid="user-b", email="user_b@example.com", name="User B")


def make_auth_override(user: User):
    """Create an auth override for the given user."""
    async def override():
        return user
    return override


@pytest.fixture(scope="function")
def client(db_session):
    """Generic test client. Does not guarantee auth or org presence."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_org(db_session):
    """Client authenticated as a user with NO organization."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[require_auth] = make_auth_override(USER_NO_ORG)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_with_org(db_session):
    """Client authenticated as a user WITH one organization provisioned."""
    from app.models.organization import Organization
    
    # Provision organization
    org = Organization(id="test-org-123", name="Provisioned Org", owner_uid=USER_WITH_ORG.uid)
    db_session.add(org)
    db_session.commit()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[require_auth] = make_auth_override(USER_WITH_ORG)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_user_a(db_session):
    """Client authenticated as User A."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[require_auth] = make_auth_override(USER_A)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_user_b(db_session):
    """Client authenticated as User B."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[require_auth] = make_auth_override(USER_B)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
