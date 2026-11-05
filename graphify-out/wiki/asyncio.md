# asyncio

> 11 nodes · cohesion 0.24

## Key Concepts

- **asyncio** (7 connections)
- **TestAutomatedFindings** (6 connections) — `tests/test_siem_integrations.py`
- **.test_generate_finding_from_xz_cve()** (4 connections) — `tests/test_siem_integrations.py`
- **.test_generate_remediation_task_ghi_impact()** (4 connections) — `tests/test_siem_integrations.py`
- **.test_process_agent_disconnections_below_threshold()** (4 connections) — `tests/test_siem_integrations.py`
- **.test_process_agent_disconnections_high_rate()** (4 connections) — `tests/test_siem_integrations.py`
- **Test suite for CVE-driven finding generation.** (1 connections) — `tests/test_siem_integrations.py`
- **Test auto-generation of finding for CVE-2024-3094.** (1 connections) — `tests/test_siem_integrations.py`
- **Test remediation task creation with GHI impact.** (1 connections) — `tests/test_siem_integrations.py`
- **Test auto-finding generation for high agent disconnection rate.** (1 connections) — `tests/test_siem_integrations.py`
- **Test no finding when disconnection rate is below threshold.** (1 connections) — `tests/test_siem_integrations.py`

## Relationships

- [automated_findings.py](automated_findings.py.md) (4 shared connections)
- [TestWazuhClient](TestWazuhClient.md) (3 shared connections)
- [test_siem_integrations.py](test_siem_integrations.py.md) (1 shared connections)

## Source Files

- `tests/test_siem_integrations.py`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*