import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { FirstRunChecklist } from '../components/readiness/FirstRunChecklist';
import { IT_HANDOFF_NOTE } from '../components/onboarding/onboardingData';
import * as api from '../api';
import { createMockDailyReadinessReport, renderWithRouter } from './utils/test-helpers';

vi.mock('../api');

const ORG = 'org-first-run-001';

function connectors(n: number) {
  return {
    connectors: Array.from({ length: n }, (_, i) => ({
      id: `conn-${i}`,
      org_id: ORG,
      connector_type: i === 0 ? 'microsoft365' : 'veeam',
      display_name: `Connector ${i}`,
      auth_method: 'oauth',
      status: 'active',
      sync_interval_minutes: 15,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })),
    total: n,
  } as any;
}

describe('FirstRunChecklist', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shows "0 of 3 done" with no connectors and no checks, with all three items and their links', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(connectors(0));
    renderWithRouter(<FirstRunChecklist orgId={ORG} report={null} />);

    await waitFor(() => expect(api.getConnectorsList).toHaveBeenCalledWith(ORG));
    expect(await screen.findByTestId('first-run-progress')).toHaveTextContent('0 of 3 done');

    expect(screen.getByRole('link', { name: /connect where your email and files live/i })).toHaveAttribute('href', '/connectors');
    expect(screen.getByRole('link', { name: /get your first monday verdict/i })).toHaveAttribute('href', '/morning-brief');
    expect(screen.getByRole('link', { name: /download your 1-page boss report/i })).toHaveAttribute('href', '/reports');
    expect(screen.getByText(/start with microsoft 365, then your backup system/i)).toBeInTheDocument();
    expect(screen.getByTestId('first-run-item-connect')).toHaveAttribute('data-done', 'false');
  });

  it('shows "1 of 3 done" once a connector exists', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(connectors(1));
    renderWithRouter(<FirstRunChecklist orgId={ORG} report={null} />);

    await waitFor(() => {
      expect(screen.getByTestId('first-run-progress')).toHaveTextContent('1 of 3 done');
    });
    expect(screen.getByTestId('first-run-item-connect')).toHaveAttribute('data-done', 'true');
    // The IT hand-off button is only offered while nothing is connected.
    expect(screen.queryByTestId('copy-it-instructions')).not.toBeInTheDocument();
  });

  it('auto-checks the verdict item when the report has passed or failed checks', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(connectors(1));
    const report = createMockDailyReadinessReport({
      passed_checks: [{ id: 'c1', name: 'MFA on', category: 'identity' }],
      failed_checks: [],
    } as any);
    renderWithRouter(<FirstRunChecklist orgId={ORG} report={report} />);

    await waitFor(() => {
      expect(screen.getByTestId('first-run-progress')).toHaveTextContent('2 of 3 done');
    });
    expect(screen.getByTestId('first-run-item-verdict')).toHaveAttribute('data-done', 'true');
    expect(screen.getByTestId('first-run-item-report')).toHaveAttribute('data-done', 'false');
  });

  it('copies the plain-English IT note (read-only, nothing installed) to the clipboard', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(connectors(0));
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });

    renderWithRouter(<FirstRunChecklist orgId={ORG} report={null} />);

    const copyBtn = await screen.findByTestId('copy-it-instructions');
    expect(copyBtn).toHaveTextContent(/i'm not the admin/i);
    fireEvent.click(copyBtn);

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(IT_HANDOFF_NOTE));
    expect(IT_HANDOFF_NOTE).toMatch(/read-only/i);
    expect(IT_HANDOFF_NOTE).toMatch(/does not install any software/i);
    expect(await screen.findByText(/copied\. paste it into an email/i)).toBeInTheDocument();
  });

  it('collapses and expands, and remembers dismissal per organisation', async () => {
    vi.mocked(api.getConnectorsList).mockResolvedValue(connectors(0));
    const { unmount } = renderWithRouter(<FirstRunChecklist orgId={ORG} report={null} />);

    await screen.findByTestId('first-run-progress');
    const toggle = screen.getByRole('button', { name: /^first steps/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByTestId('first-run-item-connect')).not.toBeInTheDocument();
    fireEvent.click(toggle);
    expect(screen.getByTestId('first-run-item-connect')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /hide first steps/i }));
    expect(screen.queryByTestId('first-run-checklist')).not.toBeInTheDocument();
    expect(localStorage.getItem(`resilai_first_run_dismissed_${ORG}`)).toBe('true');
    unmount();

    // Same org stays hidden; a different org still sees it.
    renderWithRouter(<FirstRunChecklist orgId={ORG} report={null} />);
    expect(screen.queryByTestId('first-run-checklist')).not.toBeInTheDocument();
    renderWithRouter(<FirstRunChecklist orgId="org-other-002" report={null} />);
    expect(await screen.findByTestId('first-run-checklist')).toBeInTheDocument();
  });

  it('never renders for a demo workspace and does not call the connectors API', () => {
    renderWithRouter(<FirstRunChecklist orgId="demo-health-org" report={null} isDemo />);
    expect(screen.queryByTestId('first-run-checklist')).not.toBeInTheDocument();
    expect(api.getConnectorsList).not.toHaveBeenCalled();
  });
});
