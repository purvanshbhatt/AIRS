# Security Policy

## Analytics Opt-Out and Privacy Controls

ResilAI provides first-class privacy controls at the organisation level:

- **Per-org analytics flag**: Each organisation can disable anonymised telemetry via
  `PATCH /api/orgs/{id}/analytics` with `{"analytics_enabled": false}`.
- **Settings UI**: The toggle in **Settings → Privacy & Analytics** persists the preference
  to both `localStorage` (instant) and the backend database (durable).
- **What is collected when enabled**: Anonymised feature usage signals (e.g., tab viewed,
  report downloaded). No assessment content, no PII, no scoring data.
- **What is never collected**: Assessment answers, finding details, LLM-generated narratives,
  user email addresses, or any personally identifiable information.
- **Right to erasure**: Contact `purvansh95b@gmail.com` to request deletion of all data
  associated with your organisation.

## Supported Versions

| Version | Supported |
| --- | --- |
| `v0.2.x` | Yes |
| `v0.1.x` | Limited (critical fixes only) |
| `< v0.1` | No |

## Reporting a Vulnerability

Please report vulnerabilities privately to:

- Email: `purvansh95b@gmail.com`
- Subject: `ResilAI Security Disclosure`

Please include:
- A clear description of the issue
- Reproduction steps or proof of concept
- Potential impact
- Suggested remediation (if known)

We will acknowledge reports as quickly as possible and coordinate responsible disclosure.

## Data Handling Overview

ResilAI is designed to support environment isolation and least privilege:

- Local, staging, and production are configured separately
- Sensitive runtime values are expected via environment variables / secret bindings
- API keys are stored hashed, not as plaintext
- Webhook secrets are used for signed delivery verification
- Assessment scoring remains deterministic and auditable

## Authentication and Encryption Notes

- Frontend authentication is handled through Firebase Auth
- Backend authorization uses bearer tokens and scoped API keys
- Traffic to hosted environments is expected over HTTPS/TLS
- Database access is restricted to service runtime configuration
- LLM integration uses `google-genai` credentials configured through environment variables

## Security Best Practices for Operators

- Do not commit `.env` files or secrets to source control
- Rotate exposed credentials immediately
- Restrict Firebase API keys by domain and API usage
- Use Cloud Secret Manager for staging/production secrets
- Run security scans in CI before production deployments
