import React from 'react';
import { render, RenderResult } from '@testing-library/react';
import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';
import type { DailyReadinessReport } from '../../types/readiness';
import type { Report } from '../../types/reports';

export interface ExecutiveExplanationData {
  id?: string;
  business_label: string;
  technical_label: string;
  what_it_means: string;
  why_it_matters: string;
  what_to_do_next: string;
  status: string;
  evidence_state: string;
  evidence_telemetry?: string;
  evidence_source?: string;
  confidence_score?: number;
  cryptographic_hash?: string;
  last_verified_at: string;
  domain?: string;
  target_route?: string;
  action_type?: string;
}

export interface ActionCardData {
  id: string;
  title: string;
  description: string;
  severity: string;
  category: string;
  system: string;
  explanation: ExecutiveExplanationData;
  remediation: {
    action_type: string;
    button_text: string;
    estimated_time_mins: number;
    impact: string;
  };
  delegation?: {
    suggested_role: string;
    assigned_to: string;
  };
}

export function renderWithRouter(
  ui: React.ReactElement,
  {
    initialEntries = ['/'],
    ...renderOptions
  }: { initialEntries?: MemoryRouterProps['initialEntries'] } & Parameters<typeof render>[1] = {}
): RenderResult {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      {ui}
    </MemoryRouter>,
    renderOptions
  );
}

export function createMockExecutiveExplanation(
  overrides: Partial<ExecutiveExplanationData> = {}
): ExecutiveExplanationData {
  return {
    id: 'exp-backup-001',
    business_label: 'Electronic Health Record Backup Stale',
    technical_label: 'Veeam Backup Job Status: RPO_BREACH',
    what_it_means: 'Your patient medical records were not backed up in the last 24 hours.',
    why_it_matters: 'If a ransomware attack happens today, patient chart data will be permanently lost.',
    what_to_do_next: 'Trigger an immediate snapshot or verify Veeam credentials.',
    status: 'critical',
    evidence_state: 'verified',
    evidence_telemetry: 'Last successful Veeam backup job: 26 hours ago (SLA: 24h).',
    evidence_source: 'Veeam Cloud Backup Connector API',
    confidence_score: 99,
    cryptographic_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    last_verified_at: '2026-08-31T08:00:00Z',
    domain: 'backups',
    target_route: '/recovery',
    action_type: 'trigger_backup',
    ...overrides,
  };
}

export function createMockActionCard(
  overrides: Partial<ActionCardData> = {}
): ActionCardData {
  return {
    id: 'action-ehr-backup-001',
    title: 'Electronic Health Record Backup Stale',
    description: 'Patient chart snapshots are older than the 24-hour business SLA.',
    severity: 'critical',
    category: 'Data Protection & Recovery',
    system: 'Veeam Cloud Vault',
    explanation: createMockExecutiveExplanation(),
    remediation: {
      action_type: 'trigger_backup',
      button_text: 'Trigger Backup Snapshot',
      estimated_time_mins: 15,
      impact: 'Restores RPO compliance for patient health record database.',
    },
    delegation: {
      suggested_role: 'Lead Infrastructure Engineer',
      assigned_to: 'Sarah Chen',
    },
    ...overrides,
  };
}

export function createMockDailyReadinessReport(
  overrides: Partial<DailyReadinessReport> = {}
): DailyReadinessReport {
  return {
    org_id: 'org-metro-001',
    clinic_health_pct: 78,
    connector_health_pct: 82,
    status: 'action_needed' as any,
    summary: '3 of 4 core protections verified. 1 critical backup gap requires your attention.',
    greeting: 'Good morning, Managing Partner',
    timeline: [],
    business_continuity: {
      safe_to_operate: true,
      executive_verdict: 'Clinical systems safe for outpatient appointments, but EHR backup requires remediation before close of business.',
      rto_estimate_minutes: 45,
      rpo_status: 'degraded',
      operational_readiness: {
        can_operate_today: true,
        can_recover: true,
        current_blockers: [],
        estimated_downtime_minutes: 45,
        critical_systems_verified: ['Epic EHR Database', 'Microsoft 365'],
        critical_systems_assumed: [],
      },
    } as any,
    passed_checks: [
      { id: 'chk-1', name: 'MFA Enforcement', category: 'Identity' },
      { id: 'chk-2', name: 'Endpoint Protection', category: 'Devices' },
      { id: 'chk-3', name: 'Email Gateway Filter', category: 'Email' },
    ],
    failed_checks: [
      { id: 'chk-4', name: 'Immutable Backups', category: 'Backups', explanation: createMockExecutiveExplanation() as any },
    ],
    warnings: [
      { id: 'chk-5', name: 'TLS Certificate Expiration', category: 'Network' },
    ],
    unknowns: [],
    immediate_actions: [createMockActionCard() as any],
    coverage: {
      overall_percentage: 85,
      areas: [
        { name: 'Identity & Access', monitored_items: 12, unmonitored_items: 0, percentage: 100 },
        { name: 'Data Recovery', monitored_items: 4, unmonitored_items: 1, percentage: 80 },
      ],
    },
    connectors: [
      { name: 'Microsoft Graph', status: 'healthy', last_sync: '2026-08-31T08:15:00Z' },
      { name: 'Veeam Backup API', status: 'degraded', last_sync: '2026-08-31T08:00:00Z' },
    ],
    verification: {
      overall_confidence_pct: 95,
      verified_items_count: 18,
      total_items_count: 20,
    },
    trend: {
      direction: 'down',
      percentage_change: -8,
      narrative: 'Readiness dropped 8% overnight due to EHR backup failure.',
    },
    value: {
      hours_saved: 14.5,
    },
    generated_at: '2026-08-31T08:30:00Z',
    ...overrides,
  };
}

export function createMockReportList(): { reports: Report[]; total: number } {
  return {
    total: 3,
    reports: [
      {
        id: 'rep-001',
        organization_id: 'org-metro-001',
        title: 'Executive Boardroom Readiness Story',
        description: 'Comprehensive readiness narrative for board members.',
        created_at: '2026-08-30T10:00:00Z',
        format: 'pdf',
        report_type: 'board_story',
        status: 'ready',
        assessment_id: 'asm-101',
        assessment_title: 'Q3 Clinic Cyber Resilience Audit',
        organization_name: 'Metro Health Clinics',
        overall_score: 92,
        maturity_level: 4,
        maturity_name: 'Resilient & Managed',
        findings_count: 1,
      } as unknown as Report,
      {
        id: 'rep-002',
        organization_id: 'org-metro-001',
        title: 'HIPAA Safeguards & Backup Verification Package',
        description: 'HIPAA Security and Privacy Rule operational telemetry alignment.',
        created_at: '2026-08-25T14:30:00Z',
        format: 'pdf',
        report_type: 'gap_analysis',
        status: 'ready',
        assessment_id: 'asm-102',
        assessment_title: 'HIPAA Security Rule Verification',
        organization_name: 'Metro Health Clinics',
        overall_score: 88,
        maturity_level: 4,
        maturity_name: 'Resilient & Managed',
        findings_count: 2,
      } as unknown as Report,
      {
        id: 'rep-003',
        organization_id: 'org-metro-001',
        title: 'Monthly IT Operations Resilience Summary',
        description: 'Monthly operational telemetry and SLA report.',
        created_at: '2026-08-01T09:00:00Z',
        format: 'json',
        report_type: 'technical_findings',
        status: 'ready',
        assessment_id: 'asm-099',
        assessment_title: 'July Monthly Review',
        organization_name: 'Metro Health Clinics',
        overall_score: 84,
        maturity_level: 3,
        maturity_name: 'Proactive',
        findings_count: 4,
      } as unknown as Report,
    ],
  };
}

export function createMockGovernanceData() {
  return {
    overall_score: 88,
    last_audit_date: '2026-08-30T12:00:00Z',
    compliance_frameworks: [
      { id: 'nist', name: 'NIST CSF 2.0', score: 92, status: 'aligned', alignment_framing: 'Readiness evidence aligned to NIST Cybersecurity Framework' },
      { id: 'hipaa', name: 'HIPAA Security Rule', score: 86, status: 'minor_drift', alignment_framing: 'Readiness evidence aligned to HIPAA Security Rule' },
      { id: 'soc2', name: 'SOC 2 Type II', score: 95, status: 'aligned', alignment_framing: 'Readiness evidence aligned to SOC 2 Criteria' },
    ],
    drift_tracking: [
      {
        domain: 'IAM & Multi-Factor Authentication',
        baseline: 'Strict (MFA Required for 100% accounts)',
        currentState: '100% Enforced via Microsoft 365',
        status: 'aligned',
        variance: '0.0%',
        source: 'Microsoft Entra ID Connector',
        evidenceHash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      },
      {
        domain: 'Data at Rest Encryption (ePHI Volumes)',
        baseline: 'AES-256 / KMS Managed Mandatory',
        currentState: '98.8% Encrypted (3 Staging Volumes Pending)',
        status: 'drift',
        variance: '-1.2% (3 Volumes)',
        source: 'AWS CloudTrail & KMS Audit',
        evidenceHash: 'sha256:9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72',
      },
    ],
  };
}

export function createMockFrameworks() {
  return [
    {
      id: 'fw-nist-csf',
      name: 'NIST CSF 2.0',
      shortCode: 'NIST CSF 2.0',
      alignmentFraming: 'Readiness evidence aligned to NIST CSF 2.0 (PR.AC, DE.CM, RC.RP)',
      description: 'Comprehensive risk management framework.',
      status: 'aligned',
      statusLabel: 'Aligned',
      score: 92,
      coveredControls: 104,
      totalControls: 108,
      lastScan: '2 hours ago',
      icon: 'nist',
    },
    {
      id: 'fw-hipaa',
      name: 'HIPAA Security & Privacy Rule',
      shortCode: 'HIPAA',
      alignmentFraming: 'Readiness evidence aligned to HIPAA Safeguards (45 CFR Part 164)',
      description: 'Safeguards for ePHI.',
      status: 'aligned',
      statusLabel: 'Aligned',
      score: 99,
      coveredControls: 42,
      totalControls: 42,
      lastScan: '15 mins ago',
      icon: 'hipaa',
    },
  ];
}
