# agent_audits.py

> 35 nodes · cohesion 0.12

## Key Concepts

- **agent_audits.py** (29 connections) — `app/api/agent_audits.py`
- **AgentAudit** (17 connections) — `app/models/agent_audit.py`
- **create_agent_audit()** (9 connections) — `app/api/agent_audits.py`
- **ingest_agent_telemetry()** (9 connections) — `app/api/agent_audits.py`
- **_is_demo_org()** (8 connections) — `app/api/agent_audits.py`
- **run_agent_audit_analysis()** (8 connections) — `app/api/agent_audits.py`
- **download_agent_audit_report()** (7 connections) — `app/api/agent_audits.py`
- **Session** (7 connections)
- **get_agent_audit()** (6 connections) — `app/api/agent_audits.py`
- **get_agent_audit_explanation()** (6 connections) — `app/api/agent_audits.py`
- **list_agent_audits()** (6 connections) — `app/api/agent_audits.py`
- **_dual_write_firestore()** (5 connections) — `app/api/agent_audits.py`
- **schemas/agent_audit.py** (5 connections) — `app/schemas/agent_audit.py`
- **get** (4 connections)
- **AgentAuditCreateRequest** (4 connections) — `app/schemas/agent_audit.py`
- **AgentTelemetryIngestRequest** (4 connections) — `app/schemas/agent_audit.py`
- **post** (3 connections)
- **.is_expired()** (3 connections) — `app/models/agent_audit.py`
- **.to_dict()** (3 connections) — `app/models/agent_audit.py`
- **AgentAuditExplanationResponse** (3 connections) — `app/schemas/agent_audit.py`
- **test_expired_audit_cannot_ingest_or_run()** (3 connections) — `tests/test_agent_audit.py`
- **FastAPI Router for 48-Hour Live AI Agent Blast-Radius Audit sessions.** (1 connections) — `app/api/agent_audits.py`
- **List 48-hour blast radius agent audit sessions for an organization.** (1 connections) — `app/api/agent_audits.py`
- **Start a new 48-Hour Live AI Agent Blast-Radius Audit session. Enforces a strict…** (1 connections) — `app/api/agent_audits.py`
- **Get single agent audit session detail.** (1 connections) — `app/api/agent_audits.py`
- *... and 10 more nodes in this community*

## Relationships

- [Entitlement](Entitlement.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [test_agent_audit.py](test_agent_audit.py.md) (4 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [BaseModel](BaseModel.md) (3 shared connections)

## Source Files

- `app/api/agent_audits.py`
- `app/models/agent_audit.py`
- `app/schemas/agent_audit.py`
- `tests/test_agent_audit.py`

## Audit Trail

- EXTRACTED: 83 (88%)
- INFERRED: 11 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*