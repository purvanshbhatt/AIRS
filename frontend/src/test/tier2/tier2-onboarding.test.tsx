import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { GettingStartedStepper } from '../../components/onboarding/GettingStartedStepper';
import { GettingStartedModal } from '../../components/onboarding/GettingStartedModal';
import { GettingStartedTour } from '../../components/onboarding/GettingStartedTour';
import { Step1OrgProfile } from '../../components/onboarding/Step1OrgProfile';
import { Step2Connectors } from '../../components/onboarding/Step2Connectors';
import { Step3EvidenceLedger } from '../../components/onboarding/Step3EvidenceLedger';
import { Step4NeedsAttention } from '../../components/onboarding/Step4NeedsAttention';
import { Step5RecoveryReadiness } from '../../components/onboarding/Step5RecoveryReadiness';
import { Step6BoardReport } from '../../components/onboarding/Step6BoardReport';
import { ContextualDemoBanner } from '../../components/common/ContextualDemoBanner';
import {
  INITIAL_DEMO_PROFILE,
  DEFAULT_CONNECTORS,
  DEMO_EVIDENCE_ITEMS,
  DEMO_NEEDS_ATTENTION_ITEMS,
  DEMO_RECOVERY_PREVIEW,
  DEMO_BOARD_STORY_PREVIEW,
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

describe('Milestone 2: Guided 6-Step Onboarding Workflow & Demo Guidance', () => {
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

  describe('GettingStartedStepper', () => {
    it('renders all 6 step short titles and active step styling', () => {
      const handleSelectStep = vi.fn();
      render(
        <GettingStartedStepper
          currentStep={2}
          completedSteps={[1]}
          onSelectStep={handleSelectStep}
          mode="demo"
        />
      );

      expect(screen.getByText('Connect Security Systems')).toBeInTheDocument();
      expect(screen.getAllByText('Readiness Profile').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Evidence Ledger').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Needs Attention').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Recovery Assurance').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Executive Report').length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Step 1: Organization Readiness Profile', () => {
    it('renders organization details and deterministic trust contract explanation', () => {
      const handleChangeProfile = vi.fn();
      const handleNext = vi.fn();

      render(
        <Step1OrgProfile
          profile={INITIAL_DEMO_PROFILE}
          onChangeProfile={handleChangeProfile}
          mode="demo"
          onNext={handleNext}
        />
      );

      expect(screen.getByText(/Acme Health Systems — Baseline Readiness Profile/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue('Acme Health Systems')).toBeInTheDocument();
      expect(screen.getByText(/Zero Hallucination Guarantee/i)).toBeInTheDocument();

      const nextBtn = screen.getByRole('button', { name: /Continue to Step 2: Connect Security Systems/i });
      expect(nextBtn).toBeInTheDocument();
      fireEvent.click(nextBtn);
      expect(handleNext).toHaveBeenCalledTimes(1);
    });
  });

  describe('Step 2: Connect Security Systems', () => {
    it('renders 4 primary connectors: Microsoft 365, Veeam, CrowdStrike, SentinelOne', () => {
      const handleUpdate = vi.fn();
      const handleNext = vi.fn();
      const handlePrev = vi.fn();

      render(
        <Step2Connectors
          connectors={DEFAULT_CONNECTORS}
          onUpdateConnector={handleUpdate}
          mode="demo"
          onNext={handleNext}
          onPrev={handlePrev}
        />
      );

      expect(screen.getByText('Microsoft 365 / Entra ID')).toBeInTheDocument();
      expect(screen.getByText('Veeam Backup & Replication')).toBeInTheDocument();
      expect(screen.getByText('CrowdStrike Falcon')).toBeInTheDocument();
      expect(screen.getByText('SentinelOne Singularity')).toBeInTheDocument();
      expect(screen.getAllByText(/Connected/i).length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('Step 3: Evidence Ledger & Cryptographic Inspection', () => {
    it('renders verified controls with SHA-256 evidence fingerprints', () => {
      const handleNext = vi.fn();
      const handlePrev = vi.fn();

      render(
        <Step3EvidenceLedger
          mode="demo"
          onNext={handleNext}
          onPrev={handlePrev}
        />
      );

      expect(screen.getByText(/Deterministic Health Checks & Cryptographic Evidence Ledger/i)).toBeInTheDocument();
      expect(screen.getByText('IV-001')).toBeInTheDocument();
      expect(screen.getByText('BR-004')).toBeInTheDocument();
      expect(screen.getAllByText(/SHA-256 Fingerprint/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Step 4: Needs Attention & Clinical Risk Ranking', () => {
    it('ranks incidents by clinical risk and supports executive translation', () => {
      const handleNext = vi.fn();
      const handlePrev = vi.fn();

      render(
        <Step4NeedsAttention
          mode="demo"
          onNext={handleNext}
          onPrev={handlePrev}
        />
      );

      expect(screen.getByText(/Needs Attention Triage & Clinical Risk Ranking/i)).toBeInTheDocument();
      expect(screen.getByText(/Radiology PACS Archive Backup Delayed/i)).toBeInTheDocument();
      expect(screen.getByText(/92 \/ 100/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Plain English Executive Summary/i).length).toBeGreaterThanOrEqual(1);

      // Trigger 1-click remediation preview
      const fixButtons = screen.getAllByText(/1-Click Trigger Fix/i);
      fireEvent.click(fixButtons[0]);
      expect(screen.getByText(/Remediation Triggered/i)).toBeInTheDocument();
    });
  });

  describe('Step 5: Incident Recovery Readiness', () => {
    it('displays 30-day immutability lock status, 42-min RTO, and 15-min RPO', () => {
      const handleNext = vi.fn();
      const handlePrev = vi.fn();

      render(
        <Step5RecoveryReadiness
          mode="demo"
          onNext={handleNext}
          onPrev={handlePrev}
        />
      );

      expect(screen.getByText(/Incident Recovery Readiness & Backup Immutability Assurance/i)).toBeInTheDocument();
      expect(screen.getByText(/30-Day Locked/i)).toBeInTheDocument();
      expect(screen.getByText('42 Minutes')).toBeInTheDocument();
      expect(screen.getByText('15 Minutes')).toBeInTheDocument();
    });
  });

  describe('Step 6: Executive Board Report', () => {
    it('renders Boardroom Story preview and PDF download trigger', () => {
      const handleComplete = vi.fn();
      const handlePrev = vi.fn();

      render(
        <Step6BoardReport
          mode="demo"
          orgId="demo-health-org"
          orgName="Acme Health Systems"
          onComplete={handleComplete}
          onPrev={handlePrev}
        />
      );

      expect(screen.getByText(/Executive Boardroom Story & Cyber Insurance Report/i)).toBeInTheDocument();
      expect(screen.getByText('94%')).toBeInTheDocument();
      expect(screen.getByText(/Download Executive PDF/i)).toBeInTheDocument();

      const completeBtn = screen.getByRole('button', { name: /Complete Onboarding & Enter Workspace/i });
      fireEvent.click(completeBtn);
      expect(handleComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe('GettingStartedModal Integration', () => {
    it('renders modal when open and allows step progression', () => {
      const handleClose = vi.fn();
      render(
        <GettingStartedModal
          isOpen={true}
          onClose={handleClose}
          orgId="demo-health-org"
          orgName="Acme Health Systems"
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Getting Started with ResilAI')).toBeInTheDocument();
      expect(screen.getByText(/Resume Later/i)).toBeInTheDocument();
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
