# splunk_staging_validation.py

> 31 nodes · cohesion 0.12

## Key Concepts

- **splunk_staging_validation.py** (24 connections) — `scripts/splunk_staging_validation.py`
- **validate_sentinel.py** (21 connections) — `scripts/validate_sentinel.py`
- **generate_evidence_from_telemetry()** (16 connections) — `app/sentinel/evidence/engine.py`
- **execute_simulation()** (16 connections) — `app/sentinel/twin/engine.py`
- **demo_sentinel.py** (13 connections) — `scripts/demo_sentinel.py`
- **generate_board_report()** (11 connections) — `app/sentinel/board_intelligence/generator.py`
- **SentinelSimulation** (11 connections) — `app/sentinel/twin/models.py`
- **generator.py** (10 connections) — `app/sentinel/board_intelligence/generator.py`
- **run_validation()** (10 connections) — `scripts/splunk_staging_validation.py`
- **twin/models.py** (9 connections) — `app/sentinel/twin/models.py`
- **run_validation()** (9 connections) — `scripts/validate_sentinel.py`
- **run_demo()** (7 connections) — `scripts/demo_sentinel.py`
- **SentinelTelemetryEvent** (4 connections) — `app/sentinel/db/models.py`
- **sentinel/db/database.py** (3 connections) — `app/sentinel/db/database.py`
- **db/models.py** (3 connections) — `app/sentinel/db/models.py`
- **get_sentinel_db()** (2 connections) — `app/sentinel/db/database.py`
- **format_json()** (2 connections) — `scripts/splunk_staging_validation.py`
- **Session** (1 connections)
- **Board Intelligence Engine. Generates executive narratives based purely on…** (1 connections) — `app/sentinel/board_intelligence/generator.py`
- **Generates an executive report using Gemini Flash based on a SentinelSimulation.** (1 connections) — `app/sentinel/board_intelligence/generator.py`
- **Base** (1 connections)
- **Isolated local copy of a Telemetry Event inside the Sentinel Microservice.** (1 connections) — `app/sentinel/db/models.py`
- **Session** (1 connections)
- **Processes unprocessed TelemetryEvents for an org and converts them into…** (1 connections) — `app/sentinel/evidence/engine.py`
- **Session** (1 connections)
- *... and 6 more nodes in this community*

## Relationships

- [twin/engine.py](twin-engine.py.md) (14 shared connections)
- [Organization](Organization.md) (13 shared connections)
- [Connector](Connector.md) (10 shared connections)
- [sentinel.py](sentinel.py.md) (9 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [SessionLocal](SessionLocal.md) (4 shared connections)
- [SplunkMCPClient](SplunkMCPClient.md) (4 shared connections)
- [TelemetryEvidence](TelemetryEvidence.md) (3 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (3 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [get_rubric](get_rubric.md) (2 shared connections)
- [calculate_scores](calculate_scores.md) (2 shared connections)

## Source Files

- `app/sentinel/board_intelligence/generator.py`
- `app/sentinel/db/database.py`
- `app/sentinel/db/models.py`
- `app/sentinel/evidence/engine.py`
- `app/sentinel/twin/engine.py`
- `app/sentinel/twin/models.py`
- `scripts/demo_sentinel.py`
- `scripts/splunk_staging_validation.py`
- `scripts/validate_sentinel.py`

## Audit Trail

- EXTRACTED: 123 (95%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*