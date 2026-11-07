import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import TodayPageV2 from '../features/readiness/TodayPageV2';
import { MorningBriefRoute, shouldUseMorningBriefV2 } from '../App';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import * as useAuthHook from '../contexts/AuthContext';
import { createMockDailyReadinessReport, renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');
vi.mock('../contexts/AuthContext');

const FLAG = 'resilai_dashboard_v2';

function mockOrg(overrides: Partial<ReturnType<typeof useActiveOrgHook.useActiveOrg>> = {}) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: 'org-v2-001',
    orgName: 'Riverside Family Practice',
    org: { id: 'org-v2-001', name: 'Riverside Family Practice' } as any,
    orgs: [{ id: 'org-v2-001', name: 'Riverside Family Practice' } as any],
    isDemo: false,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  } as any);
}

describe('Morning brief V2 (staging preview)', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
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

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
  });

  it('defaults to the classic view under test and switches to V2 when the localStorage flag is "true"', async () => {
    // Under vitest VITE_APP_ENV is "staging" (from .env) but MODE is "test": classic by default.
    expect(shouldUseMorningBriefV2()).toBe(false);

    localStorage.setItem(FLAG, 'true');
    expect(shouldUseMorningBriefV2()).toBe(true);

    localStorage.setItem(FLAG, 'false');
    expect(shouldUseMorningBriefV2()).toBe(false);

    // The route component honours the flag end to end.
    localStorage.setItem(FLAG, 'true');
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(createMockDailyReadinessReport());
    renderWithRouter(
      <Routes>
        <Route path="/morning-brief" element={<MorningBriefRoute />} />
      </Routes>,
      { initialEntries: ['/morning-brief'] }
    );
    await waitFor(() => {
      expect(screen.getByTestId('today-v2')).toBeInTheDocument();
    });
    expect(screen.getByTestId('brief-org-name')).toHaveTextContent('Riverside Family Practice');
    expect(screen.getByRole('link', { name: /Export 1-page report/i })).toHaveAttribute('href', '/reports');
    expect(screen.getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');
  });

  it('renders the plain verdict and three status chips for a critical_risk report', async () => {
    const report = createMockDailyReadinessReport({
      status: 'critical_risk',
      clinic_health_pct: 41,
      failed_checks: [
        { id: 'chk-a', name: 'Immutable Backups', category: 'Backups' },
        { id: 'chk-b', name: 'MFA Enforcement', category: 'Identity' },
      ],
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<TodayPageV2 />);

    await waitFor(() => {
      expect(screen.getByTestId('plain-verdict')).toBeInTheDocument();
    });
    expect(screen.getByTestId('plain-verdict')).toHaveTextContent(
      'Your practice is not protected right now. 2 things need fixing today.'
    );
    expect(screen.getByTestId('plain-today')).toHaveTextContent(/call your IT provider before opening/i);
    expect(screen.getByTestId('readiness-score')).toHaveTextContent('41');

    const chips = screen.getAllByTestId('status-chip');
    expect(chips).toHaveLength(3);
    expect(screen.getByTestId('status-area-backups')).toHaveTextContent('NEEDS ATTENTION');
    expect(screen.getByTestId('status-area-logins')).toHaveTextContent('NEEDS ATTENTION');
    // Endpoint Protection passed in the mock report, so Devices is verified.
    expect(screen.getByTestId('status-area-devices')).toHaveTextContent('VERIFIED');

    // Attention card carries the four plain-language fields and an action.
    const card = screen.getAllByTestId('attention-card')[0];
    expect(card).toHaveTextContent('What happened');
    expect(card).toHaveTextContent('Why it matters');
    expect(card).toHaveTextContent('Who fixes it');
    expect(card).toHaveTextContent('How long');
    expect(screen.getByRole('button', { name: /Fix now/i })).toBeInTheDocument();
    expect(screen.getByTestId('overnight-strip')).toBeInTheDocument();
    expect(screen.getByTestId('technical-details')).toBeInTheDocument();
  });

  it('shows the connect-first empty state for a real org with no connectors', async () => {
    const report = createMockDailyReadinessReport({
      status: 'unknown',
      clinic_health_pct: 0,
      connectors: [],
      immediate_actions: [],
      failed_checks: [],
      passed_checks: [],
      warnings: [],
      business_continuity: undefined as any,
      verification: { overall_confidence_pct: 0, verified_items_count: 0, total_items_count: 0 } as any,
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(report);

    renderWithRouter(<TodayPageV2 />);

    await waitFor(() => {
      expect(screen.getByTestId('connect-first-empty-state')).toBeInTheDocument();
    });
    expect(screen.getByTestId('plain-verdict')).toHaveTextContent(/cannot tell yet/i);
    expect(screen.queryByTestId('readiness-ring')).not.toBeInTheDocument();
    expect(screen.queryByTestId('status-chip')).not.toBeInTheDocument();
    // Header action plus the empty-state call to action both point at /connectors.
    const connectLinks = screen.getAllByRole('link', { name: /Connect a system/i });
    expect(connectLinks.length).toBeGreaterThanOrEqual(2);
    connectLinks.forEach(link => expect(link).toHaveAttribute('href', '/connectors'));
  });

  it('"Switch to classic view" writes the opt-out flag and reloads', async () => {
    localStorage.setItem(FLAG, 'true');
    const reload = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload, search: '', hostname: 'localhost' },
    });
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(createMockDailyReadinessReport());

    renderWithRouter(<TodayPageV2 />);

    await waitFor(() => {
      expect(screen.getByTestId('switch-to-classic')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId('switch-to-classic'));

    expect(localStorage.getItem(FLAG)).toBe('false');
    expect(reload).toHaveBeenCalledTimes(1);
    expect(shouldUseMorningBriefV2()).toBe(false);
  });
});
