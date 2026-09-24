# BaseModel

> 99 nodes · cohesion 0.03

## Key Concepts

- **BaseModel** (287 connections) — `app/models/base.py`
- **v1/integrations.py** (56 connections) — `app/api/v1/integrations.py`
- **schemas/integrations.py** (38 connections) — `app/schemas/integrations.py`
- **run_splunk_query()** (15 connections) — `app/api/v1/integrations.py`
- **schemas/reliability.py** (14 connections) — `app/schemas/reliability.py`
- **WazuhConfigRequest** (7 connections) — `app/schemas/integrations.py`
- **schemas/score_snapshot.py** (7 connections) — `app/schemas/score_snapshot.py`
- **ScoreDriftResponse** (6 connections) — `app/schemas/score_snapshot.py`
- **ApiKeyCreateRequest** (5 connections) — `app/schemas/integrations.py`
- **ElasticConfigRequest** (5 connections) — `app/schemas/integrations.py`
- **SIEMIntegrationStatus** (5 connections) — `app/schemas/integrations.py`
- **SplunkEvidenceResponse** (5 connections) — `app/schemas/integrations.py`
- **SplunkEvidenceResult** (5 connections) — `app/schemas/integrations.py`
- **SplunkLoggingHealthResponse** (5 connections) — `app/schemas/integrations.py`
- **SplunkQueryRequest** (5 connections) — `app/schemas/integrations.py`
- **SplunkQueryResponse** (5 connections) — `app/schemas/integrations.py`
- **AcceptRecommendationRequest** (5 connections) — `app/schemas/reliability.py`
- **BreachSimulationRequest** (5 connections) — `app/schemas/reliability.py`
- **schemas/technology.py** (5 connections) — `app/schemas/technology.py`
- **ExternalFindingResponse** (4 connections) — `app/schemas/integrations.py`
- **RoadmapTrackerItemCreate** (4 connections) — `app/schemas/integrations.py`
- **RoadmapTrackerItemResponse** (4 connections) — `app/schemas/integrations.py`
- **RoadmapTrackerItemUpdate** (4 connections) — `app/schemas/integrations.py`
- **SplunkSeedRequest** (4 connections) — `app/schemas/integrations.py`
- **WazuhAgentStatusResponse** (4 connections) — `app/schemas/integrations.py`
- *... and 74 more nodes in this community*

## Relationships

- [schemas/assessment.py](schemas-assessment.py.md) (29 shared connections)
- [api/integrations.py](api-integrations.py.md) (28 shared connections)
- [app/db/database.py](app-db-database.py.md) (26 shared connections)
- [get_user_org_id](get_user_org_id.md) (20 shared connections)
- [contracts.py](contracts.py.md) (20 shared connections)
- [Organization](Organization.md) (10 shared connections)
- [connectors.py](connectors.py.md) (10 shared connections)
- [User](User.md) (9 shared connections)
- [WazuhConfig](WazuhConfig.md) (8 shared connections)
- [inventory.py](inventory.py.md) (8 shared connections)
- [strip_dangerous](strip_dangerous.md) (8 shared connections)
- [v1/readiness.py](v1-readiness.py.md) (8 shared connections)

## Source Files

- `app/api/v1/integrations.py`
- `app/api/v1/intelligence.py`
- `app/models/base.py`
- `app/schemas/integrations.py`
- `app/schemas/reliability.py`
- `app/schemas/score_snapshot.py`
- `app/schemas/technology.py`

## Audit Trail

- EXTRACTED: 481 (95%)
- INFERRED: 23 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*