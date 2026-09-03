# ResilAI — Healthcare & Enterprise AI Incident Readiness Platform

<p align="center">
  <img src="frontend/public/android-app-icon.svg" alt="ResilAI Emblem" width="72" height="72" />
</p>

<p align="center">
  <b>Continuous, Deterministic Cyber Resilience & Operational Readiness for Healthcare Systems</b><br />
  <i>Replacing subjective compliance questionnaires with real-time mathematical evidence and executive intelligence.</i>
</p>

<p align="center">
  <a href="https://resilai.org"><img src="https://img.shields.io/badge/Production-resilai.org-006c4a.svg?style=flat-square" alt="Production"></a>
  <a href="https://staging.resilai.org"><img src="https://img.shields.io/badge/Staging-staging.resilai.org-10B981.svg?style=flat-square" alt="Staging"></a>
  <a href="https://github.com/purvanshbhatt/AIRS/actions"><img src="https://img.shields.io/badge/CI%2FCD-Passing-brightgreen.svg?style=flat-square" alt="CI/CD"></a>
  <a href="#proprietary-license"><img src="https://img.shields.io/badge/License-Commercial%20Proprietary-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://resilai.org/docs/methodology"><img src="https://img.shields.io/badge/Audit%20Model-Deterministic%20v3.0-blueviolet.svg?style=flat-square" alt="Model"></a>
</p>

---

## Executive Overview

**ResilAI** is a continuous incident readiness and operational resilience platform engineered specifically for healthcare organizations, multi-facility clinic networks, and critical infrastructure. 

For decades, cybersecurity readiness and regulatory compliance have relied on annual, subjective questionnaire assessments—static spreadsheets that become outdated minutes after completion and create a dangerous illusion of security. When ransomware strikes or medical record systems experience outages, organizations discover too late that their operational reality diverges sharply from their compliance paperwork.

ResilAI changes this paradigm through **Continuous Control Verification (CCV)**. By continuously interfacing with core enterprise infrastructure (identity directories, backup appliances, endpoint managers, cloud providers, and security operations telemetry), ResilAI calculates real-time operational readiness based on verifiable cryptographic evidence.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TRADITIONAL GRC vs. RESILAI                       │
├───────────────────────────────────┬─────────────────────────────────────┤
│ Subjective Annual GRC             │ ResilAI Continuous Verification     │
├───────────────────────────────────┼─────────────────────────────────────┤
│ ❌ Self-attested questionnaires   │ ✅ Real-time connector evidence     │
│ ❌ Annual point-in-time snapshot  │ ✅ Evaluated continuously 24/7/365  │
│ ❌ Obscure technical jargon       │ ✅ Plain-English business impact    │
│ ❌ Disconnected backup claims     │ ✅ Mathematical RTO/RPO proof       │
│ ❌ Unverified third-party claims  │ ✅ Multi-source cross-verification  │
└───────────────────────────────────┴─────────────────────────────────────┘
```

---

## Core Product Architecture

ResilAI is built on a strict **Two-Layer Architecture** designed to ensure mathematical integrity and executive clarity.

```
                  ┌────────────────────────────────────────────────┐
                  │          LIVE INFRASTRUCTURE TELEMETRY          │
                  │   M365 · Entra ID · Veeam · Intune · Sentinel  │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │             LAYER 1: DETERMINISTIC EVALUATION ENGINE (BACKEND)             │
   │  • Zero-LLM mathematical scoring algorithms                               │
   │  • Weighted multi-factor domain evaluation (0–100%)                       │
   │  • Cryptographic SHA-256 evidence hashing & immutable audit ledger         │
   │  • Cross-source control validation & discrepancy detection                 │
   └──────────────────────────────────────┬─────────────────────────────────────┘
                                          │
                         [Frozen Mathematical State JSON]
                                          │
                                          ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │             LAYER 2: GEMINI EXECUTIVE TRANSLATION (INTELLIGENCE)           │
   │  • Translates deterministic findings into plain business leadership copy   │
   │  • Answers: What changed? Why does it matter? What should we do?           │
   │  • Strict guardrails: LLMs NEVER calculate, infer, or modify scores       │
   │  • Dual-workspace presentation: Executive Briefing & Technical Telemetry   │
   └──────────────────────────────────────┬─────────────────────────────────────┘
                                          │
                                          ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │             EXECUTIVE INTERFACE & MOBILE PRODUCT (STITCH UX)               │
   │  • Web Application (Desktop & Tablet)                                      │
   │  • Mobile Phone Application (PWA & Android Optimized via Stitch MD3)       │
   │  • Exportable Board Presentation Vault & Auditor Proof Binders             │
   └────────────────────────────────────────────────────────────────────────────┘
```

### The Non-Negotiable Trust Invariants

1. **Deterministic Scoring**: No Large Language Model ever generates, calculates, or modifies a readiness score or risk metric. All scores are computed deterministically by verified backend mathematical algorithms.
2. **Telemetry Over Attestation**: Every score and status claim is backed by raw, cryptographic evidence collected from live systems.
3. **Cryptographic Provenance**: Every piece of telemetry and verification record is SHA-256 hashed and timestamped into an immutable evidence ledger.
4. **Multi-Source Cross-Verification**: Critical controls require verification from independent systems (e.g., endpoint agent health confirmed through both device management and security monitoring).

---

## Complete Feature & Functional Breakdown

### 1. Morning Operations Workspace (Executive Zoom Level)

Designed for Healthcare CEOs, Chief Medical Officers, Managing Partners, and Clinic Administrators who need to understand clinic operating risk in under 30 seconds.

* **Morning Brief (`/morning-brief`)**:
  * **North Star Hero Metric**: Instantly communicates macro operational readiness (e.g., `98% — Ready for Today`) with intuitive status semantics (`Ready`, `Attention Required`, `Critical Risk`).
  * **Executive Questions Grid**: Directly answers four foundational business questions:
    1. *Can our clinical staff safely treat patients today?*
    2. *Are our medical records and patient data intact and protected?*
    3. *If an incident occurs right now, can we recover without paying ransom?*
    4. *Are we compliant with regulatory mandates (HIPAA, NIST, CIS)?*
  * **Coverage Verification Cards**: Clear breakdown of what systems are actively verified versus unmonitored blind spots.
  * **Contextual Explanations**: One-click "Explain for Leadership" summarizing clinical and operational implications without technical jargon.

* **Needs Attention Triage (`/needs-attention`)**:
  * Prioritized queue of operational risks requiring executive decision or IT action.
  * **4-Tier Progressive Disclosure Model**:
    1. *Executive Summary*: Plain-English description of the situation.
    2. *Business Impact*: Operational and financial consequences if left unresolved.
    3. *Recommended Action*: Prescriptive remediation steps for internal IT or MSPs.
    4. *How We Know (Technical Evidence)*: Cryptographic evidence, connector source, raw payload, and evaluation timestamp.

* **Recovery Readiness Engine (`/recovery`)**:
  * **Continuous RPO & RTO Verification**: Compares measured recovery point and recovery time telemetry against clinical operational targets.
  * **Backup Immutability Auditing**: Verifies air-gapped, write-once-read-many (WORM) storage guarantees across primary and secondary repositories.
  * **Automated Restore Validation**: Tracks and validates periodic automated sandbox restoration tests to verify that backups are actually bootable.

* **Activity Stream & Historical Compliance Drift (`/activity`, `/compliance-drift`)**:
  * Real-time ledger of configuration changes, security alerts, credential rotations, and control status shifts.
  * Historical trend analysis tracking operational readiness trajectories over 7, 30, and 90 days.

---

### 2. Technology Operations ("Mini-Products" for IT & SecOps)

Seven dedicated domain workspaces providing full technical depth without compromising business context. Each domain workspace begins with an executive summary card answering *"So what?"* before presenting low-level telemetry:

* **Identity & Access (`/operations/identity`)**: MFA enforcement across clinical staff, privileged account hygiene, dormant accounts, conditional access policies, and directory sync health.
* **Devices & Endpoints (`/operations/devices`)**: EDR agent coverage, disk encryption (BitLocker/FileVault), OS patch cadence, unmanaged clinical workstations, and telemetry freshness.
* **Backups & Immutability (`/operations/backups`)**: Backup job completion states, replication lag, immutable repository configuration, and restore test cadence.
* **Email & Phishing Security (`/operations/email`)**: SPF/DKIM/DMARC alignment, inbound malware quarantine rates, automated phishing protection, and spoofing defenses.
* **Network & Perimeter (`/operations/network`)**: Firewall rule configurations, secure VPN gateways, microsegmentation boundaries between clinical and guest networks.
* **Cloud Infrastructure (`/operations/cloud`)**: Cloud security posture management across AWS, Azure, and Google Cloud, storage bucket permissions, and IAM key rotation.
* **AI & Medical Workflow Risk (`/operations/ai`)**: Inventory of AI systems in clinical workflows, model provenance, data pipeline privacy, and alignment with NIST AI RMF.

---

### 3. Governance & Regulatory Framework Alignment

ResilAI continuously maps mathematical evidence to industry standard compliance and governance frameworks:

* **NIST Cybersecurity Framework (CSF 2.0)**: Complete alignment across Govern, Identify, Protect, Detect, Respond, and Recover functions.
* **NIST AI Risk Management Framework (AI RMF 1.0)**: Govern, Map, Measure, and Manage functions for organizations deploying artificial intelligence in clinical workflows.
* **CIS Critical Security Controls v8**: Mapping to Implementation Groups 1, 2, and 3 (IG1/IG2/IG3).
* **HIPAA Security Rule**: Verification of Administrative, Physical, and Technical Safeguards (45 CFR Part 160 and Part 164, Subparts A and C).
* **SOC 2 Type II**: Alignment with Security, Availability, Processing Integrity, and Confidentiality Trust Services Criteria.
* **ISO/IEC 27001:2022**: Mapping to Annex A security controls.

---

### 4. Cryptographic Evidence Vault & Audit Center (`/documents`, `/reports`)

* **One-Click Executive Board Reports**: Instant generation of comprehensive PDF/Word board decks synthesizing current readiness, open risks, 90-day trajectory, and return on security investment (ROSI).
* **Auditor-Ready Evidence Vault**: Exportable cryptographic evidence binders containing raw configuration hashes, connector run manifests, and tamper-evident timestamps.
* **Audit Calendar & Milestone Tracker**: Tracks upcoming regulatory audits, scheduled disaster recovery drills, and policy review cadences.

---

### 5. Multi-Source Integration Fabric (`/connectors`)

ResilAI connects directly with operational systems using read-only API connectors:

* **Identity & Directory**: Microsoft Entra ID (Azure AD), Okta, Google Workspace
* **Endpoint & Device Management**: Microsoft Intune, Jamf Pro, CrowdStrike Falcon, Microsoft Defender for Endpoint
* **Backup & Disaster Recovery**: Veeam Backup & Replication, Datto, AWS Backup
* **Security Operations & SIEM**: Microsoft Sentinel, Wazuh SIEM, Splunk, Elastic Security
* **Cloud Platforms**: Amazon Web Services (AWS SSM / GuardDuty), Microsoft Azure, Google Cloud Platform

---

### 6. Mobile Application (PWA & Android Native UX)

ResilAI features a purpose-built mobile application built from Google Stitch Material Design 3 specifications:

* **Executive Mobile App Bar**: Ambient readiness indicator, instant notification badges, and one-tap workspace switching.
* **Mobile-Optimized Bottom Navigation**: Immediate thumb-driven navigation across `Today`, `Triage`, `Recovery`, and `Ops`.
* **Full Progressive Web App (PWA)**: Installable directly onto mobile devices (Android and iOS) with offline resilience, home screen icon, standalone display mode, and safe-area optimization.
* **Instant Leadership Translation**: Interactive drawer presenting plain-English answers on mobile phones for on-call executives.

---

## 5-Stage Verification Operating Model

```
   1. CONNECT             2. VERIFY             3. MEASURE             4. EXPLAIN             5. IMPROVE
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Read-Only   │  ──►  │ Cryptographic│  ──►  │Deterministic │  ──►  │ Plain-English│  ──►  │ Prescriptive │
│  API Connect │       │ Mathematical │       │ Domain Scores│       │  Leadership  │       │ Remediation  │
│  Ingestion   │       │ Evidence     │       │  & Weights   │       │ Translation  │       │  Workflows   │
└──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
```

1. **Connect**: Connect operational tools via least-privilege, read-only API tokens. No agents required on endpoints.
2. **Verify**: Systems are polled on continuous schedules. Raw outputs are evaluated against deterministic control rules.
3. **Measure**: Domain scores (0–100%) and macro readiness are calculated mathematically using weighted risk algorithms.
4. **Explain**: Gemini executive translator converts raw evidence into plain business narratives for executives and board directors.
5. **Improve**: Concrete remediation guidance with one-click script generators and MSP dispatch links enables immediate risk mitigation.

---

## Deployment & Hosting Environments

ResilAI is delivered as a managed, enterprise-grade cloud service deployed on Google Cloud Platform and Firebase infrastructure:

| Environment | Primary URL | Target Role | Access |
| :--- | :--- | :--- | :--- |
| **Production** | [`https://resilai.org`](https://resilai.org) | Primary enterprise production environment | Authenticated customers & partners |
| **Staging** | [`https://staging.resilai.org`](https://staging.resilai.org) | Staging release verification & partner previews | Authorized evaluators & QA |
| **Demo Sandbox** | [`https://resilai.org/morning-brief`](https://resilai.org) | Interactive demo workspace (Acme Health Systems) | Open evaluation & interactive trial |

---

## Security & Compliance Governance

* **Zero-Knowledge Architecture**: ResilAI connectors extract only metadata and configuration states; patient Protected Health Information (PHI) and medical record content are never ingested, stored, or processed.
* **Field-Level Encryption**: All credentials, API tokens, and tenant identifiers are protected with AES-256 GCM encryption at rest and TLS 1.3 in transit.
* **Role-Based Access Control (RBAC)**: Fine-grained permissions separating Executive Viewers, Clinic Managers, IT Operators, and External Compliance Auditors.
* **Tenant Isolation**: Multi-tenant database structures enforce cryptographic tenant isolation at the Firestore security rule layer.

---

## Access & Enterprise Subscriptions

ResilAI is proprietary enterprise software. Access to the production platform, tenant provisioning, and connector integrations is provided through enterprise subscriptions, managed service provider (MSP) partnerships, and healthcare design partner agreements.

To request an enterprise readiness assessment or explore an evaluation partnership:

* **Official Website**: [https://resilai.org](https://resilai.org)
* **Partner & Sales Inquiries**: [purvansh95b@gmail.com](mailto:purvansh95b@gmail.com)
* **Interactive Sandbox**: [Launch Acme Health Demo](https://resilai.org) (Click *Explore Demo Sandbox*)
* **Methodology & Documentation**: [https://resilai.org/docs/methodology](https://resilai.org/docs/methodology)

---

## Proprietary License

Copyright © 2025–2026 ResilAI Inc. All rights reserved.

This software, including all source code, algorithms, user interface designs, mathematical scoring models, and documentation, is the exclusive proprietary intellectual property of ResilAI Inc. Unauthorized copying, distribution, reverse engineering, deployment, or commercial exploitation is strictly prohibited without express written authorization from ResilAI Inc.
