# TestPublicConfigBoundaries

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestPublicConfigBoundaries** (8 connections) — `tests/test_e2e_vertical_config.py`
- **.test_empty_and_special_char_query()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_mixed_case_query_param()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_query_param_overrides_host_subdomain()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_subdomain_resolution_via_host_header()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_unknown_vertical_fallback()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_whitespace_padded_query()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **Validate edge cases, unknown inputs, subdomains, and normalization.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.01: Unknown vertical string safely defaults to general.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.02: Mixed-case query parameters are normalized.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.03: Whitespace in query param is trimmed.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.04: Subdomains in Host header resolve correctly.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.05: Query parameter takes precedence over Host subdomain.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test T2.06: Empty and malformed queries safely default to general.** (1 connections) — `tests/test_e2e_vertical_config.py`

## Relationships

- [public.py](public.py.md) (1 shared connections)

## Source Files

- `tests/test_e2e_vertical_config.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*