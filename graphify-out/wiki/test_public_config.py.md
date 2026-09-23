# test_public_config.py

> 20 nodes · cohesion 0.10

## Key Concepts

- **test_public_config.py** (12 connections) — `tests/test_public_config.py`
- **test_resolve_vertical_key_unit()** (3 connections) — `tests/test_public_config.py`
- **test_no_llm_imports_in_public_config()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_default()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_header_routing()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_host_subdomain_routing()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_precedence()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_query_healthcare()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_query_legal()** (2 connections) — `tests/test_public_config.py`
- **test_public_config_unknown_fallback()** (2 connections) — `tests/test_public_config.py`
- **Tests for Public Product Configuration API (M1: Host- and Route-Aware Vertical…** (1 connections) — `tests/test_public_config.py`
- **Test pure resolution logic directly.** (1 connections) — `tests/test_public_config.py`
- **Default request with no parameters returns the general vertical configuration.** (1 connections) — `tests/test_public_config.py`
- **Architectural invariant R4: Ensure app.api.public has no LLM or intelligence…** (1 connections) — `tests/test_public_config.py`
- **Query parameter vertical=healthcare returns healthcare vertical configuration.** (1 connections) — `tests/test_public_config.py`
- **Query parameter vertical=legal returns legal vertical configuration.** (1 connections) — `tests/test_public_config.py`
- **Unknown vertical key falls back gracefully to general.** (1 connections) — `tests/test_public_config.py`
- **X-ResilAI-Vertical header routes to specified vertical.** (1 connections) — `tests/test_public_config.py`
- **Host header subdomain routes to specified vertical.** (1 connections) — `tests/test_public_config.py`
- **Query parameter takes precedence over header and subdomain.** (1 connections) — `tests/test_public_config.py`

## Relationships

- [public.py](public.py.md) (3 shared connections)

## Source Files

- `tests/test_public_config.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*