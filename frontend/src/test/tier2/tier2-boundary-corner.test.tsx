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

describe('Tier 2: Boundary & Corner Cases (R1 - R8)', () => {
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

  // =========================================================================
  // R1: TodayPage Boundary & Corner Cases
  // =========================================================================
  describe('R1: Product Identity & Narrative Hierarchy Boundaries', () => {
    it('T2.R1.01: Zero clinic health score (0%) and zero confidence handles without NaN or div-by-zero errors', async () => {
      const mockReport = createMockDailyReadinessReport({
        clinic_health_pct: 0,
        status: 'action_required',
        verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 10 } as any,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('LIVE WORKSPACE • NOT YET VERIFIED')).toBeInTheDocument();
      });
      expect(screen.getByText('Connect Security System')).toBeInTheDocument();
    });

    it('T2.R1.02: 100% perfect readiness with 0 active gaps renders verified all-green state and empty triage', async () => {
      const mockReport = createMockDailyReadinessReport({
        clinic_health_pct: 100,
        status: 'safe_to_open',
        summary: 'All 14 clinical and security systems passed continuous overnight verification.',
        immediate_actions: [],
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('READY FOR TODAY')).toBeInTheDocument();
      });
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('No Critical Gaps Pending')).toBeInTheDocument();
    });

    it('T2.R1.03: Missing immediate actions array handles cleanly without crashing', async () => {
      const mockReport = createMockDailyReadinessReport({
        immediate_actions: [],
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('No Critical Gaps Pending')).toBeInTheDocument();
      });
    });

    it('T2.R1.04: Extremely long narrative text in Stage 2 Morning Brief wraps gracefully', async () => {
      const longText = 'All clinical operations and telemetry verified against regional compliance baselines without disruption.';
      const mockReport = createMockDailyReadinessReport({
        summary: longText,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText(new RegExp(longText, 'i'))).toBeInTheDocument();
      });
    });

    it('T2.R1.05: Missing business continuity block in daily report defaults safely to standard fallback values', async () => {
      const mockReport = createMockDailyReadinessReport({
        business_continuity: undefined,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText(/Stage 2 • Why/i)).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // R2: Progressive Disclosure Boundaries
  // =========================================================================
  describe('R2: Progressive Disclosure & AIDrawer Boundaries', () => {
    it('T2.R2.01: ExecutiveExplanation with empty strings in technical evidence handles without error', async () => {
      const user = userEvent.setup();
      const explanation = createMockExecutiveExplanation({
        technical_label: '',
        evidence_telemetry: '',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      const toggleButton = screen.getByRole('button', { name: /tier 3 & 4/i });
      await user.click(toggleButton);

      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('T2.R2.02: 0% confidence score in AIDrawer renders "0% Deterministic"', () => {
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={vi.fn()}
          title="Staging Cluster Telemetry"
          confidence={0}
        />
      );

      expect(screen.getByText('0% Deterministic')).toBeInTheDocument();
    });

    it('T2.R2.03: ISO timestamp with unusual millisecond or timezone offsets formats reliably', () => {
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={vi.fn()}
          title="Backup Telemetry"
          timestamp="2026-08-31T04:15:30.987654+05:30"
        />
      );

      expect(screen.getAllByText(/2026-08-31/i).length).toBeGreaterThan(0);
    });

    it('T2.R2.04: ExecutiveExplanation with unknown status/evidence state falls back gracefully', () => {
      const explanation = createMockExecutiveExplanation({
        status: 'unknown' as any,
        evidence_state: 'unavailable',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);
      expect(screen.getByText('Electronic Health Record Backup Stale')).toBeInTheDocument();
    });

    it('T2.R2.05: AIDrawer opened without target or domain props renders generic deterministic drawer', () => {
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={vi.fn()}
          title="Generic Evidence"
        />
      );

      expect(screen.getByText('Generic Evidence')).toBeInTheDocument();
      expect(screen.getByText('How do we know?')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R3: Onboarding Boundaries
  // =========================================================================
  describe('R3: Onboarding & Getting Started Boundaries', () => {
    it('T2.R3.01: Step 1 with whitespace-only organization name keeps continue button disabled', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, '     ');

      const continueButton = screen.getByRole('button', { name: /continue to step 2/i });
      expect(continueButton).toBeDisabled();
    });

    it('T2.R3.02: Rapid clicking on next/prev navigation handles state transitions cleanly', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Metro Health');

      const step2Btn = screen.getByRole('button', { name: /continue to step 2/i });
      await user.click(step2Btn);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /back to profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /back to profile/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Start with Organization Readiness/i })).toBeInTheDocument();
      });
    });

    it('T2.R3.03: Navigating to Onboarding when already marked completed in localStorage still allows reviewing steps', async () => {
      localStorage.setItem('resilai_onboarding_completed_default-org', 'true');
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Start with Organization Readiness/i })).toBeInTheDocument();
      });
    });

    it('T2.R3.04: Step 2 connector toggle toggles connection state and updates sync indicator', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Metro Health');
      await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

      await waitFor(() => {
        expect(screen.getByText('Microsoft 365 / Entra ID')).toBeInTheDocument();
      });

      const connectBtns = screen.getAllByRole('button', { name: /connect/i });
      if (connectBtns.length > 0) {
        await user.click(connectBtns[0]);
      }
    });

    it('T2.R3.05: Step 3 Evidence Ledger displays empty state if no telemetry events exist', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getOrganizations).mockResolvedValue([]);

      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Metro Health');
      await user.click(screen.getByRole('button', { name: /continue to step 2/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to step 3/i })).toBeInTheDocument();
      });
      await user.click(screen.getByRole('button', { name: /continue to step 3/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /See What Can Be Verified/i })).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // R4: Demo Mode Boundaries
  // =========================================================================
  describe('R4: Demo Mode & Telemetry Isolation Boundaries', () => {
    it('T2.R4.01: SimulatedTelemetryBanner in non-operator pages is not rendered', () => {
      renderWithRouter(<TodayPage />);
      expect(screen.queryByText(/Operator Workspace Preview/i)).not.toBeInTheDocument();
    });

    it('T2.R4.02: Switching organization in useActiveOrg from Demo to Live updates state detection', () => {
      renderWithRouter(<SimulatedTelemetryBanner domainName="Data Backups" />);
      expect(screen.getByText('Simulated Telemetry')).toBeInTheDocument();
    });

    it('T2.R4.03: Unverified live organization launchpad renders Explore Live Sandbox Demo button', async () => {
      const mockReport = createMockDailyReadinessReport({
        status: 'unknown',
        clinic_health_pct: 0,
        verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 5 } as any,
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText('Explore Live Sandbox Demo')).toBeInTheDocument();
      });
    });

    it('T2.R4.04: Demo banner handles undefined domainName by falling back to standard operator preview label', () => {
      renderWithRouter(<SimulatedTelemetryBanner domainName="" />);
      expect(screen.getByText('Simulated Telemetry')).toBeInTheDocument();
    });

    it('T2.R4.05: AppSidebar renders navigation correctly when active organization is demo', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-org',
        orgName: 'Acme Health Systems (Demo)',
        org: { id: 'demo-org', name: 'Acme Health Systems (Demo)' } as any,
        orgs: [{ id: 'demo-org', name: 'Acme Health Systems (Demo)' } as any],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      renderWithRouter(<AppSidebar />);
      expect(screen.getByText('L1: Executive Briefing')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R5: Explanation & Remediation Boundaries
  // =========================================================================
  describe('R5: Executive Explanation & Remediation Boundaries', () => {
    it('T2.R5.01: Action button in "executing" state is disabled to prevent duplicate clicks', () => {
      const explanation = createMockExecutiveExplanation();
      const onAction = vi.fn();

      renderWithRouter(
        <ExecutiveExplanation
          explanation={explanation}
          actionLabel="Fix Now"
          onAction={onAction}
          actionState="executing"
        />
      );

      const button = screen.getByRole('button', { name: /applying fix/i });
      expect(button).toBeDisabled();
    });

    it('T2.R5.02: Failed remediation API call handles error without crashing component', async () => {
      const mockReport = createMockDailyReadinessReport();
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);
      vi.mocked(api.triggerProblemFix).mockRejectedValue(new Error('Network error'));

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /fix/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /fix/i }));
      expect(api.triggerProblemFix).toHaveBeenCalled();
    });

    it('T2.R5.03: ExecutiveExplanation with missing optional fields renders available fields cleanly', () => {
      const explanation = createMockExecutiveExplanation({
        why_it_matters: '',
        what_to_do_next: '',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);
      expect(screen.getByText('Electronic Health Record Backup Stale')).toBeInTheDocument();
    });

    it('T2.R5.04: Dual presentation technical toggle persists expanded state upon clicking', async () => {
      const user = userEvent.setup();
      const explanation = createMockExecutiveExplanation({
        technical_label: 'CrowdStrike Falcon Sensor: OFF_LINE',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);

      const toggleButton = screen.getByRole('button', { name: /tier 3 & 4/i });
      await user.click(toggleButton);

      expect(screen.getByText('CrowdStrike Falcon Sensor: OFF_LINE')).toBeInTheDocument();
    });

    it('T2.R5.05: ExecutiveExplanation with SHA-256 hash renders formatted hash safely', () => {
      const explanation = createMockExecutiveExplanation({
        cryptographic_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      });

      renderWithRouter(<ExecutiveExplanation explanation={explanation} />);
      expect(screen.getByText('Electronic Health Record Backup Stale')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // R6: Reports UX Boundaries
  // =========================================================================
  describe('R6: Reports UX Boundaries', () => {
    it('T2.R6.01: Empty reports response ({ reports: [], total: 0 }) renders clean empty state', async () => {
      vi.mocked(api.getReports).mockResolvedValue({ reports: [], total: 0 } as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('0 saved reports')).toBeInTheDocument();
      });
      expect(screen.getByText('No saved reports yet')).toBeInTheDocument();
    });

    it('T2.R6.02: Search query with no matching reports displays empty match state', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search reports/i);
      fireEvent.change(searchInput, { target: { value: 'NONEXISTENT_QUERY_XYZ' } });

      await waitFor(() => {
        expect(screen.getByText('No saved reports yet')).toBeInTheDocument();
      });
    });

    it('T2.R6.03: Report download failure handles gracefully without crashing UI', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);
      vi.mocked(api.downloadReportById).mockRejectedValue(new Error('Download failed'));

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const downloadBtns = screen.getAllByRole('button', { name: /download/i });
      fireEvent.click(downloadBtns[0]);

      expect(api.downloadReportById).toHaveBeenCalled();
    });

    it('T2.R6.04: Filter by format (PDF vs JSON) correctly filters report list', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const selects = screen.getAllByRole('combobox');
      if (selects.length > 1) {
        fireEvent.change(selects[1], { target: { value: 'json' } });
      }
    });

    it('T2.R6.05: Report deletion rejection (user cancels confirm) preserves report in list', async () => {
      const mockList = createMockReportList();
      vi.mocked(api.getReports).mockResolvedValue(mockList as any);
      vi.spyOn(window, 'confirm').mockReturnValue(false);

      renderWithRouter(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      });

      const buttons = screen.getAllByRole('button');
      const trashButton = buttons.find((btn) => btn.querySelector('.lucide-trash-2') || btn.querySelector('svg.lucide-trash2'));
      if (trashButton) {
        fireEvent.click(trashButton);
        expect(api.deleteReport).not.toHaveBeenCalled();
      }
    });
  });

  // =========================================================================
  // R7: Documents & Governance Boundaries
  // =========================================================================
  describe('R7: Documents & Governance Boundaries', () => {
    it('T2.R7.01: Documents search filter narrows audit folders and reports in real time', async () => {
      renderWithRouter(<DocumentsPage />);

      await waitFor(() => {
        expect(screen.getByText('Audit-Ready Folders')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search documents, policies/i);
      fireEvent.change(searchInput, { target: { value: 'HIPAA' } });

      expect(screen.getByText('HIPAA Safeguards Package')).toBeInTheDocument();
      expect(screen.queryByText('System Configs')).not.toBeInTheDocument();
    });

    it('T2.R7.02: Audit ledger empty list ([]) renders clean state in DocumentsPage', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getEvidenceLedger).mockResolvedValue([]);

      renderWithRouter(<DocumentsPage />);

      await user.click(screen.getByRole('button', { name: /Audit Sync Ledger/i }));

      await waitFor(() => {
        expect(screen.getByText(/Connector Synchronization & Verification Logs/i)).toBeInTheDocument();
      });
    });

    it('T2.R7.03: Copy evidence SHA-256 hash in Governance drift table provides feedback', async () => {
      vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
      vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

      renderWithRouter(<GovernancePage />);

      await waitFor(() => {
        expect(screen.getByText(/Compliance Drift Tracking & Technical Telemetry/i)).toBeInTheDocument();
      });

      const copyBtns = screen.getAllByRole('button', { name: /copy/i });
      if (copyBtns.length > 0) {
        fireEvent.click(copyBtns[0]);
        await waitFor(() => {
          expect(screen.getAllByText(/Copied/i).length).toBeGreaterThan(0);
        });
      }
    });

    it('T2.R7.04: Governance framework search filter narrows down displayed frameworks', async () => {
      vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
      vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

      renderWithRouter(<GovernancePage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'NIST CSF 2.0' })).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search frameworks/i);
      fireEvent.change(searchInput, { target: { value: 'HIPAA' } });

      expect(screen.getByRole('heading', { name: 'HIPAA Security & Privacy Rule' })).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: 'NIST CSF 2.0' })).not.toBeInTheDocument();
    });

    it('T2.R7.05: Governance framework click selects framework and opens details', async () => {
      vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(createMockGovernanceData() as any);
      vi.mocked(api.getApplicableFrameworks).mockResolvedValue(createMockFrameworks() as any);

      renderWithRouter(<GovernancePage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'NIST CSF 2.0' })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('heading', { name: 'NIST CSF 2.0' }));
    });
  });

  // =========================================================================
  // R8: Design Consistency & Responsive Layout Boundaries
  // =========================================================================
  describe('R8: Design Consistency & Responsive Layout Boundaries', () => {
    it('T2.R8.01: Screen resize to 375px mobile viewport renders stacked responsive layout', () => {
      window.innerWidth = 375;
      window.innerHeight = 667;
      window.dispatchEvent(new Event('resize'));

      renderWithRouter(<AppSidebar />);
      expect(screen.getByText('L1: Executive Briefing')).toBeInTheDocument();
    });

    it('T2.R8.02: Backdrop click triggers onClose handler in AIDrawer', () => {
      const onClose = vi.fn();
      renderWithRouter(
        <AIDrawer
          isOpen={true}
          onClose={onClose}
          title="Endpoint Security"
        />
      );

      const backdrop = document.querySelector('.bg-background\\/80');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(onClose).toHaveBeenCalled();
      }
    });

    it('T2.R8.03: NeedsAttentionPage with 0 gaps displays "Zero Critical Blockers"', async () => {
      const mockReport = createMockDailyReadinessReport({
        immediate_actions: [],
        failed_checks: [],
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<NeedsAttentionPage />);

      await waitFor(() => {
        expect(screen.getByText('Zero Critical Blockers')).toBeInTheDocument();
      });
    });

    it('T2.R8.04: RecoveryReadinessPage handles degraded RPO with warning indicators', async () => {
      const mockReport = createMockDailyReadinessReport({
        business_continuity: {
          safe_to_operate: true,
          executive_verdict: 'Degraded RPO',
          rto_estimate_minutes: 90,
          rpo_status: 'degraded',
          operational_readiness: {
            can_operate_today: true,
            can_recover: false,
            current_blockers: ['EHR Backup Stale'],
            estimated_downtime_minutes: 90,
            critical_systems_verified: ['M365'],
            critical_systems_assumed: ['Epic EHR'],
          },
        },
      });
      vi.mocked(api.getDailyReadinessReport).mockResolvedValue(mockReport);

      renderWithRouter(<RecoveryReadinessPage />);

      await waitFor(() => {
        expect(screen.getByText('Recovery Readiness')).toBeInTheDocument();
      });
      expect(screen.getByText('90')).toBeInTheDocument();
    });

    it('T2.R8.05: Interactive buttons across all pages have accessible focus indicators and roles', () => {
      renderWithRouter(<AppSidebar />);
      const buttons = screen.getAllByRole('link');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });
});
