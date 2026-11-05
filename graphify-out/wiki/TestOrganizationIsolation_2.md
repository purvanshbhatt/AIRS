# TestOrganizationIsolation

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestOrganizationIsolation** (6 connections) — `tests/test_backend_contract_verification.py`
- **.test_cross_org_access_denied_when_auth_required()** (4 connections) — `tests/test_backend_contract_verification.py`
- **.test_own_org_access_allowed_when_auth_required()** (4 connections) — `tests/test_backend_contract_verification.py`
- **.test_missing_auth_returns_401_when_auth_required()** (3 connections) — `tests/test_backend_contract_verification.py`
- **AUTH_REQUIRED=true isolation tests. We patch settings.AUTH_REQUIRED to simulate…** (1 connections) — `tests/test_backend_contract_verification.py`
- **User authenticated for Org A must NOT access Org B's data. Expected: 403…** (1 connections) — `tests/test_backend_contract_verification.py`
- **User authenticated for Org A CAN access Org A's data. Expected: 200 OK.** (1 connections) — `tests/test_backend_contract_verification.py`
- **No auth header + AUTH_REQUIRED=true → 401.** (1 connections) — `tests/test_backend_contract_verification.py`

## Relationships

- [User](User.md) (3 shared connections)
- [_make_org](_make_org.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_backend_contract_verification.py`

## Audit Trail

- EXTRACTED: 13 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*