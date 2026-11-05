# TestReportCreation

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestReportCreation** (5 connections) — `tests/test_reports.py`
- **.test_create_report_assessment_not_found()** (3 connections) — `tests/test_reports.py`
- **.test_create_report_success()** (3 connections) — `tests/test_reports.py`
- **.test_create_report_unscored_assessment_fails()** (3 connections) — `tests/test_reports.py`
- **Creating a report for non-existent assessment should fail.** (1 connections) — `tests/test_reports.py`
- **Test report creation endpoints.** (1 connections) — `tests/test_reports.py`
- **Successfully create a report for a scored assessment.** (1 connections) — `tests/test_reports.py`
- **Creating a report for an unscored assessment should fail.** (1 connections) — `tests/test_reports.py`

## Relationships

- [make_auth_override](make_auth_override.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_reports.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*