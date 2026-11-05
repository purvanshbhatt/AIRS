# VerificationService

> 21 nodes · cohesion 0.17

## Key Concepts

- **VerificationService** (20 connections) — `app/services/verification.py`
- **.verify_finding()** (11 connections) — `app/services/verification.py`
- **Any** (10 connections)
- **._evaluate_wazuh_evidence()** (7 connections) — `app/services/verification.py`
- **._provisional_result()** (6 connections) — `app/services/verification.py`
- **._connection_error_result()** (5 connections) — `app/services/verification.py`
- **._evaluate_microsoft_evidence()** (5 connections) — `app/services/verification.py`
- **.verify_all_findings()** (5 connections) — `app/services/verification.py`
- **._get_latest_microsoft_telemetry()** (4 connections) — `app/services/verification.py`
- **._run_wazuh_check()** (4 connections) — `app/services/verification.py`
- **.__init__()** (2 connections) — `app/services/verification.py`
- **.disconnection_rate()** (2 connections) — `app/services/wazuh_client.py`
- **Evaluate a finding against Microsoft telemetry payload.** (1 connections) — `app/services/verification.py`
- **Verify a single finding against SIEM evidence. Args: finding: A Finding…** (1 connections) — `app/services/verification.py`
- **Batch-verify all findings against SIEM evidence.** (1 connections) — `app/services/verification.py`
- **Run a Wazuh evidence check, caching results.** (1 connections) — `app/services/verification.py`
- **Evaluate Wazuh evidence and assign verification status.** (1 connections) — `app/services/verification.py`
- **Create a Provisional verification result.** (1 connections) — `app/services/verification.py`
- **Create a Connection Error verification result.** (1 connections) — `app/services/verification.py`
- **Deterministic SIEM-corroborated finding verification. Cross-references internal…** (1 connections) — `app/services/verification.py`
- **Fetch the latest Microsoft telemetry payload from database.** (1 connections) — `app/services/verification.py`

## Relationships

- [schemas/verification.py](schemas-verification.py.md) (9 shared connections)
- [api/verification.py](api-verification.py.md) (4 shared connections)
- [test_microsoft_connector.py](test_microsoft_connector.py.md) (2 shared connections)
- [EvidenceLedger](EvidenceLedger.md) (1 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (1 shared connections)
- [WazuhConfig](WazuhConfig.md) (1 shared connections)

## Source Files

- `app/services/verification.py`
- `app/services/wazuh_client.py`

## Audit Trail

- EXTRACTED: 51 (94%)
- INFERRED: 3 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*