import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import TodayPage from '../../features/readiness/TodayPage';
import NeedsAttentionPage from '../../features/readiness/NeedsAttentionPage';
import RecoveryReadinessPage from '../../features/readiness/RecoveryReadinessPage';
import { AIDrawer } from '../../components/readiness/AIDrawer';
import Onboarding from '../../pages/Onboarding';
import Reports from '../../pages/Reports';
import DocumentsPage from '../../pages/Documents';
import GovernancePage from '../../pages/Governance';
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

describe('Tier 3: Cross-Feature Navigation & State Interaction', () => {
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
  });

  it('T3.CF.01: TodayPage -> "View All Incident Risks" link points to /needs-attention', async () => {
    const mockReport = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /View All Incident Risks/i })).toBeInTheDocument();
    });

    const link = screen.getByRole('link', { name: /View All Incident Risks/i });
    expect(link).toHaveAttribute('href', '/needs-attention');
  });

  it('T3.CF.02: TodayPage -> "Explain for Leadership" button opens Executive Briefing Translation modal', async () => {
    const user = userEvent.setup();
    const mockReport = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Explain for Leadership/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Explain for Leadership/i }));

    await waitFor(() => {
      expect(screen.getByText('Executive Briefing Translation')).toBeInTheDocument();
    });
    expect(screen.getByText('Presentation Mode')).toBeInTheDocument();
  });

  it('T3.CF.03: TodayPage -> Click "Fix Now" triggers problem remediation API call', async () => {
    const mockReport = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);
    vi.mocked(api.triggerProblemFix).mockResolvedValue({ success: true, message: 'Remediation initiated' } as any);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Fix Now/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Fix Now/i }));
    expect(api.triggerProblemFix).toHaveBeenCalledWith('action-ehr-backup-001');
  });

  it('T3.CF.04: AIDrawer -> "View Full Technical Details" triggers navigation and drawer close', async () => {
    const onClose = vi.fn();
    const onViewFullEvidence = vi.fn();

    renderWithRouter(
      <AIDrawer
        isOpen={true}
        onClose={onClose}
        title="Epic EHR Backup Gap"
        domainPath="/recovery"
        domainName="Backups & Recovery"
        onViewFullEvidence={onViewFullEvidence}
      />
    );

    const button = screen.getByRole('button', { name: /View Technical Details in Backups & Recovery/i });
    fireEvent.click(button);

    expect(onClose).toHaveBeenCalled();
    expect(onViewFullEvidence).toHaveBeenCalled();
  });

  it('T3.CF.05: Onboarding -> "Skip to Dashboard" sets localStorage and navigates to /morning-brief', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getOrganizations).mockResolvedValue([]);

    renderWithRouter(
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/morning-brief" element={<div data-testid="morning-brief-page">Morning Brief Destination</div>} />
      </Routes>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /skip to dashboard/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /skip to dashboard/i }));

    expect(localStorage.getItem('resilai_onboarding_completed_default-org')).toBe('true');
    await waitFor(() => {
      expect(screen.getByTestId('morning-brief-page')).toBeInTheDocument();
    });
  });

  it('T3.CF.06: Onboarding -> Sequential Step 1 -> Step 2 -> Step 3 transition flow', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getOrganizations).mockResolvedValue([]);

    renderWithRouter(<Onboarding />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
    });

    const orgInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
    await user.type(orgInput, 'Valley Outpatient Clinic');

    await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Connect Security Systems/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /continue to step 3/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /See What Can Be Verified/i })).toBeInTheDocument();
    });
  });

  it('T3.CF.07: AppSidebar -> Contains accessible navigation links across all tiers', () => {
    renderWithRouter(<AppSidebar />);

    const todayLink = screen.getByRole('link', { name: /^Today/i });
    expect(todayLink).toHaveAttribute('href', '/morning-brief');

    const triageLink = screen.getByRole('link', { name: /^Needs Attention/i });
    expect(triageLink).toHaveAttribute('href', '/needs-attention');

    const recoveryLink = screen.getByRole('link', { name: /^Recovery/i });
    expect(recoveryLink).toHaveAttribute('href', '/recovery');

    const governanceLink = screen.getByRole('link', { name: /^Governance/i });
    expect(governanceLink).toHaveAttribute('href', '/governance');

    const documentsLink = screen.getByRole('link', { name: /^Customer Evidence/i });
    expect(documentsLink).toHaveAttribute('href', '/documents');

    const reportsLink = screen.getByRole('link', { name: /^Reports/i });
    expect(reportsLink).toHaveAttribute('href', '/reports');
  });

  it('T3.CF.08: GovernancePage -> Framework card selection opens framework details modal', async () => {
    vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

    renderWithRouter(<GovernancePage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'NIST CSF 2.0' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('heading', { name: 'NIST CSF 2.0' }));

    await waitFor(() => {
      expect(screen.getByText('Framework Overview')).toBeInTheDocument();
    });
    expect(screen.getByText(/Sample Mapped Controls & Telemetry Proofs/i)).toBeInTheDocument();
  });

  it('T3.CF.09: DocumentsPage -> Tab switching between Evidence Vault and Audit Sync Ledger', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getEvidenceLedger).mockResolvedValue([
      {
        id: 'ledg-001',
        timestamp: '2026-08-31T08:00:00Z',
        connector: 'Microsoft Graph',
        event_type: 'SYNC_SUCCESS',
        status: 'verified',
        verification_status: 'verified',
        target: 'Identity & Access',
        evidence_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      } as any,
    ]);

    renderWithRouter(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Audit-Ready Folders')).toBeInTheDocument();
    });

    const ledgerTab = screen.getByRole('button', { name: /Audit Sync Ledger/i });
    await user.click(ledgerTab);

    await waitFor(() => {
      expect(screen.getByText(/Connector Synchronization & Verification Logs/i)).toBeInTheDocument();
    });

    const vaultTab = screen.getByRole('button', { name: /Evidence Vault/i });
    await user.click(vaultTab);

    await waitFor(() => {
      expect(screen.getByText('Audit-Ready Folders')).toBeInTheDocument();
    });
  });

  it('T3.CF.10: ReportsPage -> Form submission generates new report and renders progress', async () => {
    const user = userEvent.setup();
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);
    vi.mocked(api.generateReport).mockResolvedValue({
      id: 'rep-new-999',
      title: 'Real-Time Board Story',
      created_at: new Date().toISOString(),
      report_type: 'board_story',
      format: 'pdf',
      status: 'ready',
      overall_score: 95,
      findings_count: 0,
    } as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
    });

    const titleInput = screen.getByPlaceholderText(/e\.g\., Q3 Executive Incident Readiness Briefing/i);
    await user.type(titleInput, 'Real-Time Board Story');

    const generateBtn = screen.getByRole('button', { name: /Generate Report/i });
    await user.click(generateBtn);

    expect(api.generateReport).toHaveBeenCalled();
  });

  it('T3.CF.11: TodayPage -> Unverified workspace launchpad "Explore Live Sandbox Demo" links to demo URL', async () => {
    vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
      orgId: 'live-unverified-org',
      orgName: 'Unverified Live Workspace',
      org: { id: 'live-unverified-org', name: 'Unverified Live Workspace' } as any,
      orgs: [{ id: 'live-unverified-org', name: 'Unverified Live Workspace' } as any],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn(),
    });

    const mockReport = createMockDailyReadinessReport({
      status: 'unknown',
      clinic_health_pct: 0,
      verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 0 } as any,
      immediate_actions: [],
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Explore Live Sandbox Demo/i })).toBeInTheDocument();
    });

    const link = screen.getByRole('link', { name: /Explore Live Sandbox Demo/i });
    expect(link).toHaveAttribute('href', 'https://demo.resilai.org');
  });

  it('T3.CF.12: NeedsAttentionPage -> "Re-evaluate Gaps" button re-invokes getDailyReadinessReport', async () => {
    const mockReport = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

    renderWithRouter(<NeedsAttentionPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Re-evaluate Gaps/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Re-evaluate Gaps/i }));
    expect(api.getDailyReadinessReport).toHaveBeenCalledTimes(2);
  });
});
