import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import Settings from '../pages/Settings';
import * as api from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { renderWithRouter } from './utils/test-helpers';

/**
 * Settings > Regulatory Scope: the owner picks where the organisation operates,
 * and the list of laws is whatever the server returns for that profile. The
 * page never invents a framework, and a data toggle never changes the regions.
 */

const { addToast } = vi.hoisted(() => ({ addToast: vi.fn() }));

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { uid: 'uid-owner-1', email: 'owner@clinic.test' }, signOut: vi.fn() }),
}));
vi.mock('../components/ui/Toast', () => ({
  useToast: () => ({ toasts: [], addToast, removeToast: vi.fn() }),
}));

const ORG = 'org-live-001';

const EU_AI_ACT = {
  framework: 'EU AI Act (Regulation (EU) 2024/1689)',
  reason: 'Organisation uses AI and operates in the EU.',
  mandatory: true,
  reference_url: 'https://eur-lex.europa.eu/eli/reg/2024/1689/oj',
  jurisdiction: 'European Union',
  evidence_note: 'It does not classify your AI systems.',
};

function profile(overrides: Record<string, unknown> = {}) {
  return {
    org_id: ORG,
    geo_regions: ['US'],
    processes_pii: false,
    processes_phi: false,
    processes_cardholder_data: false,
    handles_dod_data: false,
    uses_ai_in_production: true,
    government_contractor: false,
    financial_services: false,
    ...overrides,
  } as any;
}

async function openRegulatoryScope() {
  renderWithRouter(<Settings />);
  fireEvent.click(screen.getByRole('button', { name: /Regulatory Scope/ }));
  return waitFor(() => screen.getByTestId('region-picker'));
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.mocked(useActiveOrg).mockReturnValue({
    orgId: ORG,
    orgName: 'Small Clinic',
    org: null,
    orgs: [],
    isDemo: false,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
  } as any);
  vi.mocked(api.getApiBaseUrl).mockReturnValue('https://api.resilai.test');
  vi.mocked(api.checkHealth).mockResolvedValue({ status: 'ok' } as any);
  vi.mocked(api.getOrganizationProfile).mockResolvedValue(profile());
  vi.mocked(api.getApplicableFrameworks).mockResolvedValue({ frameworks: [] } as any);
  vi.mocked(api.listApiKeys).mockResolvedValue([] as any);
  vi.mocked(api.listWebhooks).mockResolvedValue([] as any);
  vi.mocked(api.listAuditorLinks).mockResolvedValue({ org_id: ORG, active_links: [], count: 0 } as any);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Settings: regions and regional frameworks', () => {
  it('shows the saved regions as selected and offers the EU and every Gulf state', async () => {
    const picker = await openRegulatoryScope();

    await waitFor(() => {
      expect(within(picker).getByRole('button', { name: 'United States' })).toHaveAttribute('aria-pressed', 'true');
    });
    for (const label of ['European Union', 'United Kingdom', 'UAE', 'Saudi Arabia', 'Qatar', 'Bahrain', 'Kuwait', 'Oman']) {
      expect(within(picker).getByRole('button', { name: label })).toHaveAttribute('aria-pressed', 'false');
    }
  });

  it('saves a picked region and lists what the server returns, with its scope note', async () => {
    vi.mocked(api.updateOrganizationProfile).mockResolvedValue(profile({ geo_regions: ['US', 'EU'] }));
    const picker = await openRegulatoryScope();
    await waitFor(() => expect(within(picker).getByRole('button', { name: 'European Union' })).not.toBeDisabled());
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue({ frameworks: [EU_AI_ACT] } as any);

    fireEvent.click(within(picker).getByRole('button', { name: 'European Union' }));

    await waitFor(() => {
      expect(api.updateOrganizationProfile).toHaveBeenCalledWith(ORG, { geo_regions: ['US', 'EU'] });
    });
    await waitFor(() => {
      expect(screen.getByText('EU AI Act (Regulation (EU) 2024/1689)')).toBeInTheDocument();
    });
    expect(screen.getByTestId('framework-evidence-note')).toHaveTextContent('does not classify');
    expect(screen.getByText('European Union', { selector: 'p' })).toBeInTheDocument();
    expect(within(picker).getByRole('button', { name: 'European Union' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('removes a region that is already picked', async () => {
    vi.mocked(api.getOrganizationProfile).mockResolvedValue(profile({ geo_regions: ['US', 'SA'] }));
    vi.mocked(api.updateOrganizationProfile).mockResolvedValue(profile({ geo_regions: ['US'] }));
    const picker = await openRegulatoryScope();
    await waitFor(() => {
      expect(within(picker).getByRole('button', { name: 'Saudi Arabia' })).toHaveAttribute('aria-pressed', 'true');
    });

    fireEvent.click(within(picker).getByRole('button', { name: 'Saudi Arabia' }));

    await waitFor(() => {
      expect(api.updateOrganizationProfile).toHaveBeenCalledWith(ORG, { geo_regions: ['US'] });
    });
  });

  it('keeps the old selection and says so when the save fails', async () => {
    vi.mocked(api.updateOrganizationProfile).mockRejectedValue(new Error('offline'));
    const picker = await openRegulatoryScope();
    await waitFor(() => expect(within(picker).getByRole('button', { name: 'UAE' })).not.toBeDisabled());

    fireEvent.click(within(picker).getByRole('button', { name: 'UAE' }));

    await waitFor(() => {
      expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ type: 'error' }));
    });
    expect(within(picker).getByRole('button', { name: 'UAE' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('does not show a framework the server did not return', async () => {
    await openRegulatoryScope();

    expect(screen.queryByText(/EU AI Act \(Regulation/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('framework-evidence-note')).not.toBeInTheDocument();
  });
});
