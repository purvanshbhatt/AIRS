import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import React from 'react';
import IdentityPage from '../pages/technology/IdentityPage';
import DevicesPage from '../pages/technology/DevicesPage';
import BackupsPage from '../pages/technology/BackupsPage';
import EmailPage from '../pages/technology/EmailPage';
import CloudPage from '../pages/technology/CloudPage';
import AIPage from '../pages/technology/AIPage';
import { classifyDomain, sliceReportForDomain } from '../components/technology/DomainLiveView';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');

/**
 * The technology area pages (identity, devices, backups, email, cloud, AI)
 * used to render fixed sample figures to every workspace. A real organisation
 * must only ever see what its own connected systems report, or a plain
 * statement that nothing is connected.
 */

function mockOrg(isDemo: boolean) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: isDemo ? 'demo-health-org' : 'org-live-001',
    orgName: isDemo ? 'Acme Health Systems (Demo)' : 'Riverside Family Practice',
    org: null,
    orgs: [],
    isDemo,
    hasOrg: true,
    loading: false,
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
  } as any);
}

/** A report in the shape the live API returns (`/api/clinic/readiness/{org}`). */
function liveReport(overrides: Record<string, unknown> = {}) {
  return {
    generated_at: '2026-11-14T09:30:00Z',
    status: 'action_needed',
    passed_checks: [],
    failed_checks: [],
    warnings: [],
    unknowns: [],
    immediate_actions: [],
    coverage: { coverage_pct: 0, monitored: [], not_monitored: [] },
    connectors: [],
    ...overrides,
  } as any;
}

const AWS_CHECK = {
  status: 'fail',
  label: 'AWS security check failing: "EBS default encryption should be enabled" on 1 resource.',
  detail: 'A setting in your AWS account does not meet the AWS security baseline.',
  verification: { verification_source: 'Amazon Web Services', data_age_description: 'Checked 2 hours ago' },
  action: { action_id: 'review_cloud_finding', category: 'cloud_security' },
  explanation: { technical_label: 'Cloud Security Posture (AWS Security Hub / GuardDuty)' },
};

const INACTIVE_ACCOUNT_CHECK = {
  status: 'warning',
  label: 'An inactive account is still enabled.',
  detail: 'It could be used to improperly access patient records.',
  verification: { verification_source: 'Microsoft 365', data_age_description: 'Checked 10 minutes ago' },
  action: { action_id: 'disable_account', category: 'access_control' },
  explanation: { technical_label: 'Identity & Access Management' },
};

/** Figures and product names that only exist in the bundled sample pages. */
const SAMPLE_ONLY = [
  /Simulated Telemetry/i,
  /% Readiness/i,
  /2450/,
  /Okta/i,
  /CyberArk/i,
  /CrowdStrike/i,
  /SO WHAT\?/i,
];

function expectNoSampleContent() {
  const text = document.body.textContent || '';
  for (const pattern of SAMPLE_ONLY) {
    expect(text).not.toMatch(pattern);
  }
}

const PAGES: { name: string; Page: React.ComponentType; domain: string }[] = [
  { name: 'Identity', Page: IdentityPage, domain: 'identity' },
  { name: 'Devices', Page: DevicesPage, domain: 'devices' },
  { name: 'Backups', Page: BackupsPage, domain: 'backups' },
  { name: 'Email', Page: EmailPage, domain: 'email' },
  { name: 'Cloud', Page: CloudPage, domain: 'cloud' },
  { name: 'AI', Page: AIPage, domain: 'ai' },
];

describe('Technology area pages: a real organisation never sees sample figures', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each(PAGES)('$name page shows an empty state, not sample numbers, when nothing is connected', async ({ Page, domain }) => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(liveReport());

    renderWithRouter(<Page />);

    await waitFor(() => {
      expect(screen.getByTestId(`domain-empty-${domain}`)).toBeInTheDocument();
    });
    expect(api.getDailyReadinessReport).toHaveBeenCalledWith('org-live-001');
    expectNoSampleContent();
  });

  it('Cloud page lists the checks the connected AWS account reported, with their source', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(
      liveReport({
        failed_checks: [AWS_CHECK],
        warnings: [INACTIVE_ACCOUNT_CHECK],
        coverage: {
          coverage_pct: 8,
          monitored: [{ area: 'Cloud Security', monitored: true, source: 'Amazon Web Services' }],
          not_monitored: [],
        },
      })
    );

    renderWithRouter(<CloudPage />);

    await waitFor(() => {
      expect(screen.getByTestId('domain-failed')).toBeInTheDocument();
    });
    expect(screen.getByText(/EBS default encryption should be enabled/)).toBeInTheDocument();
    expect(screen.getByText(/Source: Amazon Web Services · Checked 2 hours ago/)).toBeInTheDocument();
    expect(screen.getByText(/Connected through Amazon Web Services/)).toBeInTheDocument();
    // The Microsoft 365 account warning belongs to the identity page, not here.
    expect(screen.queryByText(/inactive account/i)).not.toBeInTheDocument();
    expectNoSampleContent();
  });

  it('Identity page shows only identity checks and says which areas are not connected', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(
      liveReport({
        failed_checks: [AWS_CHECK],
        warnings: [INACTIVE_ACCOUNT_CHECK],
        coverage: {
          coverage_pct: 8,
          monitored: [{ area: 'Users & Identities', monitored: true, source: 'Microsoft 365' }],
          not_monitored: [{ area: 'Multi-Factor Authentication', monitored: false, source: null }],
        },
      })
    );

    renderWithRouter(<IdentityPage />);

    await waitFor(() => {
      expect(screen.getByTestId('domain-warnings')).toBeInTheDocument();
    });
    expect(screen.getByText('An inactive account is still enabled.')).toBeInTheDocument();
    expect(screen.queryByTestId('domain-failed')).not.toBeInTheDocument();
    expect(screen.queryByText(/EBS default encryption/)).not.toBeInTheDocument();
    expect(screen.getByText(/Connected through Microsoft 365/)).toBeInTheDocument();
    expect(screen.getByText('Not connected')).toBeInTheDocument();
    expectNoSampleContent();
  });

  it('says the items were read earlier when checks exist but no system is connected now', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(liveReport({ failed_checks: [AWS_CHECK] }));

    renderWithRouter(<CloudPage />);

    await waitFor(() => {
      expect(screen.getByTestId('domain-failed')).toBeInTheDocument();
    });
    expect(screen.getByText('No active connection. The items below were read earlier.')).toBeInTheDocument();
    expect(screen.queryByText(/Connected through/)).not.toBeInTheDocument();
  });

  it('says plainly that nothing has been verified when a system is connected but no check reported', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(
      liveReport({
        coverage: {
          coverage_pct: 8,
          monitored: [{ area: 'Email Security', monitored: true, source: 'Microsoft 365' }],
          not_monitored: [],
        },
      })
    );

    renderWithRouter(<EmailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('domain-no-checks')).toBeInTheDocument();
    });
    expect(screen.getByText(/This is not a pass/)).toBeInTheDocument();
    expect(screen.queryByTestId('domain-passed')).not.toBeInTheDocument();
    expectNoSampleContent();
  });

  it('AI page tells a real organisation that nothing is measured, with no figures', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue(liveReport({ failed_checks: [AWS_CHECK] }));

    renderWithRouter(<AIPage />);

    await waitFor(() => {
      expect(screen.getByTestId('domain-empty-ai')).toBeInTheDocument();
    });
    expect(screen.getByText(/no numbers are shown/i)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Agent Audit/i })).not.toBeInTheDocument();
    expectNoSampleContent();
  });

  it('shows an error with a retry, not sample figures, when the report cannot be loaded', async () => {
    mockOrg(false);
    vi.mocked(api.getDailyReadinessReport).mockRejectedValue(new Error('Service unavailable'));

    renderWithRouter(<BackupsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Service unavailable/)).toBeInTheDocument();
    });
    expectNoSampleContent();
  });

  it('demo workspace keeps the sample walkthrough, labelled as simulated', () => {
    mockOrg(true);

    renderWithRouter(<IdentityPage />);

    expect(screen.getByText('Simulated Telemetry')).toBeInTheDocument();
    expect(screen.getByTestId('sample-product-names-note')).toHaveTextContent(/examples only/i);
    expect(api.getDailyReadinessReport).not.toHaveBeenCalled();
  });
});

describe('classifyDomain / sliceReportForDomain', () => {
  it('uses the category the backend attached before the wording of the check', () => {
    // "password policy" reads like identity, but AWS reported it for the cloud account.
    expect(
      classifyDomain({
        label: 'AWS security check failing: "Ensure IAM password policy requires at least one number"',
        action: { category: 'cloud_security' },
      })
    ).toBe('cloud');
    expect(classifyDomain(INACTIVE_ACCOUNT_CHECK)).toBe('identity');
    expect(classifyDomain({ action: { category: 'backup' }, label: 'Server backup has not completed' })).toBe('backups');
    expect(classifyDomain({ action: { category: 'device_security' }, label: 'Laptop is missing updates' })).toBe('devices');
  });

  it('falls back to the capability label and then the wording', () => {
    expect(classifyDomain({ label: 'x', explanation: { technical_label: 'Backup / Recovery' } })).toBe('backups');
    expect(classifyDomain({ label: 'x', explanation: { technical_label: 'Email Security Gateway' } })).toBe('email');
    expect(classifyDomain({ label: 'x', explanation: { technical_label: 'Multi-Factor Authentication (MFA)' } })).toBe('identity');
    expect(classifyDomain({ label: 'x', explanation: { technical_label: 'Vulnerability Management' } })).toBe('devices');
    expect(classifyDomain({ name: 'Immutable Backups', category: 'Backups' })).toBe('backups');
    expect(classifyDomain({ label: 'Something unrelated', explanation: { technical_label: 'Telemetry' } })).toBeNull();
    expect(classifyDomain({})).toBeNull();
  });

  it('counts each check in exactly one area', () => {
    const report = liveReport({ failed_checks: [AWS_CHECK], warnings: [INACTIVE_ACCOUNT_CHECK] });
    const totals = (['identity', 'devices', 'backups', 'email', 'cloud', 'ai'] as const).map(
      (domain) => sliceReportForDomain(report, domain).total
    );
    expect(totals).toEqual([1, 0, 0, 0, 1, 0]);
  });

  it('survives a report with missing sections', () => {
    const slice = sliceReportForDomain({}, 'backups');
    expect(slice.total).toBe(0);
    expect(slice.anyMonitored).toBe(false);
    expect(slice.areas.map((a) => a.source)).toEqual([null, null]);
    expect(sliceReportForDomain(null, 'ai').areas).toEqual([]);
  });
});
