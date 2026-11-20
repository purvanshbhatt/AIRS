import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { AIActInventory } from '../components/technology/AIActInventory';
import AIPage from '../pages/technology/AIPage';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../hooks/useActiveOrg');

/**
 * EU AI Act inventory. The page shows only what the server returns: it never
 * works out a risk class itself, never shows a class before a system is
 * recorded, and labels a duty status as the owner's own statement.
 */

const ORG = 'org-live-001';

const QUESTIONNAIRE = {
  regulation: 'Regulation (EU) 2024/1689',
  scope_note: 'The Act applies if you are in the EU, or if what the system produces is used in the EU.',
  roles: [
    { key: 'deployer', text: 'We use a system that someone else built' },
    { key: 'provider', text: 'We built it, or we supply it under our own name' },
  ],
  sections: [
    { id: 'prohibited', title: 'Banned practices', article: 'Article 5', help: 'Tick any.', options: [
      { key: 'social_scoring', article: 'Article 5(1)(c)', text: 'It scores people on their social behaviour' },
    ] },
    { id: 'high_risk', title: 'High-risk uses', article: 'Article 6 and Annex III', help: 'Tick any.', options: [
      { key: 'employment', article: 'Annex III(4)', text: 'Recruits or screens job applicants' },
    ] },
    { id: 'transparency', title: 'Transparency', article: 'Article 50', help: 'Tick any.', options: [
      { key: 'talks_to_people', article: 'Article 50(1)', text: 'People interact with it directly' },
    ] },
  ],
  statuses: ['not_answered', 'in_place', 'not_in_place'],
  disclaimer: 'First classification from your own answers. This is not legal advice.',
} as any;

function system(overrides: Record<string, unknown> = {}) {
  return {
    id: 'sys-1',
    org_id: ORG,
    name: 'Hiring Screener',
    purpose: 'Ranks job applicants.',
    vendor: 'Example Vendor',
    role: 'deployer',
    answers: { employment: true },
    risk_class: 'high',
    risk_label: 'High-risk',
    basis: [{ article: 'Annex III(4)', text: 'Recruits or screens job applicants' }],
    obligations: [
      { id: 'keep_logs', article: 'Article 26(6)', title: 'Keep the logs', detail: 'Keep the logs for at least six months.', duty_of: 'you', status: 'not_answered' },
      { id: 'tell_users_ai', article: 'Article 50(1)', title: 'Say it is an AI', detail: 'This is your supplier\'s duty.', duty_of: 'supplier', status: 'not_answered' },
    ],
    exception_note: null,
    disclaimer: QUESTIONNAIRE.disclaimer,
    created_at: '2026-11-16T09:00:00Z',
    updated_at: null,
    ...overrides,
  } as any;
}

function mockOrg(isDemo = false) {
  vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
    orgId: isDemo ? 'demo-health-org' : ORG,
    orgName: 'Small Clinic',
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

function list(systems: unknown[]) {
  return { org_id: ORG, systems, total: systems.length, by_risk_class: {}, disclaimer: QUESTIONNAIRE.disclaimer } as any;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockOrg();
  vi.mocked(api.getAIActQuestionnaire).mockResolvedValue(QUESTIONNAIRE);
  vi.mocked(api.listAIActSystems).mockResolvedValue(list([]));
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('EU AI Act inventory', () => {
  it('shows no class and no duties before any system is recorded', async () => {
    renderWithRouter(<AIActInventory />);

    await waitFor(() => expect(screen.getByTestId('ai-act-empty')).toBeInTheDocument());
    expect(api.listAIActSystems).toHaveBeenCalledWith(ORG);
    expect(screen.getByTestId('ai-act-disclaimer')).toHaveTextContent('not legal advice');
    expect(screen.queryByText(/High-risk$/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('ai-act-systems')).not.toBeInTheDocument();
  });

  it('shows the class, the reasons and the duties the server returned', async () => {
    vi.mocked(api.listAIActSystems).mockResolvedValue(list([system()]));

    renderWithRouter(<AIActInventory />);

    await waitFor(() => expect(screen.getByTestId('ai-act-risk-sys-1')).toHaveTextContent('High-risk'));
    expect(screen.getByText('Hiring Screener')).toBeInTheDocument();
    expect(screen.getByText(/Annex III\(4\)/)).toBeInTheDocument();
    expect(screen.getByText('Keep the logs')).toBeInTheDocument();
    expect(screen.getByText("Supplier's duty")).toBeInTheDocument();
    expect(screen.getByText(/your own statement. ResilAI has not verified it/i)).toBeInTheDocument();
    expect(screen.queryByTestId('ai-act-empty')).not.toBeInTheDocument();
  });

  it('sends the answers to the server and shows the class it returns', async () => {
    vi.mocked(api.createAIActSystem).mockResolvedValue(system({ id: 'sys-2', name: 'Front Desk Bot', risk_class: 'limited', risk_label: 'Limited risk: transparency duties', basis: [], obligations: [] }));
    renderWithRouter(<AIActInventory />);
    await waitFor(() => screen.getByRole('button', { name: /Add an AI system/ }));

    fireEvent.click(screen.getByRole('button', { name: /Add an AI system/ }));
    const form = screen.getByRole('form', { name: 'Add an AI system' });
    fireEvent.change(within(form).getByLabelText('Name'), { target: { value: 'Front Desk Bot' } });
    fireEvent.change(within(form).getByLabelText('What it is used for'), { target: { value: 'Answers booking questions.' } });
    fireEvent.click(within(form).getByLabelText('People interact with it directly'));
    fireEvent.click(within(form).getByRole('button', { name: 'Save and classify' }));

    await waitFor(() => {
      expect(api.createAIActSystem).toHaveBeenCalledWith(ORG, {
        name: 'Front Desk Bot',
        purpose: 'Answers booking questions.',
        vendor: null,
        role: 'deployer',
        answers: { talks_to_people: true },
      });
    });
    await waitFor(() => expect(screen.getByTestId('ai-act-risk-sys-2')).toHaveTextContent('Limited risk'));
    expect(screen.queryByRole('form', { name: 'Add an AI system' })).not.toBeInTheDocument();
  });

  it('cannot save without a name and a purpose', async () => {
    renderWithRouter(<AIActInventory />);
    await waitFor(() => screen.getByRole('button', { name: /Add an AI system/ }));
    fireEvent.click(screen.getByRole('button', { name: /Add an AI system/ }));

    expect(screen.getByRole('button', { name: 'Save and classify' })).toBeDisabled();
    expect(api.createAIActSystem).not.toHaveBeenCalled();
  });

  it('keeps the form open and says so when the save fails', async () => {
    vi.mocked(api.createAIActSystem).mockRejectedValue(new Error('Service unavailable'));
    renderWithRouter(<AIActInventory />);
    await waitFor(() => screen.getByRole('button', { name: /Add an AI system/ }));
    fireEvent.click(screen.getByRole('button', { name: /Add an AI system/ }));
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Tool' } });
    fireEvent.change(screen.getByLabelText('What it is used for'), { target: { value: 'Something.' } });

    fireEvent.click(screen.getByRole('button', { name: 'Save and classify' }));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Service unavailable'));
    expect(screen.getByRole('form', { name: 'Add an AI system' })).toBeInTheDocument();
    expect(screen.queryByTestId('ai-act-systems')).not.toBeInTheDocument();
  });

  it("records the owner's statement for a duty and shows what the server stored", async () => {
    vi.mocked(api.listAIActSystems).mockResolvedValue(list([system()]));
    const stored = system();
    stored.obligations[0].status = 'in_place';
    vi.mocked(api.setAIActDutyStatus).mockResolvedValue(stored);
    renderWithRouter(<AIActInventory />);
    const select = await waitFor(() => screen.getByLabelText('Keep the logs: your statement for Hiring Screener'));

    fireEvent.change(select, { target: { value: 'in_place' } });

    await waitFor(() => expect(api.setAIActDutyStatus).toHaveBeenCalledWith(ORG, 'sys-1', 'keep_logs', 'in_place'));
    await waitFor(() => {
      expect(screen.getByLabelText('Keep the logs: your statement for Hiring Screener')).toHaveValue('in_place');
    });
  });

  it('removes a system only after the owner confirms', async () => {
    vi.mocked(api.listAIActSystems).mockResolvedValue(list([system()]));
    vi.mocked(api.deleteAIActSystem).mockResolvedValue({ status: 'deleted', id: 'sys-1' } as any);
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderWithRouter(<AIActInventory />);
    const remove = await waitFor(() => screen.getByRole('button', { name: 'Remove Hiring Screener' }));

    fireEvent.click(remove);
    expect(api.deleteAIActSystem).not.toHaveBeenCalled();
    expect(screen.getByText('Hiring Screener')).toBeInTheDocument();

    confirm.mockReturnValue(true);
    fireEvent.click(remove);
    await waitFor(() => expect(api.deleteAIActSystem).toHaveBeenCalledWith(ORG, 'sys-1'));
    await waitFor(() => expect(screen.queryByText('Hiring Screener')).not.toBeInTheDocument());
  });

  it('shows an error, not an empty inventory claim, when loading fails', async () => {
    vi.mocked(api.listAIActSystems).mockRejectedValue(new Error('Network down'));

    renderWithRouter(<AIActInventory />);

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Network down'));
    expect(screen.queryByRole('button', { name: /Add an AI system/ })).not.toBeInTheDocument();
  });
});

describe('AI page', () => {
  it('shows the inventory to a real organisation', async () => {
    vi.mocked(api.getDailyReadinessReport).mockResolvedValue({ failed_checks: [], warnings: [], passed_checks: [] } as any);

    renderWithRouter(<AIPage />);

    await waitFor(() => expect(screen.getByTestId('ai-act-inventory')).toBeInTheDocument());
  });

  it('does not show it in the demo workspace, and asks the server nothing', () => {
    mockOrg(true);

    renderWithRouter(<AIPage />);

    expect(screen.queryByTestId('ai-act-inventory')).not.toBeInTheDocument();
    expect(api.listAIActSystems).not.toHaveBeenCalled();
  });
});
