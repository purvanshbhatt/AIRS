# User

> 82 nodes · cohesion 0.07

## Key Concepts

- **User** (265 connections) — `app/core/auth.py`
- **assessments.py** (97 connections) — `app/api/assessments.py`
- **get_assessment_service()** (32 connections) — `app/api/assessments.py`
- **Session** (29 connections)
- **User** (28 connections)
- **record_audit_event()** (24 connections) — `app/services/audit.py`
- **compute_score()** (14 connections) — `app/api/assessments.py`
- **update_finding()** (12 connections) — `app/api/assessments.py`
- **get** (11 connections)
- **dispatch_assessment_scored_webhooks()** (11 connections) — `app/services/integrations.py`
- **add_finding()** (10 connections) — `app/api/assessments.py`
- **post** (10 connections)
- **_resolve_assessment_for_tracker()** (10 connections) — `app/api/assessments.py`
- **export_compliance_report_to_gcs()** (10 connections) — `app/services/compliance_export.py`
- **create_assessment()** (9 connections) — `app/api/assessments.py`
- **create_report()** (9 connections) — `app/api/assessments.py`
- **create_roadmap_item()** (9 connections) — `app/api/assessments.py`
- **rerun_assessment()** (9 connections) — `app/api/assessments.py`
- **update_roadmap_item()** (9 connections) — `app/api/assessments.py`
- **firestore_get_assessment_lifecycle()** (9 connections) — `app/db/firestore.py`
- **annotate_findings()** (8 connections) — `app/api/assessments.py`
- **delete_roadmap_item()** (8 connections) — `app/api/assessments.py`
- **generate_report()** (8 connections) — `app/api/assessments.py`
- **get_assessment()** (8 connections) — `app/api/assessments.py`
- **get_assessment_history()** (8 connections) — `app/api/assessments.py`
- *... and 57 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (41 shared connections)
- [organizations.py](organizations.py.md) (25 shared connections)
- [Organization](Organization.md) (23 shared connections)
- [api/integrations.py](api-integrations.py.md) (22 shared connections)
- [_get_org](_get_org.md) (20 shared connections)
- [connectors.py](connectors.py.md) (14 shared connections)
- [get_user_org_id](get_user_org_id.md) (13 shared connections)
- [strip_dangerous](strip_dangerous.md) (12 shared connections)
- [schemas/assessment.py](schemas-assessment.py.md) (11 shared connections)
- [get_firestore_client](get_firestore_client.md) (10 shared connections)
- [RoadmapItem](RoadmapItem.md) (10 shared connections)
- [inventory.py](inventory.py.md) (10 shared connections)

## Source Files

- `app/api/assessments.py`
- `app/core/auth.py`
- `app/db/firestore.py`
- `app/schemas/assessment.py`
- `app/services/audit.py`
- `app/services/compliance_export.py`
- `app/services/integrations.py`

## Audit Trail

- EXTRACTED: 356 (60%)
- INFERRED: 233 (40%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*