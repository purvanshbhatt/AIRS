import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import React from 'react';
import * as api from '../api';
import * as useActiveOrgIdHook from '../hooks/useActiveOrgId';
import { InsuranceAnswerPackPage } from '../pages/questionnaires/InsuranceAnswerPackPage';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrgId');

const GENERATED = '2026-11-11T12:00:00+00:00';

function answer(partial: Partial<api.QuestionnaireAnswer> & Pick<api.QuestionnaireAnswer, 'id' | 'topic' | 'value'>): api.QuestionnaireAnswer {
  const labels: Record<api.QuestionnaireAnswerValue, string> = {
    yes: 'Yes',
    no: 'No',
    partial: 'Partly',
    not_verified: 'Not verified: answer manually',
    human_only: 'You answer this',
  };
  return {
    topic_label: partial.topic,
    question: `Question ${partial.id}?`,
    help: null,
    mode: partial.value === 'human_only' ? 'human' : 'telemetry',
    value_label: labels[partial.value],
    basis: `Basis for ${partial.id}.`,
    evidence_source: null,
    evidence_time: null,
    evidence: [],
    coverage: { checked: [], not_checked: [] },
    ...partial,
  } as api.QuestionnaireAnswer;
}

function makePack(overrides: Partial<api.InsuranceAnswerPack> = {}): api.InsuranceAnswerPack {
  const answers = [
    answer({
      id: 'EMAIL_MFA',
      topic: 'identity',
      value: 'partial',
      basis: 'Microsoft 365 reports multi-factor sign-in enforced for 1 of 2 switched-on accounts.',
      evidence_source: 'Microsoft 365',
      evidence_time: GENERATED,
      evidence: [{ source: 'microsoft', source_label: 'Microsoft 365', observed_at: GENERATED }],
      coverage: { checked: ['Microsoft 365: 2 switched-on user accounts'], not_checked: ['Email accounts that are not in Microsoft 365'] },
    }),
    answer({
      id: 'BACKUP_DAILY',
      topic: 'backups',
      value: 'not_verified',
      basis: 'The Veeam Backup connection is failing (401), so its data was not used. Answer this question yourself.',
    }),
    answer({ id: 'DEVICE_ENCRYPTION', topic: 'encryption', value: 'yes', evidence_source: 'Microsoft 365', evidence_time: GENERATED }),
    answer({ id: 'IR_PLAN', topic: 'incident_response', value: 'human_only' }),
  ];
  return {
    questionnaire: { id: 'cyber_insurance_small_business', title: 'Cyber insurance application', version: '2026.11.1' },
    organization: { id: 'org-1', name: 'Test Clinic', is_demo: false },
    is_demo: false,
    data_label: 'Live data',
    generated_at: GENERATED,
    evidence_max_age_hours: 48,
    notice: 'You attest. ResilAI shows the evidence it has, as of 11 Nov 2026, 12:00 UTC.',
    attestation: { statement: 'ResilAI does not submit this application.', submitted_by_resilai: false },
    summary: {
      total: 4,
      counts: { yes: 1, no: 0, partial: 1, not_verified: 1, human_only: 1 },
      from_evidence: 2,
      generated_at: GENERATED,
      question_bank_version: '2026.11.1',
    },
    topics: [
      { id: 'identity', label: 'Email, accounts and sign-in' },
      { id: 'backups', label: 'Backups and recovery' },
      { id: 'encryption', label: 'Encryption' },
      { id: 'incident_response', label: 'Incident response' },
    ],
    sources: [
      { source: 'microsoft', label: 'Microsoft 365', state: 'fresh', reason: null, as_of: GENERATED },
      { source: 'veeam', label: 'Veeam Backup', state: 'failed', reason: 'The Veeam Backup connection is failing.', as_of: null },
    ],
    answers,
    ...overrides,
  };
}

describe('InsuranceAnswerPackPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(useActiveOrgIdHook.useActiveOrgId).mockReturnValue('org-1');
  });

  it('lists answers grouped by topic with their evidence line and the attestation notice', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(makePack());
    renderWithRouter(<InsuranceAnswerPackPage />);

    expect(await screen.findByTestId('attestation-notice')).toHaveTextContent(
      'You attest. ResilAI shows the evidence it has, as of 11 Nov 2026, 12:00 UTC.',
    );
    expect(api.getInsuranceAnswerPack).toHaveBeenCalledWith('org-1');
    expect(screen.getByRole('heading', { name: 'Email, accounts and sign-in' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Incident response' })).toBeInTheDocument();

    const mfa = screen.getByTestId('answer-EMAIL_MFA');
    expect(within(mfa).getByText('Partly')).toBeInTheDocument();
    expect(within(mfa).getByTestId('evidence-EMAIL_MFA')).toHaveTextContent('Evidence: Microsoft 365, as of');
    expect(within(mfa).getByText(/Looked at:/)).toBeInTheDocument();

    const backup = screen.getByTestId('answer-BACKUP_DAILY');
    expect(within(backup).getByText('Not verified: answer manually')).toBeInTheDocument();
    expect(within(backup).getByTestId('evidence-BACKUP_DAILY')).toHaveTextContent('No evidence used');

    const plan = screen.getByTestId('answer-IR_PLAN');
    expect(within(plan).getByText('You answer this')).toBeInTheDocument();

    expect(screen.getByTestId('data-label')).toHaveTextContent('Live data');
    expect(screen.queryByText(/sample workspace/i)).not.toBeInTheDocument();
  });

  it('filters by answer value', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(makePack());
    renderWithRouter(<InsuranceAnswerPackPage />);
    await screen.findByTestId('answer-EMAIL_MFA');

    fireEvent.click(screen.getByRole('button', { name: /Not verified/ }));
    expect(screen.getByTestId('answer-BACKUP_DAILY')).toBeInTheDocument();
    expect(screen.queryByTestId('answer-EMAIL_MFA')).not.toBeInTheDocument();
    expect(screen.queryByTestId('answer-IR_PLAN')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Not verified/ })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: /You answer/ }));
    expect(screen.getByTestId('answer-IR_PLAN')).toBeInTheDocument();
    expect(screen.queryByTestId('answer-BACKUP_DAILY')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^No\s*\d+$/ }));
    expect(screen.getByText('No answers match this filter.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^All/ }));
    expect(screen.getAllByTestId(/^answer-/)).toHaveLength(4);
  });

  it('labels demo workspaces as sample data', async () => {
    vi.mocked(useActiveOrgIdHook.useActiveOrgId).mockReturnValue('demo-health-org');
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(
      makePack({
        is_demo: true,
        data_label: 'Sample data',
        organization: { id: 'demo-health-org', name: 'Health Org (Demo)', is_demo: true },
      }),
    );
    renderWithRouter(<InsuranceAnswerPackPage />);
    expect(await screen.findByTestId('data-label')).toHaveTextContent('Sample data');
    expect(screen.getByText(/This is a sample workspace/)).toBeInTheDocument();
  });

  it('downloads the PDF', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(makePack());
    vi.mocked(api.downloadInsuranceAnswerPackPdf).mockResolvedValue(new Blob(['%PDF'], { type: 'application/pdf' }));
    const createUrl = vi.fn(() => 'blob:pack');
    const revokeUrl = vi.fn();
    Object.assign(URL, { createObjectURL: createUrl, revokeObjectURL: revokeUrl });
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    renderWithRouter(<InsuranceAnswerPackPage />);
    await screen.findByTestId('answer-EMAIL_MFA');
    fireEvent.click(screen.getByRole('button', { name: /Download PDF/ }));

    await waitFor(() => expect(api.downloadInsuranceAnswerPackPdf).toHaveBeenCalledWith('org-1'));
    await waitFor(() => expect(click).toHaveBeenCalled());
    expect(createUrl).toHaveBeenCalled();
    click.mockRestore();
  });

  it('shows the error when a download fails', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(makePack());
    vi.mocked(api.downloadInsuranceAnswerPackPdf).mockRejectedValue(new Error('Could not build the answer pack PDF.'));
    renderWithRouter(<InsuranceAnswerPackPage />);
    await screen.findByTestId('answer-EMAIL_MFA');
    fireEvent.click(screen.getByRole('button', { name: /Download PDF/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not build the answer pack PDF.');
  });

  it('points to Connectors when nothing is connected', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockResolvedValue(makePack({ sources: [] }));
    renderWithRouter(<InsuranceAnswerPackPage />);
    expect(await screen.findByRole('link', { name: /Connect a system/ })).toHaveAttribute('href', '/connectors');
  });

  it('reports a failed load', async () => {
    vi.mocked(api.getInsuranceAnswerPack).mockRejectedValue(new Error('Organization not found'));
    renderWithRouter(<InsuranceAnswerPackPage />);
    expect(await screen.findByText('The answer pack could not be built.')).toBeInTheDocument();
    expect(screen.getByText('Organization not found')).toBeInTheDocument();
  });
});
