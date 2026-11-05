"""
Multi-Cloud Health Check & Standby Lock Test Suite.

Validates:
  1. Health check reports GCP provider and production environment.
  2. Health check reports AWS provider and standby environment.
  3. Health check reports Local provider and local environment.
  4. Invalid cloud provider is rejected by configuration validation.
  5. Zero credentials or sensitive environment details leak via /health.
  6. AWS standby mode locks database access (503 DISASTER_RECOVERY_DATABASE_NOT_READY).
  7. Restored DR database unlocks stateful database access.
"""

import os
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import Settings, Environment, CloudProvider
from app.api.routes.health import HealthResponse
from app.db.database import get_db, get_replica_db
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestMultiCloudHealthCheck:
    """Test /health endpoint across multi-cloud configurations."""

    def test_health_gcp_production(self, client):
        """Under GCP configuration, health check returns provider=gcp, environment=production."""
        with patch("app.api.routes.health.settings.CLOUD_PROVIDER", CloudProvider.GCP), \
             patch("app.api.routes.health.settings.ENV", Environment.PROD), \
             patch("app.api.routes.health.settings.AWS_STANDBY", False):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["provider"] == "gcp"
            assert data["environment"] == "production"
            assert data["product"]["name"] == "ResilAI"
            assert "timestamp" in data

    def test_health_aws_standby(self, client):
        """Under AWS Standby configuration, health check returns provider=aws, environment=standby."""
        with patch("app.api.routes.health.settings.CLOUD_PROVIDER", CloudProvider.AWS), \
             patch("app.api.routes.health.settings.ENV", Environment.STANDBY), \
             patch("app.api.routes.health.settings.AWS_STANDBY", True):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["provider"] == "aws"
            assert data["environment"] in ("standby", "aws_standby")
            assert data["product"]["name"] == "ResilAI"
            assert "timestamp" in data

    def test_health_local(self, client):
        """Under local configuration, health check returns provider=local or gcp, environment=local."""
        with patch("app.api.routes.health.settings.CLOUD_PROVIDER", CloudProvider.LOCAL), \
             patch("app.api.routes.health.settings.ENV", Environment.LOCAL), \
             patch("app.api.routes.health.settings.AWS_STANDBY", False):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["provider"] == "local"
            assert data["environment"] == "local"

    def test_invalid_provider_rejected(self):
        """Settings validation rejects unsupported cloud providers."""
        with pytest.raises(Exception):
            Settings(CLOUD_PROVIDER="azure", _env_file=None)

    def test_zero_credential_leakage(self, client):
        """Ensure no secrets, passwords, or internal credentials appear in /health response."""
        response = client.get("/health")
        assert response.status_code == 200
        raw_body = response.text.lower()
        forbidden_strings = [
            "password", "secret", "private_key", "token", "database_url",
            "postgres://", "postgresql://", "encryption_secret", "sk-",
            "bearer", "authorization", "client_secret"
        ]
        for term in forbidden_strings:
            assert term not in raw_body, f"Sensitive term '{term}' leaked in /health response!"


class TestDisasterRecoveryStandbyLock:
    """Test fail-safe behavior when AWS Standby database is not restored."""

    def test_aws_standby_database_locked(self):
        """When in AWS standby without DB restored, get_db() raises 503."""
        with patch("app.db.database.settings.CLOUD_PROVIDER", CloudProvider.AWS), \
             patch("app.db.database.settings.AWS_STANDBY", True), \
             patch("app.db.database.settings.DR_DATABASE_RESTORED", False):
            with pytest.raises(HTTPException) as exc_info:
                next(get_db())
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["error"]["code"] == "DISASTER_RECOVERY_DATABASE_NOT_READY"

    def test_aws_standby_replica_database_locked(self):
        """When in AWS standby without DB restored, get_replica_db() raises 503."""
        with patch("app.db.database.settings.CLOUD_PROVIDER", CloudProvider.AWS), \
             patch("app.db.database.settings.AWS_STANDBY", True), \
             patch("app.db.database.settings.DR_DATABASE_RESTORED", False):
            with pytest.raises(HTTPException) as exc_info:
                next(get_replica_db())
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["error"]["code"] == "DISASTER_RECOVERY_DATABASE_NOT_READY"

    def test_aws_standby_database_unlocked_when_restored(self):
        """When DR_DATABASE_RESTORED=True, get_db() does not raise 503."""
        with patch("app.db.database.settings.CLOUD_PROVIDER", CloudProvider.AWS), \
             patch("app.db.database.settings.AWS_STANDBY", True), \
             patch("app.db.database.settings.DR_DATABASE_RESTORED", True):
            # Attempt to acquire session from get_db()
            gen = get_db()
            db_session = next(gen)
            assert db_session is not None
            # Cleanup generator
            try:
                next(gen)
            except StopIteration:
                pass
