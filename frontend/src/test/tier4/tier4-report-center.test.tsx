import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import Reports from '../../pages/Reports';
import * as api from '../../api';
import * as useAuthHook from '../../contexts/AuthContext';
import * as useActiveOrgHook from '../../hooks/useActiveOrg';
import * as useActiveOrgIdHook from '../../hooks/useActiveOrgId';
import { renderWithRouter, createMockReportList } from '../utils/test-helpers';

vi.mock('../../api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api')>();
  return {
    ...actual,
    getReports: vi.fn(),
    generateReport: vi.fn(),
    downloadReportById: vi.fn(),
    deleteReport: vi.fn(),
    getBoardStory: vi.fn(),
  };
});

describe('Milestone 4: Report Center & History Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(useAuthHook, 'useAuth').mockReturnValue({
      user: {
        uid: 'user-001',
        email: 'doctor@metrohealth.org',
        displayName: 'Dr. Smith',
        photoURL: null,
      },
      loading: false,
      error: null,
      isConfigured: true,
      hasOrganizations: true,
      getToken: vi.fn().mockResolvedValue('token-xyz'),
      signInWithGoogle: vi.fn(),
      signInWithEmail: vi.fn(),
      signUpWithEmail: vi.fn(),
      signInAsDemo: vi.fn(),
      signOut: vi.fn(),
      clearError: vi.fn(),
      refreshAuth: vi.fn(),
    });

    vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
      orgName: 'Metro Health Clinics',
      orgId: 'org-health-123',
      org: null,
      orgs: [],
      isDemo: false,
      hasOrg: true,
      loading: false,
      selectOrg: vi.fn(),
      resetOrg: vi.fn(),
      refresh: vi.fn().mockResolvedValue(undefined),
    });

    vi.spyOn(useActiveOrgIdHook, 'useActiveOrgId').mockReturnValue('org-health-123');
  });

  it('renders Report Center header with active organization and report counts', async () => {
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Reports')).toBeInTheDocument();
    });
    expect(screen.getByText('3 saved reports')).toBeInTheDocument();
    expect(screen.getAllByText('Metro Health Clinics')[0]).toBeInTheDocument();
  });

  it('renders executive report templates in on-demand generation panel', async () => {
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Generate Executive Readiness Briefing')).toBeInTheDocument();
    });

    expect(screen.getByText('Boardroom Cyber Resilience Briefing')).toBeInTheDocument();
    expect(screen.getByText('Monthly Operations Health Review')).toBeInTheDocument();
    expect(screen.getByText('HIPAA Safeguards Verification Dossier')).toBeInTheDocument();
    expect(screen.getByText('Cryptographic Telemetry Ledger Export')).toBeInTheDocument();
  });

  it('triggers on-demand report generation and updates history list', async () => {
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);
    vi.mocked(api.generateReport).mockResolvedValue({
      id: 'rep-new-999',
      status: 'ready',
      progress: 100,
      message: 'Report generated successfully',
      created_at: new Date().toISOString(),
    } as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
    });

    const generateButton = screen.getByRole('button', { name: /generate report/i });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/has been generated and added to your archive/i)).toBeInTheDocument();
    });
  });

  it('filters reports dynamically by search query', async () => {
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
      expect(screen.getByText('Monthly IT Operations Resilience Summary')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search reports...');
    fireEvent.change(searchInput, { target: { value: 'HIPAA' } });

    expect(screen.getByText('HIPAA Safeguards & Backup Verification Package')).toBeInTheDocument();
    expect(screen.queryByText('Monthly IT Operations Resilience Summary')).not.toBeInTheDocument();
  });

  it('renders empty state when no reports are found and allows quick generation', async () => {
    vi.mocked(api.getReports).mockResolvedValue({ reports: [], total: 0 } as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('No saved reports yet')).toBeInTheDocument();
    });
    expect(screen.getByText('0 saved reports')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate Board Report' })).toBeInTheDocument();
  });

  it('contains zero legacy assessment wording across the UI', async () => {
    const mockList = createMockReportList();
    vi.mocked(api.getReports).mockResolvedValue(mockList as any);

    renderWithRouter(<Reports />);

    await waitFor(() => {
      expect(screen.getByText('Executive Boardroom Readiness Story')).toBeInTheDocument();
    });

    // Verify absence of legacy strings
    expect(screen.queryByText(/Complete an assessment and save/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Start Assessment/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Need to run another assessment/i)).not.toBeInTheDocument();
  });

  it('generates correct board story PDF url helper', () => {
    const url = api.getBoardStoryPdfUrl('org-health-123');
    expect(url).toContain('/api/v1/reports/board-story.pdf?org_id=org-health-123');
  });
});
