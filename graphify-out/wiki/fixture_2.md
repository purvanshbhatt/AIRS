# fixture

> 13 nodes · cohesion 0.18

## Key Concepts

- **fixture** (7 connections)
- **client_with_org()** (5 connections) — `tests/conftest.py`
- **client_no_org()** (4 connections) — `tests/conftest.py`
- **client_user_a()** (4 connections) — `tests/conftest.py`
- **client_user_b()** (4 connections) — `tests/conftest.py`
- **_mock_firestore_if_no_emulator()** (4 connections) — `tests/conftest.py`
- **client()** (3 connections) — `tests/conftest.py`
- **_emulator_available()** (3 connections) — `tests/conftest.py`
- **Client authenticated as a user with NO organization.** (2 connections) — `tests/conftest.py`
- **Client authenticated as User A.** (2 connections) — `tests/conftest.py`
- **Generic test client. Does not guarantee auth or org presence.** (1 connections) — `tests/conftest.py`
- **Return True if the Firestore emulator appears to be running.** (1 connections) — `tests/conftest.py`
- **If the Firestore emulator is NOT reachable, patch the save/delete/get functions…** (1 connections) — `tests/conftest.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [make_auth_override](make_auth_override.md) (4 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `tests/conftest.py`

## Audit Trail

- EXTRACTED: 26 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*