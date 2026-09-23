# api/logic_firewall.py

> 41 nodes · cohesion 0.08

## Key Concepts

- **api/logic_firewall.py** (19 connections) — `app/api/logic_firewall.py`
- **run_logic_firewall_simulation()** (13 connections) — `app/api/logic_firewall.py`
- **services/logic_firewall.py** (12 connections) — `app/services/logic_firewall.py`
- **LogicFirewallService** (12 connections) — `app/services/logic_firewall.py`
- **get_logic_firewall_trace()** (7 connections) — `app/api/logic_firewall.py`
- **schemas/logic_firewall.py** (6 connections) — `app/schemas/logic_firewall.py`
- **test_logic_firewall.py** (6 connections) — `tests/test_logic_firewall.py`
- **LogicTraceResponse** (5 connections) — `app/schemas/logic_firewall.py`
- **get_logic_firewall_service()** (5 connections) — `app/services/logic_firewall.py`
- **LogicFirewallSimulationRequest** (4 connections) — `app/schemas/logic_firewall.py`
- **LogicFirewallSimulationResponse** (4 connections) — `app/schemas/logic_firewall.py`
- **QuarantinedChunkResponse** (4 connections) — `app/schemas/logic_firewall.py`
- **build_simulated_retrieval_chunks()** (4 connections) — `app/services/logic_firewall.py`
- **.store_trace()** (4 connections) — `app/services/logic_firewall.py`
- **render_raw_llm_like_answer()** (4 connections) — `app/services/logic_firewall.py`
- **render_safe_answer()** (4 connections) — `app/services/logic_firewall.py`
- **.logic_firewall()** (3 connections) — `app/services/logic_firewall.py`
- **LogicTrace** (3 connections) — `app/services/logic_firewall.py`
- **User** (2 connections)
- **.detect_injection()** (2 connections) — `app/services/logic_firewall.py`
- **.get_trace()** (2 connections) — `app/services/logic_firewall.py`
- **._prune_store()** (2 connections) — `app/services/logic_firewall.py`
- **QuarantinedChunk** (2 connections) — `app/services/logic_firewall.py`
- **_utc_now_iso()** (2 connections) — `app/services/logic_firewall.py`
- **test_logic_firewall_quarantines_poisoned_chunk()** (2 connections) — `tests/test_logic_firewall.py`
- *... and 16 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (5 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [User](User.md) (3 shared connections)

## Source Files

- `app/api/logic_firewall.py`
- `app/schemas/logic_firewall.py`
- `app/services/logic_firewall.py`
- `tests/test_logic_firewall.py`

## Audit Trail

- EXTRACTED: 74 (91%)
- INFERRED: 7 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*