# TestReportRetrieval

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestReportRetrieval** (4 connections) — `tests/test_reports.py`
- **.test_get_report_not_found()** (3 connections) — `tests/test_reports.py`
- **.test_get_report_with_snapshot()** (3 connections) — `tests/test_reports.py`
- **Test report retrieval endpoints.** (1 connections) — `tests/test_reports.py`
- **Get report with full snapshot data.** (1 connections) — `tests/test_reports.py`
- **Get non-existent report should return 404.** (1 connections) — `tests/test_reports.py`

## Relationships

- [make_auth_override](make_auth_override.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_reports.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*