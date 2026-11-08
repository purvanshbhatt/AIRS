import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Onboarding from '../pages/Onboarding';
import NewOrg from '../pages/NewOrg';
import * as api from '../api';
import * as useAuthHook from '../contexts/AuthContext';
import { renderWithRouter } from './utils/test-helpers';

vi.mock('../api');
vi.mock('../contexts/AuthContext');

const refreshAuth = vi.fn().mockResolvedValue(undefined);

function mockAuth(overrides: Record<string, unknown> = {}) {
  vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
    user: { uid: 'user-new-001', email: 'owner@riverside.example', displayName: 'Owner', photoURL: null },
    loading: false,
    error: null,
    isConfigured: true,
    hasOrganizations: false,
    getToken: vi.fn().mockResolvedValue('token'),
    signInWithGoogle: vi.fn(),
    signInWithEmail: vi.fn(),
    signUpWithEmail: vi.fn(),
    signInAsDemo: vi.fn(),
    signOut: vi.fn(),
    clearError: vi.fn(),
    refreshAuth,
    ...overrides,
  } as any);
}

function renderOnboarding(initialEntry = '/onboarding') {
  return renderWithRouter(
    <Routes>
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/new-org" element={<NewOrg />} />
      <Route path="/morning-brief" element={<div data-testid="morning-brief-page">Morning brief</div>} />
      <Route path="/demo" element={<div data-testid="demo-page">Demo</div>} />
    </Routes>,
    { initialEntries: [initialEntry] }
  );
}

describe('One-screen onboarding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockAuth();
    vi.mocked(api.getOrganizations).mockResolvedValue([]);
    vi.mocked(api.createOrganization).mockResolvedValue({ id: 'org-riverside', name: 'Riverside Family Practice' } as any);
  });

  it('renders a single screen: name, two industry cards, "More", one primary button, example link', async () => {
    renderOnboarding();

    expect(await screen.findByTestId('create-workspace-screen')).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation name/i)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /healthcare clinic/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /legal practice/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /more \(optional\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create my workspace/i })).toBeDisabled();
    expect(screen.getByRole('link', { name: /just show me an example/i })).toHaveAttribute('href', '/demo');

    // No wizard chrome left behind.
    expect(screen.queryByText(/step 1 of 6/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /continue to step/i })).not.toBeInTheDocument();
    // Team size is collapsed until "More" is opened.
    expect(screen.queryByLabelText(/team size/i)).not.toBeInTheDocument();
  });

  it('creates the organisation with healthcare by default, stores the org id and lands on the morning brief', async () => {
    const user = userEvent.setup();
    renderOnboarding();

    const nameInput = await screen.findByLabelText(/organisation name/i);
    await user.type(nameInput, '  Riverside Family Practice  ');
    await user.click(screen.getByRole('button', { name: /create my workspace/i }));

    await waitFor(() => {
      expect(api.createOrganization).toHaveBeenCalledWith({
        name: 'Riverside Family Practice',
        industry: 'healthcare',
        size: '1-50',
      });
    });
    expect(refreshAuth).toHaveBeenCalled();
    expect(localStorage.getItem('resilai_selected_org_id')).toBe('org-riverside');
    expect(localStorage.getItem('resilai_operating_profile')).toBe('healthcare');
    expect(await screen.findByTestId('morning-brief-page')).toBeInTheDocument();
  });

  it('industry cards set the value: Legal practice sends industry "legal"', async () => {
    const user = userEvent.setup();
    renderOnboarding();

    await user.type(await screen.findByLabelText(/organisation name/i), 'Northstar & Cole LLP');
    const legal = screen.getByRole('radio', { name: /legal practice/i });
    await user.click(legal);
    expect(legal).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: /healthcare clinic/i })).toHaveAttribute('aria-checked', 'false');

    await user.click(screen.getByRole('button', { name: /create my workspace/i }));
    await waitFor(() => {
      expect(api.createOrganization).toHaveBeenCalledWith(expect.objectContaining({ industry: 'legal' }));
    });
  });

  it('the small "Other" link maps to industry "general" and team size under "More" is sent', async () => {
    const user = userEvent.setup();
    renderOnboarding();

    await user.type(await screen.findByLabelText(/organisation name/i), 'Acme Accounting');
    await user.click(screen.getByTestId('industry-other-link'));
    expect(screen.getByTestId('industry-other-selected')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /healthcare clinic/i })).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByRole('radio', { name: /legal practice/i })).toHaveAttribute('aria-checked', 'false');

    await user.click(screen.getByRole('button', { name: /more \(optional\)/i }));
    await user.selectOptions(screen.getByLabelText(/team size/i), '51-200');

    await user.click(screen.getByRole('button', { name: /create my workspace/i }));
    await waitFor(() => {
      expect(api.createOrganization).toHaveBeenCalledWith({ name: 'Acme Accounting', industry: 'general', size: '51-200' });
    });
  });

  it('whitespace-only name keeps the primary button disabled and never calls the API', async () => {
    const user = userEvent.setup();
    renderOnboarding();

    await user.type(await screen.findByLabelText(/organisation name/i), '     ');
    expect(screen.getByRole('button', { name: /create my workspace/i })).toBeDisabled();
    expect(api.createOrganization).not.toHaveBeenCalled();
  });

  it('shows the API error in plain words and stays on the screen', async () => {
    const user = userEvent.setup();
    vi.mocked(api.createOrganization).mockRejectedValue(new Error('Name already taken'));
    renderOnboarding();

    await user.type(await screen.findByLabelText(/organisation name/i), 'Dup Clinic');
    await user.click(screen.getByRole('button', { name: /create my workspace/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Name already taken');
    expect(screen.getByTestId('create-workspace-screen')).toBeInTheDocument();
    expect(screen.queryByTestId('morning-brief-page')).not.toBeInTheDocument();
  });

  it('a user who already has a workspace is sent to the morning brief', async () => {
    vi.mocked(api.getOrganizations).mockResolvedValue([{ id: 'org-existing', name: 'Existing Clinic' } as any]);
    renderOnboarding();

    expect(await screen.findByTestId('morning-brief-page')).toBeInTheDocument();
    expect(localStorage.getItem('resilai_selected_org_id')).toBe('org-existing');
    expect(screen.queryByTestId('create-workspace-screen')).not.toBeInTheDocument();
  });

  it('?new=true keeps the screen for an additional workspace even when one exists', async () => {
    vi.mocked(api.getOrganizations).mockResolvedValue([{ id: 'org-existing', name: 'Existing Clinic' } as any]);
    renderOnboarding('/onboarding?new=true');

    expect(await screen.findByTestId('create-workspace-screen')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /add another workspace/i })).toBeInTheDocument();
    expect(api.getOrganizations).not.toHaveBeenCalled();
    expect(screen.queryByRole('link', { name: /just show me an example/i })).not.toBeInTheDocument();
  });

  it('/new-org renders the same one-screen component and creates the org', async () => {
    const user = userEvent.setup();
    renderOnboarding('/new-org');

    expect(await screen.findByTestId('create-workspace-screen')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /add another workspace/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /healthcare clinic/i })).toBeInTheDocument();

    await user.type(screen.getByLabelText(/organisation name/i), 'Second Site');
    await user.click(screen.getByRole('button', { name: /create my workspace/i }));

    await waitFor(() => {
      expect(api.createOrganization).toHaveBeenCalledWith(expect.objectContaining({ name: 'Second Site' }));
    });
    expect(await screen.findByTestId('morning-brief-page')).toBeInTheDocument();
  });
});
