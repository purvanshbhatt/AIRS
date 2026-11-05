# test_siem_integrations.py

> 22 nodes · cohesion 0.17

## Key Concepts

- **test_siem_integrations.py** (21 connections) — `tests/test_siem_integrations.py`
- **scoring_v2.py** (11 connections) — `app/services/governance/scoring_v2.py`
- **GovernanceHealthIndex** (11 connections) — `app/services/governance/validation_engine.py`
- **TestGHIScoringV2** (11 connections) — `tests/test_siem_integrations.py`
- **apply_siem_multiplier()** (9 connections) — `app/services/governance/scoring_v2.py`
- **SIEMVerificationContext** (9 connections) — `app/services/governance/scoring_v2.py`
- **compute_ghi_with_siem()** (8 connections) — `app/services/governance/scoring_v2.py`
- **.test_apply_siem_multiplier_capped_at_100()** (5 connections) — `tests/test_siem_integrations.py`
- **.test_apply_siem_multiplier_no_verification()** (5 connections) — `tests/test_siem_integrations.py`
- **.test_apply_siem_multiplier_with_verification()** (5 connections) — `tests/test_siem_integrations.py`
- **Any** (2 connections)
- **Session** (1 connections)
- **GHI Scoring Engine V2 — SIEM Verification Enhancement. This module extends the…** (1 connections) — `app/services/governance/scoring_v2.py`
- **Compute GHI with SIEM enhancement and return a response payload.** (1 connections) — `app/services/governance/scoring_v2.py`
- **Apply a 1.2x multiplier when any SIEM control is verified.** (1 connections) — `app/services/governance/scoring_v2.py`
- **.to_dict()** (1 connections) — `app/services/governance/validation_engine.py`
- **Composite Governance Health Index.** (1 connections) — `app/services/governance/validation_engine.py`
- **Unit tests for SIEM/XDR integration modules. Tests cover: - Wazuh client (agent…** (1 connections) — `tests/test_siem_integrations.py`
- **Test suite for SIEM-enhanced GHI scoring.** (1 connections) — `tests/test_siem_integrations.py`
- **Test 1.2x multiplier when SIEM controls are verified.** (1 connections) — `tests/test_siem_integrations.py`
- **Test that SIEM multiplier is capped at 100.** (1 connections) — `tests/test_siem_integrations.py`
- **Test no multiplier when SIEM controls are not verified.** (1 connections) — `tests/test_siem_integrations.py`

## Relationships

- [evaluate_siem_context](evaluate_siem_context.md) (8 shared connections)
- [WazuhConfig](WazuhConfig.md) (7 shared connections)
- [automated_findings.py](automated_findings.py.md) (4 shared connections)
- [compute_ghi](compute_ghi.md) (3 shared connections)
- [_make_org](_make_org.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [apply_siem_multipliers](apply_siem_multipliers.md) (1 shared connections)
- [asyncio](asyncio.md) (1 shared connections)
- [TestWazuhClient](TestWazuhClient.md) (1 shared connections)

## Source Files

- `app/services/governance/scoring_v2.py`
- `app/services/governance/validation_engine.py`
- `tests/test_siem_integrations.py`

## Audit Trail

- EXTRACTED: 66 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*