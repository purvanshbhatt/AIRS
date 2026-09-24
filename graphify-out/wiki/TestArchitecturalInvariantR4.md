# TestArchitecturalInvariantR4

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestArchitecturalInvariantR4** (6 connections) — `tests/test_e2e_vertical_config.py`
- **.test_deterministic_scoring_calculation()** (3 connections) — `tests/test_e2e_vertical_config.py`
- **.test_scoring_engine_centralized_definition()** (3 connections) — `tests/test_e2e_vertical_config.py`
- **.test_scoring_engine_ast_llm_isolation()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **.test_zero_duplicate_scoring_engines()** (2 connections) — `tests/test_e2e_vertical_config.py`
- **Verify shared scoring engine integrity, AST LLM isolation, and zero duplicate…** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test R4.01: calculate_readiness_delta is defined in app.services.scoring.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test R4.02: app/services/scoring.py has zero LLM or generative imports.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test R4.03: Zero duplicate scoring engine files exist in app/.** (1 connections) — `tests/test_e2e_vertical_config.py`
- **Test R4.04: Readiness delta calculation is pure and deterministic.** (1 connections) — `tests/test_e2e_vertical_config.py`

## Relationships

- [calculate_readiness_delta](calculate_readiness_delta.md) (2 shared connections)
- [public.py](public.py.md) (1 shared connections)

## Source Files

- `tests/test_e2e_vertical_config.py`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*