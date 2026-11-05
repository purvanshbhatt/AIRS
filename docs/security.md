# ResilAI Security Overview

This page summarizes platform security practices. For coordinated disclosure policy, see the repository root file `SECURITY.md`.

## Authentication

- Frontend authentication uses Firebase Auth
- Backend validates bearer tokens and scoped access
- Auth requirements are controlled by environment policy

## Authorization and Tenant Scope

- Organization-scoped access checks are enforced server-side
- API resources are filtered by authenticated ownership context
- Cross-tenant access is denied

## Data Protection

- Database and storage access are controlled by runtime identity and configuration
- API keys are stored hashed
- Webhook secrets are used for signed delivery support
- TLS/HTTPS is expected in hosted environments

## Runtime and Infrastructure

- Backend runs on Google Cloud Run
- Frontend runs on Firebase Hosting
- Environment separation is maintained across local, staging, and production

## API Security Controls

- Input validation through typed schemas
- Structured error responses without sensitive internals
- Request-level diagnostics via health and status endpoints

## Logging and Monitoring

ResilAI supports operational diagnostics through:

- `/health`
- `/health/system`
- `/health/llm`
- `/health/cors`

## Secret Management

- Sensitive values should not be committed to source control
- Staging/production secrets should be provided via environment bindings or secret manager
- Exposed keys should be rotated immediately

## Security Contact

Report security issues privately to `purvansh95b@gmail.com`.
