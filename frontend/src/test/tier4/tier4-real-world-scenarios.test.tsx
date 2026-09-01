import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import TodayPage from '../../features/readiness/TodayPage';
import NeedsAttentionPage from '../../features/readiness/NeedsAttentionPage';
import Onboarding from '../../pages/Onboarding';
import Reports from '../../pages/Reports';
import DocumentsPage from '../../pages/Documents';
import GovernancePage from '../../pages/Governance';
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

describe('Tier 4: Real-World Scenarios & Persona Journeys', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
      orgId: 'org-metro-health',
      orgName: 'Metro Health Clinics',
      org: { id: 'org-metro-health', name: 'Metro Health Clinics' } as any,
      orgs: [{ id: 'org-metro-health', name: 'Metro Health Clinics' } as any],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn(),
    });

    vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
      user: { uid: 'user-001', email: 'director@metrohealth.org', displayName: 'Dr. Evelyn Vance', photoURL: null },
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
  });

  // =========================================================================
  // Journey 1: Managing Partner 30-Second Morning Briefing & Leadership Translation
  // =========================================================================
  it('Journey 1: Managing Partner 30-Second Morning Briefing & Leadership Translation', async () => {
    const user = userEvent.setup();
    const mockReport = createMockDailyReadinessReport({
      clinic_health_pct: 94,
      status: 'safe_to_open',
      summary: 'All clinical systems and security safeguards verified continuously overnight.',
      greeting: 'Good morning, Dr. Vance',
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

    renderWithRouter(<TodayPage />);

    // Step 1: Verify Stage 1 Status and Score
    await waitFor(() => {
      expect(screen.getByText('Stage 1 • READY FOR TODAY')).toBeInTheDocument();
    });
    expect(screen.getByText('94')).toBeInTheDocument();

    // Step 2: Verify Stage 2 Morning Brief Narrative
    expect(screen.getByText(/Good morning, Dr. Vance/i)).toBeInTheDocument();

    // Step 3: Open "Explain for Leadership" modal
    const explainBtn = screen.getByRole('button', { name: /Explain for Leadership/i });
    await user.click(explainBtn);

    await waitFor(() => {
      expect(screen.getByText('Executive Briefing Translation')).toBeInTheDocument();
    });

    // Step 4: Toggle between Executive and Technical View
    const techModeBtn = screen.getByRole('button', { name: /Technical Telemetry/i });
    await user.click(techModeBtn);

    const execModeBtn = screen.getByRole('button', { name: /Executive View/i });
    await user.click(execModeBtn);

    // Step 5: Close modal
    const closeBtn = screen.getByRole('button', { name: /close modal/i });
    await user.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByText('Executive Briefing Translation')).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // Journey 2: IT Operator Critical Triage, Progressive Disclosure, & 1-Click Remediation
  // =========================================================================
  it('Journey 2: IT Operator Critical Triage, Progressive Disclosure, & 1-Click Remediation', async () => {
    const user = userEvent.setup();
    const action = createMockActionCard();
    const initialReport = createMockDailyReadinessReport({
      clinic_health_pct: 78,
      status: 'action_required',
      immediate_actions: [action as any],
    });
    const remediatedReport = createMockDailyReadinessReport({
      clinic_health_pct: 95,
      status: 'safe_to_open',
      immediate_actions: [],
    });

    vi.mocked(api.getDailyReadinessReport)
      .mockResolvedValueOnce(initialReport)
      .mockResolvedValueOnce(remediatedReport);
    vi.mocked(api.triggerProblemFix).mockResolvedValue({ success: true } as any);

    renderWithRouter(
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/needs-attention" element={<NeedsAttentionPage />} />
      </Routes>
    );

    // Step 1: See Stage 3 Action Required on Morning Brief
    await waitFor(() => {
      expect(screen.getByText(/Stage 3 • What Needs Attention/i)).toBeInTheDocument();
    });

    // Step 2: Follow link to Triage & Action page
    const triageLink = screen.getByRole('link', { name: /View All Incident Risks/i });
    expect(triageLink).toHaveAttribute('href', '/needs-attention');

    // Step 3: Trigger 1-Click Fix
    const fixButton = screen.getByRole('button', { name: /Fix Now/i });
    await user.click(fixButton);

    expect(api.triggerProblemFix).toHaveBeenCalledWith('action-ehr-backup-001');

    // Step 4: Verify reload reflects remediated healthy state
    await waitFor(() => {
      expect(screen.getByText('Stage 1 • READY FOR TODAY')).toBeInTheDocument();
    });
    expect(screen.getByText('No Critical Gaps Pending')).toBeInTheDocument();
  });

  // =========================================================================
  // Journey 3: New Clinic Practice Manager Onboarding & Connector Setup
  // =========================================================================
  it('Journey 3: New Clinic Practice Manager Onboarding & Connector Setup', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getOrganizations).mockResolvedValue([]);
    vi.mocked(api.createOrganization).mockResolvedValue({
      id: 'org-summit-health',
      name: 'Summit Family Medicine',
    } as any);

    renderWithRouter(
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/morning-brief" element={<div data-testid="morning-brief-landing">Morning Brief Landing</div>} />
      </Routes>
    );

    // Step 1: Organization Profile
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
    });

    const orgInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
    await user.type(orgInput, 'Summit Family Medicine');

    const step2Btn = screen.getByRole('button', { name: /continue to step 2/i });
    await user.click(step2Btn);

    // Step 2: Connect Security Systems
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Connect Security Systems/i })).toBeInTheDocument();
    });

    const step3Btn = screen.getByRole('button', { name: /continue to step 3/i });
    await user.click(step3Btn);

    // Step 3: See What Can Be Verified (Evidence Ledger)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /See What Can Be Verified/i })).toBeInTheDocument();
    });

    // Step 4: Skip to Dashboard
    const skipBtn = screen.getByRole('button', { name: /skip to dashboard/i });
    await user.click(skipBtn);

    await waitFor(() => {
      expect(screen.getByTestId('morning-brief-landing')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // Journey 4: Compliance Officer Board Audit Preparation & Report Generation
  // =========================================================================
  it('Journey 4: Compliance Officer Board Audit Preparation & Report Generation', async () => {
    const user = userEvent.setup();
    const mockReports = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockReports as any);
    vi.mocked(api.generateReport).mockResolvedValue({
      id: 'rep-q3-board',
      title: 'Q3 Executive Cyber Resilience & Board Briefing',
      created_at: new Date().toISOString(),
      report_type: 'board_story',
      format: 'pdf',
      status: 'ready',
      overall_score: 96,
      findings_count: 0,
    } as any);

    const mockBlob = new Blob(['mock-pdf-bytes'], { type: 'application/pdf' });
    vi.mocked(api.downloadReportById).mockResolvedValue(mockBlob);

    renderWithRouter(<Reports />);

    // Step 1: View existing reports list
    await waitFor(() => {
      expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
    });

    // Step 2: Fill in custom title and generate report
    const titleInput = screen.getByPlaceholderText(/e\.g\., Q3 Executive Incident Readiness Briefing/i);
    await user.type(titleInput, 'Q3 Executive Cyber Resilience & Board Briefing');

    const generateBtn = screen.getByRole('button', { name: /Generate Report/i });
    await user.click(generateBtn);

    expect(api.generateReport).toHaveBeenCalled();

    // Step 3: Trigger download on existing report
    const downloadBtns = screen.getAllByRole('button', { name: /download/i });
    await user.click(downloadBtns[0]);

    expect(api.downloadReportById).toHaveBeenCalledWith('rep-001');
  });

  // =========================================================================
  // Journey 5: Security Auditor Evidence Vault & Policy Drift Inspection
  // =========================================================================
  it('Journey 5: Security Auditor Evidence Vault & Policy Drift Inspection', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);
    vi.mocked(api.getEvidenceLedger).mockResolvedValue([
      {
        id: 'ledg-audit-01',
        timestamp: '2026-08-31T08:00:00Z',
        source_name: 'Microsoft Entra ID',
        connector: 'Microsoft Entra ID',
        event_type: 'POLICY_VERIFIED',
        status: 'verified',
        verification_status: 'verified',
        target: 'IAM & Multi-Factor Authentication',
        evidence_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      } as any,
    ]);

    // Step 1: Open Governance page and inspect frameworks & drift tracking
    const govView = renderWithRouter(<GovernancePage />);

    await waitFor(() => {
      expect(screen.getByText('Governance & Framework Alignment')).toBeInTheDocument();
    });
    expect(screen.getByText(/Compliance Drift Tracking & Technical Telemetry/i)).toBeInTheDocument();

    // Step 2: Copy cryptographic SHA-256 evidence proof
    const copyBtns = screen.getAllByRole('button', { name: /copy/i });
    if (copyBtns.length > 0) {
      await user.click(copyBtns[0]);
      await waitFor(() => {
        expect(screen.getAllByText(/Copied/i).length).toBeGreaterThan(0);
      });
    }

    govView.unmount();

    // Step 3: Open Documents & Evidence Vault
    renderWithRouter(<DocumentsPage />);
    await waitFor(() => {
      expect(screen.getByText('Documents & Evidence Vault')).toBeInTheDocument();
    });

    // Step 4: Switch to Audit Sync Ledger
    const ledgerTab = screen.getByRole('button', { name: /Audit Sync Ledger/i });
    await user.click(ledgerTab);

    await waitFor(() => {
      expect(screen.getByText(/Connector Synchronization & Verification Logs/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Microsoft Entra ID')).toBeInTheDocument();
  });
});
