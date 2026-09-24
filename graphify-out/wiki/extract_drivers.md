# extract_drivers

> 25 nodes · cohesion 0.16

## Key Concepts

- **extract_drivers()** (15 connections) — `app/services/readiness_drivers.py`
- **readiness_drivers.py** (10 connections) — `app/services/readiness_drivers.py`
- **TestExtractDrivers** (9 connections) — `tests/test_readiness_drivers.py`
- **extract_action_items()** (8 connections) — `app/services/readiness_drivers.py`
- **_build_inputs()** (8 connections) — `tests/test_readiness_drivers.py`
- **_driver_from_reason()** (6 connections) — `app/services/readiness_drivers.py`
- **test_readiness_drivers.py** (6 connections) — `tests/test_readiness_drivers.py`
- **Any** (5 connections)
- **_derive_evidence_source()** (4 connections) — `app/services/readiness_drivers.py`
- **_extract_impact()** (4 connections) — `app/services/readiness_drivers.py`
- **.test_action_items_renders_rationale()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_empty_inputs_return_empty_lists()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_invalid_top_n_raises()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_negative_drivers_sorted_most_negative_first()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_positive_drivers_sorted_descending()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_top_n_truncation()** (3 connections) — `tests/test_readiness_drivers.py`
- **.test_zero_impact_drivers_excluded()** (3 connections) — `tests/test_readiness_drivers.py`
- **Readiness Driver Extraction. Consumes the ``reasons`` block produced by…** (1 connections) — `app/services/readiness_drivers.py`
- **Render negative drivers as 'Executive Actions' (Mon-morning list). Each item is…** (1 connections) — `app/services/readiness_drivers.py`
- **Extract an impact value from a scoring reason dict. Scoring reasons have shape:…** (1 connections) — `app/services/readiness_drivers.py`
- **Map a scoring ``reasons`` entry to a clean driver record.** (1 connections) — `app/services/readiness_drivers.py`
- **Best-effort mapping from controller category to evidence source. Categories: -…** (1 connections) — `app/services/readiness_drivers.py`
- **Produce sorted top-N positive and top-N negative drivers. Args:…** (1 connections) — `app/services/readiness_drivers.py`
- **Tests for the Readiness Driver extraction module (Sprint 1.8, Task S1.8-A3).…** (1 connections) — `tests/test_readiness_drivers.py`
- **.test_no_db_writes_no_llm_imports()** (1 connections) — `tests/test_readiness_drivers.py`

## Relationships

- [v1/readiness.py](v1-readiness.py.md) (5 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (2 shared connections)
- [calculate_scores](calculate_scores.md) (1 shared connections)

## Source Files

- `app/services/readiness_drivers.py`
- `tests/test_readiness_drivers.py`

## Audit Trail

- EXTRACTED: 56 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*