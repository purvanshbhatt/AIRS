# API Reference

Base URL comes from environment configuration.

## Health and Diagnostics

- `GET /health`
- `GET /health/system`
- `GET /health/llm`
- `GET /health/cors`

## Assessments

- `POST /api/assessments`
- `GET /api/assessments`
- `GET /api/assessments/{id}`
- `POST /api/assessments/{id}/answers`
- `POST /api/assessments/{id}/score`
- `GET /api/assessments/{id}/summary`

## Reports

- `GET /api/assessments/{id}/report`
- `GET /api/assessments/{id}/executive-summary`
- `GET /api/assessments/{id}/export`

## Integrations

- `POST /api/orgs/{org_id}/api-keys`
- `GET /api/orgs/{org_id}/api-keys`
- `DELETE /api/api-keys/{id}`
- `POST /api/orgs/{org_id}/webhooks`
- `GET /api/orgs/{org_id}/webhooks`
- `DELETE /api/webhooks/{id}`
- `POST /api/webhooks/{id}/test`

## Public Beta API Docs

Interactive OpenAPI docs are available at:

`https://airs-api-staging-227825933697.us-central1.run.app/docs`
