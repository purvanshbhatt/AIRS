import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force deterministic local test settings regardless of host environment.
os.environ.setdefault("ENV", "local")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DEMO_MODE", "true")

from app.main import app
from app.db.database import Base, get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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

    with patch("app.db.firestore.firestore_save_org", return_value=True), \
         patch("app.db.firestore.firestore_delete_org", return_value=True), \
         patch("app.db.firestore.firestore_get_all_orgs", return_value=[]), \
         patch("app.db.firestore.sync_orgs_from_firestore", return_value=0), \
         patch("app.db.firestore.require_firestore", return_value=True), \
         patch("app.db.firestore.is_firestore_available", return_value=True), \
         patch("app.services.organization.firestore_save_org", return_value=True), \
         patch("app.services.organization.firestore_delete_org", return_value=True), \
         patch("app.api.governance.firestore_save_org", return_value=True):
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


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
