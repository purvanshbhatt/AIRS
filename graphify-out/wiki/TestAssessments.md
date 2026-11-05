# TestAssessments

> 39 nodes · cohesion 0.06

## Key Concepts

- **TestAssessments** (12 connections) — `tests/test_assessments.py`
- **TestOrganizations** (10 connections) — `tests/test_assessments.py`
- **TestReports** (7 connections) — `tests/test_assessments.py`
- **SystemAuditor** (6 connections) — `app/services/audit.py`
- **test_assessments.py** (6 connections) — `tests/test_assessments.py`
- **._record_mutation()** (5 connections) — `app/services/audit.py`
- **.after_flush()** (3 connections) — `app/services/audit.py`
- **.setup_listeners()** (3 connections) — `app/services/audit.py`
- **.org_id()** (3 connections) — `tests/test_assessments.py`
- **.test_demo_mode_auto_seeds_demo_org_and_splunk()** (3 connections) — `tests/test_assessments.py`
- **fixture** (2 connections)
- **Tests for assessment API endpoints.** (2 connections) — `tests/test_assessments.py`
- **.scored_assessment()** (2 connections) — `tests/test_assessments.py`
- **Automated system auditing trace class that listens to SQLAlchemy session…** (1 connections) — `app/services/audit.py`
- **Bind the after_flush listener to the Session context.** (1 connections) — `app/services/audit.py`
- **Intercepts all changes before commit and generates AuditEvents.** (1 connections) — `app/services/audit.py`
- **Tests for organization endpoints.** (1 connections) — `tests/test_assessments.py`
- **Tests for report generation.** (1 connections) — `tests/test_assessments.py`
- **Verify ensure_demo_seed_data works when invoked explicitly in demo mode. NOTE:…** (1 connections) — `tests/test_assessments.py`
- **.test_add_manual_finding()** (1 connections) — `tests/test_assessments.py`
- **.test_compute_score()** (1 connections) — `tests/test_assessments.py`
- **.test_create_assessment()** (1 connections) — `tests/test_assessments.py`
- **.test_create_assessment_invalid_org()** (1 connections) — `tests/test_assessments.py`
- **.test_get_assessment_detail()** (1 connections) — `tests/test_assessments.py`
- **.test_get_findings()** (1 connections) — `tests/test_assessments.py`
- *... and 14 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)

## Source Files

- `app/services/audit.py`
- `tests/test_assessments.py`

## Audit Trail

- EXTRACTED: 47 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*