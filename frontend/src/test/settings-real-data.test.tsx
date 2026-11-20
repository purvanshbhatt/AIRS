import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Settings from '../pages/Settings';
import * as api from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { readPreferences, DEFAULT_PREFERENCES } from '../lib/preferences';
import { renderWithRouter } from './utils/test-helpers';

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
const OTHER_ORG = 'org-live-002';
const LEGACY_KEYS = ['resilai_settings_api_keys', 'resilai_settings_webhooks', 'resilai_settings_auditor_links'];
const SEEDED_NAMES = [
  'M365 Telemetry Ingestion Agent',
  'Veeam WORM Backup Sentinel',
  'Executive Reporting Dashboard API',
  'Splunk SIEM Critical Readiness Drift Ingestion',
  'Security & Operations On-Call Alerts',
  'Coalfire SOC 2 Audit Team',
  'Travelers Cyber Underwriting Risk Assessment',
];
const SERVER_SECRET = 'airs_live_SERVER_ISSUED_SECRET_0123456789';
const AUDITOR_TOKEN = 'server-issued-auditor-token';
const AUDITOR_EXPIRES = '2099-01-31T10:00:00+00:00';

function activeOrg(overrides: Record<string, unknown> = {}) {
  return {
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
    ...overrides,
  } as any;
}

function serverKey(overrides: Record<string, unknown> = {}) {
  return {
    id: 'key-srv-1',
    org_id: ORG,
    prefix: 'airs_live_srvprefix01',
    scopes: ['scores:read'],
    is_active: true,
    created_at: '2026-10-01T09:00:00Z',
    last_used_at: null,
    ...overrides,
  };
}

function serverWebhook(overrides: Record<string, unknown> = {}) {
  return {
    id: 'wh-srv-1',
    org_id: ORG,
    url: 'https://hooks.clinic.test/resilai',
    event_types: ['assessment.scored'],
    is_active: true,
    created_at: '2026-10-02T09:00:00Z',
    ...overrides,
  };
}

/** What `request()` throws: an Error carrying the HTTP status and the server's words. */
function apiError(status: number, message: string, extra: Record<string, unknown> = {}) {
  return Object.assign(new Error(message), { status, ...extra });
}

function openTab(name: RegExp) {
  fireEvent.click(screen.getByRole('button', { name }));
}

function expectNoSeededRows() {
  for (const name of SEEDED_NAMES) {
    expect(screen.queryByText(name)).toBeNull();
  }
}

const settingsApiCalls = () => [
  api.listApiKeys,
  api.createApiKey,
  api.revokeApiKey,
  api.listWebhooks,
  api.createWebhook,
  api.deleteWebhook,
  api.testWebhook,
  api.listAuditorLinks,
  api.generateAuditorLink,
  api.revokeAuditorLink,
];

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  vi.mocked(useActiveOrg).mockReturnValue(activeOrg());
  vi.mocked(api.getApiBaseUrl).mockReturnValue('https://api.resilai.test');
  vi.mocked(api.checkHealth).mockResolvedValue({ status: 'ok' } as any);
  vi.mocked(api.getOrganizationProfile).mockResolvedValue({} as any);
  vi.mocked(api.getApplicableFrameworks).mockResolvedValue({ frameworks: [] } as any);
  vi.mocked(api.listApiKeys).mockResolvedValue([serverKey()] as any);
  vi.mocked(api.listWebhooks).mockResolvedValue([serverWebhook()] as any);
  vi.mocked(api.listAuditorLinks).mockResolvedValue({ org_id: ORG, active_links: [], count: 0 } as any);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Settings: a live workspace shows only what the server holds', () => {
  it('shows server API keys and never the seeded sample rows', async () => {
    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);

    expect(await screen.findByText('airs_live_srvprefix01')).toBeInTheDocument();
    expect(api.listApiKeys).toHaveBeenCalledWith(ORG);
    expect(screen.getByText('Not used yet')).toBeInTheDocument();
    expect(screen.queryByText(/Sample data/)).toBeNull();
    expectNoSeededRows();
  });

  it('does not load anything until the tab is opened', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => expect(api.checkHealth).toHaveBeenCalled());
    expect(api.listApiKeys).not.toHaveBeenCalled();
    expect(api.listWebhooks).not.toHaveBeenCalled();
    expect(api.listAuditorLinks).not.toHaveBeenCalled();
  });

  it('removes the old localStorage rows and never writes them again', async () => {
    localStorage.setItem(LEGACY_KEYS[0], JSON.stringify([{ id: 'x', name: 'Stale Local Key', prefix: 'stale', scope: 's', createdAt: '2026-01-01' }]));
    localStorage.setItem(LEGACY_KEYS[1], '[]');
    localStorage.setItem(LEGACY_KEYS[2], '[]');

    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');
    openTab(/Webhooks & Auditor Links/);
    await screen.findByText('https://hooks.clinic.test/resilai');

    expect(screen.queryByText('Stale Local Key')).toBeNull();
    for (const key of LEGACY_KEYS) {
      expect(localStorage.getItem(key)).toBeNull();
    }
  });

  it('says so honestly when the server has no API keys', async () => {
    vi.mocked(api.listApiKeys).mockResolvedValue([] as any);
    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);

    expect(await screen.findByText('No API keys yet.')).toBeInTheDocument();
    expectNoSeededRows();
  });

  it('creating a key calls createApiKey and shows the secret the server returned', async () => {
    const random = vi.spyOn(Math, 'random');
    vi.mocked(api.createApiKey).mockResolvedValue({
      id: 'key-srv-2',
      org_id: ORG,
      prefix: 'airs_live_SERVER_ISS',
      scopes: ['scores:read'],
      api_key: SERVER_SECRET,
      created_at: '2026-11-11T09:00:00Z',
    } as any);

    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');

    fireEvent.click(screen.getByRole('button', { name: /Generate New API Key/ }));
    expect(screen.queryByLabelText(/Key Name/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Generate Key' }));

    expect(await screen.findByText(SERVER_SECRET)).toBeInTheDocument();
    expect(api.createApiKey).toHaveBeenCalledWith(ORG, ['scores:read']);
    expect(random).not.toHaveBeenCalled();
    await waitFor(() => expect(api.listApiKeys).toHaveBeenCalledTimes(2));

    // Shown once: closing the dialog drops it.
    fireEvent.click(screen.getByRole('button', { name: 'Done / Close' }));
    expect(screen.queryByText(SERVER_SECRET)).toBeNull();
  });

  it('only offers scopes the server accepts', async () => {
    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');
    fireEvent.click(screen.getByRole('button', { name: /Generate New API Key/ }));

    const options = within(screen.getByLabelText('Authorization Scope')).getAllByRole('option').map((o) => (o as HTMLOptionElement).value);
    expect(options).toEqual([
      'scores:read',
      'scores:write',
      'findings:read',
      'findings:write',
      'reports:read',
      'webhooks:read',
      'webhooks:write',
    ]);
  });

  it('revoke calls revokeApiKey and reloads from the server', async () => {
    vi.mocked(api.revokeApiKey).mockResolvedValue(undefined as any);
    vi.mocked(api.listApiKeys)
      .mockResolvedValueOnce([serverKey()] as any)
      .mockResolvedValue([serverKey({ is_active: false })] as any);

    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');

    fireEvent.click(screen.getByRole('button', { name: 'Revoke Key' }));

    await waitFor(() => expect(api.revokeApiKey).toHaveBeenCalledWith('key-srv-1'));
    expect(await screen.findByText('Revoked')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Revoke Key' })).toBeNull();
    expect(api.listApiKeys).toHaveBeenCalledTimes(2);
  });

  it('shows the server 403 message when the list is refused', async () => {
    vi.mocked(api.listApiKeys).mockRejectedValue(apiError(403, 'Access denied: API keys need the Professional plan.'));

    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Your plan does not include API keys. Access denied: API keys need the Professional plan.');
    expect(screen.queryByText('No API keys yet.')).toBeNull();
    expectNoSeededRows();
  });

  it('shows the server plan refusal when creating a key is refused', async () => {
    vi.mocked(api.createApiKey).mockRejectedValue(
      apiError(402, 'An active ResilAI subscription is required to access this feature.', {
        code: 'PAYMENT_REQUIRED',
        detail: JSON.stringify({ required_entitlement: 'api_keys', current_plan: 'free' }),
      })
    );

    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');
    fireEvent.click(screen.getByRole('button', { name: /Generate New API Key/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Generate Key' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(
      'Your plan does not include API keys. An active ResilAI subscription is required to access this feature. Current plan: free.'
    );
    expect(screen.queryByText(/airs_live_SERVER/)).toBeNull();
  });

  it('webhooks: lists server rows, and test and delete call the server', async () => {
    vi.mocked(api.testWebhook).mockResolvedValue({ webhook_id: 'wh-srv-1', delivered: false, status_code: 500, error: 'HTTP 500 from endpoint' } as any);
    vi.mocked(api.deleteWebhook).mockResolvedValue(undefined as any);

    renderWithRouter(<Settings />);
    openTab(/Webhooks & Auditor Links/);

    expect(await screen.findByText('https://hooks.clinic.test/resilai')).toBeInTheDocument();
    expect(api.listWebhooks).toHaveBeenCalledWith(ORG);
    expect(await screen.findByText('No auditor links yet.')).toBeInTheDocument();
    expectNoSeededRows();

    fireEvent.click(screen.getByRole('button', { name: /Test Ping/ }));
    await waitFor(() => expect(api.testWebhook).toHaveBeenCalledWith('wh-srv-1'));
    expect(await screen.findByRole('alert')).toHaveTextContent('Test ping was not delivered. HTTP 500 from endpoint');

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(api.deleteWebhook).toHaveBeenCalledWith('wh-srv-1'));
    await waitFor(() => expect(api.listWebhooks).toHaveBeenCalledTimes(2));
  });

  it('webhooks: creating one sends the real event type to the server', async () => {
    vi.mocked(api.createWebhook).mockResolvedValue(serverWebhook({ id: 'wh-srv-2' }) as any);

    renderWithRouter(<Settings />);
    openTab(/Webhooks & Auditor Links/);
    await screen.findByText('https://hooks.clinic.test/resilai');

    fireEvent.click(screen.getByRole('button', { name: /Add Webhook Endpoint/ }));
    fireEvent.change(screen.getByLabelText('Destination URL'), { target: { value: 'https://siem.clinic.test/in' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Webhook' }));

    await waitFor(() =>
      expect(api.createWebhook).toHaveBeenCalledWith(ORG, {
        url: 'https://siem.clinic.test/in',
        event_types: ['assessment.scored'],
        secret: undefined,
      })
    );
    await waitFor(() => expect(api.listWebhooks).toHaveBeenCalledTimes(2));
  });

  it('auditor links: shows server fields, and offers Revoke only for a link created in this session', async () => {
    const earlier = { created_by: 'uid-someone-else', created_at: '2026-11-01T10:00:00+00:00', expires_at: '2098-12-01T10:00:00+00:00', access_count: 3 };
    const fresh = { created_by: 'uid-owner-1', created_at: '2026-11-11T10:00:00+00:00', expires_at: AUDITOR_EXPIRES, access_count: 0 };
    vi.mocked(api.listAuditorLinks)
      .mockResolvedValueOnce({ org_id: ORG, active_links: [earlier], count: 1 } as any)
      .mockResolvedValueOnce({ org_id: ORG, active_links: [earlier, fresh], count: 2 } as any)
      .mockResolvedValue({ org_id: ORG, active_links: [earlier], count: 1 } as any);
    vi.mocked(api.generateAuditorLink).mockResolvedValue({
      token: AUDITOR_TOKEN,
      org_id: ORG,
      org_name: 'Small Clinic',
      expires_at: AUDITOR_EXPIRES,
      ttl_hours: 336,
    } as any);
    vi.mocked(api.revokeAuditorLink).mockResolvedValue({ status: 'revoked' } as any);

    renderWithRouter(<Settings />);
    openTab(/Webhooks & Auditor Links/);

    // A link from an earlier session: real fields, no token, no revoke button.
    expect(await screen.findByText('Created by: uid-someone-else')).toBeInTheDocument();
    expect(screen.getByText('Opened: 3 times')).toBeInTheDocument();
    expect(screen.getByText(/cannot be revoked from here/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Revoke' })).toBeNull();
    expect(screen.queryByText(/auditor\?token=/)).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Create Auditor Access Link/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Generate Link' }));

    expect(await screen.findByText(`${window.location.origin}/auditor?token=${AUDITOR_TOKEN}`)).toBeInTheDocument();
    expect(api.generateAuditorLink).toHaveBeenCalledWith(ORG, 14 * 24);

    fireEvent.click(screen.getByRole('button', { name: 'Done / Close' }));
    expect(screen.queryByText(/auditor\?token=/)).toBeNull();
    expect(await screen.findByText('Created by: you')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Revoke' }));
    await waitFor(() => expect(api.revokeAuditorLink).toHaveBeenCalledWith(ORG, AUDITOR_TOKEN));
    await waitFor(() => expect(screen.queryByText('Created by: you')).toBeNull());
  });

  it('resets and reloads when the active organisation changes', async () => {
    vi.mocked(api.listApiKeys).mockImplementation(async (orgId: string) =>
      (orgId === ORG ? [serverKey()] : [serverKey({ id: 'key-srv-9', org_id: OTHER_ORG, prefix: 'airs_live_otherorg99' })]) as any
    );

    const view = renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);
    await screen.findByText('airs_live_srvprefix01');

    vi.mocked(useActiveOrg).mockReturnValue(activeOrg({ orgId: OTHER_ORG, orgName: 'Second Clinic' }));
    view.rerender(
      <MemoryRouter initialEntries={['/']}>
        <Settings />
      </MemoryRouter>
    );

    expect(await screen.findByText('airs_live_otherorg99')).toBeInTheDocument();
    expect(screen.queryByText('airs_live_srvprefix01')).toBeNull();
    expect(api.listApiKeys).toHaveBeenLastCalledWith(OTHER_ORG);
  });
});

describe('Settings: the demo sandbox shows labelled samples and touches nothing', () => {
  beforeEach(() => {
    vi.mocked(useActiveOrg).mockReturnValue(activeOrg({ orgId: 'demo-health-org', orgName: 'Acme Health Systems', isDemo: true }));
  });

  it('shows sample rows marked as sample and calls no API', async () => {
    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);

    expect(screen.getByText('M365 Telemetry Ingestion Agent')).toBeInTheDocument();
    expect(screen.getByRole('note')).toHaveTextContent('Sample data: nothing is created in the demo.');
    expect(screen.getAllByText('Sample')).toHaveLength(3);

    openTab(/Webhooks & Auditor Links/);
    expect(screen.getByText('Coalfire SOC 2 Audit Team')).toBeInTheDocument();
    expect(screen.getByRole('note')).toHaveTextContent('Sample data: nothing is created in the demo.');
    expect(screen.getAllByText('Sample')).toHaveLength(4);

    await waitFor(() => expect(api.checkHealth).toHaveBeenCalled());
    for (const call of settingsApiCalls()) {
      expect(call).not.toHaveBeenCalled();
    }
  });

  it('simulated create and revoke say they are samples, stay in memory and call no API', async () => {
    renderWithRouter(<Settings />);
    openTab(/API Keys & Ingest/);

    fireEvent.click(screen.getByRole('button', { name: /Generate New API Key/ }));
    fireEvent.change(screen.getByLabelText(/Key Name/), { target: { value: 'Sandbox Forwarder' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate Key' }));

    expect(await screen.findByText(/This sample key does not work/)).toBeInTheDocument();
    expect(addToast).toHaveBeenLastCalledWith(
      expect.objectContaining({ message: expect.stringContaining('Sample data: nothing is created in the demo.') })
    );
    fireEvent.click(screen.getByRole('button', { name: 'Done / Close' }));
    expect(screen.getByText('Sandbox Forwarder')).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: 'Revoke Key' })[0]);
    expect(screen.queryByText('Sandbox Forwarder')).toBeNull();
    expect(addToast).toHaveBeenLastCalledWith(
      expect.objectContaining({ message: expect.stringContaining('Sample data: nothing is created in the demo.') })
    );

    for (const key of LEGACY_KEYS) {
      expect(localStorage.getItem(key)).toBeNull();
    }
    for (const call of settingsApiCalls()) {
      expect(call).not.toHaveBeenCalled();
    }
  });
});

describe('Settings: Preferences tab', () => {
  it('persists every change through readPreferences()', async () => {
    renderWithRouter(<Settings />);
    openTab(/^Preferences$/);

    expect(screen.getByText(/Saved in this browser only\. They do not change your organisation's data or what your team sees\./)).toBeInTheDocument();
    expect(readPreferences()).toEqual(DEFAULT_PREFERENCES);

    fireEvent.click(within(screen.getByRole('radiogroup', { name: 'Start page' })).getByRole('radio', { name: /Network Map/ }));
    expect(readPreferences().startPage).toBe('/network');

    fireEvent.click(screen.getByRole('radio', { name: /^2D/ }));
    expect(readPreferences().mapView).toBe('2d');

    const refresh = screen.getByRole('switch', { name: 'Refresh from connected systems every 45 seconds' });
    expect(refresh).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(refresh);
    expect(refresh).toHaveAttribute('aria-checked', 'false');
    expect(readPreferences().mapLiveRefresh).toBe(false);

    const motion = screen.getByRole('switch', { name: 'Reduce motion' });
    expect(motion).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(motion);
    expect(motion).toHaveAttribute('aria-checked', 'true');
    expect(readPreferences().reduceMotion).toBe(true);
    expect(document.documentElement.getAttribute('data-reduce-motion')).toBe('true');
  });

  it('Reset preferences puts the defaults back', async () => {
    renderWithRouter(<Settings />);
    openTab(/^Preferences$/);

    fireEvent.click(screen.getByRole('radio', { name: /Reports/ }));
    fireEvent.click(screen.getByRole('switch', { name: 'Reduce motion' }));
    expect(readPreferences().startPage).toBe('/reports');

    fireEvent.click(screen.getByRole('button', { name: 'Reset preferences' }));

    expect(readPreferences()).toEqual(DEFAULT_PREFERENCES);
    await waitFor(() => expect(screen.getByRole('switch', { name: 'Reduce motion' })).toHaveAttribute('aria-checked', 'false'));
    expect(screen.getByRole('radio', { name: /Today/ })).toBeChecked();
    expect(document.documentElement.hasAttribute('data-reduce-motion')).toBe(false);
  });
});
