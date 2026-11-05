# AuditCalendarService

> 29 nodes · cohesion 0.10

## Key Concepts

- **AuditCalendarService** (38 connections) — `app/services/governance/audit_calendar.py`
- **AuditCalendarCreate** (18 connections) — `app/schemas/audit_calendar.py`
- **.update()** (6 connections) — `app/services/governance/audit_calendar.py`
- **AuditCalendarEntry** (6 connections)
- **.create()** (5 connections) — `app/services/governance/audit_calendar.py`
- **.get()** (5 connections) — `app/services/governance/audit_calendar.py`
- **.test_tenant_isolation()** (5 connections) — `tests/test_governance.py`
- **TestAuditCalendarEnrich** (5 connections) — `tests/test_governance.py`
- **.enrich_response()** (4 connections) — `app/services/governance/audit_calendar.py`
- **.get_forecast()** (4 connections) — `app/services/governance/audit_calendar.py`
- **.test_future_audit_is_upcoming_within_reminder()** (4 connections) — `tests/test_governance.py`
- **.test_future_audit_not_upcoming_outside_reminder()** (4 connections) — `tests/test_governance.py`
- **.test_past_audit_days_until_is_zero()** (4 connections) — `tests/test_governance.py`
- **.list_all()** (3 connections) — `app/services/governance/audit_calendar.py`
- **.delete()** (2 connections) — `app/services/governance/audit_calendar.py`
- **.__init__()** (2 connections) — `app/services/governance/audit_calendar.py`
- **Schema for creating an audit calendar entry.** (1 connections) — `app/schemas/audit_calendar.py`
- **AuditCalendarCreate** (1 connections)
- **Session** (1 connections)
- **Convert model to response with computed fields.** (1 connections) — `app/services/governance/audit_calendar.py`
- **Generate pre-audit risk forecast by cross-referencing findings with the audit…** (1 connections) — `app/services/governance/audit_calendar.py`
- **Service for audit calendar CRUD and forecasting.** (1 connections) — `app/services/governance/audit_calendar.py`
- **Create a new audit calendar entry.** (1 connections) — `app/services/governance/audit_calendar.py`
- **Get a single entry by ID.** (1 connections) — `app/services/governance/audit_calendar.py`
- **List all audit calendar entries for the org.** (1 connections) — `app/services/governance/audit_calendar.py`
- *... and 4 more nodes in this community*

## Relationships

- [Organization](Organization.md) (14 shared connections)
- [_make_audit_entry](_make_audit_entry.md) (9 shared connections)
- [._setup](_setup.md) (8 shared connections)
- [_verify_org](_verify_org.md) (5 shared connections)
- [_make_org](_make_org.md) (5 shared connections)
- [TestAuditForecast](TestAuditForecast.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/schemas/audit_calendar.py`
- `app/services/governance/audit_calendar.py`
- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 83 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*