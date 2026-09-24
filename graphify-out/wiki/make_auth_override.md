# make_auth_override

> 10 nodes · cohesion 0.20

## Key Concepts

- **make_auth_override()** (39 connections) — `tests/conftest.py`
- **setup_user_a_assessment()** (4 connections) — `tests/test_reports.py`
- **.test_assessment_has_owner_uid()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_organization_has_owner_uid()** (3 connections) — `tests/test_tenant_isolation.py`
- **User** (1 connections)
- **Create an auth override for the given user.** (1 connections) — `tests/conftest.py`
- **fixture** (1 connections)
- **Create an organization and scored assessment for User A.** (1 connections) — `tests/test_reports.py`
- **Created organization should have owner_uid set.** (1 connections) — `tests/test_tenant_isolation.py`
- **Created assessment should have owner_uid set.** (1 connections) — `tests/test_tenant_isolation.py`

## Relationships

- [TestAssessmentIsolation](TestAssessmentIsolation.md) (7 shared connections)
- [fixture](fixture.md) (4 shared connections)
- [TestReportTenantIsolation](TestReportTenantIsolation.md) (4 shared connections)
- [TestOrganizationIsolation](TestOrganizationIsolation.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [TestReportCreation](TestReportCreation.md) (3 shared connections)
- [TestReportListing](TestReportListing.md) (2 shared connections)
- [TestReportRetrieval](TestReportRetrieval.md) (2 shared connections)
- [client_user_a](client_user_a.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [TestReportDeletion](TestReportDeletion.md) (1 shared connections)
- [TestReportDownload](TestReportDownload.md) (1 shared connections)

## Source Files

- `tests/conftest.py`
- `tests/test_reports.py`
- `tests/test_tenant_isolation.py`

## Audit Trail

- EXTRACTED: 45 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*