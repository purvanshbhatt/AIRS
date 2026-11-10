import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import React from 'react';
import TechnologyIntelligence from '../pages/TechnologyIntelligence';
import { AdvisoryAlert } from '../components/techintel/AdvisoryAlert';
import { deriveCoverage, deriveFixActions, feedsAsOf, normalizeWebUrl, sortStackItems } from '../components/techintel/shared';
import * as api from '../api';
import type {
  StackItem,
  StackResponse,
  TechAdvisoriesResponse,
  TechAdvisory,
  TechDeploymentsResponse,
  TechTopAction,
  WebAssetScanResult,
} from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');

const ORG = 'org-clinic-001';

function mockOrg(overrides: Partial<ReturnType<typeof useActiveOrgHook.useActiveOrg>> = {}) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: ORG,
    orgName: 'Riverside Family Practice',
    org: { id: ORG, name: 'Riverside Family Practice' } as any,
    orgs: [{ id: ORG, name: 'Riverside Family Practice' } as any],
    isDemo: false,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  } as any);
}

const item = (overrides: Partial<StackItem>): StackItem => ({
  id: 'item-x',
  name: 'Example',
  vendor: 'Example Corp',
  version: '1.0.0',
  category: 'application',
  source: 'aws',
  asset: null,
  last_seen: '2026-11-08T08:00:00Z',
  eol: null,
  vulnerabilities: [],
  status: 'ok',
  ...overrides,
});

const STACK: StackResponse = {
  items: [
    item({ id: 'item-redis', name: 'Redis', vendor: 'Redis Ltd', version: '7.2.4', category: 'database', asset: 'cache-01', status: 'ok' }),
    item({
      id: 'item-nginx',
      name: 'nginx',
      vendor: 'F5',
      version: '1.18.0',
      category: 'web_server',
      asset: 'web-01',
      status: 'vulnerable',
      confidence: 'confirmed',
      eol: { is_eol: true, eol_date: '2021-04-20', latest_version: '1.26.2', source: 'endoflife.date' },
      vulnerabilities: [
        {
          id: 'CVE-2021-23017',
          severity: 'high',
          cvss: 7.7,
          summary: 'A crafted DNS answer can crash or take over the web server.',
          fixed_version: '1.20.1',
          published: '2021-06-01',
          known_exploited: true,
          references: ['https://nvd.nist.gov/vuln/detail/CVE-2021-23017', 'javascript:alert(1)'],
          remediation: 'Restart the service after upgrading.',
        },
      ],
    }),
    item({
      id: 'item-pg',
      name: 'PostgreSQL',
      vendor: 'PostgreSQL Global Development Group',
      version: '13.2',
      category: 'database',
      asset: 'db-01',
      status: 'vulnerable',
      vulnerabilities: [
        {
          id: 'CVE-2024-10979',
          severity: 'critical',
          cvss: 9.1,
          summary: 'A database user can run commands on the server.',
          fixed_version: '13.17',
          published: '2024-11-14',
          known_exploited: false,
          references: [],
          remediation: '',
        },
      ],
    }),
    item({ id: 'item-node', name: 'Node.js', vendor: 'OpenJS', version: '18.19.0', category: 'runtime', asset: 'api-01', status: 'vulnerable',
      vulnerabilities: [
        { id: 'CVE-2024-22019', severity: 'medium', cvss: 5.3, summary: 'A slow request can exhaust the server.', fixed_version: '18.19.1', published: null, known_exploited: false, references: [], remediation: '' },
      ],
    }),
  ],
  summary: { total: 4, vulnerable: 3, critical: 1, known_exploited: 1, end_of_life: 1, last_intel_refresh: '2026-11-09T06:00:00Z' },
  sources: { aws: 'connected', web_scan: 'not_connected' },
  demo: false,
};

const advisory = (overrides: Partial<TechAdvisory>): TechAdvisory => ({
  id: 'CVE-0000-0000',
  severity: 'medium',
  cvss: 5,
  summary: 'Example advisory.',
  published: '2026-10-01',
  known_exploited: false,
  affected: [],
  fixed_version: null,
  steps: [],
  references: [],
  ...overrides,
});

const ADVISORIES: TechAdvisoriesResponse = {
  advisories: [
    advisory({
      id: 'CVE-2021-23017',
      severity: 'high',
      cvss: 7.7,
      summary: 'Your web server can be taken over by a crafted network reply.',
      known_exploited: true,
      confidence: 'confirmed',
      affected: [{ name: 'nginx', version: '1.18.0', asset: 'web-01' }],
      fixed_version: '1.20.1',
      steps: ['Back up the nginx configuration.', 'Upgrade nginx to 1.20.1 or newer.', 'Restart nginx and confirm the site loads.'],
      references: ['https://nginx.org/en/security_advisories.html'],
    }),
    advisory({
      id: 'CVE-2024-22019',
      severity: 'medium',
      summary: 'A slow request can make the booking app stop answering.',
      affected: [{ name: 'Node.js', version: '18.19.0', asset: 'api-01' }],
      fixed_version: '18.19.1',
      steps: ['Upgrade Node.js to 18.19.1.'],
    }),
  ],
  generated_at: '2026-11-09T06:00:00Z',
};

const EMPTY_DEPLOYMENTS: TechDeploymentsResponse = { deployments: [], sources: { aws: 'not_connected' }, collected_at: null };

const SCAN: WebAssetScanResult = {
  url: 'https://portal.example.com/',
  reachable: true,
  status_code: 200,
  final_url: 'https://portal.example.com/',
  tls: { valid: true, expires_at: '2026-11-19T00:00:00Z', days_left: 10, issuer: "Let's Encrypt" },
  headers: { hsts: true, csp: false, x_frame_options: true, x_content_type_options: true, referrer_policy: false },
  detected: [{ name: 'WordPress', version: '6.2', evidence: 'meta generator' }],
  issues: [{ title: 'Certificate expires soon', severity: 'high', fix: 'Renew the certificate with your hosting provider.' }],
  scanned_at: '2026-11-09T07:00:00Z',
};

function mockApi(overrides: {
  stack?: StackResponse;
  advisories?: TechAdvisoriesResponse;
  deployments?: TechDeploymentsResponse;
  assets?: any[];
} = {}) {
  vi.mocked(api.getSoftwareStack).mockResolvedValue(overrides.stack ?? STACK);
  vi.mocked(api.getTechAdvisories).mockResolvedValue(overrides.advisories ?? ADVISORIES);
  vi.mocked(api.getWebAssets).mockResolvedValue({ assets: overrides.assets ?? [] });
  vi.mocked(api.getTechDeployments).mockResolvedValue(overrides.deployments ?? EMPTY_DEPLOYMENTS);
}

async function renderPage() {
  const view = renderWithRouter(<TechnologyIntelligence />, { initialEntries: ['/technology/intelligence'] });
  await screen.findByTestId('technology-intelligence');
  return view;
}

/** The full inventory lives in the collapsed "Everything we checked" section. */
function openEverything(tab?: 'software' | 'advisories' | 'websites' | 'cloud') {
  if (screen.getByTestId('everything-toggle').getAttribute('aria-expanded') !== 'true') {
    fireEvent.click(screen.getByTestId('everything-toggle'));
  }
  if (tab) fireEvent.click(screen.getByTestId(`tab-${tab}`));
}

const topAction = (n: number, overrides: Partial<TechTopAction> = {}): TechTopAction => ({
  id: `CVE-2026-100${n}`,
  title: `Update program ${n} on the front desk computers`,
  confidence: 'confirmed',
  where: [`desk-${n}a`, `desk-${n}b`],
  count: 2,
  fix: `Install the newest version of program ${n}.`,
  send_to_it_text: `Please update program ${n} this week.`,
  source_url: `https://vendor.example.com/advisories/${n}`,
  known_exploited: n === 1,
  ...overrides,
});

describe('Software Watch (/technology/intelligence)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOrg();
    mockApi();
  });

  describe('fix this week', () => {
    it('leads with a short action list in plain English, not a list of CVEs or totals', async () => {
      await renderPage();
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Software Watch');

      // No top_actions from the backend: derived from the exploited advisory and the unsupported program.
      const cards = screen.getAllByTestId('fix-card');
      expect(cards).toHaveLength(2);
      expect(within(cards[0]).getByTestId('fix-card-title')).toHaveTextContent(
        'Your web server can be taken over by a crafted network reply.'
      );
      expect(within(cards[0]).getByTestId('fix-card-where')).toHaveTextContent('Found in 1 place: web-01');
      expect(within(cards[0]).getByTestId('fix-card-step')).toHaveTextContent('Fix: Upgrade nginx to version 1.20.1 or newer.');
      expect(within(cards[0]).getByTestId('fix-card-reference')).toHaveTextContent('CVE-2021-23017');
      expect(within(cards[0]).getByTestId('fix-card-source')).toHaveAttribute('href', 'https://nginx.org/en/security_advisories.html');
      expect(within(cards[1]).getByTestId('fix-card-title')).toHaveTextContent('nginx 1.18.0 no longer gets security fixes from its maker');

      screen.getAllByTestId('fix-card-title').forEach(t => expect(t.textContent).not.toMatch(/CVE-\d/));
      // The inventory, severity tiers and counts stay out of the main view.
      expect(screen.getByTestId('everything-toggle')).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByTestId('stack-row')).not.toBeInTheDocument();
      expect(screen.queryByTestId('advisory-card')).not.toBeInTheDocument();
      expect(screen.queryByTestId('count-total')).not.toBeInTheDocument();
      expect(api.getSoftwareStack).toHaveBeenCalledWith(ORG);
    });

    it('reads the backend top_actions, coverage and feed shapes as sent', async () => {
      const actions = deriveFixActions({
        topActions: [
          {
            id: 'EOL-windows-10-22h2',
            kind: 'end_of_life',
            title: 'Replace or upgrade Windows 10 22H2 on 2 computers',
            where: { count: 2, label: '2 computers', names: ['FRONT-DESK-01', 'BILLING-02'] },
            fix: 'Upgrade to Windows 11.',
            send_to_it_text: 'Please upgrade two PCs.',
            source_url: 'https://endoflife.date/windows',
            confidence: 'confirmed',
          },
          { id: 'no-confidence', title: 'Backend did not classify this', where: { count: 1, names: ['x'] } },
        ],
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].names).toEqual(['FRONT-DESK-01', 'BILLING-02']);
      expect(actions[0].count).toBe(2);
      expect(actions[0].endOfLife).toBe(true);
      expect(actions[0].sendText).toBe('Please upgrade two PCs.');

      const view = deriveCoverage({
        sources_seen: ['AWS Systems Manager'],
        not_seen: ['Website not added'],
        products_total: 3,
        products_checked: 2,
        products_not_checked: 1,
        level: 'partial',
        message: '',
      });
      expect(view).toEqual({ checked: ['AWS Systems Manager'], unseen: ['Website not added'] });

      expect(
        feedsAsOf({
          osv: { status: 'ok', as_of: '2026-11-09T06:00:00Z' },
          cisa_kev: { status: 'stale', as_of: '2026-11-07T06:00:00Z' },
          nvd: { status: 'not_used', as_of: '2026-01-01T00:00:00Z' },
        })
      ).toBe('2026-11-07T06:00:00Z');
    });

    it('never shows more than 5 cards and leaves out anything that is not confirmed', async () => {
      const actions = [
        topAction(0, { confidence: 'unconfirmed', title: 'A possible match nobody verified' }),
        ...[1, 2, 3, 4, 5, 6, 7].map(n => topAction(n)),
      ];
      mockApi({ advisories: { ...ADVISORIES, top_actions: actions } });
      await renderPage();

      const cards = screen.getAllByTestId('fix-card');
      expect(cards).toHaveLength(5);
      expect(cards[0]).toHaveTextContent('Update program 1 on the front desk computers');
      expect(cards[4]).toHaveTextContent('Update program 5 on the front desk computers');
      expect(screen.queryByText('A possible match nobody verified')).not.toBeInTheDocument();
      expect(within(cards[0]).getByTestId('fix-card-where')).toHaveTextContent('Found in 2 places: desk-1a, desk-1b');

      expect(deriveFixActions({ topActions: actions })).toHaveLength(5);
      expect(deriveFixActions({ topActions: [topAction(0, { confidence: 'possible' })] })).toHaveLength(0);
    });

    it('keeps CVE numbers out of the headline and shows them as small secondary text', async () => {
      mockApi({
        advisories: {
          ...ADVISORIES,
          top_actions: [topAction(1, { id: 'CVE-2021-23017', title: 'CVE-2021-23017: your web server can be taken over' })],
        },
      });
      await renderPage();
      expect(screen.getByTestId('fix-card-title')).toHaveTextContent(/^your web server can be taken over$/);
      expect(screen.getByTestId('fix-card-reference')).toHaveTextContent('CVE-2021-23017');
    });

    it('copies the message for the IT person, using send_to_it_text or a generated sentence', async () => {
      vi.mocked(navigator.clipboard.writeText).mockResolvedValue(undefined);
      mockApi({
        advisories: {
          ...ADVISORIES,
          top_actions: [topAction(1), topAction(2, { send_to_it_text: undefined })],
        },
      });
      await renderPage();
      const buttons = screen.getAllByTestId('copy-for-it');
      expect(buttons[0]).toHaveTextContent('Copy message for my IT person');

      fireEvent.click(buttons[0]);
      await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Please update program 1 this week.'));
      await waitFor(() => expect(buttons[0]).toHaveTextContent(/Copied/));

      fireEvent.click(buttons[1]);
      await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(2));
      const generated = vi.mocked(navigator.clipboard.writeText).mock.calls[1][0];
      expect(generated).toContain('Update program 2 on the front desk computers');
      expect(generated).toContain('desk-2a, desk-2b');
      expect(generated).toContain('Install the newest version of program 2.');
      expect(generated).toContain('https://vendor.example.com/advisories/2');
    });

    it('always shows what was checked and what could not be seen', async () => {
      mockApi({
        stack: { ...STACK, coverage: { checked: ['AWS account', 'Website scan'], could_not_see: ['Staff laptops', 'Office printers'] } },
      });
      await renderPage();
      expect(screen.getByTestId('coverage-checked')).toHaveTextContent('We checked: AWS account, Website scan.');
      expect(screen.getByTestId('coverage-unseen')).toHaveTextContent('We could not see: Staff laptops, Office printers.');
    });

    it('builds the coverage line from the source status map when the backend sends no coverage block', async () => {
      await renderPage();
      expect(screen.getByTestId('coverage-checked')).toHaveTextContent('We checked: servers in AWS.');
      expect(screen.getByTestId('coverage-unseen')).toHaveTextContent('We could not see: your website.');
      expect(deriveCoverage(null, {})).toEqual({ checked: [], unseen: [] });
    });

    it('says so, and links to Integrations, when no inventory source is connected (never an all-clear)', async () => {
      mockApi({
        stack: { items: [], summary: { ...STACK.summary, total: 0, vulnerable: 0, critical: 0, known_exploited: 0, end_of_life: 0, last_intel_refresh: null }, sources: { aws: 'not_connected' }, demo: false },
        advisories: { advisories: [], generated_at: null },
      });
      await renderPage();

      const empty = screen.getByTestId('no-source-empty');
      expect(empty).toHaveTextContent('We cannot see your software yet');
      expect(empty).toHaveTextContent('This is not an all-clear.');
      expect(within(empty).getByRole('link', { name: /Integrations/i })).toHaveAttribute('href', '/connectors');
      expect(screen.queryByTestId('fix-this-week-clear')).not.toBeInTheDocument();
      expect(screen.queryByTestId('fix-card')).not.toBeInTheDocument();
      expect(screen.getByTestId('coverage-checked')).toHaveTextContent('We checked: nothing yet.');
      expect(screen.getByTestId('coverage-unseen')).toHaveTextContent('We could not see: servers in AWS.');
      expect(screen.getByTestId('last-checked')).toHaveTextContent('Not checked yet');
    });

    it('says nothing confirmed needs fixing only when a source was actually checked', async () => {
      mockApi({
        stack: { ...STACK, items: [STACK.items[0]] },
        advisories: { advisories: [advisory({ id: 'CVE-2025-0001', known_exploited: true, confidence: 'unconfirmed' })], generated_at: null },
      });
      await renderPage();
      expect(screen.getByTestId('fix-this-week-clear')).toBeInTheDocument();
      expect(screen.queryByTestId('no-source-empty')).not.toBeInTheDocument();
      expect(screen.queryByTestId('fix-card')).not.toBeInTheDocument();
    });

    it('shows "Last checked" from as_of and a quiet amber note when the feed is stale', async () => {
      mockApi({ stack: { ...STACK, as_of: '2026-11-01T06:00:00Z', stale: true } });
      await renderPage();
      expect(screen.getByTestId('last-checked')).toHaveTextContent(/^Last checked /);
      expect(screen.getByTestId('stale-note')).toHaveTextContent('The security feed could not be refreshed');
      expect(screen.getByTestId('stale-note').className).toContain('text-drift-amber');
    });

    it('has no stale note when the feed is fresh, and no example chip for a real workspace', async () => {
      await renderPage();
      expect(screen.queryByTestId('stale-note')).not.toBeInTheDocument();
      expect(screen.getByTestId('last-checked')).toHaveTextContent(/^Last checked /);
      expect(screen.queryByTestId('example-data-chip')).not.toBeInTheDocument();
    });

    it('shows the example-data chip for demo organizations', async () => {
      mockOrg({ isDemo: true });
      mockApi({ stack: { ...STACK, demo: true } });
      await renderPage();
      expect(screen.getByTestId('example-data-chip')).toHaveTextContent('Example data');
    });

    it('"Check now" calls refresh, reloads the list and explains lookups that failed', async () => {
      vi.mocked(api.refreshSoftwareStack).mockResolvedValue({
        total: 4, vulnerable: 3, critical: 1, known_exploited: 1, end_of_life: 1,
        last_intel_refresh: '2026-11-09T09:00:00Z', looked_up: 4, errors: ['osv.dev timeout for Redis 7.2.4'],
      });
      await renderPage();
      const callsBefore = vi.mocked(api.getSoftwareStack).mock.calls.length;

      fireEvent.click(screen.getByTestId('check-now'));

      await waitFor(() => expect(screen.getByTestId('refresh-result')).toBeInTheDocument());
      expect(api.refreshSoftwareStack).toHaveBeenCalledWith(ORG);
      expect(screen.getByTestId('refresh-result')).toHaveTextContent('Check finished.');
      expect(screen.getByTestId('refresh-warnings')).toHaveTextContent('1 lookup did not finish');
      await waitFor(() => expect(vi.mocked(api.getSoftwareStack).mock.calls.length).toBeGreaterThan(callsBefore));
    });

    it('shows the paywall card when the refresh answers 402', async () => {
      vi.mocked(api.refreshSoftwareStack).mockRejectedValue(Object.assign(new Error('Subscription required'), { status: 402 }));
      await renderPage();
      fireEvent.click(screen.getByTestId('check-now'));
      await waitFor(() => expect(screen.getByTestId('refresh-paywall')).toBeInTheDocument());
      expect(screen.getByTestId('refresh-paywall')).toHaveTextContent(/requires Design Partner plan/);
      expect(screen.queryByTestId('refresh-error')).not.toBeInTheDocument();
      // What was already found stays visible.
      expect(screen.getAllByTestId('fix-card')).toHaveLength(2);
      openEverything();
      expect(screen.getAllByTestId('stack-row').length).toBe(4);
    });

    it('treats a missing endpoint (404) as "nothing connected" with a next action', async () => {
      vi.mocked(api.getSoftwareStack).mockRejectedValue(Object.assign(new Error('Not found'), { status: 404 }));
      vi.mocked(api.getTechAdvisories).mockRejectedValue(Object.assign(new Error('Not found'), { status: 404 }));
      vi.mocked(api.getTechDeployments).mockRejectedValue(Object.assign(new Error('Not found'), { status: 404 }));
      await renderPage();
      expect(screen.getByTestId('no-source-empty')).toBeInTheDocument();
      expect(screen.queryByTestId('section-error')).not.toBeInTheDocument();
      openEverything();
      expect(within(screen.getByTestId('stack-empty')).getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');
    });

    it('explains a server failure in plain words and offers a retry', async () => {
      vi.mocked(api.getSoftwareStack).mockRejectedValue(Object.assign(new Error('Server error: boom'), { status: 500 }));
      await renderPage();
      expect(screen.getByTestId('section-error')).toHaveTextContent('We could not load your software list right now.');
      expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument();
      expect(screen.queryByTestId('fix-this-week-clear')).not.toBeInTheDocument();
    });
  });

  describe('everything we checked', () => {
    it('is collapsed by default and opens on request', async () => {
      await renderPage();
      expect(screen.queryByTestId('software-table')).not.toBeInTheDocument();
      openEverything();
      expect(screen.getByTestId('everything-toggle')).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByTestId('software-table')).toBeInTheDocument();
      expect(screen.getByTestId('stack-sources')).toHaveTextContent(/aws/i);
    });

    it('labels matches that were not verified as "Not confirmed" in the inventory and the findings', async () => {
      const unverified = item({
        id: 'item-openssl',
        name: 'OpenSSL',
        vendor: 'OpenSSL',
        version: '3.0.2',
        category: 'library',
        asset: 'web-01',
        status: 'vulnerable',
        vulnerabilities: [
          { id: 'CVE-2022-3602', confidence: 'unconfirmed', severity: 'high', cvss: 7.5, summary: 'A crafted certificate may crash the program.', fixed_version: '3.0.7', published: null, known_exploited: true, references: [], remediation: '' },
        ],
      });
      mockApi({
        stack: { ...STACK, items: [...STACK.items, unverified] },
        advisories: {
          advisories: [
            ...ADVISORIES.advisories,
            advisory({ id: 'CVE-2022-3602', confidence: 'unconfirmed', severity: 'high', known_exploited: true, summary: 'A crafted certificate may crash OpenSSL.' }),
          ],
          generated_at: null,
        },
      });
      await renderPage();

      // Not on the action list, even though it is flagged as exploited.
      expect(screen.getAllByTestId('fix-card')).toHaveLength(2);
      expect(screen.queryByText('A crafted certificate may crash OpenSSL.')).not.toBeInTheDocument();

      openEverything('software');
      const row = screen.getAllByTestId('stack-row').find(r => /OpenSSL/.test(r.textContent || ''))!;
      expect(within(row).getByTestId('status-chip')).toHaveTextContent('Not confirmed');
      expect(within(row).queryByTestId('exploited-badge')).not.toBeInTheDocument();
      fireEvent.click(within(row).getByRole('button', { name: /OpenSSL/i }));
      const vuln = within(row).getByTestId('vulnerability-row');
      expect(vuln).toHaveAttribute('data-confirmed', 'false');
      expect(within(vuln).getByTestId('not-confirmed-chip')).toHaveTextContent('Not confirmed');

      openEverything('advisories');
      const cards = screen.getAllByTestId('advisory-card');
      const last = cards[cards.length - 1];
      expect(last).toHaveTextContent('A crafted certificate may crash OpenSSL.');
      expect(last).toHaveAttribute('data-confirmed', 'false');
      expect(within(last).getByTestId('not-confirmed-chip')).toBeInTheDocument();
      expect(within(cards[0]).queryByTestId('not-confirmed-chip')).not.toBeInTheDocument();
    });
  });

  describe('software and versions', () => {
    it('lists every program, most urgent first, with status and newest safe version', async () => {
      await renderPage();
      openEverything('software');
      const rows = screen.getAllByTestId('stack-row');
      expect(rows).toHaveLength(4);
      // Being exploited first, then critical, then the rest; healthy last.
      expect(rows[0]).toHaveTextContent('nginx');
      expect(rows[1]).toHaveTextContent('PostgreSQL');
      expect(rows[3]).toHaveTextContent('Redis');
      expect(sortStackItems(STACK.items).map(i => i.id)).toEqual(['item-nginx', 'item-pg', 'item-node', 'item-redis']);

      expect(within(rows[0]).getByTestId('status-chip')).toHaveTextContent('Needs an update');
      expect(within(rows[0]).getByTestId('exploited-badge')).toBeInTheDocument();
      expect(rows[0]).toHaveTextContent('web-01');
      expect(rows[0]).toHaveTextContent('1.26.2');
      expect(within(rows[3]).getByTestId('status-chip')).toHaveTextContent('Up to date');
    });

    it('expands a row to show each vulnerability, the fix, safe links and end-of-life info', async () => {
      await renderPage();
      openEverything('software');
      const row = screen.getAllByTestId('stack-row')[0];
      expect(within(row).queryByTestId('stack-detail')).not.toBeInTheDocument();

      fireEvent.click(within(row).getByRole('button', { name: /nginx/i }));

      const detail = within(row).getByTestId('stack-detail');
      expect(detail).toHaveTextContent('CVE-2021-23017');
      expect(detail).toHaveTextContent('A crafted DNS answer can crash or take over the web server.');
      expect(detail).toHaveTextContent('Fix: upgrade to 1.20.1');
      expect(within(detail).getByTestId('exploited-badge')).toHaveTextContent('Being exploited now');
      const links = within(detail).getAllByRole('link');
      expect(links).toHaveLength(1);
      expect(links[0]).toHaveAttribute('href', 'https://nvd.nist.gov/vuln/detail/CVE-2021-23017');
      expect(links[0]).toHaveAttribute('rel', expect.stringContaining('noopener'));
      expect(within(detail).getByTestId('eol-info')).toHaveTextContent(/stopped releasing security fixes/);

      fireEvent.click(within(row).getByRole('button', { name: /nginx/i }));
      expect(within(row).queryByTestId('stack-detail')).not.toBeInTheDocument();
    });

    it('filters by search text and by status', async () => {
      await renderPage();
      openEverything('software');
      fireEvent.change(screen.getByTestId('stack-search'), { target: { value: 'postgres' } });
      expect(screen.getAllByTestId('stack-row')).toHaveLength(1);

      fireEvent.change(screen.getByTestId('stack-search'), { target: { value: 'CVE-2024-22019' } });
      expect(screen.getAllByTestId('stack-row')[0]).toHaveTextContent('Node.js');

      fireEvent.change(screen.getByTestId('stack-search'), { target: { value: 'no such program' } });
      expect(screen.getByTestId('stack-no-match')).toBeInTheDocument();

      fireEvent.change(screen.getByTestId('stack-search'), { target: { value: '' } });
      fireEvent.click(screen.getByTestId('stack-filter-ok'));
      expect(screen.getAllByTestId('stack-row')).toHaveLength(1);
      expect(screen.getByTestId('stack-row')).toHaveTextContent('Redis');
    });
  });

  describe('all findings', () => {
    it('renders one card per advisory with affected systems and numbered steps', async () => {
      await renderPage();
      openEverything('advisories');

      const cards = screen.getAllByTestId('advisory-card');
      expect(cards).toHaveLength(2);
      expect(cards[0]).toHaveAttribute('data-urgent', 'true');
      expect(cards[1]).toHaveAttribute('data-urgent', 'false');
      expect(cards[0]).toHaveTextContent('Your web server can be taken over by a crafted network reply.');
      expect(within(cards[0]).getByTestId('exploited-badge')).toBeInTheDocument();
      expect(within(cards[0]).getByTestId('advisory-affected')).toHaveTextContent('nginx 1.18.0 on web-01');

      const steps = within(within(cards[0]).getByTestId('advisory-steps')).getAllByRole('listitem');
      expect(steps.map(s => s.textContent)).toEqual([
        'Back up the nginx configuration.',
        'Upgrade nginx to 1.20.1 or newer.',
        'Restart nginx and confirm the site loads.',
      ]);
      expect(cards[0]).toHaveTextContent('Who should do it');
      expect(within(cards[0]).getByRole('link', { name: /nginx\.org/ })).toHaveAttribute('href', 'https://nginx.org/en/security_advisories.html');
    });

    it('says there is nothing to fix when the list is empty', async () => {
      mockApi({ advisories: { advisories: [], generated_at: null } });
      await renderPage();
      openEverything('advisories');
      expect(screen.getByTestId('advisories-empty')).toHaveTextContent('Nothing to fix right now');
    });
  });

  describe('websites and apps', () => {
    it('rejects addresses that are not http or https without calling the API', async () => {
      await renderPage();
      openEverything('websites');
      expect(screen.getByTestId('web-assets-empty')).toBeInTheDocument();

      for (const bad of ['ftp://files.example.com', 'javascript:alert(1)', 'not a url', '']) {
        fireEvent.change(screen.getByLabelText('Web address'), { target: { value: bad } });
        fireEvent.click(screen.getByTestId('web-asset-add'));
        expect(await screen.findByTestId('web-asset-error')).toBeInTheDocument();
      }
      expect(api.addWebAsset).not.toHaveBeenCalled();

      expect(normalizeWebUrl('ftp://files.example.com')).toHaveProperty('error');
      expect(normalizeWebUrl('https://user:secret@example.com')).toHaveProperty('error');
      expect(normalizeWebUrl('portal.example.com')).toEqual({ url: 'https://portal.example.com/' });
      expect(normalizeWebUrl('http://intranet.example.com:8080/login')).toEqual({ url: 'http://intranet.example.com:8080/login' });
    });

    it('adds a valid address through the API and lists it', async () => {
      vi.mocked(api.addWebAsset).mockResolvedValue({ id: 'wa-1', url: 'https://portal.example.com/', label: 'Patient portal', last_scan: null });
      await renderPage();
      openEverything('websites');

      fireEvent.change(screen.getByLabelText('Web address'), { target: { value: '  https://portal.example.com ' } });
      fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: 'Patient portal' } });
      fireEvent.click(screen.getByTestId('web-asset-add'));

      await waitFor(() =>
        expect(api.addWebAsset).toHaveBeenCalledWith(ORG, { url: 'https://portal.example.com/', label: 'Patient portal' })
      );
      const card = await screen.findByTestId('web-asset-card');
      expect(card).toHaveTextContent('Patient portal');
      expect(card).toHaveTextContent('Not scanned yet');
      expect(screen.queryByTestId('web-asset-error')).not.toBeInTheDocument();
    });

    it('scans a site and reports the result as plain checks with fixes', async () => {
      mockApi({ assets: [{ id: 'wa-1', url: 'https://portal.example.com/', label: 'Patient portal', last_scan: null }] });
      vi.mocked(api.scanWebAsset).mockResolvedValue(SCAN);
      await renderPage();
      openEverything('websites');

      fireEvent.click(screen.getByTestId('web-scan-button'));
      const result = await screen.findByTestId('web-scan-result');
      expect(api.scanWebAsset).toHaveBeenCalledWith(ORG, 'wa-1');
      expect(result).toHaveTextContent('The site is up and answering visitors.');
      expect(result).toHaveTextContent('The security certificate expires in 10 days. Ask IT to renew it now.');
      const headerChecks = within(within(result).getByTestId('web-header-checks')).getAllByTestId('web-check');
      expect(headerChecks).toHaveLength(5);
      expect(headerChecks.filter(c => c.getAttribute('data-tone') === 'warning')).toHaveLength(2);
      expect(within(result).getByTestId('web-issues')).toHaveTextContent('Renew the certificate with your hosting provider.');

      fireEvent.click(within(within(result).getByTestId('web-detected')).getByRole('button'));
      expect(within(result).getByTestId('web-detected')).toHaveTextContent('WordPress 6.2');
    });

    it('removes a site only after a second confirmation', async () => {
      mockApi({ assets: [{ id: 'wa-1', url: 'https://portal.example.com/', label: 'Patient portal', last_scan: null }] });
      vi.mocked(api.deleteWebAsset).mockResolvedValue(undefined);
      await renderPage();
      openEverything('websites');

      fireEvent.click(screen.getByTestId('web-remove-button'));
      expect(api.deleteWebAsset).not.toHaveBeenCalled();
      fireEvent.click(screen.getByTestId('web-remove-confirm'));
      await waitFor(() => expect(api.deleteWebAsset).toHaveBeenCalledWith(ORG, 'wa-1'));
      await waitFor(() => expect(screen.queryByTestId('web-asset-card')).not.toBeInTheDocument());
    });
  });

  describe('cloud services', () => {
    it('empty state tells the reader to connect AWS and links to /connectors', async () => {
      await renderPage();
      openEverything('cloud');

      const empty = screen.getByTestId('deployments-empty');
      expect(empty).toHaveTextContent('Connect AWS to list what is running');
      expect(within(empty).getByRole('link', { name: /Connect AWS/i })).toHaveAttribute('href', '/connectors');
      expect(screen.getByTestId('deployment-sources')).toHaveTextContent(/aws/i);
    });

    it('groups deployments by type and flags public exposure and issues', async () => {
      mockApi({
        deployments: {
          deployments: [
            { id: 'd1', type: 'ec2', name: 'web-01', provider: 'aws', region: 'us-east-1', runtime: 'Ubuntu', version: '20.04', public: true, issues: [{ title: 'Remote login open to everyone', severity: 'critical', fix: 'Limit port 22 to the office address.' }] },
            { id: 'd2', type: 'ec2', name: 'api-01', provider: 'aws', region: 'us-east-1', runtime: null, version: null, public: false, issues: [] },
            { id: 'd3', type: 'rds', name: 'records-db', provider: 'aws', region: 'us-east-1', runtime: 'postgres', version: '13.2', public: null, issues: [] },
          ],
          sources: { aws: 'connected' },
          collected_at: '2026-11-09T05:00:00Z',
        },
      });
      await renderPage();
      openEverything('cloud');

      const groups = screen.getAllByTestId('deployment-group');
      expect(groups).toHaveLength(2);
      expect(groups[0]).toHaveTextContent('Virtual servers');
      expect(within(groups[0]).getAllByTestId('deployment-card')).toHaveLength(2);
      expect(groups[1]).toHaveTextContent('Databases');
      expect(within(groups[0]).getByTestId('deployment-public')).toHaveTextContent('Open to the internet');
      expect(within(groups[0]).getByTestId('deployment-issues')).toHaveTextContent('Limit port 22 to the office address.');
      expect(within(groups[1]).getByTestId('deployment-exposure-unknown')).toBeInTheDocument();
      expect(screen.getByTestId('deployments-summary')).toHaveTextContent('3 cloud services running. 1 is open to the internet. 1 thing to fix.');
      expect(screen.queryByTestId('deployments-empty')).not.toBeInTheDocument();
    });
  });
});

describe('AdvisoryAlert (morning brief line)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows one line linking to Software Watch when confirmed items exist', async () => {
    vi.mocked(api.getTechAdvisories).mockResolvedValue({
      advisories: [
        advisory({ id: 'A', severity: 'critical', summary: 'Rated critical but not being exploited.' }),
        advisory({ id: 'B', severity: 'high', known_exploited: true, confidence: 'confirmed', summary: 'Your web server can be taken over.' }),
        advisory({ id: 'C', severity: 'medium', summary: 'Routine update.' }),
        advisory({ id: 'D', severity: 'low', end_of_life: true, confidence: 'confirmed', summary: 'Your database version is no longer supported.' }),
      ],
      generated_at: '2026-11-09T06:00:00Z',
    });
    renderWithRouter(<AdvisoryAlert orgId={ORG} />);

    const alert = await screen.findByTestId('advisory-alert');
    expect(api.getTechAdvisories).toHaveBeenCalledWith(ORG);
    expect(alert).toHaveTextContent('2 things to fix this week: Your web server can be taken over.');
    expect(alert).toHaveAttribute('href', '/technology/intelligence');
    expect(alert.textContent).not.toMatch(/CVE-\d/);
  });

  it('prefers the backend top_actions, counts confirmed ones only and uses the singular', async () => {
    vi.mocked(api.getTechAdvisories).mockResolvedValue({
      advisories: [advisory({ id: 'B', known_exploited: true, summary: 'Ignored when top_actions is present.' })],
      top_actions: [topAction(0, { confidence: 'unconfirmed' }), topAction(1)],
      generated_at: null,
    });
    renderWithRouter(<AdvisoryAlert orgId={ORG} />);
    expect(await screen.findByTestId('advisory-alert')).toHaveTextContent(
      '1 thing to fix this week: Update program 1 on the front desk computers'
    );
  });

  it('renders nothing when no item is confirmed', async () => {
    vi.mocked(api.getTechAdvisories).mockResolvedValue({
      advisories: [
        advisory({ id: 'C', severity: 'critical' }),
        advisory({ id: 'D', severity: 'high', known_exploited: true, confidence: 'unconfirmed' }),
      ],
      generated_at: null,
    });
    const { container } = renderWithRouter(<AdvisoryAlert orgId={ORG} />);
    await waitFor(() => expect(api.getTechAdvisories).toHaveBeenCalled());
    await Promise.resolve();
    expect(screen.queryByTestId('advisory-alert')).not.toBeInTheDocument();
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing on error, on an unexpected answer, or without an organization', async () => {
    vi.mocked(api.getTechAdvisories).mockRejectedValue(Object.assign(new Error('Server error'), { status: 500 }));
    const failed = renderWithRouter(<AdvisoryAlert orgId={ORG} />);
    await waitFor(() => expect(api.getTechAdvisories).toHaveBeenCalledTimes(1));
    await Promise.resolve();
    expect(failed.container).toBeEmptyDOMElement();
    failed.unmount();

    vi.mocked(api.getTechAdvisories).mockReturnValue(undefined as any);
    const odd = renderWithRouter(<AdvisoryAlert orgId={ORG} />);
    await waitFor(() => expect(api.getTechAdvisories).toHaveBeenCalledTimes(2));
    await Promise.resolve();
    expect(odd.container).toBeEmptyDOMElement();
    odd.unmount();

    const none = renderWithRouter(<AdvisoryAlert orgId="" />);
    expect(none.container).toBeEmptyDOMElement();
    expect(api.getTechAdvisories).toHaveBeenCalledTimes(2);
  });
});
