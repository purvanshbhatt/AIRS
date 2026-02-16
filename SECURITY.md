# Security Policy

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
