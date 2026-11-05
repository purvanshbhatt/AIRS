# auditor_view

> 25 nodes · cohesion 0.11

## Key Concepts

- **auditor_view()** (8 connections) — `app/api/auditor_view.py`
- **generate_auditor_link()** (8 connections) — `app/api/auditor_view.py`
- **get_auditor_links()** (8 connections) — `app/api/auditor_view.py`
- **services/auditor_view.py** (8 connections) — `app/services/auditor_view.py`
- **revoke_auditor_link()** (7 connections) — `app/api/auditor_view.py`
- **create_auditor_link()** (5 connections) — `app/services/auditor_view.py`
- **_hash_token()** (5 connections) — `app/services/auditor_view.py`
- **revoke_token()** (5 connections) — `app/services/auditor_view.py`
- **validate_token()** (5 connections) — `app/services/auditor_view.py`
- **Session** (4 connections)
- **list_active_tokens()** (4 connections) — `app/services/auditor_view.py`
- **User** (3 connections)
- **get** (2 connections)
- **delete** (1 connections)
- **post** (1 connections)
- **GET /api/governance/auditor-view?token=...** (1 connections) — `app/api/auditor_view.py`
- **POST /api/governance/orgs/{org_id}/auditor-link** (1 connections) — `app/api/auditor_view.py`
- **GET /api/governance/orgs/{org_id}/auditor-links** (1 connections) — `app/api/auditor_view.py`
- **DELETE /api/governance/orgs/{org_id}/auditor-link** (1 connections) — `app/api/auditor_view.py`
- **Auditor View Service – shareable read-only access for external auditors.…** (1 connections) — `app/services/auditor_view.py`
- **List non-expired, non-revoked tokens for an org (metadata only).** (1 connections) — `app/services/auditor_view.py`
- **SHA-256 hash for storage (never store raw tokens).** (1 connections) — `app/services/auditor_view.py`
- **Generate a time-limited auditor access token. Returns dict with token,…** (1 connections) — `app/services/auditor_view.py`
- **Validate an auditor token. Returns metadata if valid, None otherwise.…** (1 connections) — `app/services/auditor_view.py`
- **Revoke an auditor token. Returns True if found and revoked.** (1 connections) — `app/services/auditor_view.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (12 shared connections)
- [User](User.md) (3 shared connections)
- [_make_org](_make_org.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/api/auditor_view.py`
- `app/services/auditor_view.py`

## Audit Trail

- EXTRACTED: 47 (92%)
- INFERRED: 4 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*