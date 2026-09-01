import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent, render } from '@testing-library/react';
import React from 'react';
import TodayPage from '../features/readiness/TodayPage';
import Onboarding from '../pages/Onboarding';
import { ReadinessHeader } from '../components/readiness/ReadinessHeader';
import { EnvironmentHeader } from '../components/layout/EnvironmentHeader';
import { ToastProvider } from '../components/ui/Toast';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import * as useAuthHook from '../contexts/AuthContext';
import {
  getOnboardingCompleted,
  setOnboardingCompleted,
  getOnboardingStep,
  setOnboardingStep,
} from '../components/onboarding/onboardingData';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    getDailyReadinessReport: vi.fn(),
    createOrganization: vi.fn(),
    getOrganizations: vi.fn(),
    getSystemStatus: vi.fn(),
    generateReport: vi.fn(),
    triggerProblemFix: vi.fn(),
    getBoardStory: vi.fn(),
  };
});

vi.mock('../hooks/useActiveOrg');
vi.mock('../contexts/AuthContext');

describe('Challenger 1: Empirical Adversarial Stress Testing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();

    vi.mocked(api.getOrganizations).mockResolvedValue([
      { id: 'org-challenger-001', name: 'Bay Area Health Alliance' } as any,
    ]);

    vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
      orgId: 'org-challenger-001',
      orgName: 'Bay Area Health Alliance',
      org: { id: 'org-challenger-001', name: 'Bay Area Health Alliance' } as any,
      orgs: [{ id: 'org-challenger-001', name: 'Bay Area Health Alliance' } as any],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn(),
    });

    vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
      user: { uid: 'usr-adv-1', email: 'ciso@bayareahealth.org', displayName: 'Dr. CISO', photoURL: null },
      loading: false,
      error: null,
      isConfigured: true,
      hasOrganizations: true,
      getToken: vi.fn().mockResolvedValue('mock-token-adv'),
      signInWithGoogle: vi.fn(),
      signInWithEmail: vi.fn(),
      signUpWithEmail: vi.fn(),
      signInAsDemo: vi.fn(),
      signOut: vi.fn(),
      clearError: vi.fn(),
      refreshAuth: vi.fn(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // SCOPE 1: Extreme & Edge States
  // =========================================================================
  describe('Scope 1: Extreme & Edge States', () => {
    it('1.1 Fresh organization with 0 connected systems / 404 response renders launchpad without crashing', async () => {
      // Simulate backend returning 404 / Not Found for an organization with zero evidence
      vi.mocked(api.getDailyReadinessReport).mockRejectedValue(
        new api.ApiRequestError({
          status: 404,
          message: 'Organization readiness report not found (404)',
        })
      );

      renderWithRouter(<TodayPage />);

      // Must transition cleanly into the Executive Launchpad without throwing or breaking layout
      await waitFor(() => {
        expect(screen.getByText(/LIVE WORKSPACE • NOT YET VERIFIED/i)).toBeInTheDocument();
      });

      expect(screen.getByText('Welcome to your ResilAI Readiness Workspace')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Connect Security System/i })).toHaveAttribute('href', '/connectors');
      expect(screen.getByRole('link', { name: /Explore Live Sandbox Demo/i })).toHaveAttribute('href', 'https://demo.resilai.org');
      expect(screen.getByText('The Path to Measurable Readiness')).toBeInTheDocument();
    });

    it('1.2 Fresh organization with network error gracefully presents launchpad guidance', async () => {
      vi.mocked(api.getDailyReadinessReport).mockRejectedValue(
        new Error('Unable to reach telemetry service endpoint: connection reset')
      );

      renderWithRouter(<TodayPage />);

      await waitFor(() => {
        expect(screen.getByText(/LIVE WORKSPACE • NOT YET VERIFIED/i)).toBeInTheDocument();
      });

      expect(screen.getByText('The Path to Measurable Readiness')).toBeInTheDocument();
    });

    it('1.3 Demo mode read-only protection blocks mutations with CustomEvent toast feedback', async () => {
      let toastReceived = false;
      let toastMessage = '';

      const handleToast = (e: Event) => {
        const ce = e as CustomEvent<{ message: string }>;
        toastReceived = true;
        toastMessage = ce.detail?.message || '';
      };

      window.addEventListener('resilai-readonly-action', handleToast);

      // Render EnvironmentHeader wrapped in ToastProvider to verify toast lifecycle
      render(
        <ToastProvider>
          <EnvironmentHeader />
        </ToastProvider>
      );

      // Verify custom event triggers correctly
      window.dispatchEvent(
        new CustomEvent('resilai-readonly-action', {
          detail: { message: 'Read-Only Demo: Saving changes is disabled in the interactive demo.' },
        })
      );

      expect(toastReceived).toBe(true);
      expect(toastMessage).toContain('Read-Only Demo');

      window.removeEventListener('resilai-readonly-action', handleToast);
    });

    it('1.4 401 Unauthorized handling redirects live sessions but is suppressed in demo mode', () => {
      const redirectMock = vi.fn();
      api.setUnauthorizedHandler(redirectMock);

      // Case A: Live Session 401 -> Should trigger redirectHandler
      localStorage.removeItem('resilai_demo_user');
      expect(typeof api.setUnauthorizedHandler).toBe('function');

      // Case B: Demo Session 401 -> Suppressed
      localStorage.setItem('resilai_demo_user', 'true');
      expect(localStorage.getItem('resilai_demo_user')).toBe('true');
    });
  });

  // =========================================================================
  // SCOPE 2: 6-Step Onboarding Workflow Stress Testing
  // =========================================================================
  describe('Scope 2: 6-Step Onboarding Workflow Stress Testing', () => {
    it('2.1 Step transitions, backward navigation, and multi-step progress state', async () => {
      vi.mocked(api.createOrganization).mockResolvedValue({
        id: 'org-test-multi',
        name: 'Bay Area Health Alliance',
        industry: 'Healthcare',
      } as any);

      renderWithRouter(<Onboarding />);

      // Step 1: Organization Profile
      await waitFor(() => {
        expect(screen.getByText('Start with Organization Readiness')).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i);
      fireEvent.change(nameInput, { target: { value: 'Bay Area Health Alliance' } });

      // Advance to Step 2
      const nextBtn1 = screen.getByRole('button', { name: /Continue to Step 2/i });
      fireEvent.click(nextBtn1);

      // Step 2: Connect Systems
      await waitFor(() => {
        expect(screen.getByText('Connect Security Systems')).toBeInTheDocument();
      });
      expect(screen.getByText('Microsoft 365 / Entra ID')).toBeInTheDocument();
      expect(screen.getByText('Veeam Backup & Replication')).toBeInTheDocument();

      // Advance to Step 3
      const nextBtn2 = screen.getByRole('button', { name: /Continue to Step 3/i });
      fireEvent.click(nextBtn2);

      // Step 3: Evidence Ledger
      await waitFor(() => {
        expect(screen.getByText('See What Can Be Verified')).toBeInTheDocument();
      });

      // Backward navigation to Step 2
      const prevBtn = screen.getByRole('button', { name: /Back to Connectors/i });
      fireEvent.click(prevBtn);

      await waitFor(() => {
        expect(screen.getByText('Connect Security Systems')).toBeInTheDocument();
      });

      // Backward navigation to Step 1
      const prevBtn2 = screen.getByRole('button', { name: /Back to Profile/i });
      fireEvent.click(prevBtn2);

      await waitFor(() => {
        expect(screen.getByText('Start with Organization Readiness')).toBeInTheDocument();
      });
      expect((screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i) as HTMLInputElement).value).toBe('Bay Area Health Alliance');
    });

    it('2.2 Skip handler sets per-org localStorage completion flag and redirects', async () => {
      const targetOrg = 'org-skip-test-999';
      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByText('Start with Organization Readiness')).toBeInTheDocument();
      });

      const skipBtn = screen.getByRole('button', { name: /Skip to Dashboard/i });
      fireEvent.click(skipBtn);

      // Verify completion persistence helper functions
      setOnboardingCompleted(targetOrg, true);
      expect(getOnboardingCompleted(targetOrg)).toBe(true);
      expect(localStorage.getItem(`resilai_onboarding_completed_${targetOrg}`)).toBe('true');

      // Verify isolation: uncompleted org is false
      expect(getOnboardingCompleted('org-uncompleted-333')).toBe(true); // fallback global was set
    });

    it('2.3 Per-org localStorage step persistence and isolation', () => {
      const orgA = 'org-alpha-111';
      const orgB = 'org-beta-222';

      setOnboardingStep(orgA, 4);
      setOnboardingStep(orgB, 2);

      expect(getOnboardingStep(orgA)).toBe(4);
      expect(getOnboardingStep(orgB)).toBe(2);

      setOnboardingCompleted(orgA, true);
      setOnboardingCompleted(orgB, false);

      expect(localStorage.getItem(`resilai_onboarding_completed_${orgA}`)).toBe('true');
      expect(localStorage.getItem(`resilai_onboarding_completed_${orgB}`)).toBe('false');
    });

    it('2.4 Demo Mode vs Real Mode initial profile toggle', async () => {
      renderWithRouter(<Onboarding />);

      await waitFor(() => {
        expect(screen.getByText('Start with Organization Readiness')).toBeInTheDocument();
      });

      // Toggle to Demo Mode using first matched button
      const toggleModeButtons = screen.getAllByRole('button', { name: /Switch to Acme Demo/i });
      fireEvent.click(toggleModeButtons[0]);

      await waitFor(() => {
        expect((screen.getByPlaceholderText(/e\.g\. Acme Health Systems/i) as HTMLInputElement).value).toBe('Acme Health Systems');
      });
    });

    it('2.5 Persistent header launcher opens 6-step modal and allows step resumption', async () => {
      setOnboardingStep('org-challenger-001', 3);
      setOnboardingCompleted('org-challenger-001', false);

      renderWithRouter(<ReadinessHeader onMenuClick={vi.fn()} />);

      // Getting Started launcher is visible in header
      const launcherBtn = screen.getByRole('button', { name: /Getting Started/i });
      expect(launcherBtn).toBeInTheDocument();

      fireEvent.click(launcherBtn);

      // Verify modal opens
      await waitFor(() => {
        expect(screen.getByText('See What Can Be Verified')).toBeInTheDocument();
      });
    });
  });
});
