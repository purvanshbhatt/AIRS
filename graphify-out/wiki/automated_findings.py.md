# automated_findings.py

> 14 nodes · cohesion 0.24

## Key Concepts

- **automated_findings.py** (15 connections) — `app/services/governance/automated_findings.py`
- **process_wazuh_agent_disconnections()** (12 connections) — `app/services/governance/automated_findings.py`
- **generate_finding_from_cve()** (11 connections) — `app/services/governance/automated_findings.py`
- **process_wazuh_vulnerabilities()** (8 connections) — `app/services/governance/automated_findings.py`
- **generate_remediation_task_from_cve()** (7 connections) — `app/services/governance/automated_findings.py`
- **Session** (4 connections)
- **Assessment** (3 connections)
- **Any** (2 connections)
- **Finding** (2 connections)
- **Automated Finding Generation — SIEM-Driven Remediation. When Wazuh reports…** (1 connections) — `app/services/governance/automated_findings.py`
- **Create a Remediation Ledger task for a critical CVE. This is the mechanism for…** (1 connections) — `app/services/governance/automated_findings.py`
- **Process all vulnerabilities from Wazuh and auto-generate findings. Args: db:…** (1 connections) — `app/services/governance/automated_findings.py`
- **Auto-generate finding if agent disconnection exceeds threshold. Per…** (1 connections) — `app/services/governance/automated_findings.py`
- **Automatically generate a finding from a Wazuh CVE detection. Args: db: Database…** (1 connections) — `app/services/governance/automated_findings.py`

## Relationships

- [Organization](Organization.md) (14 shared connections)
- [test_siem_integrations.py](test_siem_integrations.py.md) (4 shared connections)
- [asyncio](asyncio.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [RoadmapItem](RoadmapItem.md) (1 shared connections)

## Source Files

- `app/services/governance/automated_findings.py`

## Audit Trail

- EXTRACTED: 41 (87%)
- INFERRED: 6 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*