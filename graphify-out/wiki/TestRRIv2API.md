# TestRRIv2API

> 19 nodes · cohesion 0.11

## Key Concepts

- **TestRRIv2API** (11 connections) — `tests/test_reliability.py`
- **.test_accept_recommendation_endpoint()** (3 connections) — `tests/test_reliability.py`
- **.test_confidence_endpoint()** (3 connections) — `tests/test_reliability.py`
- **.test_history_after_calculation()** (3 connections) — `tests/test_reliability.py`
- **.test_history_endpoint_empty()** (3 connections) — `tests/test_reliability.py`
- **.test_rri_response_includes_v2_fields()** (3 connections) — `tests/test_reliability.py`
- **.test_staging_gate_on_new_endpoints()** (3 connections) — `tests/test_reliability.py`
- **._setup()** (2 connections) — `tests/test_reliability.py`
- **.test_accept_recommendation_404_no_org()** (2 connections) — `tests/test_reliability.py`
- **.test_confidence_404_no_org()** (2 connections) — `tests/test_reliability.py`
- **Verify new v2 API endpoints: confidence, accept-recommendation, history.** (1 connections) — `tests/test_reliability.py`
- **GET /confidence returns RCS data.** (1 connections) — `tests/test_reliability.py`
- **GET /confidence for nonexistent org → 404.** (1 connections) — `tests/test_reliability.py`
- **POST /accept-recommendation updates org fields.** (1 connections) — `tests/test_reliability.py`
- **POST /accept-recommendation for nonexistent org → 404.** (1 connections) — `tests/test_reliability.py`
- **GET /history returns empty list when no audit events.** (1 connections) — `tests/test_reliability.py`
- **GET /history returns snapshots after RRI calculation.** (1 connections) — `tests/test_reliability.py`
- **GET /reliability-index response includes v2 fields.** (1 connections) — `tests/test_reliability.py`
- **New endpoints return 404 outside staging.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [_make_org](_make_org.md) (6 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)
- [fixture](fixture.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 26 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*