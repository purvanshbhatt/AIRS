import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { GettingStartedModal } from '../../components/onboarding/GettingStartedModal';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import {
  FIRST_RUN_COPY,
  INDUSTRY_CARDS,
  getOnboardingCompleted,
  setOnboardingCompleted,
  getOnboardingStep,
  setOnboardingStep,
} from '../../components/onboarding/onboardingData';

// Mock active org hook
vi.mock('../../hooks/useActiveOrg', () => ({
  useActiveOrg: () => ({
    orgId: 'demo-health-org',
    orgName: 'Acme Health Systems',
    isDemo: true,
    hasOrg: true,
    loading: false,
    orgs: [{ id: 'demo-health-org', name: 'Acme Health Systems' }],
    selectOrg: vi.fn(),
    resetOrg: vi.fn(),
    refresh: vi.fn(),
  }),
}));

describe('Milestone 2: Onboarding helpers, first-steps modal and demo guidance', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('LocalStorage Persistence Helpers', () => {
    it('saves and retrieves onboarding completion state per organization', () => {
      expect(getOnboardingCompleted('org-123')).toBe(false);
      setOnboardingCompleted('org-123', true);
      expect(getOnboardingCompleted('org-123')).toBe(true);
      expect(getOnboardingCompleted('other-org')).toBe(true); // global fallback
    });

    it('saves and retrieves onboarding step per organization', () => {
      expect(getOnboardingStep('org-123')).toBe(1);
      setOnboardingStep('org-123', 4);
      expect(getOnboardingStep('org-123')).toBe(4);
    });
  });

  describe('Onboarding copy', () => {
    it('offers exactly two industry cards that map to API values', () => {
      expect(INDUSTRY_CARDS.map((c) => c.id)).toEqual(['healthcare', 'legal']);
      expect(INDUSTRY_CARDS.map((c) => c.title)).toEqual(['Healthcare clinic', 'Legal practice']);
    });

    it('first-run captions point at connectors, the brief and the report', () => {
      expect(FIRST_RUN_COPY.connect.href).toBe('/connectors');
      expect(FIRST_RUN_COPY.verdict.href).toBe('/morning-brief');
      expect(FIRST_RUN_COPY.report.href).toBe('/reports');
    });
  });

  describe('GettingStartedModal', () => {
    it('renders the three first steps when open and closes from the Close button', () => {
      const handleClose = vi.fn();
      render(
        <MemoryRouter>
          <GettingStartedModal isOpen={true} onClose={handleClose} orgId="demo-health-org" orgName="Acme Health Systems" />
        </MemoryRouter>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Getting started with ResilAI')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /connect where your email and files live/i })).toHaveAttribute('href', '/connectors');
      expect(screen.getByRole('link', { name: /get your first monday verdict/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /download your 1-page boss report/i })).toHaveAttribute('href', '/reports');

      fireEvent.click(screen.getByRole('button', { name: /^close$/i }));
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('renders nothing when closed', () => {
      render(
        <MemoryRouter>
          <GettingStartedModal isOpen={false} onClose={vi.fn()} />
        </MemoryRouter>
      );
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('ContextualDemoBanner', () => {
    it('renders amber simulated data warning and section-specific guidance', () => {
      render(
        <MemoryRouter>
          <ContextualDemoBanner section="today" />
        </MemoryRouter>
      );

      expect(screen.getByText(/DEMO ENVIRONMENT \(SIMULATED DATA\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Acme Health Systems — Illustrative Executive Briefing/i)).toBeInTheDocument();
      expect(screen.getByText(/Notice: No LLM hallucinates scores/i)).toBeInTheDocument();
    });
  });
});
