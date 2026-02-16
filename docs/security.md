# Security Posture

## Overview

ResilAI is built with security as a foundational requirement. This document outlines the security controls, architecture decisions, and practices that protect your assessment data.

## Authentication

### Firebase Authentication
- **Provider:** Google Firebase Authentication
- **Methods:** Email/password, Google OAuth
- **Token Validation:** JWT tokens validated on every API request
- **Session Management:** Stateless authentication with short-lived tokens

### Implementation Details
```
Client â†’ Firebase SDK â†’ JWT Token â†’ API Gateway â†’ Token Validation â†’ Request Processing
```

- Tokens are validated server-side using Firebase Admin SDK
- Invalid/expired tokens return 401 Unauthorized
- No session cookies or server-side session storage

## Tenant Isolation

### Multi-Tenant Architecture
ResilAI implements strict tenant isolation at the database level:

| Resource | Isolation Method |
|----------|------------------|
| Organizations | `owner_uid` column filter |
| Assessments | `owner_uid` column filter |
| Reports | `owner_uid` column filter |
| Answers | Via assessment ownership |

### Enforcement
- Every database query includes `owner_uid` filter
- Cross-tenant access returns 404 (not 403) to prevent enumeration
- Audit logging includes user context for all operations

### Example Query Pattern
```sql
-- All queries include tenant filter
SELECT * FROM assessments 
WHERE id = :assessment_id 
AND owner_uid = :current_user_uid
```

## Data Storage

### Cloud SQL (PostgreSQL)
- **Location:** Google Cloud SQL (regional)
- **Encryption:** AES-256 at rest (Google-managed keys)
- **Network:** Private IP only, no public access
- **Connections:** Cloud SQL Auth Proxy with IAM authentication

### Cloud Storage (Reports)
- **Access:** Signed URLs with expiration (15 minutes)
- **Encryption:** AES-256 at rest
- **Permissions:** Service account access only
- **Public Access:** Disabled at bucket level

## API Security

### Request Tracing
Every request includes:
- **Request ID:** UUID for correlation (`X-Request-ID` header)
- **Timestamp:** ISO 8601 request time
- **User Context:** Firebase UID (logged, not exposed)

### Rate Limiting
- Implemented at Cloud Run level
- Per-user rate limits for write operations
- Graceful degradation under load

### Input Validation
- Pydantic schemas for all request bodies
- SQL injection prevention via SQLAlchemy ORM
- Path parameter validation

### Error Responses
```json
{
  "error": {
    "code": "ASSESSMENT_NOT_FOUND",
    "message": "Assessment not found",
    "request_id": "abc123-def456"
  }
}
```
- No stack traces in production
- Request ID for support correlation
- Generic messages to prevent information disclosure

## Infrastructure

### Cloud Run
- **Scaling:** 0-10 instances (auto-scaling)
- **Concurrency:** 80 requests per instance
- **Timeout:** 300 seconds max
- **Memory:** 1GB per instance
- **CPU:** 2 vCPU per instance

### Network Security
- HTTPS only (TLS 1.2+)
- Cloud Run managed certificates
- No direct database access from internet

### Secrets Management
- **Method:** Environment variables via Cloud Run
- **Storage:** Google Secret Manager
- **Rotation:** Manual, documented process
- **Access:** IAM-controlled, principle of least privilege

## Logging & Monitoring

### Structured Logging
```json
{
  "timestamp": "2026-01-25T12:00:00Z",
  "level": "INFO",
  "request_id": "abc123",
  "event": "assessment.created",
  "assessment_id": "...",
  "user_uid": "...(hashed)"
}
```

### What We Log
- API requests (method, path, status, duration)
- Authentication events (login, token refresh)
- Business events (assessment created, score computed)
- Errors with stack traces (sanitized)

### What We Don't Log
- Full request/response bodies
- Sensitive PII (emails in plain text)
- Passwords or tokens
- Assessment answers (content)

### Retention
- Application logs: 30 days
- Audit logs: 90 days
- Error logs: 90 days

## Vulnerability Management

### Dependencies
- Weekly automated dependency scanning
- Critical vulnerabilities patched within 24 hours
- `requirements.txt` pinned versions

### Code Security
- No secrets in source control
- `.gitignore` for sensitive files
- Pre-commit hooks for secret detection

## Security Contacts

For security concerns or vulnerability reports:
- **Email:** purvansh95b@gmail.com
- **Response Time:** 24-48 hours for initial acknowledgment

## Compliance Notes

ResilAI is designed with compliance-friendly architecture:
- SOC 2 Type II controls alignment
- GDPR data handling capabilities
- Audit trail for all data modifications

*Note: ResilAI itself does not hold compliance certifications. Organizations should conduct their own compliance assessments.*
