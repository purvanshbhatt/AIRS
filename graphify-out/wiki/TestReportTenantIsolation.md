# TestReportTenantIsolation

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestReportTenantIsolation** (6 connections) — `tests/test_reports.py`
- **.test_user_b_cannot_access_user_a_report_by_id()** (3 connections) — `tests/test_reports.py`
- **.test_user_b_cannot_delete_user_a_report()** (3 connections) — `tests/test_reports.py`
- **.test_user_b_cannot_download_user_a_report()** (3 connections) — `tests/test_reports.py`
- **.test_user_b_cannot_see_user_a_reports()** (3 connections) — `tests/test_reports.py`
- **Test that reports are properly isolated per user.** (1 connections) — `tests/test_reports.py`
- **User B should not see User A's reports in list.** (1 connections) — `tests/test_reports.py`
- **User B should get 404 when trying to access User A's report.** (1 connections) — `tests/test_reports.py`
- **User B should get 404 when trying to download User A's report.** (1 connections) — `tests/test_reports.py`
- **User B should get 404 when trying to delete User A's report.** (1 connections) — `tests/test_reports.py`

## Relationships

- [make_auth_override](make_auth_override.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_reports.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*