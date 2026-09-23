# TestReportTenantIsolationV2

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestReportTenantIsolationV2** (4 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_report_get_returns_none_for_wrong_owner()** (3 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_report_query_scoped_to_owner()** (3 connections) — `tests/test_tenant_isolation_v2.py`
- **Validate reports are scoped to owner_uid.** (1 connections) — `tests/test_tenant_isolation_v2.py`
- **Report queries must be filtered by owner_uid.** (1 connections) — `tests/test_tenant_isolation_v2.py`
- **Getting a report that doesn't belong to the user returns None.** (1 connections) — `tests/test_tenant_isolation_v2.py`

## Relationships

- [organizations.py](organizations.py.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_tenant_isolation_v2.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*