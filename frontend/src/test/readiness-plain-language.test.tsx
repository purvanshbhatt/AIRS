import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import React from 'react';
import TodayPage from '../features/readiness/TodayPage';
import NeedsAttentionPage from '../features/readiness/NeedsAttentionPage';
import RecoveryReadinessPage from '../features/readiness/RecoveryReadinessPage';
import { derivePlainVerdict, deriveCheckGuidance } from '../components/readiness/PlainLanguage';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import * as useAuthHook from '../contexts/AuthContext';
import { createMockDailyReadinessReport, renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');
vi.mock('../contexts/AuthContext');

function mockOrg(overrides: Partial<ReturnType<typeof useActiveOrgHook.useActiveOrg>> = {}) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: 'org-plain-001',
    orgName: 'Riverside Family Practice',
    org: { id: 'org-plain-001', name: 'Riverside Family Practice' } as any,
    orgs: [{ id: 'org-plain-001', name: 'Riverside Family Practice' } as any],
    isDemo: false,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  } as any);
}

describe('Readiness pages: plain-English verdict for non-technical readers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOrg();
    vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
      user: { uid: 'user-pm', email: 'manager@riverside.example', displayName: 'Practice Manager', photoURL: null },
      loading: false,
      error: null,
      isConfigured: true,
      hasOrganizations: true,
      getToken: vi.fn().mockResolvedValue('token'),
      signInWithGoogle: vi.fn(),
      signInWithEmail: vi.fn(),
      signUpWithEmail: vi.fn(),
      signInAsDemo: vi.fn(),
      signOut: vi.fn(),
      clearError: vi.fn(),
      refreshAuth: vi.fn(),
    } as any);
  });

  it('renders a critical verdict first on the morning brief for a critical_risk report', async () => {
    const report = createMockDailyReadinessReport({
      status: 'critical_risk',
      clinic_health_pct: 41,
      failed_checks: [
        { id: 'chk-a', name: 'Immutable Backups', category: 'Backups' },
        { id: 'chk-b', name: 'MFA Enforcement', category: 'Identity' },
      ],
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByTestId('plain-verdict')).toBeInTheDocument();
    });
    expect(screen.getByTestId('plain-verdict')).toHaveTextContent(
      'Your practice is not protected right now. 2 things need fixing today.'
    );
    expect(screen.getByTestId('plain-today')).toHaveTextContent(/call your IT provider before opening/i);
    expect(screen.getByTestId('plain-today')).toHaveTextContent(/backups come first/i);
    // Existing status label is still a heading
    expect(screen.getByRole('heading', { name: 'ACTION REQUIRED' })).toBeInTheDocument();
  });

  it('renders a reassuring verdict first on the morning brief for a healthy report', async () => {
    const report = createMockDailyReadinessReport({
      status: 'safe_to_open',
      clinic_health_pct: 96,
      failed_checks: [],
      immediate_actions: [],
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByTestId('plain-verdict')).toHaveTextContent(
        'You can keep operating if something goes wrong tonight.'
      );
    });
    expect(screen.getByTestId('plain-today')).toHaveTextContent(/nothing needs your time/i);
    expect(screen.getByText('READY FOR TODAY')).toBeInTheDocument();
    expect(screen.getByText('96')).toBeInTheDocument();
  });

  it('keeps technical details collapsed by default for a real org and shows connector table when opened', async () => {
    const report = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByTestId('technical-details')).toBeInTheDocument();
    });
    expect(screen.queryByText('Veeam Backup API')).not.toBeInTheDocument();

    const toggle = screen.getByRole('button', { name: /Technical details/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    toggle.click();
    await waitFor(() => {
      expect(screen.getByText('Veeam Backup API')).toBeInTheDocument();
    });
  });

  it('shows who should fix each failed item and how long it usually takes', async () => {
    const report = createMockDailyReadinessReport();
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<NeedsAttentionPage />);

    await waitFor(() => {
      expect(screen.getByTestId('plain-verdict')).toBeInTheDocument();
    });
    const strip = screen.getByTestId('check-owner-strip');
    expect(strip).toHaveTextContent('Who should fix it');
    expect(strip).toHaveTextContent('IT / MSP');
    expect(strip).toHaveTextContent('How long it usually takes');
  });

  it('tells a real org with no connected systems what to connect first and links to /connectors', async () => {
    const report = createMockDailyReadinessReport({
      status: 'unknown',
      clinic_health_pct: 0,
      connectors: [],
      immediate_actions: [],
      failed_checks: [],
      business_continuity: undefined as any,
      verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 0 } as any,
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<NeedsAttentionPage />);

    await waitFor(() => {
      expect(screen.getByTestId('connect-first-empty-state')).toBeInTheDocument();
    });
    expect(screen.getByText(/no systems are connected/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');

    renderWithRouter(<RecoveryReadinessPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId('connect-first-empty-state').length).toBeGreaterThanOrEqual(2);
    });
  });

  it('derives verdicts deterministically without inventing numbers', () => {
    const healthy = derivePlainVerdict(createMockDailyReadinessReport({ status: 'safe_to_open', failed_checks: [], immediate_actions: [] }));
    expect(healthy.tone).toBe('ready');

    const warning = derivePlainVerdict(createMockDailyReadinessReport({ status: 'action_required', clinic_health_pct: 78 }));
    expect(warning.tone).toBe('warning');
    expect(warning.verdict).toBe('1 thing needs attention before you are fully protected.');

    const guidance = deriveCheckGuidance({ title: 'MFA Enforcement', category: 'Identity', severity: 'high' });
    expect(guidance.whoFixes).toBe('IT / MSP');
    expect(guidance.whyItMatters).toMatch(/second login step \(MFA\)/i);
    expect(guidance.howLong).not.toMatch(/\d/);
  });
});
