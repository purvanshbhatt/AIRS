# RoadmapItem

> 19 nodes · cohesion 0.12

## Key Concepts

- **RoadmapItem** (16 connections) — `app/models/roadmap_item.py`
- **patch_remediation()** (13 connections) — `app/api/remediations.py`
- **sync_finding_to_ticketing()** (11 connections) — `app/api/remediations.py`
- **run_remediation_agent()** (9 connections) — `app/api/remediations.py`
- **Session** (3 connections)
- **User** (3 connections)
- **RemediationPatchRequest** (3 connections) — `app/api/remediations.py`
- **TicketSyncRequest** (3 connections) — `app/api/remediations.py`
- **_from_remediation_status()** (2 connections) — `app/api/remediations.py`
- **_normalize_priority()** (2 connections) — `app/api/remediations.py`
- **_normalize_remediation_status()** (2 connections) — `app/api/remediations.py`
- **post** (2 connections)
- **patch** (1 connections)
- **Executes the Google Antigravity SDK agent to propose technical remediation…** (1 connections) — `app/api/remediations.py`
- **Exports a compliance finding directly as a tracking ticket in Jira, ServiceNow,…** (1 connections) — `app/api/remediations.py`
- **Update remediation/action tracker item by id.** (1 connections) — `app/api/remediations.py`
- **Base** (1 connections)
- **User-managed roadmap tracking items for an assessment.** (1 connections) — `app/models/roadmap_item.py`
- **.__repr__()** (1 connections) — `app/models/roadmap_item.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (11 shared connections)
- [User](User.md) (10 shared connections)
- [Organization](Organization.md) (7 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [organizations.py](organizations.py.md) (2 shared connections)
- [ElasticService](ElasticService.md) (1 shared connections)
- [automated_findings.py](automated_findings.py.md) (1 shared connections)

## Source Files

- `app/api/remediations.py`
- `app/models/roadmap_item.py`

## Audit Trail

- EXTRACTED: 40 (73%)
- INFERRED: 15 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*