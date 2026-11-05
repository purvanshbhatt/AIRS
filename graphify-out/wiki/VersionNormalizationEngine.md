# VersionNormalizationEngine

> 16 nodes · cohesion 0.17

## Key Concepts

- **VersionNormalizationEngine** (14 connections) — `app/services/lifecycle/normalization.py`
- **test_normalization_eol.py** (7 connections) — `tests/test_normalization_eol.py`
- **TestNormalizationEngine** (6 connections) — `tests/test_normalization_eol.py`
- **NormalizedSoftware** (4 connections) — `app/services/lifecycle/normalization.py`
- **.normalize()** (3 connections) — `app/services/lifecycle/normalization.py`
- **test_normalization.py** (3 connections) — `tests/test_normalization.py`
- **.test_postgres_15()** (2 connections) — `tests/test_normalization_eol.py`
- **.test_python_311()** (2 connections) — `tests/test_normalization_eol.py`
- **.test_ubuntu_2204()** (2 connections) — `tests/test_normalization_eol.py`
- **.test_unknown_product_returns_unknown_vendor()** (2 connections) — `tests/test_normalization_eol.py`
- **test_normalization_accuracy()** (2 connections) — `tests/test_normalization.py`
- **Represents a successfully normalized software string.** (1 connections) — `app/services/lifecycle/normalization.py`
- **Deterministic engine for parsing and normalizing software versions.** (1 connections) — `app/services/lifecycle/normalization.py`
- **Takes a raw software version string and normalizes it.** (1 connections) — `app/services/lifecycle/normalization.py`
- **.__init__()** (1 connections) — `app/services/lifecycle/normalization.py`
- **Tests for Sprint 1.8, Task S1.8-B1 — strict EOL normalization. Covers: - Exact…** (1 connections) — `tests/test_normalization_eol.py`

## Relationships

- [LifecycleIntelligenceService](LifecycleIntelligenceService.md) (4 shared connections)
- [resolve_eol_status](resolve_eol_status.md) (3 shared connections)
- [validate_delta.py](validate_delta.py.md) (2 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/services/lifecycle/normalization.py`
- `tests/test_normalization.py`
- `tests/test_normalization_eol.py`

## Audit Trail

- EXTRACTED: 30 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*