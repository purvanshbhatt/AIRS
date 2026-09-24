# test_explainability.py

> 39 nodes · cohesion 0.07

## Key Concepts

- **test_explainability.py** (18 connections) — `tests/test_explainability.py`
- **VerificationContext** (16 connections) — `app/services/clinic_engine/v2/contracts.py`
- **ExplainabilityEngine** (13 connections) — `app/services/clinic_engine/v2/explainability_engine.py`
- **engine()** (12 connections) — `tests/test_explainability.py`
- **explainability_engine.py** (9 connections) — `app/services/clinic_engine/v2/explainability_engine.py`
- **.build_explanation()** (7 connections) — `app/services/clinic_engine/v2/explainability_engine.py`
- **ExecutiveExplanation** (5 connections) — `app/services/clinic_engine/v2/contracts.py`
- **mock_moment()** (5 connections) — `tests/test_explainability.py`
- **._determine_evidence_state()** (4 connections) — `app/services/clinic_engine/v2/explainability_engine.py`
- **test_action_mapping()** (4 connections) — `tests/test_explainability.py`
- **_auto_create_sqlite_tables()** (3 connections) — `app/main.py`
- **db()** (3 connections) — `tests/test_ai_frameworks_coverage.py`
- **test_explainability_determinism()** (3 connections) — `tests/test_explainability.py`
- **test_failed_finding()** (3 connections) — `tests/test_explainability.py`
- **test_no_evidence_never_healthy()** (3 connections) — `tests/test_explainability.py`
- **test_stale_finding()** (3 connections) — `tests/test_explainability.py`
- **test_tenant_isolation()** (3 connections) — `tests/test_explainability.py`
- **test_unknown_finding()** (3 connections) — `tests/test_explainability.py`
- **db()** (3 connections) — `tests/test_technology_intelligence.py`
- **VerificationContext** (2 connections)
- **fixture** (2 connections)
- **Create all tables for SQLite databases (ephemeral filesystem on Cloud Run).** (1 connections) — `app/main.py`
- **Plain-English explanation of a security finding for non-technical executives.** (1 connections) — `app/services/clinic_engine/v2/contracts.py`
- **Per-item verification metadata. Answers 'Why are you telling me this?** (1 connections) — `app/services/clinic_engine/v2/contracts.py`
- **ActionCard** (1 connections)
- *... and 14 more nodes in this community*

## Relationships

- [contracts.py](contracts.py.md) (15 shared connections)
- [schema.py](schema.py.md) (6 shared connections)
- [ClinicMoment](ClinicMoment.md) (4 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [FrameworkMappingRegistry](FrameworkMappingRegistry.md) (1 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [router.py](router.py.md) (1 shared connections)
- [SessionLocal](SessionLocal.md) (1 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)

## Source Files

- `app/main.py`
- `app/services/clinic_engine/v2/contracts.py`
- `app/services/clinic_engine/v2/explainability_engine.py`
- `tests/test_ai_frameworks_coverage.py`
- `tests/test_explainability.py`
- `tests/test_technology_intelligence.py`

## Audit Trail

- EXTRACTED: 70 (79%)
- INFERRED: 19 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*