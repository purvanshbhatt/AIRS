# Integrations Guide

ResilAI supports both pull-based and push-based integration models.

## API Key Integrations (Pull)

Use org-scoped API keys for machine-to-machine access.

- Create API key: `POST /api/orgs/{org_id}/api-keys`
- Read latest score: `GET /api/external/latest-score`

Keys are shown once and stored hashed server-side.

## Webhooks (Push)

Send assessment events to external systems.

- Create webhook: `POST /api/orgs/{org_id}/webhooks`
- List webhooks: `GET /api/orgs/{org_id}/webhooks`
- Disable webhook: `DELETE /api/webhooks/{id}`
- Test delivery: `POST /api/webhooks/{id}/test`

## External Findings (Demo Path)

- Seed synthetic Splunk findings: `POST /api/integrations/mock/splunk-seed`
- List external findings: `GET /api/integrations/external-findings?source=splunk`

## Security Notes

- Restrict API keys to least privilege scopes
- Use webhook signing secrets
- Rotate keys on suspected exposure
