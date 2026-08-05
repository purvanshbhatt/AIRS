# Product Specification Map — ResilAI (AIRS)

**Version**: 1.3.0  
**Architecture**: Dual Workspace Progressive Disclosure (Business & Technology Operations)  

---

## 1. Executive Vision & Core Question
ResilAI answers the single morning business question for healthcare leadership:
> **"Can our clinics safely open for patient care today?"**

It transforms complex cybersecurity telemetry across 7 primary domain silos into a deterministic, executive readiness score (**DailyReadinessReport**) supported by deep operational evidence.

---

## 2. Target Personas & Workspace Alignment

| Persona | Target Workspace | Core Business Need | Primary UI View |
|---|---|---|---|
| Executive / C-Suite | Business Workspace | Rapid readiness assessment, business continuity, ROI metrics | Morning Brief, Executive Summary |
| IT Operations / SecOps | Technology Operations | Telemetry inspection, connector status, root-cause investigation | Identity, Devices, Backups, Email, Network, Cloud, AI |
| Administrator | Administration Workspace | Connector management, audit logs, environment settings | Connectors, Activity, Audit, Settings |

---

## 3. 9 Backend Engine Architecture

1. **Connector Engine**: Integrates M365, Wazuh, Veeam, CrowdStrike, SentinelOne, Cisco Umbrella, Okta.
2. **Extraction Engine**: Converts raw API events into normalized evidence objects.
3. **Evaluation Engine**: Evaluates evidence against clinical readiness rules.
4. **Risk Engine**: Identifies active blockers and ransomware threats.
5. **Action Engine**: Generates recommended remediation steps.
6. **Trust Engine**: Computes cryptographic health check hashes.
7. **Coverage Engine**: Measures connector telemetry completeness.
8. **Metrics Engine**: Calculates business continuity metrics and cost savings.
9. **Aggregator Engine**: Consolidates scores into `DailyReadinessReport`.
