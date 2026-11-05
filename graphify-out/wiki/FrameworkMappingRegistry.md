# FrameworkMappingRegistry

> 21 nodes · cohesion 0.17

## Key Concepts

- **FrameworkMappingRegistry** (20 connections) — `app/models/framework_mapping.py`
- **calculate_ai_framework_coverage()** (13 connections) — `app/services/ai_frameworks.py`
- **test_ai_frameworks_coverage.py** (13 connections) — `tests/test_ai_frameworks_coverage.py`
- **framework_mapping.py** (11 connections) — `app/models/framework_mapping.py`
- **v1/frameworks.py** (10 connections) — `app/api/v1/frameworks.py`
- **ai_frameworks.py** (9 connections) — `app/services/ai_frameworks.py`
- **FrameworkType** (8 connections) — `app/models/framework_mapping.py`
- **test_calculate_ai_framework_coverage_with_data()** (6 connections) — `tests/test_ai_frameworks_coverage.py`
- **test_calculate_ai_framework_coverage_empty()** (3 connections) — `tests/test_ai_frameworks_coverage.py`
- **.test_framework_mapping_created()** (3 connections) — `tests/test_telemetry_verification.py`
- **Frameworks API — Serves the compliance mappings for the Frontend FrameworkTab.** (1 connections) — `app/api/v1/frameworks.py`
- **.__repr__()** (1 connections) — `app/models/framework_mapping.py`
- **Base** (1 connections)
- **str** (1 connections)
- **FrameworkMappingRegistry — Links findings to compliance framework controls.…** (1 connections) — `app/models/framework_mapping.py`
- **Supported compliance and governance frameworks.** (1 connections) — `app/models/framework_mapping.py`
- **Static registry linking findings to compliance framework control IDs. Design…** (1 connections) — `app/models/framework_mapping.py`
- **Any** (1 connections)
- **Session** (1 connections)
- **Calculate 0-100 coverage score per AI framework for a given organization. This…** (1 connections) — `app/services/ai_frameworks.py`
- **FrameworkMappingRegistry can be created with all control IDs.** (1 connections) — `tests/test_telemetry_verification.py`

## Relationships

- [Organization](Organization.md) (15 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (6 shared connections)
- [get_framework_coverage_data](get_framework_coverage_data.md) (4 shared connections)
- [calculate_scores](calculate_scores.md) (3 shared connections)
- [test_explainability.py](test_explainability.py.md) (1 shared connections)

## Source Files

- `app/api/v1/frameworks.py`
- `app/models/framework_mapping.py`
- `app/services/ai_frameworks.py`
- `tests/test_ai_frameworks_coverage.py`
- `tests/test_telemetry_verification.py`

## Audit Trail

- EXTRACTED: 63 (88%)
- INFERRED: 9 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*