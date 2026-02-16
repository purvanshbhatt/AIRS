# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and follows Semantic Versioning.

## [Unreleased]

### Added
- Public launch documentation and repository community templates
- GitHub Pages-ready `docs/` navigation pages
- CI and automated release workflow definitions

### Changed
- Repository messaging standardized for ResilAI public beta positioning

## [0.2.0-staging] - 2026-02-16

### Added
- Integration-ready backend primitives:
  - API key lifecycle endpoints (`/api/orgs/{org_id}/api-keys`, list, revoke)
  - API key-protected external pull endpoint (`GET /api/external/latest-score`)
  - Webhook lifecycle and test endpoints
  - Background webhook dispatch on assessment scoring with retry/backoff logging
- Roadmap tracker persistence model and endpoints (`/api/assessments/{id}/roadmap*`)
- Frontend Integrations page for API keys, webhooks, and external findings
- Environment mode support for local/staging/production

### Changed
- LLM narrative integration migrated to `google-genai`
- `/health/llm` exposes lightweight runtime status checks
- Frontend build scripts support explicit staging/production modes
- Results and analytics contract alignment for dashboard compatibility

### Security
- Deployment safeguards for production service overwrite (`--prod` guard)
- Local development defaults to isolated SQLite and local CORS

## [0.1.0-beta] - 2026-02-14

### Added
- Baseline production demo and end-to-end assessment flow
- Deterministic scoring and narrative generation pipeline
- PDF report generation and framework mapping outputs
- Initial docs for local development and staging deployment
