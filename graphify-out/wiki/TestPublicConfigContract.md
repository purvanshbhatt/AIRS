# TestPublicConfigContract

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestPublicConfigContract** (7 connections) — `tests/test_e2e_vertical_config.py`
- **.test_default_returns_general_vertical()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_header_resolution()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_healthcare_query_param()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_legal_query_param()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_query_param_overrides_header()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **Validate GET /api/public/product-config adheres to interface contract.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test F4.01: Unparameterized GET returns general vertical configuration.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test F4.02: ?vertical=healthcare returns healthcare vertical configuration.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test F4.03: ?vertical=legal returns legal vertical configuration.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test F4.04: X-ResilAI-Vertical header sets active vertical.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test F4.05: Query parameter takes precedence over header.** (1 connections) — `tests/test_e2e_vertical_config.py`

## Relationships

- [public.py](public.py.md) (1 shared connections)

## Source Files

- `tests/test_e2e_vertical_config.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*