# Active Context
Date: 2026-09-21
Status: Daily Backup Sync Verified & Live Origin Push Completed (35/35 Pytest Passing)

## Recent Actions
- Daily Backup Sync GitHub Actions Workflow & Remote Push (`.github/workflows/daily-backup-sync.yml`):
  - Verified cron schedule `0 4 * * *` (Daily at 4:00 AM UTC / midnight EST) and `workflow_dispatch` manual trigger.
  - Confirmed repository checkout with `fetch-depth: 0` and `contents: write` permissions.
  - Confirmed branch management: checks out or creates `daily-sync` branch, fetches and merges latest commits from `staging`.
  - Live Synchronization & Upstream Push: Successfully merged latest `staging` commit `61dbc32` into `daily-sync` (merge commit `fbf124d`), cleanly pushed `daily-sync` to `origin`.
  - Confirmed multi-tier branch protection: pre-push git hook and step-level validation guard explicitly blocking any push targeting `main` or `demo-stable`.
  - Confirmed Git ref integrity: audited hierarchical ref `refs/heads/backup/dev-before-sync` preventing collisions with loose `backup` ref (`fatal: 'refs/heads/backup/dev-before-sync' exists; cannot create 'refs/heads/backup'`), keeping `daily-sync` as the canonical secure snapshot branch per specifications.
  - Confirmed real-time audit logging: writes structured markdown audit log with commit SHA, sync status, source/target branches, run ID, and UTC timestamp to `$GITHUB_STEP_SUMMARY`.
  - Automated test suite `TestDailyBackupSyncWorkflow` in `tests/test_daily_git_sync.py` verified green (35/35 tests passing).

- Multi-Vertical Host & Path Aware Positioning Experiment Deployed to Staging:
- Phase 20 Live AWS Deployment & Security Hub Integration:
  - Live AWS CloudFormation Stack Deployed: Executed `infra/aws-test/deploy.sh` creating stack `resilai-test-env` in `us-east-1` (account `505467908065`).
  - Active Resources: Security Hub (`arn:aws:securityhub:us-east-1:505467908065:hub/default`), GuardDuty (`654eddc77fa54d3bbd4bce47e3dc818c`), unencrypted S3 bucket `resilai-test-505467908065-us-east-1`, overpermissive IAM test role `resilai-test-overpermissive-role`, connector IAM role `arn:aws:iam::505467908065:role/resilai-test-connector-role`, and CloudTrail `resilai-test-trail`.
  - Installed `boto3` and `awscrt` in virtual environment; verified live connectivity: `describe_hub()` HTTP 200 (122 ms latency), permissions valid.
  - Live End-to-End Pipeline Tested: Registered live connector via `tests/aws_integration/configure_connector.py`; executed live sync against AWS Security Hub in 778.00 ms with success=True.
  - Live Integration Test Suite (`tests/aws_integration/test_live_aws.py`): 5/5 live tests passed; full test suite 78/78 tests passed in 8.76s.
  - Validation Matrix Updated: `AWS Security Hub API Reachability: PROVEN`, `AWS Security Hub Ingestion: PROVEN`, `AWS_ENVIRONMENT_STATUS=DEPLOYED` written to `tests/aws_integration/VALIDATION_REPORT.md` and `validation_report.json`.
  - AWS Evidence Adapter & Integration Test Suite (39/39 Passing):
    - Created canonical `app/services/evidence/adapters/aws_security_hub.py` and registered in `ConnectorManager`.
    - Implemented 39 unit tests in `tests/aws_integration/` covering authentication, STS assume-role, permission validation, pagination, normalization, TelemetryEvent deduplication, hash determinism, tenant isolation (`org_id`), negative cases, and deterministic scoring invariants (AST validation of zero LLM imports).
  - SHA-256 Evidence Integrity Enforcement (Phase A8):
    - Created `app/services/evidence/integrity.py` implementing `canonicalize_payload`, `compute_evidence_hash`, and `verify_evidence_hash`.
    - Added `NormalizedEvidence.verify_integrity()` and delegated hashing in `app/schemas/evidence.py`.
    - Updated `EvidenceOrchestrator.ingest_collection_result` in `app/services/evidence/orchestrator.py` to verify evidence integrity *before* writing to `EvidenceLedger` or `NormalizedEvidenceRecord`, failing closed (`EvidenceIntegrityError`) on tampered payloads.
    - 7/7 unit tests passing in `tests/test_evidence_integrity.py`.
  - Server-Side PDF HMAC Signature & Cryptographic Traceability:
    - Created `app/reports/hmac_service.py` implementing `sign_report_content`, `verify_report_hmac`, `build_audit_metadata`, and `compute_content_sha256`. Uses server-side `REPORT_HMAC_SECRET` (or falls back to `SECRET_KEY`); secret is never exposed to browser, Gemini, or PDF text.
    - Updated `app/reports/pdf.py` to embed cryptographic audit verification section with Report ID, Organization ID, UTC Timestamp, Content SHA-256, and HMAC-SHA256 signature. Set `pageCompression=0` in `SimpleDocTemplate` for audit stream inspection.
    - 7/7 unit tests passing in `tests/test_pdf_hmac.py`.
  - Frontend Demo Sandbox Boundary:
    - Updated `frontend/src/components/common/ContextualDemoBanner.tsx` and `frontend/src/components/common/SimulatedTelemetryBanner.tsx` to prominently display `DEMO ENVIRONMENT • SIMULATED DATA` with the exact mandated copy: *"This environment uses simulated security telemetry. Results shown here are not evidence from a connected customer environment."*
    - Verified TypeScript compiles cleanly (`node node_modules/typescript/bin/tsc --noEmit` exit code 0).
  - Validation Reports:
    - Generated `tests/aws_integration/VALIDATION_REPORT.md` and `tests/aws_integration/validation_report.json` with honest capability classification: AWS Security Hub ingestion (`PARTIALLY_PROVEN`), direct EC2/S3/CloudTrail/CloudWatch (`NOT_IMPLEMENTED`), connector credential encryption (`GAP`), SHA-256 integrity (`PROVEN`), PDF HMAC (`PROVEN`), and scoring invariance (`PROVEN`).
  - Full Regression Suite:
    - 73/73 tests passing in `.venv_linux/bin/pytest` across `tests/aws_integration/`, `test_evidence_integrity.py`, `test_pdf_hmac.py`, `test_multicloud_portability.py`, and `test_dr_restore.py`.
