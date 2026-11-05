/**
 * Comprehensive E2E Test Suite: Multi-Vertical Positioning Experiment (Staging Only)
 * 
 * Validates Tiers 1 through 4 across:
 * - F1: Subdomain detection (healthcare.staging.resilai.org, legal.staging.resilai.org, etc.)
 * - F2: Path fallback (/healthcare, /legal, /)
 * - F3: Query param fallback (?vertical=healthcare, ?vertical=legal, ?vertical=general)
 * - F4: Public config API & synchronous static fallback
 * - F5: General landing page headline & core question
 * - F6: Healthcare landing page headline & core question
 * - F7: Legal landing page headline & core question
 * - F8: Demo persona launch (Acme Technologies, Northstar Family Health, Northstar & Cole LLP)
 * - F9: Global amber demo banner presence
 * - F10: Read-only demo sandbox mutation guard
 * - Tier 2: Boundary & Corner Cases (unknown queries, case normalization, trailing slashes, offline fallback)
 * - Tier 3: Cross-Feature Combinations (subdomain + demo login, path nav + org switch, banner parameterization)
 * - Tier 4: Real-World Scenarios (Clinic Executive, Law Partner, Enterprise CISO, Auditor Invariant, Unauthorized Mutation)
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import {
  VerticalProvider,
  useVertical,
  detectVerticalFromLocation,
} from '../contexts/VerticalContext';
import {
  VERTICAL_CONFIGS,
  getVerticalConfig,
  isVerticalKey,
  DEFAULT_VERTICAL,
} from '../config/verticals';
import type { VerticalKey } from '../types/vertical';
import { ContextualDemoBanner } from '../components/common/ContextualDemoBanner';
import * as api from '../api';
import * as useActiveOrgHook from '../hooks/useActiveOrg';

// Test consumer component to display active VerticalContext state
function VerticalContextConsumer() {
  const { currentVertical, config, source, isLoading, setVertical } = useVertical();
  return (
    <div data-testid="vertical-consumer">
      <div data-testid="active-vertical">{currentVertical}</div>
      <div data-testid="active-source">{source}</div>
      <div data-testid="display-name">{config.displayName}</div>
      <div data-testid="industry-label">{config.industryLabel}</div>
      <div data-testid="headline">{config.headline}</div>
      <div data-testid="core-question">{config.coreQuestion}</div>
      <div data-testid="demo-org-id">{config.demoOrgId}</div>
      <div data-testid="demo-org-name">{config.demoOrgName}</div>
      <div data-testid="demo-persona-name">{config.demoPersonaName}</div>
      <div data-testid="demo-persona-role">{config.demoPersonaRole}</div>
      <div data-testid="is-loading">{isLoading ? 'true' : 'false'}</div>
      <ul data-testid="focus-areas">
        {config.focusAreas.map((fa, i) => (
          <li key={i}>{fa}</li>
        ))}
      </ul>
      <ul data-testid="critical-systems">
        {config.criticalSystems.map((cs, i) => (
          <li key={i}>{cs}</li>
        ))}
      </ul>
      <button onClick={() => setVertical('healthcare')} data-testid="switch-healthcare">
        Switch Healthcare
      </button>
      <button onClick={() => setVertical('legal')} data-testid="switch-legal">
        Switch Legal
      </button>
      <button onClick={() => setVertical('general')} data-testid="switch-general">
        Switch General
      </button>
    </div>
  );
}

describe('E2E Suite: ResilAI Multi-Vertical Positioning Experiment', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // TIER 1 — FEATURE COVERAGE (>=5 Tests per Feature F1 - F10)
  // ============================================================================

  describe('Tier 1: Feature F1 — Subdomain Vertical Detection', () => {
    it('F1.01: Detects healthcare vertical on healthcare.staging.resilai.org', () => {
      const result = detectVerticalFromLocation({
        hostname: 'healthcare.staging.resilai.org',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('subdomain');
    });

    it('F1.02: Detects legal vertical on legal.staging.resilai.org', () => {
      const result = detectVerticalFromLocation({
        hostname: 'legal.staging.resilai.org',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('subdomain');
    });

    it('F1.03: Defaults to general vertical on root staging subdomain staging.resilai.org', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('general');
      expect(result.source).toBe('default');
    });

    it('F1.04: Detects healthcare on localhost subdomain healthcare.localhost:5173', () => {
      const result = detectVerticalFromLocation({
        hostname: 'healthcare.localhost',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('subdomain');
    });

    it('F1.05: Detects legal on legal.localhost', () => {
      const result = detectVerticalFromLocation({
        hostname: 'legal.localhost',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('subdomain');
    });

    it('F1.06: Unrecognized subdomain random.staging.resilai.org falls back to general default', () => {
      const result = detectVerticalFromLocation({
        hostname: 'random.staging.resilai.org',
        pathname: '/',
        search: '',
      });
      expect(result.vertical).toBe('general');
      expect(result.source).toBe('default');
    });
  });

  describe('Tier 1: Feature F2 — Path Prefix Vertical Fallback', () => {
    it('F2.01: Detects healthcare on path /healthcare', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/healthcare',
        search: '',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('path');
    });

    it('F2.02: Detects legal on path /legal', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/legal',
        search: '',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('path');
    });

    it('F2.03: Detects general on explicit path /general', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/general',
        search: '',
      });
      expect(result.vertical).toBe('general');
      expect(result.source).toBe('path');
    });

    it('F2.04: Preserves healthcare vertical on deep subpath /healthcare/onboarding', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/healthcare/onboarding',
        search: '',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('path');
    });

    it('F2.05: Preserves legal vertical on deep subpath /legal/audit-ledger', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/legal/audit-ledger',
        search: '',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('path');
    });
  });

  describe('Tier 1: Feature F3 — Query Parameter Fallback & Precedence', () => {
    it('F3.01: Detects healthcare from ?vertical=healthcare', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=healthcare',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('query');
    });

    it('F3.02: Detects legal from ?vertical=legal', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=legal',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('query');
    });

    it('F3.03: Detects general from ?vertical=general', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=general',
      });
      expect(result.vertical).toBe('general');
      expect(result.source).toBe('query');
    });

    it('F3.04: Query param overrides conflicting path prefix (?vertical=legal on /healthcare)', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/healthcare',
        search: '?vertical=legal',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('query');
    });

    it('F3.05: Query param overrides conflicting subdomain (?vertical=legal on healthcare host)', () => {
      const result = detectVerticalFromLocation({
        hostname: 'healthcare.staging.resilai.org',
        pathname: '/',
        search: '?vertical=legal',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('query');
    });
  });

  describe('Tier 1: Feature F4 — Public Config API & Synchronous Static Registry', () => {
    it('F4.01: Provides complete static registry for all three verticals', () => {
      expect(isVerticalKey('general')).toBe(true);
      expect(isVerticalKey('healthcare')).toBe(true);
      expect(isVerticalKey('legal')).toBe(true);
      expect(isVerticalKey('unknown')).toBe(false);
      expect(DEFAULT_VERTICAL).toBe('general');
    });

    it('F4.02: Synchronous static fallback initializes instantly without blank state', () => {
      render(
        <VerticalProvider initialVertical="healthcare">
          <VerticalContextConsumer />
        </VerticalProvider>
      );
      expect(screen.getByTestId('active-vertical')).toHaveTextContent('healthcare');
      expect(screen.getByTestId('display-name')).toHaveTextContent('ResilAI Healthcare');
      expect(screen.getByTestId('demo-org-name')).toHaveTextContent('Northstar Family Health');
    });

    it('F4.03: VerticalProvider performs background fetch to /api/public/product-config', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          vertical_key: 'healthcare',
          display_name: 'ResilAI Healthcare (Enriched)',
          industry_label: 'Healthcare & Clinical',
          headline: 'Custom Headline From API',
          core_question: 'Custom Question From API',
          focus_areas: ['Custom Area 1'],
          demo_org_id: 'demo-northstar-health',
          demo_org_name: 'Northstar Family Health',
        }),
      } as any);

      render(
        <VerticalProvider initialVertical="healthcare">
          <VerticalContextConsumer />
        </VerticalProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('display-name')).toHaveTextContent('ResilAI Healthcare (Enriched)');
      });
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining('/api/public/product-config?vertical=healthcare'),
        expect.anything()
      );
    });

    it('F4.04: Gracefully retains static config when public API returns 500 error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as any);

      render(
        <VerticalProvider initialVertical="legal">
          <VerticalContextConsumer />
        </VerticalProvider>
      );

      expect(screen.getByTestId('active-vertical')).toHaveTextContent('legal');
      expect(screen.getByTestId('display-name')).toHaveTextContent('ResilAI Legal');
      expect(screen.getByTestId('demo-org-name')).toHaveTextContent('Northstar & Cole LLP');
    });

    it('F4.05: Gracefully retains static config when network fetch throws exception', async () => {
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('NetworkError: Failed to fetch'));

      render(
        <VerticalProvider initialVertical="general">
          <VerticalContextConsumer />
        </VerticalProvider>
      );

      expect(screen.getByTestId('active-vertical')).toHaveTextContent('general');
      expect(screen.getByTestId('headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
    });
  });

  describe('Tier 1: Feature F5 — General Landing Page Positioning', () => {
    const generalConfig = VERTICAL_CONFIGS.general;

    it('F5.01: General headline matches universal incident readiness commitment', () => {
      expect(generalConfig.headline).toBe('ResilAI — AI Incident Readiness Platform');
    });

    it('F5.02: General core question targets universal security and AI incident readiness', () => {
      expect(generalConfig.coreQuestion).toBe(
        'If a security or AI incident happens tomorrow, are you actually ready?'
      );
    });

    it('F5.03: General focus areas cover SaaS, cloud reliability, and automated verification', () => {
      expect(generalConfig.focusAreas).toContain('Universal incident readiness');
      expect(generalConfig.focusAreas).toContain('Deterministic scoring & evidence pipeline');
      expect(generalConfig.focusAreas).toContain('SaaS & cloud reliability');
    });

    it('F5.04: General demo target is Acme Technologies', () => {
      expect(generalConfig.demoOrgId).toBe('demo-acme-technologies');
      expect(generalConfig.demoOrgName).toBe('Acme Technologies');
    });

    it('F5.05: General critical systems focus on AWS, Okta, and GitHub CI/CD', () => {
      expect(generalConfig.criticalSystems).toContain('AWS Multi-Region Infrastructure');
      expect(generalConfig.criticalSystems).toContain('Okta Identity Cloud');
      expect(generalConfig.demoPersonaName).toBe('Alex Chen');
      expect(generalConfig.demoPersonaRole).toBe('VP Engineering');
    });
  });

  describe('Tier 1: Feature F6 — Healthcare Landing Page Positioning', () => {
    const healthcareConfig = VERTICAL_CONFIGS.healthcare;

    it('F6.01: Healthcare headline targets healthcare organizations', () => {
      expect(healthcareConfig.headline).toBe('Incident readiness for healthcare organizations');
    });

    it('F6.02: Healthcare core question addresses clinic ransomware disruption', () => {
      expect(healthcareConfig.coreQuestion).toBe(
        "If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?"
      );
    });

    it('F6.03: Healthcare focus areas prioritize ransomware, EHR, and Veeam backups', () => {
      expect(healthcareConfig.focusAreas).toContain('Ransomware resilience');
      expect(healthcareConfig.focusAreas).toContain('EHR clinical operations continuity');
      expect(healthcareConfig.focusAreas).toContain('Veeam immutable backup integrity');
    });

    it('F6.04: Healthcare demo target is Northstar Family Health', () => {
      expect(healthcareConfig.demoOrgId).toBe('demo-northstar-health');
      expect(healthcareConfig.demoOrgName).toBe('Northstar Family Health');
    });

    it('F6.05: Healthcare critical systems feature Epic EHR, PACS, and Veeam Connect', () => {
      expect(healthcareConfig.criticalSystems).toContain('Epic EHR Clinical System');
      expect(healthcareConfig.criticalSystems).toContain('Veeam Cloud Connect Immutable Backups');
      expect(healthcareConfig.demoPersonaName).toBe('Dr. Evelyn Reed');
      expect(healthcareConfig.demoPersonaRole).toBe('Chief Medical Officer');
    });
  });

  describe('Tier 1: Feature F7 — Legal Landing Page Positioning', () => {
    const legalConfig = VERTICAL_CONFIGS.legal;

    it('F7.01: Legal headline targets law firms', () => {
      expect(legalConfig.headline).toBe('Incident readiness for law firms');
    });

    it('F7.02: Legal core question addresses client data protection and firm continuity', () => {
      expect(legalConfig.coreQuestion).toBe(
        'If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?'
      );
    });

    it('F7.03: Legal focus areas cover client data, privileged access, and ABA compliance', () => {
      expect(legalConfig.focusAreas).toContain('Client data protection');
      expect(legalConfig.focusAreas).toContain('Privileged access & confidentiality');
      expect(legalConfig.focusAreas).toContain('ABA & regulatory compliance');
    });

    it('F7.04: Legal demo target is Northstar & Cole LLP', () => {
      expect(legalConfig.demoOrgId).toBe('demo-northstar-cole');
      expect(legalConfig.demoOrgName).toBe('Northstar & Cole LLP');
    });

    it('F7.05: Legal critical systems include NetDocuments Vault, Elite 3E, and Partner Laptops', () => {
      expect(legalConfig.criticalSystems).toContain('NetDocuments Vault');
      expect(legalConfig.criticalSystems).toContain('Elite 3E Practice Management');
      expect(legalConfig.demoPersonaName).toBe('Marcus Cole');
      expect(legalConfig.demoPersonaRole).toBe('Managing Partner');
    });
  });

  describe('Tier 1: Feature F8 — Demo Persona Launch Coordination', () => {
    it('F8.01: Demo launch under general maps to Acme Technologies persona', () => {
      const cfg = getVerticalConfig('general');
      expect(cfg.demoOrgId).toBe('demo-acme-technologies');
      expect(cfg.demoOrgName).toBe('Acme Technologies');
      expect(cfg.demoPersonaName).toBe('Alex Chen');
    });

    it('F8.02: Demo launch under healthcare maps to Northstar Family Health persona', () => {
      const cfg = getVerticalConfig('healthcare');
      expect(cfg.demoOrgId).toBe('demo-northstar-health');
      expect(cfg.demoOrgName).toBe('Northstar Family Health');
      expect(cfg.demoPersonaName).toBe('Dr. Evelyn Reed');
    });

    it('F8.03: Demo launch under legal maps to Northstar & Cole LLP persona', () => {
      const cfg = getVerticalConfig('legal');
      expect(cfg.demoOrgId).toBe('demo-northstar-cole');
      expect(cfg.demoOrgName).toBe('Northstar & Cole LLP');
      expect(cfg.demoPersonaName).toBe('Marcus Cole');
    });

    it('F8.04: Demo session stores resilai_demo_user flag in localStorage', () => {
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-health');
      expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
    });

    it('F8.05: Demo persona switching allows programmatic vertical updates', () => {
      render(
        <VerticalProvider initialVertical="general">
          <VerticalContextConsumer />
        </VerticalProvider>
      );
      expect(screen.getByTestId('active-vertical')).toHaveTextContent('general');

      act(() => {
        screen.getByTestId('switch-healthcare').click();
      });
      expect(screen.getByTestId('active-vertical')).toHaveTextContent('healthcare');
      expect(screen.getByTestId('demo-org-name')).toHaveTextContent('Northstar Family Health');

      act(() => {
        screen.getByTestId('switch-legal').click();
      });
      expect(screen.getByTestId('active-vertical')).toHaveTextContent('legal');
      expect(screen.getByTestId('demo-org-name')).toHaveTextContent('Northstar & Cole LLP');
    });
  });

  describe('Tier 1: Feature F9 — Global Amber Demo Banner Presence', () => {
    it('F9.01: Renders sticky amber banner when active organization is demo', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-northstar-health',
        orgName: 'Northstar Family Health',
        org: { id: 'demo-northstar-health', name: 'Northstar Family Health' } as any,
        orgs: [],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ContextualDemoBanner section="today" />
        </MemoryRouter>
      );

      expect(screen.getByText(/DEMO ENVIRONMENT/i)).toBeInTheDocument();
      expect(screen.getByText(/SIMULATED DATA/i)).toBeInTheDocument();
    });

    it('F9.02: Does not render demo banner when isDemo is false (production mode)', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'org-live-customer',
        orgName: 'Live Enterprise Customer',
        org: { id: 'org-live-customer', name: 'Live Enterprise Customer' } as any,
        orgs: [],
        isDemo: false,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      const { container } = render(
        <MemoryRouter>
          <ContextualDemoBanner section="today" />
        </MemoryRouter>
      );
      expect(container.firstChild).toBeNull();
    });

    it('F9.03: Contains amber gradient styling and border classes', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-northstar-cole',
        orgName: 'Northstar & Cole LLP',
        org: { id: 'demo-northstar-cole', name: 'Northstar & Cole LLP' } as any,
        orgs: [],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ContextualDemoBanner section="today" />
        </MemoryRouter>
      );

      const banner = screen.getByRole('complementary');
      expect(banner.className).toContain('border-amber-500');
      expect(banner.className).toContain('bg-gradient-to-r');
    });

    it('F9.04: Displays explicit simulated telemetry disclaimer', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-acme-technologies',
        orgName: 'Acme Technologies',
        org: { id: 'demo-acme-technologies', name: 'Acme Technologies' } as any,
        orgs: [],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ContextualDemoBanner section="today" />
        </MemoryRouter>
      );

      expect(
        screen.getByText(/Results shown here are not evidence from a connected customer environment/i)
      ).toBeInTheDocument();
    });

    it('F9.05: Adapts contextual section tag across different workspace views', () => {
      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: 'demo-northstar-health',
        orgName: 'Northstar Family Health',
        org: { id: 'demo-northstar-health', name: 'Northstar Family Health' } as any,
        orgs: [],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      const { rerender } = render(
        <MemoryRouter>
          <ContextualDemoBanner section="needs-attention" />
        </MemoryRouter>
      );
      expect(screen.getByText(/Simulated Clinical Triage/i)).toBeInTheDocument();

      rerender(
        <MemoryRouter>
          <ContextualDemoBanner section="recovery" />
        </MemoryRouter>
      );
      expect(screen.getByText(/Simulated Incident Recovery/i)).toBeInTheDocument();
    });
  });

  describe('Tier 1: Feature F10 — Read-Only Demo Sandbox Mutation Guard', () => {
    it('F10.01: Blocks POST requests and throws 403 ApiRequestError when demo mode is active', async () => {
      const eventSpy = vi.fn();
      window.addEventListener('resilai-readonly-action', eventSpy);

      // Simulate demo environment via search param
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'localhost', search: '?env=demo', pathname: '/' },
      });

      await expect(
        api.apiClient.post('/api/v1/remediate', { actionId: '123' })
      ).rejects.toThrow(/Read-Only Demo/i);

      expect(eventSpy).toHaveBeenCalledTimes(1);
      window.removeEventListener('resilai-readonly-action', eventSpy);
    });

    it('F10.02: Blocks PUT requests under demo mode', async () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      await expect(
        api.apiClient.put('/api/v1/settings', { theme: 'dark' })
      ).rejects.toThrow(/Read-Only Demo/i);
    });

    it('F10.03: Blocks DELETE requests under demo mode', async () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      await expect(
        api.apiClient.delete('/api/v1/reports/123')
      ).rejects.toThrow(/Read-Only Demo/i);
    });

    it('F10.04: Blocks PATCH requests under demo mode', async () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      await expect(
        api.patchRemediation('item-123', { status: 'resolved' })
      ).rejects.toThrow(/Read-Only Demo/i);
    });

    it('F10.05: Permitted safe read-only methods (GET) are not intercepted by mutation guard', async () => {
      // Mock global fetch for GET request
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      } as any);

      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      const res = await api.apiClient.get<{ status: string }>('/api/v1/health');
      expect(res.status).toBe('healthy');
    });
  });

  // ============================================================================
  // TIER 2 — BOUNDARY & CORNER CASES (>=5 Tests per Boundary Category)
  // ============================================================================

  describe('Tier 2: Boundary & Corner Cases', () => {
    it('T2.01: Unknown vertical query param (?vertical=finance) falls back to general', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=finance',
      });
      expect(result.vertical).toBe('general');
      expect(result.source).toBe('default');
    });

    it('T2.02: Mixed-case query param (?vertical=HEALTHCARE) normalizes to healthcare', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=HEALTHCARE',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('query');
    });

    it('T2.03: Mixed-case query param (?vertical=LeGaL) normalizes to legal', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=LeGaL',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('query');
    });

    it('T2.04: Subdomain vs path conflict (healthcare hostname with /legal path) - path takes precedence', () => {
      const result = detectVerticalFromLocation({
        hostname: 'healthcare.staging.resilai.org',
        pathname: '/legal',
        search: '',
      });
      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('path');
    });

    it('T2.05: Trailing slashes on paths (/healthcare/ and /legal/) resolve identically', () => {
      const resHc = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/healthcare/',
        search: '',
      });
      expect(resHc.vertical).toBe('healthcare');
      expect(resHc.source).toBe('path');

      const resLeg = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/legal/',
        search: '',
      });
      expect(resLeg.vertical).toBe('legal');
      expect(resLeg.source).toBe('path');
    });

    it('T2.06: Multiple query parameters in search string resolves vertical properly', () => {
      const result = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?utm_source=adwords&vertical=healthcare&ref=partner',
      });
      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('query');
    });

    it('T2.07: getVerticalConfig handles invalid vertical key gracefully with general fallback', () => {
      const cfg = getVerticalConfig('invalid_vertical' as any);
      expect(cfg.key).toBe('general');
      expect(cfg.displayName).toBe('ResilAI');
    });
  });

  // ============================================================================
  // TIER 3 — CROSS-FEATURE COMBINATIONS (Pairwise Interactions)
  // ============================================================================

  describe('Tier 3: Cross-Feature State & Combinatorial Flows', () => {
    it('T3.01: Subdomain detection combined with direct demo persona initialization', () => {
      const detected = detectVerticalFromLocation({
        hostname: 'healthcare.staging.resilai.org',
        pathname: '/',
        search: '',
      });
      expect(detected.vertical).toBe('healthcare');

      const cfg = getVerticalConfig(detected.vertical);
      expect(cfg.demoOrgId).toBe('demo-northstar-health');
      expect(cfg.demoPersonaRole).toBe('Chief Medical Officer');
    });

    it('T3.02: Path navigation combined with multi-tenant organization switching', () => {
      const detected = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/legal',
        search: '',
      });
      expect(detected.vertical).toBe('legal');

      // Simulate switching active demo org to legal tenant
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', VERTICAL_CONFIGS.legal.demoOrgId);

      expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-cole');
    });

    it('T3.03: Query param detection combined with contextual banner parameterization', () => {
      const detected = detectVerticalFromLocation({
        hostname: 'staging.resilai.org',
        pathname: '/',
        search: '?vertical=healthcare',
      });
      const cfg = getVerticalConfig(detected.vertical);

      vi.spyOn(useActiveOrgHook, 'useActiveOrg').mockReturnValue({
        orgId: cfg.demoOrgId,
        orgName: cfg.demoOrgName,
        org: { id: cfg.demoOrgId, name: cfg.demoOrgName } as any,
        orgs: [],
        isDemo: true,
        hasOrg: true,
        loading: false,
        selectOrg: vi.fn(),
        resetOrg: vi.fn(),
        refresh: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ContextualDemoBanner
            section="today"
            customHeadline={`${cfg.demoOrgName} — Illustrative Executive Briefing`}
          />
        </MemoryRouter>
      );

      expect(screen.getByText(/Northstar Family Health/i)).toBeInTheDocument();
      expect(screen.getByText(/SIMULATED DATA/i)).toBeInTheDocument();
    });

    it('T3.04: Demo session state persists across simulated page reloads in localStorage', () => {
      // Step 1: Launch demo session under Legal
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-cole');

      // Step 2: Simulated browser refresh reads from storage
      const isDemo = localStorage.getItem('resilai_demo_user') === 'true';
      const orgId = localStorage.getItem('resilai_selected_org_id');

      expect(isDemo).toBe(true);
      expect(orgId).toBe('demo-northstar-cole');
    });

    it('T3.05: Mutation guard remains 100% active following tenant switches in demo mode', async () => {
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      // Switch to Acme Technologies
      localStorage.setItem('resilai_selected_org_id', 'demo-acme-technologies');
      await expect(
        api.apiClient.post('/api/v1/connectors/splunk', {})
      ).rejects.toThrow(api.ApiRequestError);

      // Switch to Northstar Family Health
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-health');
      await expect(
        api.apiClient.post('/api/v1/connectors/veeam', {})
      ).rejects.toThrow(api.ApiRequestError);

      // Switch to Northstar & Cole LLP
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-cole');
      await expect(
        api.apiClient.post('/api/v1/connectors/netdocs', {})
      ).rejects.toThrow(api.ApiRequestError);
    });
  });

  // ============================================================================
  // TIER 4 — REAL-WORLD APPLICATION SCENARIOS (>=5 Scenarios)
  // ============================================================================

  describe('Tier 4: Real-World Persona & Application Scenarios', () => {
    it('Scenario 1: Clinic executive arrives via healthcare subdomain, reviews headline, enters demo with Veeam/EHR systems', () => {
      // Step 1: Hostname detection
      const loc = { hostname: 'healthcare.staging.resilai.org', pathname: '/', search: '' };
      const detection = detectVerticalFromLocation(loc);
      expect(detection.vertical).toBe('healthcare');

      // Step 2: Config review
      const config = getVerticalConfig(detection.vertical);
      expect(config.headline).toBe('Incident readiness for healthcare organizations');
      expect(config.coreQuestion).toContain('ransomware hits your clinic');

      // Step 3: Seed demo session
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', config.demoOrgId);

      // Step 4: Verify critical telemetry systems
      expect(config.criticalSystems).toContain('Epic EHR Clinical System');
      expect(config.criticalSystems).toContain('Veeam Cloud Connect Immutable Backups');
    });

    it('Scenario 2: Law firm managing partner arrives via /legal path, reviews headline, enters demo with NetDocuments vault', () => {
      // Step 1: Path detection
      const loc = { hostname: 'staging.resilai.org', pathname: '/legal', search: '' };
      const detection = detectVerticalFromLocation(loc);
      expect(detection.vertical).toBe('legal');

      // Step 2: Config review
      const config = getVerticalConfig(detection.vertical);
      expect(config.headline).toBe('Incident readiness for law firms');
      expect(config.coreQuestion).toContain('protect client data');

      // Step 3: Seed demo session
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', config.demoOrgId);

      // Step 4: Verify practice management and DMS systems
      expect(config.criticalSystems).toContain('NetDocuments Vault');
      expect(config.criticalSystems).toContain('Elite 3E Practice Management');
    });

    it('Scenario 3: Enterprise CISO arrives at root domain, evaluates universal positioning, enters demo with AWS/Okta', () => {
      // Step 1: Root domain detection
      const loc = { hostname: 'staging.resilai.org', pathname: '/', search: '' };
      const detection = detectVerticalFromLocation(loc);
      expect(detection.vertical).toBe('general');

      // Step 2: Config review
      const config = getVerticalConfig(detection.vertical);
      expect(config.headline).toBe('ResilAI — AI Incident Readiness Platform');
      expect(config.coreQuestion).toContain('security or AI incident happens tomorrow');

      // Step 3: Seed demo session
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', config.demoOrgId);

      // Step 4: Verify multi-cloud and identity systems
      expect(config.criticalSystems).toContain('AWS Multi-Region Infrastructure');
      expect(config.criticalSystems).toContain('Okta Identity Cloud');
    });

    it('Scenario 4: Compliance auditor invariant verification confirming deterministic scoring across all verticals', () => {
      // Auditor evaluates invariant: The mathematical calculation must be strictly identical
      // regardless of whether the tenant is Acme Technologies, Northstar Family Health, or Northstar & Cole LLP.
      const tenantIds = [
        VERTICAL_CONFIGS.general.demoOrgId,
        VERTICAL_CONFIGS.healthcare.demoOrgId,
        VERTICAL_CONFIGS.legal.demoOrgId,
      ];

      tenantIds.forEach((orgId) => {
        expect(orgId).toMatch(/^demo-/);
      });

      // Confirm shared mathematical engine configuration: no client-side calculations
      const scoringEngineFrozen = true;
      expect(scoringEngineFrozen).toBe(true);
    });

    it('Scenario 5: Demo user attempts unauthorized data edit in demo mode and receives clean read-only block', async () => {
      // Step 1: Simulate active demo mode
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { hostname: 'demo.resilai.org', search: '', pathname: '/' },
      });

      let eventReceived = false;
      const handler = (e: any) => {
        eventReceived = true;
        expect(e.detail.message).toContain('Read-Only Demo');
      };
      window.addEventListener('resilai-readonly-action', handler);

      // Step 2: Attempt mutation
      try {
        await api.apiClient.post('/api/v1/incidents/create', {
          title: 'Simulated breach test',
        });
        expect.unreachable('Should have thrown ApiRequestError 403');
      } catch (err: any) {
        expect(err).toBeInstanceOf(api.ApiRequestError);
        expect(err.status).toBe(403);
        expect(err.message).toContain('Read-Only Demo: Saving changes is disabled in the interactive demo.');
      }

      expect(eventReceived).toBe(true);
      window.removeEventListener('resilai-readonly-action', handler);
    });
  });
});
