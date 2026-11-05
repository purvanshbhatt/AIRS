# organizations.py

> 69 nodes · cohesion 0.06

## Key Concepts

- **organizations.py** (76 connections) — `app/api/organizations.py`
- **ReportService** (26 connections) — `app/services/report.py`
- **get_org_service()** (20 connections) — `app/api/organizations.py`
- **Session** (17 connections)
- **User** (17 connections)
- **create_org_report()** (12 connections) — `app/api/organizations.py`
- **download_org_report()** (12 connections) — `app/api/organizations.py`
- **create_organization_assessment()** (11 connections) — `app/api/organizations.py`
- **list_org_remediations()** (11 connections) — `app/api/organizations.py`
- **list_suggested_questions()** (11 connections) — `app/api/organizations.py`
- **_compute_function_scores_from_db()** (10 connections) — `app/services/question_suggestions.py`
- **create_organization()** (9 connections) — `app/api/organizations.py`
- **get** (9 connections)
- **export_audit_trail()** (8 connections) — `app/api/organizations.py`
- **get_org_report()** (8 connections) — `app/api/organizations.py`
- **list_org_reports()** (8 connections) — `app/api/organizations.py`
- **list_organization_audit_events()** (8 connections) — `app/api/organizations.py`
- **toggle_analytics()** (8 connections) — `app/api/organizations.py`
- **update_organization()** (8 connections) — `app/api/organizations.py`
- **get_suggestions()** (8 connections) — `app/services/question_suggestions.py`
- **delete_organization()** (7 connections) — `app/api/organizations.py`
- **get_assessment_service()** (7 connections) — `app/api/organizations.py`
- **get_organization()** (7 connections) — `app/api/organizations.py`
- **list_organizations()** (7 connections) — `app/api/organizations.py`
- **SuggestionsResponse** (5 connections) — `app/schemas/suggestions.py`
- *... and 44 more nodes in this community*

## Relationships

- [User](User.md) (25 shared connections)
- [Organization](Organization.md) (25 shared connections)
- [app/db/database.py](app-db-database.py.md) (22 shared connections)
- [schemas/report.py](schemas-report.py.md) (10 shared connections)
- [BaseModel](BaseModel.md) (7 shared connections)
- [Entitlement](Entitlement.md) (6 shared connections)
- [test_suggestions.py](test_suggestions.py.md) (5 shared connections)
- [BaseSchema](BaseSchema.md) (4 shared connections)
- [strip_dangerous](strip_dangerous.md) (2 shared connections)
- [schemas/assessment.py](schemas-assessment.py.md) (2 shared connections)
- [RoadmapItem](RoadmapItem.md) (2 shared connections)
- [ProfessionalPDFGenerator](ProfessionalPDFGenerator.md) (2 shared connections)

## Source Files

- `app/api/organizations.py`
- `app/schemas/audit.py`
- `app/schemas/integrations.py`
- `app/schemas/suggestions.py`
- `app/services/question_suggestions.py`
- `app/services/report.py`
- `tests/test_tenant_isolation_v2.py`

## Audit Trail

- EXTRACTED: 227 (88%)
- INFERRED: 31 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*