# TestInternalAssuranceAPI

> 24 nodes · cohesion 0.09

## Key Concepts

- **TestInternalAssuranceAPI** (14 connections) — `tests/test_igvf.py`
- **._create_org()** (5 connections) — `tests/test_igvf.py`
- **.test_ghi_in_response()** (4 connections) — `tests/test_igvf.py`
- **.setup_client()** (3 connections) — `tests/test_igvf.py`
- **.test_200_valid_request()** (3 connections) — `tests/test_igvf.py`
- **.test_validate_all_endpoint()** (3 connections) — `tests/test_igvf.py`
- **fixture** (2 connections)
- **.test_403_wrong_token()** (2 connections) — `tests/test_igvf.py`
- **.test_404_org_not_found()** (2 connections) — `tests/test_igvf.py`
- **.test_404_when_not_staging()** (2 connections) — `tests/test_igvf.py`
- **.test_422_missing_token()** (2 connections) — `tests/test_igvf.py`
- **.test_demo_env_returns_404()** (2 connections) — `tests/test_igvf.py`
- **.test_prod_env_returns_404()** (2 connections) — `tests/test_igvf.py`
- **Test the /internal/governance/validate endpoint.** (1 connections) — `tests/test_igvf.py`
- **Set up test client with DB override.** (1 connections) — `tests/test_igvf.py`
- **Non-staging environment → 404 (invisible).** (1 connections) — `tests/test_igvf.py`
- **Wrong admin token → 403.** (1 connections) — `tests/test_igvf.py`
- **Missing admin token header → 422.** (1 connections) — `tests/test_igvf.py`
- **Valid token + staging but nonexistent org → 404.** (1 connections) — `tests/test_igvf.py`
- **Valid staging + token + org → 200 with full IGVF result.** (1 connections) — `tests/test_igvf.py`
- **Response includes GHI with grade.** (1 connections) — `tests/test_igvf.py`
- **GET /internal/governance/validate → summary of all orgs.** (1 connections) — `tests/test_igvf.py`
- **Production environment → 404 (safety net).** (1 connections) — `tests/test_igvf.py`
- **Demo environment → 404 (safety net).** (1 connections) — `tests/test_igvf.py`

## Relationships

- [_make_org](_make_org.md) (4 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)

## Source Files

- `tests/test_igvf.py`

## Audit Trail

- EXTRACTED: 30 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*