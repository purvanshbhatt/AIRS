# TelemetryEvent

> 19 nodes · cohesion 0.13

## Key Concepts

- **TelemetryEvent** (53 connections) — `app/models/telemetry_event.py`
- **TelemetryIngestionService** (9 connections) — `app/services/telemetry_ingestion.py`
- **.compute_evidence_freshness()** (4 connections) — `app/services/telemetry_ingestion.py`
- **.get_stats()** (4 connections) — `app/services/telemetry_ingestion.py`
- **.ingest_events()** (4 connections) — `app/services/telemetry_ingestion.py`
- **Any** (3 connections)
- **.get_unprocessed_events()** (3 connections) — `app/services/telemetry_ingestion.py`
- **.__init__()** (2 connections) — `app/services/telemetry_ingestion.py`
- **.mark_events_processed()** (2 connections) — `app/services/telemetry_ingestion.py`
- **Base** (1 connections)
- **Raw telemetry event ingested from an external connector. Design Rationale: -…** (1 connections) — `app/models/telemetry_event.py`
- **.__repr__()** (1 connections) — `app/models/telemetry_event.py`
- **Session** (1 connections)
- **Fetch unprocessed events for consumption by the scoring engine. Args: limit:…** (1 connections) — `app/services/telemetry_ingestion.py`
- **Mark events as processed after consumption by the scoring engine. Returns:…** (1 connections) — `app/services/telemetry_ingestion.py`
- **Compute evidence freshness metrics across all source systems. Freshness is…** (1 connections) — `app/services/telemetry_ingestion.py`
- **Get aggregated telemetry statistics for this organization. Returns: Dict with…** (1 connections) — `app/services/telemetry_ingestion.py`
- **Organization-scoped telemetry event processing pipeline. Responsibilities: 1.…** (1 connections) — `app/services/telemetry_ingestion.py`
- **Batch-ingest telemetry events with idempotent deduplication. Args: events: List…** (1 connections) — `app/services/telemetry_ingestion.py`

## Relationships

- [ConnectorManager](ConnectorManager.md) (6 shared connections)
- [telemetry_events.py](telemetry_events.py.md) (5 shared connections)
- [Organization](Organization.md) (5 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (4 shared connections)
- [test_reliability.py](test_reliability.py.md) (4 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [router.py](router.py.md) (2 shared connections)
- [sentinel.py](sentinel.py.md) (2 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [Connector](Connector.md) (2 shared connections)
- [v1/control_verification.py](v1-control_verification.py.md) (2 shared connections)

## Source Files

- `app/models/telemetry_event.py`
- `app/services/telemetry_ingestion.py`

## Audit Trail

- EXTRACTED: 50 (70%)
- INFERRED: 21 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*