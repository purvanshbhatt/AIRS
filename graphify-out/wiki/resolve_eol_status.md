# resolve_eol_status

> 18 nodes · cohesion 0.24

## Key Concepts

- **resolve_eol_status()** (19 connections) — `app/services/lifecycle/normalization.py`
- **_catalog()** (13 connections) — `tests/test_normalization_eol.py`
- **TestEOLResolve** (12 connections) — `tests/test_normalization_eol.py`
- **_major_minor_of()** (3 connections) — `app/services/lifecycle/normalization.py`
- **.test_different_minor_returns_unknown()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_exact_match_eol_returns_true()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_exact_match_expiring_future_returns_false()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_exact_match_expiring_past_returns_true()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_exact_match_supported_returns_false()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_only_major_version_returns_unknown()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_status_with_no_eol_date_returns_unknown()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_strict_match_is_required()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_unknown_major_minor_returns_unknown()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_unknown_product_returns_unknown()** (3 connections) — `tests/test_normalization_eol.py`
- **.test_unknown_status_returns_unknown_not_true()** (3 connections) — `tests/test_normalization_eol.py`
- **Return ``(major, minor)`` for a normalized version string. Anything that does…** (1 connections) — `app/services/lifecycle/normalization.py`
- **Strict EOL status lookup against ``GlobalSoftwareCatalog``. Behavior: - If the…** (1 connections) — `app/services/lifecycle/normalization.py`
- **Build an in-memory catalog keyed by product_name.lower(). Each product maps a…** (1 connections) — `tests/test_normalization_eol.py`

## Relationships

- [LifecycleIntelligenceService](LifecycleIntelligenceService.md) (6 shared connections)
- [VersionNormalizationEngine](VersionNormalizationEngine.md) (3 shared connections)

## Source Files

- `app/services/lifecycle/normalization.py`
- `tests/test_normalization_eol.py`

## Audit Trail

- EXTRACTED: 44 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*