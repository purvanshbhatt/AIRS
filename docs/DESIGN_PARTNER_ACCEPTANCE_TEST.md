# Design Partner Acceptance Test

This document outlines 8 non-technical scenarios to prove the ResilAI MVP is ready for executive, managerial, and IT personas. These tests validate that the product successfully shifts the narrative from "cybersecurity" to "operational resilience" and builds deterministic trust.

## Scenario 1: The Executive Morning Brief
**Persona**: CEO / Board Member
**Context**: The user logs in at 8:00 AM to check if the organization is ready to operate.
**Steps**:
1. Log into the ResilAI dashboard.
2. Observe the North Star Hero section and the Executive Questions Grid.
**Acceptance Criteria**:
- The user can instantly answer "Are we safe to operate today?" without interpreting a score out of 100 or severity metrics.
- The language is business-centric (e.g., "Patient Data Integrity", "Ransomware Recovery").
- There are no technical jargon or CVSS scores visible on the main executive view.

## Scenario 2: Triaging a Critical Blocker
**Persona**: IT Manager / CISO
**Context**: The Morning Brief indicates a critical blocker regarding MFA enforcement.
**Steps**:
1. Click on the "Needs Attention" / Triage view.
2. Locate the "Critical Blocking Actions" section.
3. Review the provided context ("What to do" and "How we know").
**Acceptance Criteria**:
- The user sees clear, actionable steps instead of generic alerts.
- The exact deterministic evidence (e.g., "Verified via Microsoft Graph Telemetry") is displayed, proving *why* the alert was triggered.

## Scenario 3: Attempting Remediation
**Persona**: IT Operations Analyst
**Context**: The user clicks "Fix Issue Now" for a known compliance drift.
**Steps**:
1. Click the "Fix Issue Now" button on a Needs Attention card.
2. Wait for the remediation to process and the system to re-verify.
**Acceptance Criteria**:
- The UI strictly follows the Remediation State Machine (`Executing Fix` -> `Polling Telemetry`).
- If the telemetry does not confirm the fix, the state changes to `Unable to Verify` and demands manual verification. It does not optimistically assume success.

## Scenario 4: Investigating Telemetry Confidence
**Persona**: Compliance Officer / Auditor
**Context**: The user needs to verify what systems are actually connected and providing data.
**Steps**:
1. Navigate to the "Connectors & Integrations" page.
2. Review the list of active integrations and their states.
**Acceptance Criteria**:
- Connectors display real-time statuses (e.g., `CONNECTED`, `DEGRADED`, `NOT CONFIGURED`).
- The "Visibility Gap" clearly highlights what controls are *not* being monitored, ensuring the organization does not have a false sense of security.

## Scenario 5: Reviewing the Document Center
**Persona**: Executive / Auditor
**Context**: The user needs a formal report for a board meeting or a compliance audit.
**Steps**:
1. Navigate to the "Documents" / Document Center page.
2. Explore the three tabs: Executive Reports, Evidence Vault, and Audit Trail.
**Acceptance Criteria**:
- The Executive Reports tab provides clear, downloadable snapshots of readiness.
- The Audit Trail dynamically lists verification logs with source systems, proving historical compliance.
- No dummy data is used—every ledger item is cryptographically linked to a source event.

## Scenario 6: Assessing Disaster Recovery Readiness
**Persona**: IT Director
**Context**: The user needs to verify if the organization can recover from a ransomware attack today.
**Steps**:
1. Navigate to the "Recovery Readiness" page.
2. Review the Time to Recovery (RTO), Backup Health Timeline, and Critical Systems.
**Acceptance Criteria**:
- If backup telemetry is missing, the system aggressively displays "Unable to verify" instead of defaulting to "Healthy".
- Active recovery blockers are prominently highlighted in a critical warning block.

## Scenario 7: Exploring the Tenant / MSP View
**Persona**: Managed Service Provider (MSP) Admin
**Context**: The user logs in to manage a specific clinic within their portfolio.
**Steps**:
1. View the top navigation bar.
**Acceptance Criteria**:
- The `MSP Managed` tag is visible, indicating the tenant isolation context.
- The sandbox mode is clearly labeled with a `SANDBOX` tag, ensuring the user knows they are not looking at live production data.

## Scenario 8: Fallback / Disconnected Mode
**Persona**: Any User
**Context**: The organization's connectors fail to sync overnight due to an API outage.
**Steps**:
1. Log into the ResilAI dashboard when evidence is stale (simulated).
**Acceptance Criteria**:
- The dashboard does not show "100% Ready". Instead, it degrades to an "Unknown" state.
- The user is prompted to reconnect the failing integration or manually attest to the controls.
