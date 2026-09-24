# LifecycleIntelligenceService

> 24 nodes · cohesion 0.13

## Key Concepts

- **LifecycleIntelligenceService** (15 connections) — `app/services/lifecycle/lifecycle_intelligence.py`
- **GlobalSoftwareCatalog** (13 connections) — `app/models/lifecycle_catalog.py`
- **SoftwareVersion** (12 connections) — `app/models/lifecycle_catalog.py`
- **normalization.py** (11 connections) — `app/services/lifecycle/normalization.py`
- **test_lifecycle.py** (10 connections) — `tests/test_lifecycle.py`
- **lifecycle_catalog.py** (8 connections) — `app/models/lifecycle_catalog.py`
- **lifecycle_analysis.py** (7 connections) — `app/services/governance/lifecycle_analysis.py`
- **LifecycleReference** (5 connections) — `app/models/lifecycle_catalog.py`
- **test_lifecycle_validation()** (5 connections) — `tests/test_lifecycle.py`
- **Base** (3 connections)
- **_derive_eol_from_entry()** (3 connections) — `app/services/lifecycle/normalization.py`
- **date** (3 connections)
- **.__init__()** (2 connections) — `app/services/lifecycle/lifecycle_intelligence.py`
- **.__repr__()** (1 connections) — `app/models/lifecycle_catalog.py`
- **.__repr__()** (1 connections) — `app/models/lifecycle_catalog.py`
- **Global Software Catalog and Lifecycle Intelligence Models. These models…** (1 connections) — `app/models/lifecycle_catalog.py`
- **A globally recognized software product (e.g. PostgreSQL, Python).** (1 connections) — `app/models/lifecycle_catalog.py`
- **Specific version lifecycle intelligence for a product.** (1 connections) — `app/models/lifecycle_catalog.py`
- **Source provenance and reference links for the lifecycle intelligence.** (1 connections) — `app/models/lifecycle_catalog.py`
- **.__repr__()** (1 connections) — `app/models/lifecycle_catalog.py`
- **Deterministic Tech Stack Lifecycle Analysis Engine.** (1 connections) — `app/services/governance/lifecycle_analysis.py`
- **Session** (1 connections)
- **Deterministic software lifecycle intelligence. Checks installed software…** (1 connections) — `app/services/lifecycle/lifecycle_intelligence.py`
- **Deterministic Version Normalization Engine. Maps raw version strings into…** (1 connections) — `app/services/lifecycle/normalization.py`

## Relationships

- [resolve_eol_status](resolve_eol_status.md) (6 shared connections)
- [test_reliability.py](test_reliability.py.md) (5 shared connections)
- [Organization](Organization.md) (4 shared connections)
- [lifecycle_intelligence.py](lifecycle_intelligence.py.md) (4 shared connections)
- [.check_lifecycle_status](check_lifecycle_status.md) (4 shared connections)
- [VersionNormalizationEngine](VersionNormalizationEngine.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [discovery/orchestrator.py](discovery-orchestrator.py.md) (3 shared connections)
- [validate_delta.py](validate_delta.py.md) (3 shared connections)

## Source Files

- `app/models/lifecycle_catalog.py`
- `app/services/governance/lifecycle_analysis.py`
- `app/services/lifecycle/lifecycle_intelligence.py`
- `app/services/lifecycle/normalization.py`
- `tests/test_lifecycle.py`

## Audit Trail

- EXTRACTED: 64 (89%)
- INFERRED: 8 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*