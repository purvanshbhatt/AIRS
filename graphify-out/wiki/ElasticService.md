# ElasticService

> 62 nodes · cohesion 0.06

## Key Concepts

- **ElasticService** (20 connections) — `app/services/elastic.py`
- **TicketSyncService** (16 connections) — `app/services/ticket_sync.py`
- **elastic.py** (9 connections) — `app/services/elastic.py`
- **EvidenceResult** (9 connections) — `app/services/evidence_result_types.py`
- **LoggingHealthResult** (8 connections) — `app/services/evidence_result_types.py`
- **._run_search()** (7 connections) — `app/services/elastic.py`
- **EvidenceStatus** (7 connections) — `app/services/evidence_result_types.py`
- **.verify_logging_health()** (6 connections) — `app/services/elastic.py`
- **evidence_result_types.py** (6 connections) — `app/services/evidence_result_types.py`
- **.sync_finding_to_target()** (6 connections) — `app/services/ticket_sync.py`
- **asyncio** (6 connections)
- **TestElasticService** (6 connections) — `tests/test_remediation_and_elastic.py`
- **TestTicketSyncService** (6 connections) — `tests/test_remediation_and_elastic.py`
- **.pull_all_evidence()** (5 connections) — `app/services/elastic.py`
- **.verify_edr_coverage()** (5 connections) — `app/services/elastic.py`
- **.verify_mfa_enforcement()** (5 connections) — `app/services/elastic.py`
- **Any** (5 connections)
- **._sync_to_webhook()** (5 connections) — `app/services/ticket_sync.py`
- **._get_mock_search_results()** (4 connections) — `app/services/elastic.py`
- **.verify_heartbeat()** (4 connections) — `app/services/elastic.py`
- **Any** (4 connections)
- **._sync_to_jira()** (4 connections) — `app/services/ticket_sync.py`
- **._sync_to_servicenow()** (4 connections) — `app/services/ticket_sync.py`
- **.test_verify_edr_coverage_mock()** (4 connections) — `tests/test_remediation_and_elastic.py`
- **.test_verify_logging_health_mock()** (4 connections) — `tests/test_remediation_and_elastic.py`
- *... and 37 more nodes in this community*

## Relationships

- [Organization](Organization.md) (5 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [services/integrations.py](services-integrations.py.md) (2 shared connections)
- [get_user_org_id](get_user_org_id.md) (1 shared connections)
- [RoadmapItem](RoadmapItem.md) (1 shared connections)

## Source Files

- `app/services/elastic.py`
- `app/services/evidence_result_types.py`
- `app/services/ticket_sync.py`
- `tests/test_remediation_and_elastic.py`

## Audit Trail

- EXTRACTED: 112 (94%)
- INFERRED: 7 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*