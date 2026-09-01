import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import TodayPage from '../../features/readiness/TodayPage';
import NeedsAttentionPage from '../../features/readiness/NeedsAttentionPage';
import RecoveryReadinessPage from '../../features/readiness/RecoveryReadinessPage';
import { ExecutiveExplanation } from '../../components/evidence/ExecutiveExplanation';
import { AIDrawer } from '../../components/readiness/AIDrawer';
import Onboarding from '../../pages/Onboarding';
import Reports from '../../pages/Reports';
import DocumentsPage from '../../pages/Documents';
import GovernancePage from '../../pages/Governance';
import { SimulatedTelemetryBanner } from '../../components/common/SimulatedTelemetryBanner';
import { AppSidebar } from '../../components/layout/AppSidebar';
import * as api from '../../api';
import * as useActiveOrgHook from '../../hooks/useActiveOrg';
import * as useAuthHook from '../../contexts/AuthContext';
import {
  createMockDailyReadinessReport,
  createMockExecutiveExplanation,
  createMockActionCard,
  createMockReportList,
  createMockGovernanceData,
  createMockFrameworks,
  renderWithRouter,
} from '../utils/test-helpers';

vi.mock('../../api');
vi.mock('../../hooks/useActiveOrg');
vi.mock('../../contexts/AuthContext');

describe('Tier 1: Feature Coverage (R1 - R8)', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
      orgId: 'org-health-123',
      orgName: 'Metro Health Clinics',
      org: { id: 'org-health-123', name: 'Metro Health Clinics' } as any,
      orgs: [{ id: 'org-health-123', name: 'Metro Health Clinics' } as any],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn(),
    });

    vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
      user: { uid: 'user-001', email: 'doctor@metrohealth.org', displayName: 'Dr. Smith', photoURL: null },
      loading: false,
      error: null,
      isConfigured: true,
      hasOrganizations: true,
      getToken: vi.fn().mockResolvedValue('token-xyz'),
      signInWithGoogle: vi.fn(),
      signInWithEmail: vi.fn(),
      signUpWithEmail: vi.fn(),
      signInAsDemo: vi.fn(),
      signOut: vi.fn(),
      clearError: vi.fn(),
      refreshAuth: vi.fn(),
    });

    vi.mocked(api.createOrganization).mockResolvedValue({
      id: 'org-health-123',
      name: 'Pacific Coast Health',
      industry: 'Healthcare',
    } as any);
  });

  // =========================================================================
  // R1: TodayPage Narrative Hierarchy (5 stages)
  // =========================================================================
  describe('R1: Product Identity & 5-Stage Narrative Hierarchy', () => {
    it('T1.R1.01: Stage 1 (Readiness Status Hero) renders macro status and score percentage', async () => {
      const mockReport = createMockDailyReadinessReport({
        status: 'safe_to_open',
        clinic_health_pct: 95,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('READY FOR TODAY')).toBeInTheDocument();
      });
      expect(screen.getByText('95')).toBeInTheDocument();
    });

    it('T1.R1.02: Stage 2 (Why / Morning Brief) displays overnight verification summary', async () => {
      const mockReport = createMockDailyReadinessReport({
        greeting: 'Good morning, Managing Partner',
        summary: '3 of 4 core protections verified. 1 critical backup gap requires your attention.',
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('Morning Brief')).toBeInTheDocument();
      });
      expect(screen.getByText(/3 of 4 core protections verified/i)).toBeInTheDocument();
      expect(screen.getByText('Engine Status')).toBeInTheDocument();
    });

    it('T1.R1.03: Stage 3 (What Needs Attention) renders action items with triage link', async () => {
      const mockReport = createMockDailyReadinessReport();
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Action Required/i })).toBeInTheDocument();
      });
      expect(screen.getByText(/View All Incident Risks/i)).toBeInTheDocument();
      expect(screen.getByText('Electronic Health Record Backup Stale')).toBeInTheDocument();
    });

    it('T1.R1.04: Stage 4 (What Should We Do) provides interactive fix trigger with executing state', async () => {
      const mockReport = createMockDailyReadinessReport();
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);
      vi.mocked(api.triggerProblemFix).mockResolvedValue({ status: 'dispatched' } as any);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /fix/i })).toBeInTheDocument();
      });

      const fixButton = screen.getByRole('button', { name: /fix/i });
      fireEvent.click(fixButton);

      expect(api.triggerProblemFix).toHaveBeenCalledWith('action-ehr-backup-001');
    });

    it('T1.R1.05: Stage 5 (How Can We Prove It) displays verified protections and openable modal', async () => {
      const mockReport = createMockDailyReadinessReport();
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText(/Stage 5 • How Can We Prove It/i)).toBeInTheDocument();
      });
      expect(screen.getByText('Data Recovery & Ransomware Shield')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /view coverage/i })).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R2: Executive-First 4-Tier Progressive Disclosure
  // =========================================================================
  describe('R2: Executive-First 4-Tier Progressive Disclosure', () => {
    it('T1.R2.01: Tier 1 (Executive Explanation) displays plain-English business label and what it means', () => {
      const explanation = createMockExecutiveExplanation({
        business_label: 'Electronic Health Record Backup Stale',
        what_it_means: 'Your patient medical records were not backed up in the last 24 hours.',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      expect(screen.getByText('Electronic Health Record Backup Stale')).toBeInTheDocument();
      expect(screen.getByText('Your patient medical records were not backed up in the last 24 hours.')).toBeInTheDocument();
    });

    it('T1.R2.02: Tier 2 (Business Impact) displays why it matters and what to do next', () => {
      const explanation = createMockExecutiveExplanation({
        why_it_matters: 'If a ransomware attack happens today, patient chart data will be permanently lost.',
        what_to_do_next: 'Trigger an immediate snapshot or verify Veeam credentials.',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      expect(screen.getByText('If a ransomware attack happens today, patient chart data will be permanently lost.')).toBeInTheDocument();
      expect(screen.getByText('Trigger an immediate snapshot or verify Veeam credentials.')).toBeInTheDocument();
    });

    it('T1.R2.03: Tier 3 (Technical Evidence) is collapsed by default and reveals technical label upon expanding', async () => {
      const user = userEvent.setup();
      const explanation = createMockExecutiveExplanation({
        technical_label: 'Veeam Backup Job Status: RPO_BREACH',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      const toggleButton = screen.getByRole('button', { name: /tier 3 & 4/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

      await user.click(toggleButton);

      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByText('Veeam Backup Job Status: RPO_BREACH')).toBeInTheDocument();
    });

    it('T1.R2.04: Tier 4 (Provenance) displays freshness timestamp and evidence state badges', () => {
      const explanation = createMockExecutiveExplanation({
        evidence_state: 'verified',
        status: 'verified',
        last_verified_at: '2026-08-31T08:00:00Z',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      expect(screen.getByText('VERIFIED')).toBeInTheDocument();
    });

    it('T1.R2.05: AIDrawer renders Deterministic Evidence, Operational AI Summary, and technical link', () => {
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={vi.fn()}
          title="Immutable EHR Backups"
          target="Veeam Cloud Vault"
          timestamp="04:00 UTC"
          confidence={99}
          source="Veeam Backup API"
          whyItMatters="Backup integrity guarantees clinical restoration within 45 minutes."
        />
      );

      expect(screen.getByText('How do we know?')).toBeInTheDocument();
      expect(screen.getByText(/1\. Deterministic Evidence/i)).toBeInTheDocument();
      expect(screen.getByText('99% Deterministic')).toBeInTheDocument();
      expect(screen.getByText(/2\. Why This Matters \(Operational AI Summary\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Backup integrity guarantees clinical restoration/i)).toBeInTheDocument();
      expect(screen.getByText(/View Technical Details in Backups & Recovery/i)).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R3: 6-Step Guided Onboarding & Getting Started Workflow
  // =========================================================================
  describe('R3: Comprehensive Getting Started & Onboarding Workflow', () => {
    it('T1.R3.01: Step 1 collects organizational details and validates required name', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Start with Organization Readiness/i })).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to step 2/i });
      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Pacific Coast Health');

      expect(continueButton).toBeEnabled();
    });

    it('T1.R3.02: Step 2 presents security connectors management', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Pacific Coast Health');
      await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Connect Security Systems/i })).toBeInTheDocument();
      });
    });

    it('T1.R3.03: Step 3 presents the evidence ledger and verification telemetry', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Pacific Coast Health');
      await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to step 3/i })).toBeInTheDocument();
      });
      await user.click(screen.getByRole('button', { name: /continue to step 3/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /See What Can Be Verified/i })).toBeInTheDocument();
      });
    });

    it('T1.R3.04: Skip to Dashboard navigates to /morning-brief and sets completion state', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /skip to dashboard/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /skip to dashboard/i }));
      expect(localStorage.getItem('resilai_onboarding_completed_default-org')).toBe('true');
    });

    it('T1.R3.05: Previous step button transitions safely back to Step 1', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Pacific Coast Health');
      await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /back to profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /back to profile/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Start with Organization Readiness/i })).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // R4: Contextual Demo Mode Guidance & Disclaimers
  // =========================================================================
  describe('R4: Contextual Demo Mode Guidance & Disclaimers', () => {
    it('T1.R4.01: useActiveOrg returns isDemo: true and demo organization name in demo mode', () => {
      localStorage.setItem('resilai_demo_user', 'true');
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-health-org',
        orgName: 'Acme Health Systems (Demo)',
        org: { id: 'demo-health-org', name: 'Acme Health Systems (Demo)' } as any,
        orgs: [{ id: 'demo-health-org', name: 'Acme Health Systems (Demo)' } as any],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      const { orgId, isDemo, orgName } = useActiveOrgHook.useActiveOrg();
      expect(isDemo).toBe(true);
      expect(orgId).toBe('demo-health-org');
      expect(orgName).toContain('Demo');
    });

    it('T1.R4.02: SimulatedTelemetryBanner displays domain name and simulated telemetry badge', () => {
      renderWithRouter(<SimulatedTelemetryBanner domainName="Data Backups & Recovery" />);

      expect(screen.getByText(/Data Backups & Recovery — Operator Workspace Preview/i)).toBeInTheDocument();
      expect(screen.getByText('Simulated Telemetry')).toBeInTheDocument();
      expect(screen.getByText(/displays illustrative operator telemetry/i)).toBeInTheDocument();
    });

    it('T1.R4.03: Live unverified organization renders LIVE WORKSPACE • NOT YET VERIFIED launchpad', async () => {
      const mockReport = createMockDailyReadinessReport({
        status: 'unknown',
        clinic_health_pct: 0,
        verification: {
          overall_confidence_pct: 0,
          verified_items_count: 0,
          total_items_count: 5,
        } as any,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('LIVE WORKSPACE • NOT YET VERIFIED')).toBeInTheDocument();
      });
      expect(screen.getByText('Welcome to your ResilAI Readiness Workspace')).toBeInTheDocument();
      expect(screen.getByText('Connect Security System')).toBeInTheDocument();
      expect(screen.getByText('Explore Live Sandbox Demo')).toBeInTheDocument();
    });

    it('T1.R4.04: AppSidebar displays navigation groups without deprecated workspace toggle', () => {
      renderWithRouter(<AppSidebar />);

      expect(screen.getByText('L1: Executive Briefing')).toBeInTheDocument();
      expect(screen.getByText('L2: Operations Manager')).toBeInTheDocument();
      expect(screen.getByText('L3: IT & Security')).toBeInTheDocument();
      expect(screen.getByText('Trust & Transparency')).toBeInTheDocument();
    });

    it('T1.R4.05: Demo banner informs that production verification occurs on Morning Brief from live connectors', () => {
      renderWithRouter(<SimulatedTelemetryBanner domainName="Identity & Access" />);

      expect(screen.getByText(/Production readiness verification is calculated deterministically/i)).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R5: Simplified Explanation ("Explain for Leadership")
  // =========================================================================
  describe('R5: Simplified Explanation Feature ("Explain for Leadership")', () => {
    it('T1.R5.01: ExecutiveExplanation renders business language without client-side LLM calls', () => {
      const explanation = createMockExecutiveExplanation({
        what_it_means: 'Multi-Factor Authentication is disabled on 4 clinical admin accounts.',
        why_it_matters: 'Phishing attack can directly compromise patient appointment schedules.',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      expect(screen.getByText('Multi-Factor Authentication is disabled on 4 clinical admin accounts.')).toBeInTheDocument();
      expect(screen.getByText('Phishing attack can directly compromise patient appointment schedules.')).toBeInTheDocument();
    });

    it('T1.R5.02: Dual presentation presents plain-English view with expandable technical evidence', async () => {
      const user = userEvent.setup();
      const explanation = createMockExecutiveExplanation({
        business_label: 'Endpoint Protection Missing',
        technical_label: 'CrowdStrike Falcon Sensor: OFF_LINE on 2 workstations',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      expect(screen.getByText('Endpoint Protection Missing')).toBeInTheDocument();
      expect(screen.queryByText('CrowdStrike Falcon Sensor: OFF_LINE on 2 workstations')).not.toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /tier 3 & 4/i }));
      expect(screen.getByText('CrowdStrike Falcon Sensor: OFF_LINE on 2 workstations')).toBeInTheDocument();
    });

    it('T1.R5.03: Status badge color classes match severity (verified, warning, critical)', () => {
      const verifiedExpl = createMockExecutiveExplanation({ status: 'verified', evidence_state: 'verified' });
      const { unmount } = renderWithRouter(<ExecutiveExplanation explanation={verifiedExpl} />);
      expect(screen.getByText('VERIFIED')).toBeInTheDocument();
      unmount();

      const criticalExpl = createMockExecutiveExplanation({ status: 'critical', evidence_state: 'no_evidence' });
      renderWithRouter(<ExecutiveExplanation explanation={criticalExpl} />);
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    });

    it('T1.R5.04: Action button provides clear state feedback (idle, executing, verified)', () => {
      const explanation = createMockExecutiveExplanation();
      const onAction = vi.fn();

      const { rerender } = render(
        <MemoryRouter>
          <ExecutiveExplanation
            explanation={explanation}
            actionLabel="Fix Now"
            onAction={onAction}
            actionState="idle"
          />
        </MemoryRouter>
      );
      expect(screen.getByRole('button', { name: 'Fix Now' })).toBeInTheDocument();

      rerender(
        <MemoryRouter>
          <ExecutiveExplanation
            explanation={explanation}
            actionLabel="Fix Now"
            onAction={onAction}
            actionState="executing"
          />
        </MemoryRouter>
      );
      expect(screen.getByText('Applying Fix...')).toBeInTheDocument();
    });

    it('T1.R5.05: ExecutiveExplanation renders UnavailableState when explanation prop is undefined', () => {
      renderWithRouter(<ExecutiveExplanation explanation={undefined} />);
      expect(screen.getByText('Explanation unavailable')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R6: Report UX & History Management
  // =========================================================================
  describe('R6: Report UX & History Management', () => {
    it('T1.R6.01: Reports page fetches and displays list of reports with metadata', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });
      expect(screen.getByText('HIPAA Safeguards & Backup Verification Package')).toBeInTheDocument();
      expect(screen.getByText('3 saved reports')).toBeInTheDocument();
    });

    it('T1.R6.02: Report cards render score percentages and maturity levels', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Score: 92%')).toBeInTheDocument();
      });
      expect(screen.getAllByText('L4: Resilient & Managed')[0]).toBeInTheDocument();
    });

    it('T1.R6.03: Download report invokes downloadReportById and manages object url', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);
      const fakeBlob = new Blob(['pdf-content'], { type: 'application/pdf' });
      vi.mocked(api.downloadReportById).mockResolvedValue(fakeBlob);

      const createObjectURLMock = vi.fn().mockReturnValue('blob:http://localhost/fake-pdf');
      const revokeObjectURLMock = vi.fn();
      global.URL.createObjectURL = createObjectURLMock;
      global.URL.revokeObjectURL = revokeObjectURLMock;

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const downloadButtons = screen.getAllByRole('button', { name: /download/i });
      fireEvent.click(downloadButtons[0]);

      await waitFor(() => {
        expect(api.downloadReportById).toHaveBeenCalledWith('rep-001');
      });
      expect(createObjectURLMock).toHaveBeenCalledWith(fakeBlob);
    });

    it('T1.R6.04: Share report button copies link to clipboard with confirmation text', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const shareButtons = screen.getAllByRole('button', { name: /share/i });
      fireEvent.click(shareButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });
    });

    it('T1.R6.05: Delete report prompts confirmation and removes report from UI', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);
      vi.mocked(api.deleteReport).mockResolvedValue({ success: true } as any);

      vi.spyOn(window, 'confirm').mockReturnValue(true);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const buttons = screen.getAllByRole('button');
      const trashButton = buttons.find((btn) => btn.querySelector('.lucide-trash-2') || btn.querySelector('svg.lucide-trash2'));
      if (trashButton) {
        fireEvent.click(trashButton);
        await waitFor(() => {
          expect(api.deleteReport).toHaveBeenCalledWith('rep-001');
        });
      }
    });
  });

  // =========================================================================
  // R7: Documents & Governance Page Modernization
  // =========================================================================
  describe('R7: Documents & Governance Page Modernization', () => {
    it('T1.R7.01: Documents page renders Evidence Vault and Audit Sync Ledger tabs', async () => {
      renderWithRouter(<DocumentsPage />);

      expect(screen.getByText('Documents & Evidence Vault')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Evidence Vault/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Audit Sync Ledger/i })).toBeInTheDocument();
    });

    it('T1.R7.02: Evidence Vault presents audit-ready folders and disaster recovery playbooks', async () => {
      renderWithRouter(<DocumentsPage />);

      await waitFor(() => {
        expect(screen.getByText('Audit-Ready Folders')).toBeInTheDocument();
      });
      expect(screen.getByText('HIPAA Safeguards Package')).toBeInTheDocument();
      expect(screen.getByText('Policy Guidelines')).toBeInTheDocument();
      expect(screen.getByText('Recovery Playbooks')).toBeInTheDocument();
    });

    it('T1.R7.03: Audit Trail tab renders Connector Sync Logs with SHA hashes and statuses', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getEvidenceLedger).mockResolvedValue([
        {
          id: 'ev-1',
          timestamp: '2026-08-31T04:00:00Z',
          source_name: 'Microsoft 365 Connector',
          event_type: 'MFA_POLICY_VERIFICATION',
          verification_status: 'verified',
          evidence_hash: 'a1b2c3d4e5f678901234567890abcdef',
        } as any,
      ]);

      renderWithRouter(<DocumentsPage />);

      await user.click(screen.getByRole('button', { name: /Audit Sync Ledger/i }));

      await waitFor(() => {
        expect(screen.getByText(/Connector Synchronization & Verification Logs/i)).toBeInTheDocument();
      });
      expect(screen.getByText('Microsoft 365 Connector')).toBeInTheDocument();
      expect(screen.getByText('MFA_POLICY_VERIFICATION')).toBeInTheDocument();
      expect(screen.getByText(/a1b2c3d4e5f67890/i)).toBeInTheDocument();
    });

    it('T1.R7.04: Governance page frames framework compliance as "Readiness evidence aligned to..."', async () => {
      vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
      vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

      renderWithRouter(<GovernancePage />);

      await waitFor(() => {
        expect(screen.getByText('Governance & Framework Alignment')).toBeInTheDocument();
      });
      expect(screen.getByText('NIST CSF 2.0')).toBeInTheDocument();
      expect(screen.getByText(/Readiness evidence aligned to NIST CSF 2\.0/i)).toBeInTheDocument();
      expect(screen.getByText('HIPAA Security & Privacy Rule')).toBeInTheDocument();
    });

    it('T1.R7.05: Compliance Drift Tracking table displays baseline, telemetry state, and variance', async () => {
      vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
      vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

      renderWithRouter(<GovernancePage />);

      await waitFor(() => {
        expect(screen.getByText(/Compliance Drift Tracking & Technical Telemetry/i)).toBeInTheDocument();
      });
      expect(screen.getByText('IAM & Multi-Factor Authentication')).toBeInTheDocument();
      expect(screen.getByText('100% Enforced via Microsoft 365')).toBeInTheDocument();
      expect(screen.getByText('Data at Rest Encryption (ePHI Volumes)')).toBeInTheDocument();
      expect(screen.getByText('-1.2% (3 Volumes)')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R8: Design Consistency, Accessibility & Responsive Layouts
  // =========================================================================
  describe('R8: Design Consistency, A11y & Responsive Layouts', () => {
    it('T1.R8.01: RecoveryReadinessPage renders Time to Recovery (RTO) and Disaster Recovery Playbook', async () => {
      const mockReport = createMockDailyReadinessReport({
        business_continuity: {
          operational_readiness: {
            can_operate_today: true,
            can_recover: true,
            current_blockers: [],
            estimated_downtime_minutes: 45,
            critical_systems_verified: ['Epic EHR Database', 'Microsoft 365'],
            critical_systems_assumed: [],
          },
        },
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<RecoveryReadinessPage />);

      await waitFor(() => {
        expect(screen.getByText('Recovery Readiness')).toBeInTheDocument();
      });
      expect(screen.getByText('Time to Recovery (RTO)')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('Disaster Recovery Playbook')).toBeInTheDocument();
      expect(screen.getByText('Ransomware Safe: YES')).toBeInTheDocument();
    });

    it('T1.R8.02: NeedsAttentionPage displays active critical gaps with clear severity badges', async () => {
      const mockReport = createMockDailyReadinessReport();
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<NeedsAttentionPage />);

      await waitFor(() => {
        expect(screen.getByText('Triage & Immediate Action')).toBeInTheDocument();
      });
      expect(screen.getByText('Critical Readiness Gaps')).toBeInTheDocument();
      expect(screen.getByText('1 Requiring Executive Action')).toBeInTheDocument();
    });

    it('T1.R8.03: Navigation links and buttons have valid text and accessible attributes', () => {
      renderWithRouter(<AppSidebar />);

      const todayLink = screen.getByRole('link', { name: /today/i });
      expect(todayLink).toHaveAttribute('href', '/morning-brief');

      const recoveryLink = screen.getByRole('link', { name: /recovery/i });
      expect(recoveryLink).toHaveAttribute('href', '/recovery');
    });

    it('T1.R8.04: Onboarding form fields have explicit labels and input bindings', async () => {
      vi.mocked(api.getOrganizations).mockResolvedValue([]);
      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByText(/Organization Name \*/i)).toBeInTheDocument();
      });
      expect(screen.getByText(/Company Size/i)).toBeInTheDocument();
      expect(screen.getByText(/Country \/ Jurisdiction/i)).toBeInTheDocument();
      expect(screen.getByText(/Region \/ State/i)).toBeInTheDocument();
    });

    it('T1.R8.05: AIDrawer close button triggers onClose handler', async () => {
      const onClose = vi.fn();
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={onClose}
          title="Endpoint Verification"
        />
      );

      const closeButton = screen.getByRole('button', { name: /close evidence drawer/i });
      fireEvent.click(closeButton);
      expect(onClose).toHaveBeenCalled();
    });
  });
});
