# Changelog

## 2026-02-14

### Added
- Integration-ready backend primitives:
  - API key lifecycle endpoints (`/api/orgs/{org_id}/api-keys`, list/revoke)
  - API key-protected external pull endpoint (`/api/external/latest-score`)
  - Webhook lifecycle + test endpoints (`/api/orgs/{org_id}/webhooks`, `/api/webhooks/{id}/test`)
  - Background webhook dispatch on assessment scoring with retry/backoff logging
- Roadmap tracker persistence model and endpoints (`/api/assessments/{id}/roadmap*`)
- Frontend Integrations page for API key generation and webhook management
- Environment mode support for `local/staging/prod` and staging env file (`gcp/env.staging.yaml`)
- Staging-safe deployment workflow and production overwrite guard usage in docs
- New documentation:
  - `docs/LOCAL_DEV.md`
  - `docs/STAGING_DEPLOY.md`
  - `docs/dev/contract_map.md`

### Changed
- LLM narrative implementation migrated to `google.genai` (google-genai SDK)
- `/health/llm` now exposes lightweight runtime checks
- Analytics/framework/roadmap contracts aligned for results UI compatibility
- Frontend build scripts now support explicit `staging` and `production` modes

### Safety
- Deployment script requires explicit `--prod` confirmation for `airs-api` production service
- Local development defaults to isolated SQLite (`airs_dev.db`) and localhost CORS
