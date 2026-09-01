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

Next Tasks:
- Phase B — Sprint 1.8 S1.8-B3: AI finding rules AI-001..AI-010 (READY, next).
- Phase B — Sprint 1.8 S1.8-B5: AiAsset enum expansion (READY).
- Phase C — Sprint 1.8 S1.8-C1: EvidenceAdapter ABC + EvidenceRegistry (READY).
- Sprint 2 prep — S2-B4: Organization model is_clone + source_org_id (READY).
