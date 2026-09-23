# TelemetryEvidence

> 17 nodes · cohesion 0.16

## Key Concepts

- **TelemetryEvidence** (16 connections) — `app/sentinel/evidence/models.py`
- **EvidenceAdapter** (6 connections) — `app/sentinel/adapters/base.py`
- **adapters/base.py** (5 connections) — `app/sentinel/adapters/base.py`
- **sentinel/adapters/splunk.py** (5 connections) — `app/sentinel/adapters/splunk.py`
- **SplunkAdapter** (5 connections) — `app/sentinel/adapters/splunk.py`
- **.parse_payload()** (4 connections) — `app/sentinel/adapters/base.py`
- **.parse_payload()** (3 connections) — `app/sentinel/adapters/splunk.py`
- **ABC** (2 connections)
- **Any** (1 connections)
- **Parses the raw transport data into a list of canonical TelemetryEvidence items.** (1 connections) — `app/sentinel/adapters/base.py`
- **Abstract base class for all Evidence Adapters. Adapters are responsible for…** (1 connections) — `app/sentinel/adapters/base.py`
- **Any** (1 connections)
- **EvidenceAdapter** (1 connections)
- **Adapter for converting Splunk search results (both from MCP and HEC) into…** (1 connections) — `app/sentinel/adapters/splunk.py`
- **Base** (1 connections)
- **Deterministic evidence mapped from raw telemetry. This evidence feeds into the…** (1 connections) — `app/sentinel/evidence/models.py`
- **.__repr__()** (1 connections) — `app/sentinel/evidence/models.py`

## Relationships

- [twin/engine.py](twin-engine.py.md) (6 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (3 shared connections)
- [sentinel.py](sentinel.py.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/sentinel/adapters/base.py`
- `app/sentinel/adapters/splunk.py`
- `app/sentinel/evidence/models.py`

## Audit Trail

- EXTRACTED: 32 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*