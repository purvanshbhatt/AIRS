# EvidenceLedger

> 35 nodes · cohesion 0.11

## Key Concepts

- **EvidenceLedger** (17 connections) — `app/models/evidence.py`
- **v1/evidence.py** (16 connections) — `app/api/v1/evidence.py`
- **NormalizedEvidenceRecord** (14 connections) — `app/models/evidence.py`
- **NormalizedEvidence** (11 connections) — `app/schemas/evidence.py`
- **EvidenceOrchestrator** (11 connections) — `app/services/evidence/orchestrator.py`
- **EvidenceCollectionResult** (9 connections) — `app/schemas/evidence.py`
- **evidence/orchestrator.py** (9 connections) — `app/services/evidence/orchestrator.py`
- **models/evidence.py** (8 connections) — `app/models/evidence.py`
- **._ingest_into_evidence_registry()** (8 connections) — `app/services/connector_manager.py`
- **test_orchestrator_rejects_tampered_evidence()** (8 connections) — `tests/test_evidence_integrity.py`
- **get_evidence_ledger()** (7 connections) — `app/api/v1/evidence.py`
- **get_evidence_lineage()** (7 connections) — `app/api/v1/evidence.py`
- **get_evidence_packages()** (7 connections) — `app/api/v1/evidence.py`
- **get_monday_morning_actions()** (7 connections) — `app/api/v1/evidence.py`
- **.seed_mock_splunk_findings()** (6 connections) — `app/services/integrations.py`
- **test_orchestrator_handles_duplicates()** (6 connections) — `tests/test_evidence_integrity.py`
- **.ingest_collection_result()** (5 connections) — `app/services/evidence/orchestrator.py`
- **get** (4 connections)
- **Session** (4 connections)
- **User** (4 connections)
- **Base** (2 connections)
- **.__init__()** (2 connections) — `app/services/evidence/orchestrator.py`
- **Returns prioritized Monday Morning actions with score projections.** (1 connections) — `app/api/v1/evidence.py`
- **Returns the lineage of a piece of evidence. Connector -> Event -> Evidence…** (1 connections) — `app/api/v1/evidence.py`
- **Returns the evidence ledger (Audit Trail).** (1 connections) — `app/api/v1/evidence.py`
- *... and 10 more nodes in this community*

## Relationships

- [test_evidence_integrity.py](test_evidence_integrity.py.md) (16 shared connections)
- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [services/integrations.py](services-integrations.py.md) (8 shared connections)
- [User](User.md) (5 shared connections)
- [Organization](Organization.md) (5 shared connections)
- [monday_morning.py](monday_morning.py.md) (4 shared connections)
- [Connector](Connector.md) (4 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (3 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [ConnectorManager](ConnectorManager.md) (2 shared connections)
- [schemas/verification.py](schemas-verification.py.md) (1 shared connections)
- [VerificationService](VerificationService.md) (1 shared connections)

## Source Files

- `app/api/v1/evidence.py`
- `app/models/evidence.py`
- `app/schemas/evidence.py`
- `app/services/connector_manager.py`
- `app/services/evidence/orchestrator.py`
- `app/services/integrations.py`
- `tests/test_evidence_integrity.py`

## Audit Trail

- EXTRACTED: 108 (89%)
- INFERRED: 14 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*