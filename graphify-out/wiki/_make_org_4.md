# _make_org

> 25 nodes · cohesion 0.10

## Key Concepts

- **_make_org()** (12 connections) — `tests/test_backend_contract_verification.py`
- **TestClinicReadinessAuthentication** (8 connections) — `tests/test_backend_contract_verification.py`
- **TestEvidenceInvariant** (7 connections) — `tests/test_backend_contract_verification.py`
- **Organization** (4 connections)
- **.test_missing_evidence_returns_explicit_unknown_not_zero_or_hundred()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_no_fabricated_readiness_score_via_frontend_input()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_response_contains_required_contract_fields()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_valid_unauthenticated_request_succeeds_in_dev()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_no_connectors_means_zero_confidence()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_no_connectors_means_zero_health()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_response_has_no_fabricated_fields()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_stale_evidence_state_is_exposed()** (3 connections) — `tests/test_backend_contract_verification.py`
- **.test_invalid_assessment_id_returns_404()** (2 connections) — `tests/test_backend_contract_verification.py`
- **Verify the /api/clinic/readiness/{org_id} endpoint enforces the configured auth…** (1 connections) — `tests/test_backend_contract_verification.py`
- **In dev/staging with AUTH_REQUIRED=false: unauthenticated requests succeed. This…** (1 connections) — `tests/test_backend_contract_verification.py`
- **Verify the DailyReadinessReport contract shape: all required fields present.…** (1 connections) — `tests/test_backend_contract_verification.py`
- **INVARIANT: Absence of evidence must never become evidence of readiness. When no…** (1 connections) — `tests/test_backend_contract_verification.py`
- **GET /api/clinic/readiness/{non_existent_id} → gracefully handled.** (1 connections) — `tests/test_backend_contract_verification.py`
- **Scoring must remain server-side/deterministic. Frontend cannot inject a score…** (1 connections) — `tests/test_backend_contract_verification.py`
- **Create a minimal org in the test database.** (1 connections) — `tests/test_backend_contract_verification.py`
- **Core product invariant: No evidence → no inferred readiness. These tests verify…** (1 connections) — `tests/test_backend_contract_verification.py`
- **When org has no connectors, verification confidence must be 0.** (1 connections) — `tests/test_backend_contract_verification.py`
- **When org has no connectors, clinic_health_pct must not be 100.** (1 connections) — `tests/test_backend_contract_verification.py`
- **Stale evidence must not be silently treated as current. The verification…** (1 connections) — `tests/test_backend_contract_verification.py`
- **Response must not contain any legacy fabricated default fields like || 98, ||…** (1 connections) — `tests/test_backend_contract_verification.py`

## Relationships

- [Organization](Organization.md) (3 shared connections)
- [TestOrganizationIsolation](TestOrganizationIsolation.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)

## Source Files

- `tests/test_backend_contract_verification.py`

## Audit Trail

- EXTRACTED: 37 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*