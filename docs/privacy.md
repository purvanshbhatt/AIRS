# Privacy & Data Handling

## Overview

AIRS is designed with privacy by design principles. This document explains what data is collected, how it's used, and how to manage your data.

## Data Categories

### User Account Data
| Data | Purpose | Storage |
|------|---------|---------|
| Email address | Authentication, notifications | Firebase Auth |
| Display name | UI personalization | Firebase Auth |
| Firebase UID | User identification | All tables |

### Organization Data
| Data | Purpose | Storage |
|------|---------|---------|
| Organization name | Display, reports | Cloud SQL |
| Industry (optional) | Baseline comparison | Cloud SQL |
| Size category (optional) | Baseline comparison | Cloud SQL |
| Contact info (optional) | Report metadata | Cloud SQL |

### Assessment Data
| Data | Purpose | Storage |
|------|---------|---------|
| Assessment answers | Scoring calculation | Cloud SQL |
| Computed scores | Results display | Cloud SQL |
| Generated findings | Gap analysis | Cloud SQL |
| Timestamps | Audit trail | Cloud SQL |

### Report Data
| Data | Purpose | Storage |
|------|---------|---------|
| PDF files | Download, archive | Cloud Storage |
| Report metadata | Library management | Cloud SQL |
| Snapshot data | Report regeneration | Cloud SQL (JSON) |

## Data Retention

### Default Retention Periods

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| User accounts | Until deletion requested | Account functionality |
| Organizations | Until user deletes | Assessment association |
| Assessments | Until user deletes | Historical comparison |
| Reports | Until user deletes | Archive access |
| Application logs | 30 days | Troubleshooting |
| Audit logs | 90 days | Security investigation |

### Demo Data
Demo environment data may be purged periodically:
- Demo assessments: 7 days
- Demo reports: 7 days
- Anonymous demo accounts: 30 days

## Data Access

### Who Can Access Your Data

| Actor | Access Level | Purpose |
|-------|--------------|---------|
| You | Full CRUD | Normal usage |
| AIRS Admin | Read-only (support) | Troubleshooting with consent |
| Google Cloud | Infrastructure | Hosting, no data access |
| No third parties | None | Data not shared or sold |

### Tenant Isolation
- Your data is isolated from other users
- Cross-tenant access is technically prevented
- Queries are scoped by your user ID

## Data Deletion

### Self-Service Deletion

#### Delete Assessment
```
DELETE /api/assessments/{id}
```
- Removes assessment, answers, scores, findings
- Cascade deletes related data

#### Delete Organization
```
DELETE /api/orgs/{id}
```
- Removes organization and all assessments
- Requires confirmation (has dependent data)

#### Delete Report
```
DELETE /api/reports/{id}
```
- Removes report metadata and PDF file

### Account Deletion
To delete your entire account:
1. Delete all organizations (cascades to assessments/reports)
2. Contact support for Firebase account deletion
3. Or delete via Firebase Auth directly

### Deletion Verification
After deletion:
- Data removed from active database
- Backup retention: 7 days (Cloud SQL)
- Log references anonymized after 30 days

## Data Export

### Assessment Export
Download your data via:
- **PDF Report:** Full formatted export
- **API Access:** JSON via `/api/assessments/{id}/summary`

### Bulk Export
Contact support for bulk data export requests.

## Data Processing

### Where Data is Processed
| Component | Location | Provider |
|-----------|----------|----------|
| Application | US (Cloud Run) | Google Cloud |
| Database | US (Cloud SQL) | Google Cloud |
| File Storage | US (Cloud Storage) | Google Cloud |
| Authentication | Global (Firebase) | Google/Firebase |

### AI Processing (Optional)
When LLM features are enabled:
- Assessment summaries sent to Google Gemini API
- No PII included in prompts
- Responses not stored by Google (API terms)
- Can be disabled entirely

## Cookies & Tracking

### Essential Cookies Only
- Firebase authentication tokens (session)
- No analytics cookies
- No advertising cookies
- No cross-site tracking

### Local Storage
- Draft assessment autosave (browser only)
- UI preferences (theme, etc.)
- Cleared on logout

## Children's Privacy

AIRS is not intended for users under 18. We do not knowingly collect data from minors.

## Changes to Privacy Practices

- Changes documented in release notes
- Material changes communicated via email
- Continued use constitutes acceptance

## Contact

For privacy questions or data requests:
- **Email:** privacy@[domain]
- **Response Time:** 5 business days

## Summary

| Practice | AIRS Approach |
|----------|---------------|
| Data minimization | Collect only what's needed |
| Purpose limitation | Used only for assessment |
| User control | Self-service deletion |
| Transparency | This documentation |
| Security | See [security.md](security.md) |
