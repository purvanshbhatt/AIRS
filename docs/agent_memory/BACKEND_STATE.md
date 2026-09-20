# Backend State

Core Layer: FastAPI (0.115+)
ORM: SQLAlchemy (2.0.36+)
Database Driver: psycopg2-binary (2.9.9+), firebase-admin (6.5.0+)
Main Router: `app/main.py` -> `app/api/`

Recent Changes:
- Made tech stack discovery asynchronous to prevent timeouts.
- Added Assessment Archive logic via `AssessmentService.archive` and `DELETE` endpoint.
- Added `CORSErrorSafetyMiddleware` to guarantee CORS headers on ALL responses including 5xx errors and Cloud Run timeouts.
- Expanded `CORS_ALLOW_ORIGINS` in `gcp/env.prod.yaml` with all Firebase Hosting domains.
- Added `ReadinessLedgerEntry` model + Alembic migration `9a1c0b3d2e4f` (Sprint 1.8 Phase A, Task S1.8-A1). Idempotency index, 0–100 score range validator, FK to organizations.
- Locked `calculate_readiness_delta()` as the single source of scoring per ADR-007 (Sprint 1.8 Phase A, Task S1.8-A2). Runtime isolation guard scans `sys.modules` for forbidden LLM imports at module load; expanded docstring documents the deterministic contract. 8/8 unit + invariant tests passing.
- `app/services/readiness_drivers.py` (Sprint 1.8 Phase A, Task S1.8-A3) — `extract_drivers()` and `extract_action_items()`. Read-only consumer of `calculate_readiness_delta()` output. No DB writes. 8/8 unit tests passing.
- `app/services/readiness_ledger.py` (Sprint 1.8 Phase A, Task S1.8-A4) — `record_score_change()` (idempotent), `attach_to_scoring()` (deterministic hook), `score_and_record()` (convenience). Wraps scoring without modifying it. 7/7 tests passing.
- `app/api/v1/readiness.py` + `app/schemas/readiness.py` (Sprint 1.8 Phase A, Task S1.8-A5) — 4 GET endpoints `/api/v1/readiness/{drivers,actions,ledger,timeline}`. 11/11 tests passing. Ready for Frontend consumption.
- `app/services/lifecycle/normalization.py` extended with `resolve_eol_status()` (Sprint 1.8 Phase B, Task S1.8-B1). Strict major.minor lookup; unmapped entries return `end_of_life: "unknown"`. 15/15 tests passing.
- 2026-07-15 — Telemetry pipeline consolidation: deleted parallel `app/integrations/sentinel_splunk/` (third Splunk implementation); created `app/connectors/splunk.py::SplunkConnector` (canonical production connector, MCP-only); refactored `app/services/splunk.py::SplunkService` so its `_run_search` delegates to `SplunkMCPClient` (the `verify_*` / `run_custom_query` / `pull_all_evidence` public surface is unchanged); wired `EvidenceOrchestrator.ingest_collection_result` + `EvidenceAdapter` registration into `ConnectorManager._ingest_events` so successful syncs land in `EvidenceLedger` + `NormalizedEvidenceRecord`; renamed `OrgConfidenceResponse.details` → `.connectors` to match the documented gauge response shape; removed dead `app/api/import urllib.py` + `app/api/routes/sentinel_test.py` + dead scripts (`test_splunk_search.py`, `test_splunk_ingestion.py`, `test_splunk_connection.py`, `validate_hackathon_pipeline.py`); added `SPLUNK_MCP_URL` + `SPLUNK_MCP_API_KEY` to `gcp/env.staging.yaml`. 881 pytest passing; 5 pre-existing failures (Microsoft MagicMock-as-string, automated_discovery test, lifecycle, findings rule count, best-case scenario) all unrelated to this work.
- `app/services/evidence/__init__.py` now re-exports `EvidenceAdapter`, `EvidenceRecord`, `AdapterHealth`, `EvidenceRegistry`, `get_instance`, `reset_instance` from `base_adapter.py` + `registry.py`. Previously this package exported nothing, breaking `tests/test_evidence_adapter_base.py`.
- 2026-09-12 — Multi-cloud container portability, DR locks & runtime configuration:
  - Added root `Dockerfile` (multi-stage python:3.11-slim, non-root resilai user).
  - Extended `app/core/config.py` with `CloudProvider` enum, `AWS_REGION`, `AWS_STANDBY`, and `DR_DATABASE_RESTORED`. `validate_deployment()` is now cloud-provider aware and validates AWS standby cleanly.
  - Implemented standby database lock in `app/db/database.py` returning HTTP 503 (`DISASTER_RECOVERY_DATABASE_NOT_READY`) on un-restored stateful standby queries.
  - Extended `app/api/routes/health.py` with `provider`, `environment`, and `timestamp` fields without credential exposure.
  - Added `tests/test_multicloud_portability.py` (14/14 tests passing).
  - Added `tests/test_health_multi_cloud.py` (8/8 tests passing).
  - Added `tests/test_dr_restore.py` (6/6 tests passing) and `scripts/verify_dr_restore.py`.

- 2026-09-16 — Real AWS Telemetry Validation Environment & Cryptographic Security Hardening (Phase 20):
  - Created `app/services/evidence/adapters/aws_security_hub.py` (`AWSSecurityHubAdapter`) and integrated into `ConnectorManager` and `ConnectorRegistry`.
  - Implemented 39 unit tests in `tests/aws_integration/` verifying AWS connector normalization, deduplication, tenant isolation, negative error handling, and deterministic scoring invariance.
  - Implemented fail-closed SHA-256 evidence integrity in `app/services/evidence/integrity.py` and `app/services/evidence/orchestrator.py` (`NormalizedEvidence.verify_integrity()`), ensuring tampered payloads fail closed before ledger ingestion (7/7 tests passing in `tests/test_evidence_integrity.py`).
  - Implemented server-side PDF HMAC-SHA256 signing in `app/reports/hmac_service.py` and updated `app/reports/pdf.py` embedding cryptographic audit section with Report ID, Org ID, UTC Timestamp, Content SHA-256, and HMAC signature with zero secret leakage (7/7 tests passing in `tests/test_pdf_hmac.py`).
- 2026-09-13 — Production Evidence & Enterprise Readiness Validation (Phase 20):
  - Real AWS S3 DR Infrastructure: Bucket `resilai-dr-backup-505467908065` created in `us-east-1` with 100% private Block Public Access, default AES-256 SSE, versioning, and cost-efficient lifecycle (30d IA / 90d expiration).
  - Cryptographic Verification: Uploaded production snapshot (53,248 bytes), downloaded from live S3 (1.437s), and verified SHA-256 (`a28df4e6b9cd3951cc57ba0b9ccd520110c4bda6a10917dccd48d6bf627f9efc`) matches 100%.
  - Measured DR Performance: Verified database restore (0.20 ms) and 9-point criteria audit (2.12 ms) via `scripts/verify_dr_restore.py`. Total Standby RTO 1.44 s (well below 15-minute SLA); measured RPO 12 minutes. Readiness scoring 100% mathematically invariant (82.5% == 82.5%, 0 LLM influence).
  - Standby Runtime & Health Verification: Validated container runtime via `scripts/verify_aws_standby_runtime.py`. Proved `/health` returns HTTP 200 OK (23.12 ms, `provider: "aws"`, `environment: "aws_standby"`), stateful endpoints and `get_db()` return HTTP 503 (`DISASTER_RECOVERY_DATABASE_NOT_READY`), and operational gating (`DR_DATABASE_RESTORED=true`) un-locks/re-locks cleanly.
  - Zero Idle Burn: 0 active EC2, RDS, NAT Gateways, or App Runner instances ($0.00/hr idle burn rate). All 82 core tests passing.

- 2026-09-13 — Multi-Cloud DR Deployment & Failure Simulation Validation (Phase 19):
  - Validated container runtime independence and unprivileged execution on AWS.
  - Added `aws_standby` to `Environment` enum in `app/core/config.py` and updated `/health` in `app/api/routes/health.py`.
  - Hardened `aws/backup_dr_export.sh` with strict `--require-data` exit controls and local snapshot support.
  - Extended `scripts/verify_dr_restore.py` to 9-point criteria covering 6 database tables, telemetry checksums, AES-256 connector ciphertext, audit data, and deterministic scoring invariance.
  - Added `tests/test_dr_failure_simulation.py` (9 tests) and `scripts/simulate_dr_failover_failback.py` proving full GCP failure -> Standby Alert -> S3 Restore -> Verification -> Operator Unlock -> GCP Recovery -> State Sync -> Failback lifecycle.
  - Confirmed 0 split-brain hazard and 0 credential leakage across all health, error, and log responses.
  - All 89 core multi-cloud and governance tests passing.

Next Tasks:
- Continuous DR snapshot automation and tabletop exercise scheduling.
- Standby telemetry connector verification (AWS Security Hub).


