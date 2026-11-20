import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import GovernancePage from '../pages/Governance';
import DocumentsPage from '../pages/Documents';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');

/**
 * The Governance and Documents ("Customer Evidence") pages used to render
 * fixed sample scores, control counts, files, hashes and summaries to every
 * workspace. A real organisation must only ever see what the backend returned
 * for it, or a plain statement that there is nothing yet. The sample content
 * stays in the demo workspace, tagged "Sample data".
 */

const LIVE_ORG_ID = 'org-live-001';

function mockOrg(isDemo: boolean, overrides: Record<string, unknown> = {}) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: isDemo ? 'demo-health-org' : LIVE_ORG_ID,
    orgName: isDemo ? 'Acme Health Systems (Demo)' : 'Riverside Family Practice',
    org: null,
    orgs: [],
    isDemo,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  } as any);
}

/** Figures, names, hashes and claims that only exist in the bundled sample content. */
const SAMPLE_ONLY = [
  /104/,
  /CrowdStrike/i,
  /Veeam/i,
  /Q3 SOC 2/i,
  /42-minute/i,
  /sha256:7f83/i,
  /% Readiness/i,
  /Controls Verified/i,
  /2 hours ago/i,
  /Oct 12, 2023/i,
  /Continuous Telemetry/i,
  /Audit-Ready/i,
  /HIPAA Safeguards Package/i,
  /Zero Critical Breaches/i,
  /Cryptographic/i,
  /Sample data/i,
];

function expectNoSampleContent() {
  const text = document.body.textContent || '';
  for (const pattern of SAMPLE_ONLY) {
    expect(text).not.toMatch(pattern);
  }
}

/**
 * What `GET /api/governance/{org}/health-index` returns for an organisation
 * with no findings, no tracked components, no service-level tier and no
 * profile: the formula's starting value (app/services/governance/validation_engine.py).
 */
function untouchedOrgHealthIndex() {
  return {
    org_id: LIVE_ORG_ID,
    ghi: 70,
    grade: 'C',
    dimensions: { audit: 100, lifecycle: 100, sla: 0, compliance: 0 },
    weights: { audit: 0.4, lifecycle: 0.3, sla: 0.2, compliance: 0.1 },
    audit_readiness: { score: 100, total_open: 0 },
    lifecycle: { score: 100, total_components: 0 },
    sla: { status: 'not_configured', score: 0 },
    compliance: { total_frameworks: 0, score: 0, frameworks: [] },
    passed: false,
    issues: ['No governance profile configured — compliance unknown'],
  } as any;
}

function measuredHealthIndex() {
  return {
    org_id: LIVE_ORG_ID,
    ghi: 82.5,
    grade: 'B',
    dimensions: { audit: 85, lifecycle: 75, sla: 80, compliance: 100 },
    weights: { audit: 0.4, lifecycle: 0.3, sla: 0.2, compliance: 0.1 },
    audit_readiness: { score: 85, total_open: 3 },
    lifecycle: { score: 75, total_components: 9 },
    sla: { status: 'on_track', score: 80 },
    compliance: { total_frameworks: 2, score: 100, frameworks: [] },
    passed: true,
    issues: ['1 component(s) at end-of-life — immediate upgrade required'],
  } as any;
}

beforeEach(() => {
  vi.resetAllMocks();
});

// =============================================================================
// Governance
// =============================================================================

describe('Governance page: a real organisation never sees sample figures', () => {
  it('shows "Not measured yet" and an empty state when the backend has nothing for the organisation', async () => {
    mockOrg(false);
    vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(untouchedOrgHealthIndex());
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue({ org_id: LIVE_ORG_ID, frameworks: [], total: 0 } as any);
    vi.mocked(api.getFrameworkCoverage).mockResolvedValue([
      { framework: 'MITRE_ATLAS', covered_controls: 0, total_controls: 14, coverage_percent: 0 },
      { framework: 'NIST_AI_RMF', covered_controls: 0, total_controls: 72, coverage_percent: 0 },
    ]);

    renderWithRouter(<GovernancePage />);

    expect(await screen.findByTestId('governance-ghi-not-measured')).toHaveTextContent('Not measured yet');
    expect(screen.queryByTestId('governance-ghi-value')).not.toBeInTheDocument();

    const empty = screen.getByTestId('governance-empty-state');
    expect(within(empty).getByRole('link', { name: /Complete organisation profile/i })).toHaveAttribute('href', '/settings');
    expect(within(empty).getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');

    // The formula's starting value is not a measurement of this organisation.
    expect(document.body.textContent).not.toMatch(/\b70\b/);
    expect(screen.queryByTestId('governance-framework-card')).not.toBeInTheDocument();
    expect(api.getGovernanceHealthIndex).toHaveBeenCalledWith(LIVE_ORG_ID);
    expect(api.getApplicableFrameworks).toHaveBeenCalledWith(LIVE_ORG_ID);
    expectNoSampleContent();
  });

  it('never falls back to a number when the health index request fails', async () => {
    mockOrg(false);
    vi.mocked(api.getGovernanceHealthIndex).mockRejectedValue(new Error('500'));
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue({
      org_id: LIVE_ORG_ID,
      frameworks: [{ framework: 'HIPAA', reason: 'Organization processes PHI', mandatory: true }],
      total: 1,
    } as any);
    vi.mocked(api.getFrameworkCoverage).mockResolvedValue([]);

    renderWithRouter(<GovernancePage />);

    expect(await screen.findByTestId('governance-ghi-not-measured')).toBeInTheDocument();
    expect(screen.getByTestId('governance-partial-notice')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'HIPAA' })).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\b96\b/);
    expectNoSampleContent();
  });

  it('renders the index, frameworks and coverage exactly as the backend returned them', async () => {
    mockOrg(false);
    vi.mocked(api.getGovernanceHealthIndex).mockResolvedValue(measuredHealthIndex());
    vi.mocked(api.getApplicableFrameworks).mockResolvedValue({
      org_id: LIVE_ORG_ID,
      frameworks: [
        { framework: 'HIPAA', reason: 'Organization processes PHI', mandatory: true },
        { framework: 'NIST AI RMF', reason: 'Organization uses AI in production', mandatory: false },
      ],
      total: 2,
    } as any);
    vi.mocked(api.getFrameworkCoverage).mockResolvedValue([
      { framework: 'MITRE_ATLAS', covered_controls: 0, total_controls: 14, coverage_percent: 0 },
      { framework: 'NIST_AI_RMF', covered_controls: 12, total_controls: 72, coverage_percent: 16.7 },
    ]);

    renderWithRouter(<GovernancePage />);

    expect(await screen.findByTestId('governance-ghi-value')).toHaveTextContent('82.5');
    expect(screen.getByText('Grade B')).toBeInTheDocument();
    expect(screen.getByText(/3 open findings, 9 tracked technology components/)).toBeInTheDocument();
    expect(screen.getByText(/1 component\(s\) at end-of-life/)).toBeInTheDocument();

    const cards = screen.getAllByTestId('governance-framework-card');
    expect(cards).toHaveLength(2);

    const hipaa = cards[0];
    expect(within(hipaa).getByRole('heading', { name: 'HIPAA' })).toBeInTheDocument();
    expect(within(hipaa).getByText('Organization processes PHI')).toBeInTheDocument();
    expect(within(hipaa).getByText('Mandatory')).toBeInTheDocument();
    // No coverage row came back for HIPAA, so none is shown.
    expect(within(hipaa).getByText('Coverage not measured yet')).toBeInTheDocument();

    const aiRmf = cards[1];
    expect(within(aiRmf).getByRole('heading', { name: 'NIST AI RMF' })).toBeInTheDocument();
    expect(within(aiRmf).getByText('Recommended')).toBeInTheDocument();
    expect(within(aiRmf).getByText('12 of 72 controls tracked')).toBeInTheDocument();
    expect(within(aiRmf).getByText('16.7% coverage')).toBeInTheDocument();

    expect(screen.queryByTestId('governance-empty-state')).not.toBeInTheDocument();
    expect(screen.queryByTestId('governance-partial-notice')).not.toBeInTheDocument();
    expectNoSampleContent();
  });

  it('shows an error, not sample content, when every request fails', async () => {
    mockOrg(false);
    vi.mocked(api.getGovernanceHealthIndex).mockRejectedValue(new Error('offline'));
    vi.mocked(api.getApplicableFrameworks).mockRejectedValue(new Error('offline'));
    vi.mocked(api.getFrameworkCoverage).mockRejectedValue(new Error('offline'));

    renderWithRouter(<GovernancePage />);

    expect(await screen.findByText('Unable to Load Data')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
    expectNoSampleContent();
  });

  it('waits for the organisation before asking the backend for anything', () => {
    mockOrg(false, { orgId: '', loading: true });

    renderWithRouter(<GovernancePage />);

    expect(api.getGovernanceHealthIndex).not.toHaveBeenCalled();
    expect(api.getApplicableFrameworks).not.toHaveBeenCalled();
    expect(api.getFrameworkCoverage).not.toHaveBeenCalled();
    expectNoSampleContent();
  });

  it('keeps the sample walkthrough in the demo workspace, tagged "Sample data"', async () => {
    mockOrg(true);

    renderWithRouter(<GovernancePage />);

    expect(await screen.findByRole('heading', { name: 'NIST CSF 2.0' })).toBeInTheDocument();
    expect(screen.getByTestId('sample-data-tag')).toHaveTextContent('Sample data');
    expect(screen.getByText('104/108 Controls Verified')).toBeInTheDocument();
    expect(screen.getByText('CrowdStrike Falcon API')).toBeInTheDocument();
    expect(screen.getByText('IAM & Multi-Factor Authentication')).toBeInTheDocument();
    // The live view's coverage request is never made for the sample walkthrough.
    expect(api.getFrameworkCoverage).not.toHaveBeenCalled();
    expect(screen.queryByTestId('governance-live')).not.toBeInTheDocument();
  });
});

// =============================================================================
// Documents ("Customer Evidence")
// =============================================================================

describe('Documents page: a real organisation never sees sample documents', () => {
  it('shows an honest empty state when no report exists and no evidence is recorded', async () => {
    const user = userEvent.setup();
    mockOrg(false);
    vi.mocked(api.getReports).mockResolvedValue({ reports: [], total: 0 });
    vi.mocked(api.getEvidenceLedger).mockResolvedValue([]);

    renderWithRouter(<DocumentsPage />);

    const empty = await screen.findByTestId('documents-empty-state');
    expect(within(empty).getByText('No documents yet.')).toBeInTheDocument();
    expect(within(empty).getByRole('link', { name: /Go to Reports/i })).toHaveAttribute('href', '/reports');
    expect(within(empty).getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');
    expect(api.getReports).toHaveBeenCalledWith({ organization_id: LIVE_ORG_ID, limit: 50 });

    // Nothing that would fabricate a file is offered.
    expect(screen.queryByRole('button', { name: /Download/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Upload Evidence/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Audit-Ready Folders')).not.toBeInTheDocument();
    expect(screen.queryByText('Executive Summaries')).not.toBeInTheDocument();
    expectNoSampleContent();

    await user.click(screen.getByRole('button', { name: /Audit Sync Ledger/i }));

    const ledgerEmpty = await screen.findByTestId('documents-ledger-empty-state');
    expect(within(ledgerEmpty).getByRole('link', { name: /Connect a system/i })).toHaveAttribute('href', '/connectors');
    expect(api.getEvidenceLedger).toHaveBeenCalledWith(LIVE_ORG_ID, 50);
    expectNoSampleContent();
  });

  it('lists the organisation\'s own reports and ledger rows, and downloads through the real endpoint', async () => {
    const user = userEvent.setup();
    mockOrg(false);
    vi.mocked(api.getReports).mockResolvedValue({
      total: 3,
      reports: [
        {
          id: 'rep-live-1',
          organization_id: LIVE_ORG_ID,
          report_type: 'cyber_insurance',
          title: 'Riverside insurance renewal pack',
          format: 'pdf',
          status: 'completed',
          created_at: '2026-11-10T09:30:00Z',
        },
        {
          id: 'rep-live-2',
          organization_id: LIVE_ORG_ID,
          report_type: 'monthly_ops',
          title: 'Riverside monthly operations',
          format: 'csv',
          status: 'generating',
          created_at: '2026-11-12T14:00:00Z',
        },
        {
          id: 'rep-other-org',
          organization_id: 'org-someone-else',
          report_type: 'board_story',
          title: 'Another organisation board story',
          format: 'pdf',
          status: 'completed',
          created_at: '2026-11-01T08:00:00Z',
        },
      ],
    } as any);
    vi.mocked(api.downloadReportById).mockResolvedValue(new Blob(['pdf']));
    vi.mocked(api.getEvidenceLedger).mockResolvedValue([
      {
        id: 'row-1',
        timestamp: '2026-11-14T06:00:00Z',
        source_name: 'Microsoft 365',
        event_type: 'mfa_policy_check',
        verification_status: 'verified',
        evidence_hash: 'c0ffee11c0ffee22c0ffee33c0ffee44c0ffee55c0ffee66c0ffee77c0ffee88',
      },
    ]);
    const createObjectURL = vi.fn(() => 'blob:report');
    const revokeObjectURL = vi.fn();
    Object.assign(URL, { createObjectURL, revokeObjectURL });

    renderWithRouter(<DocumentsPage />);

    expect(await screen.findByText('Riverside insurance renewal pack')).toBeInTheDocument();
    expect(screen.getByText('Riverside monthly operations')).toBeInTheDocument();
    // A report belonging to another organisation is never listed.
    expect(screen.queryByText('Another organisation board story')).not.toBeInTheDocument();
    expect(screen.getAllByTestId('documents-report-row')).toHaveLength(2);

    // Only a finished report can be downloaded, and only through the real download call.
    const downloadButtons = screen.getAllByRole('button', { name: /^Download /i });
    expect(downloadButtons).toHaveLength(1);
    await user.click(downloadButtons[0]);
    await waitFor(() => expect(api.downloadReportById).toHaveBeenCalledWith('rep-live-1'));
    await waitFor(() => expect(createObjectURL).toHaveBeenCalledTimes(1));
    expect(screen.getByText('generating')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Audit Sync Ledger/i }));

    expect(await screen.findByText('Microsoft 365')).toBeInTheDocument();
    expect(screen.getByText('mfa_policy_check')).toBeInTheDocument();
    expect(screen.getByText('c0ffee11c0ffee22...c0ffee88')).toBeInTheDocument();
    expectNoSampleContent();
  });

  it('shows errors, not sample rows, when the backend fails', async () => {
    const user = userEvent.setup();
    mockOrg(false);
    vi.mocked(api.getReports).mockRejectedValue(new Error('500'));
    vi.mocked(api.getEvidenceLedger).mockRejectedValue(new Error('500'));
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithRouter(<DocumentsPage />);

    expect(await screen.findByText(/We could not load your documents/i)).toBeInTheDocument();
    expectNoSampleContent();

    await user.click(screen.getByRole('button', { name: /Audit Sync Ledger/i }));

    expect(await screen.findByText(/We could not load the evidence ledger/i)).toBeInTheDocument();
    expectNoSampleContent();
    consoleError.mockRestore();
  });

  it('waits for the organisation before asking the backend for anything', () => {
    mockOrg(false, { orgId: '', loading: true });

    renderWithRouter(<DocumentsPage />);

    expect(api.getReports).not.toHaveBeenCalled();
    expect(api.getEvidenceLedger).not.toHaveBeenCalled();
    expectNoSampleContent();
  });

  it('keeps the sample vault in the demo workspace, tagged "Sample data"', async () => {
    mockOrg(true);

    renderWithRouter(<DocumentsPage />);

    expect(await screen.findByText('Audit-Ready Folders')).toBeInTheDocument();
    expect(screen.getByTestId('sample-data-tag')).toHaveTextContent('Sample data');
    expect(screen.getByText('HIPAA Safeguards Package')).toBeInTheDocument();
    expect(screen.getByText('Q3 SOC 2 Readiness Assessment Package')).toBeInTheDocument();
    expect(screen.getByText(/42-minute Recovery Time Objective/)).toBeInTheDocument();
    // The sample vault is bundled: no report list is requested from the backend.
    expect(api.getReports).not.toHaveBeenCalled();
    expect(screen.queryByTestId('documents-live')).not.toBeInTheDocument();
  });
});

// =============================================================================
// api.ts: evidence ledger and packages
// =============================================================================

describe('Evidence API: sample rows are for demo organisations only', () => {
  let actual: typeof import('../api');
  let fetchMock: ReturnType<typeof vi.fn>;

  const jsonResponse = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

  beforeEach(async () => {
    actual = await vi.importActual<typeof import('../api')>('../api');
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns the bundled rows for a demo organisation without calling the backend', async () => {
    const rows = await actual.getEvidenceLedger('demo-health-org', 50);

    expect(rows.map((row) => row.id)).toEqual(['led-1', 'led-2']);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('reads a real organisation\'s ledger from GET /api/v1/evidence/ledger and maps each row', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse([
        {
          id: 'f3b1c2d4',
          evidence_hash: 'c0ffee11c0ffee22c0ffee33c0ffee44c0ffee55c0ffee66c0ffee77c0ffee88',
          source_name: 'Microsoft 365',
          event_type: 'mfa_policy_check',
          timestamp: '2026-11-14T06:00:00+00:00',
          overall_confidence: 95,
          verification_status: 'verified',
        },
      ])
    );

    const rows = await actual.getEvidenceLedger(LIVE_ORG_ID, 25);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain(`/api/v1/evidence/ledger?org_id=${LIVE_ORG_ID}&limit=25`);
    expect((init?.method || 'GET').toUpperCase()).toBe('GET');
    expect(rows).toEqual([
      {
        id: 'f3b1c2d4',
        timestamp: '2026-11-14T06:00:00+00:00',
        source_name: 'Microsoft 365',
        event_type: 'mfa_policy_check',
        verification_status: 'verified',
        evidence_hash: 'c0ffee11c0ffee22c0ffee33c0ffee44c0ffee55c0ffee66c0ffee77c0ffee88',
      },
    ]);
  });

  it('returns an empty ledger, not sample rows, when a real organisation has none', async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));

    await expect(actual.getEvidenceLedger(LIVE_ORG_ID)).resolves.toEqual([]);
    expect(String(fetchMock.mock.calls[0][0])).toContain('limit=50');
  });

  it('throws for a real organisation when the backend fails, instead of falling back to samples', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));

    await expect(actual.getEvidenceLedger(LIVE_ORG_ID, 50)).rejects.toBeDefined();
  });

  it('never claims an evidence package is available for a real organisation', async () => {
    await expect(actual.getEvidencePackages(LIVE_ORG_ID)).resolves.toEqual({
      hipaa: { available: false },
      security: { available: false },
      backup: { available: false },
    });
    await expect(actual.getEvidencePackages()).resolves.toEqual({
      hipaa: { available: false },
      security: { available: false },
      backup: { available: false },
    });
    await expect(actual.getEvidencePackages('demo-health-org')).resolves.toEqual({
      hipaa: { available: true },
      security: { available: true },
      backup: { available: true },
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
