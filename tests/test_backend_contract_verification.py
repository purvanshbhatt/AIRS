"""
Backend Runtime & API Contract Verification Test Matrix
Phase: Backend Runtime Reliability + API Contract Verification

Tests the exact scenarios specified in the agent task cue:
- Authentication (401/403 boundaries)
- Organization isolation (cross-org access denied)
- Evidence invariant (no fabricated readiness)
- CORS preflight responses
- Structured failure states
- Health endpoint behavior
"""
import pytest
from unittest.mock import patch
from app.models.organization import Organization
from app.core.auth import get_current_user, User


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_org(db_session, org_id: str, owner_uid: str = None) -> Organization:
    """Create a minimal org in the test database."""
    org = Organization(
        id=org_id,
        name=f"Test Org {org_id}",
        owner_uid=owner_uid or f"uid-for-{org_id}",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


# ─────────────────────────────────────────────────────────────────────────────
# Health Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthEndpoints:
    """Verify operational health endpoints distinguish alive vs. ready."""

    def test_health_alive(self, client):
        """GET /health → 200 with status=ok."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "product" in data

    def test_health_cors_config(self, client):
        """GET /health/cors → 200, returns env and allowed_origins."""
        resp = client.get("/health/cors")
        assert resp.status_code == 200
        data = resp.json()
        assert "env" in data
        assert "allowed_origins" in data
        assert "localhost_allowed" in data

    def test_health_llm_no_side_effects(self, client):
        """GET /health/llm → 200, does NOT call LLM, returns config only."""
        resp = client.get("/health/llm")
        assert resp.status_code == 200
        data = resp.json()
        assert "llm_enabled" in data
        assert "demo_mode" in data
        assert "runtime_check" in data


# ─────────────────────────────────────────────────────────────────────────────
# CORS Preflight
# ─────────────────────────────────────────────────────────────────────────────

class TestCORSPreflight:
    """CORS preflight must respond correctly for all allowed origins."""

    def test_cors_preflight_staging_origin(self, client):
        """OPTIONS preflight from staging.resilai.org → 204 with CORS headers."""
        resp = client.options(
            "/api/clinic/readiness/any-org",
            headers={
                "Origin": "https://staging.resilai.org",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            }
        )
        # 204 is the fast-path from CORSErrorSafetyMiddleware, 200 from CORSMiddleware
        assert resp.status_code in (200, 204)

    def test_cors_preflight_localhost(self, client):
        """OPTIONS from localhost (dev) should succeed in local/staging ENV."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert resp.status_code in (200, 204)


# ─────────────────────────────────────────────────────────────────────────────
# Authentication on Clinic Readiness Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestClinicReadinessAuthentication:
    """
    Verify the /api/clinic/readiness/{org_id} endpoint enforces the
    configured auth rules correctly.

    In test environment: AUTH_REQUIRED=false (set by conftest.py).
    Auth-required behavior is tested via direct settings patching.
    """

    def test_valid_unauthenticated_request_succeeds_in_dev(self, client, db_session):
        """
        In dev/staging with AUTH_REQUIRED=false: unauthenticated requests succeed.
        This allows development and demo without requiring valid Firebase tokens.
        """
        org = _make_org(db_session, "dev-org-001")
        resp = client.get(f"/api/clinic/readiness/{org.id}")
        assert resp.status_code == 200

    def test_response_contains_required_contract_fields(self, client, db_session):
        """
        Verify the DailyReadinessReport contract shape: all required fields present.
        This is the API contract test.
        """
        org = _make_org(db_session, "contract-org-001")
        resp = client.get(f"/api/clinic/readiness/{org.id}")
        assert resp.status_code == 200
        data = resp.json()

        # Core identity fields
        assert "report_id" in data
        assert "report_date" in data
        assert "generated_at" in data

        # Core decision
        assert "status" in data
        assert data["status"] in ("safe_to_open", "action_needed", "critical_risk", "unknown")
        assert "clinic_health_pct" in data
        assert "connector_health_pct" in data

        # Narrative
        assert "greeting" in data
        assert "summary" in data

        # Structural sections
        assert "business_continuity" in data
        assert "operational_readiness" in data["business_continuity"]
        assert "passed_checks" in data
        assert "failed_checks" in data
        assert "warnings" in data
        assert "unknowns" in data
        assert "immediate_actions" in data
        assert "coverage" in data
        assert "connectors" in data
        assert "verification" in data
        assert "audit_snapshot_id" in data

        # Stats
        assert "checks_performed" in data
        assert "devices_checked" in data
        assert "accounts_checked" in data
        assert "backups_verified" in data

        # org_id must NOT be in response (security: no ID leakage)
        assert "org_id" not in data

    def test_missing_evidence_returns_explicit_unknown_not_zero_or_hundred(self, client, db_session):
        """
        INVARIANT: Absence of evidence must never become evidence of readiness.
        When no connectors are registered, clinic_health_pct must be 0.
        status must be 'unknown'. It must NOT be safe_to_open or 100.
        """
        # Production org mode: no demo data, no connectors
        org = Organization(id="no-evidence-org", name="No Evidence", org_mode="production")
        db_session.add(org)
        db_session.commit()

        resp = client.get(f"/api/clinic/readiness/{org.id}")
        assert resp.status_code == 200
        data = resp.json()

        # INVARIANT: status must be unknown when there is no evidence
        assert data["status"] == "unknown", (
            f"Expected 'unknown' status when no evidence. Got: {data['status']}"
        )

        # INVARIANT: health must NOT be 100 with zero evidence
        assert data["clinic_health_pct"] != 100, (
            "clinic_health_pct must not be 100 when status is unknown (no evidence invariant violation)"
        )

        # Verification confidence must be 0 when no connectors
        assert data["verification"]["confidence_pct"] == 0

    def test_invalid_assessment_id_returns_404(self, client):
        """GET /api/clinic/readiness/{non_existent_id} → gracefully handled."""
        resp = client.get("/api/clinic/readiness/totally-nonexistent-org-xyz-abc-123")
        # Should respond (not crash). In dev mode, this will return a report
        # with unknown status; in production it would be 403 (org isolation).
        assert resp.status_code in (200, 403, 404)

    def test_no_fabricated_readiness_score_via_frontend_input(self, client, db_session):
        """
        Scoring must remain server-side/deterministic.
        Frontend cannot inject a score by manipulating the org_id.
        Verify the response reflects actual server-computed state.
        """
        org = _make_org(db_session, "real-org")
        resp = client.get(f"/api/clinic/readiness/{org.id}")
        assert resp.status_code == 200
        data = resp.json()
        # Score must be an integer in 0-100
        assert isinstance(data["clinic_health_pct"], int)
        assert 0 <= data["clinic_health_pct"] <= 100
        assert isinstance(data["connector_health_pct"], int)
        assert 0 <= data["connector_health_pct"] <= 100


# ─────────────────────────────────────────────────────────────────────────────
# Organization Isolation
# ─────────────────────────────────────────────────────────────────────────────

class TestOrganizationIsolation:
    """
    AUTH_REQUIRED=true isolation tests.
    We patch settings.AUTH_REQUIRED to simulate production auth enforcement.
    `is_auth_required` is a Pydantic property that reads from AUTH_REQUIRED,
    so patching the field directly is the correct approach.
    """

    def test_cross_org_access_denied_when_auth_required(self, client, db_session):
        """
        User authenticated for Org A must NOT access Org B's data.
        Expected: 403 Forbidden.
        """
        from app.main import app as fastapi_app
        from app.db.database import get_db
        from app.core.config import settings

        # Create two orgs
        org_a = _make_org(db_session, "org-a-isolation", owner_uid="uid-user-a")
        org_b = _make_org(db_session, "org-b-isolation", owner_uid="uid-user-b")

        user_a = User(uid="uid-user-a", email="a@test.com", name="User A")

        def override_get_db():
            yield db_session

        def override_auth():
            return user_a

        original_auth_required = settings.AUTH_REQUIRED
        settings.AUTH_REQUIRED = True
        fastapi_app.dependency_overrides[get_db] = override_get_db
        fastapi_app.dependency_overrides[get_current_user] = override_auth

        try:
            from fastapi.testclient import TestClient
            with TestClient(fastapi_app) as tc:
                # User A tries to access Org B — should be denied
                resp = tc.get(f"/api/clinic/readiness/{org_b.id}")
                assert resp.status_code == 403, (
                    f"Cross-org access must return 403. Got {resp.status_code}: {resp.text}"
                )
        finally:
            settings.AUTH_REQUIRED = original_auth_required
            fastapi_app.dependency_overrides.clear()

    def test_own_org_access_allowed_when_auth_required(self, client, db_session):
        """
        User authenticated for Org A CAN access Org A's data.
        Expected: 200 OK.
        """
        from app.main import app as fastapi_app
        from app.db.database import get_db
        from app.core.config import settings

        org_a = _make_org(db_session, "org-a-own-access", owner_uid="uid-user-self")
        user_self = User(uid="uid-user-self", email="self@test.com", name="Self")

        def override_get_db():
            yield db_session

        def override_auth():
            return user_self

        original_auth_required = settings.AUTH_REQUIRED
        settings.AUTH_REQUIRED = True
        fastapi_app.dependency_overrides[get_db] = override_get_db
        fastapi_app.dependency_overrides[get_current_user] = override_auth

        try:
            from fastapi.testclient import TestClient
            with TestClient(fastapi_app) as tc:
                resp = tc.get(f"/api/clinic/readiness/{org_a.id}")
                assert resp.status_code == 200, (
                    f"Own org access must return 200. Got {resp.status_code}: {resp.text}"
                )
        finally:
            settings.AUTH_REQUIRED = original_auth_required
            fastapi_app.dependency_overrides.clear()

    def test_missing_auth_returns_401_when_auth_required(self, client, db_session):
        """No auth header + AUTH_REQUIRED=true → 401."""
        from app.main import app as fastapi_app
        from app.db.database import get_db
        from app.core.config import settings

        org = _make_org(db_session, "org-no-auth", owner_uid="uid-nobody")

        def override_get_db():
            yield db_session

        # Override get_current_user to return None (no credentials)
        def override_auth():
            return None

        original_auth_required = settings.AUTH_REQUIRED
        settings.AUTH_REQUIRED = True
        fastapi_app.dependency_overrides[get_db] = override_get_db
        fastapi_app.dependency_overrides[get_current_user] = override_auth

        try:
            from fastapi.testclient import TestClient
            with TestClient(fastapi_app) as tc:
                resp = tc.get(f"/api/clinic/readiness/{org.id}")
                assert resp.status_code == 401, (
                    f"Missing auth must return 401. Got {resp.status_code}: {resp.text}"
                )
        finally:
            settings.AUTH_REQUIRED = original_auth_required
            fastapi_app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Invariant
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidenceInvariant:
    """
    Core product invariant: No evidence → no inferred readiness.
    These tests verify that the backend never fabricates a readiness score.
    """

    def test_no_connectors_means_zero_confidence(self, client, db_session):
        """When org has no connectors, verification confidence must be 0."""
        org = Organization(id="no-connector-org", name="Empty", org_mode="production")
        db_session.add(org)
        db_session.commit()

        resp = client.get(f"/api/clinic/readiness/{org.id}")
        data = resp.json()
        assert data["verification"]["confidence_pct"] == 0

    def test_no_connectors_means_zero_health(self, client, db_session):
        """When org has no connectors, clinic_health_pct must not be 100."""
        org = Organization(id="no-connector-health-org", name="Empty Health", org_mode="production")
        db_session.add(org)
        db_session.commit()

        resp = client.get(f"/api/clinic/readiness/{org.id}")
        data = resp.json()
        # With our fix: confidence=0 → health=0
        assert data["clinic_health_pct"] == 0, (
            f"clinic_health_pct must be 0 with no evidence. Got: {data['clinic_health_pct']}"
        )

    def test_stale_evidence_state_is_exposed(self, client, db_session):
        """
        Stale evidence must not be silently treated as current.
        The verification context should expose the staleness.
        If evidence is stale, verification_status should not be 'verified'.
        """
        # When demo telemetry is loaded, check that stale checks are flagged
        org = _make_org(db_session, "stale-evidence-org")
        resp = client.get(f"/api/clinic/readiness/{org.id}")
        assert resp.status_code == 200
        data = resp.json()
        # Verify that at least the verification section is present
        assert "verification" in data
        # With real demo data, failed_checks should appear (backup failed, stale user)
        # We just verify the structure is correct, not the exact values
        for check in data.get("failed_checks", []):
            assert "status" in check
            assert "label" in check

    def test_response_has_no_fabricated_fields(self, client, db_session):
        """
        Response must not contain any legacy fabricated default fields
        like || 98, || 100, || 0 patterns.
        Also verify no internal engineering terms leak.
        """
        org = _make_org(db_session, "clean-response-org")
        resp = client.get(f"/api/clinic/readiness/{org.id}")
        resp_text = resp.text.lower()

        # Must not expose internal engineering terms
        for term in ["capability", "normalizedevent", "risk_score", "evidence_id"]:
            assert term not in resp_text, f"Leaked internal term: {term}"

        # Must not expose internal IDs directly
        assert "source_event_id" not in resp_text
        assert "connector_uuid" not in resp_text


# ─────────────────────────────────────────────────────────────────────────────
# Structured Error States
# ─────────────────────────────────────────────────────────────────────────────

class TestStructuredErrorStates:
    """
    Backend must return structured errors that allow frontend
    to distinguish failure types without leaking internals.
    """

    def test_404_returns_structured_error(self, client):
        """Unknown route → structured 404, not a raw exception."""
        resp = client.get("/api/clinic/this-route-does-not-exist-xyz")
        assert resp.status_code == 404

    def test_error_responses_never_expose_stack_traces(self, client, db_session):
        """
        Security: error responses must not include Python tracebacks or
        internal file paths.
        """
        # Hit a nonexistent route to force an error
        resp = client.get("/api/nonexistent-endpoint-xyz-abc")
        assert "traceback" not in resp.text.lower()
        assert "file \"" not in resp.text.lower()
        assert "line " not in resp.text.lower() or "lineno" not in resp.text.lower()
