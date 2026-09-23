# _verify_org

> 19 nodes · cohesion 0.17

## Key Concepts

- **_verify_org()** (11 connections) — `app/api/audit_calendar.py`
- **create_entry()** (9 connections) — `app/api/audit_calendar.py`
- **list_entries()** (9 connections) — `app/api/audit_calendar.py`
- **update_entry()** (9 connections) — `app/api/audit_calendar.py`
- **audit_forecast()** (8 connections) — `app/api/audit_calendar.py`
- **delete_entry()** (8 connections) — `app/api/audit_calendar.py`
- **Session** (6 connections)
- **User** (6 connections)
- **get** (2 connections)
- **AuditCalendarCreate** (1 connections)
- **delete** (1 connections)
- **post** (1 connections)
- **put** (1 connections)
- **DELETE /api/governance/{org_id}/audit-calendar/{entry_id}** (1 connections) — `app/api/audit_calendar.py`
- **GET /api/governance/{org_id}/audit-calendar/{entry_id}/forecast** (1 connections) — `app/api/audit_calendar.py`
- **Verify org exists and belongs to user.** (1 connections) — `app/api/audit_calendar.py`
- **GET /api/governance/{org_id}/audit-calendar** (1 connections) — `app/api/audit_calendar.py`
- **POST /api/governance/{org_id}/audit-calendar** (1 connections) — `app/api/audit_calendar.py`
- **PUT /api/governance/{org_id}/audit-calendar/{entry_id}** (1 connections) — `app/api/audit_calendar.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [User](User.md) (6 shared connections)
- [AuditCalendarService](AuditCalendarService.md) (5 shared connections)
- [._setup](_setup.md) (1 shared connections)

## Source Files

- `app/api/audit_calendar.py`

## Audit Trail

- EXTRACTED: 43 (88%)
- INFERRED: 6 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*