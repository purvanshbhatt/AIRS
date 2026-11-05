/**
 * Unit & Integration Tests for Vertical Context, Detection, and Static Configuration
 * (Milestone 1: Host- and Route-Aware Vertical Architecture)
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import {
  VerticalProvider,
  useVertical,
  detectVerticalFromLocation,
} from '../contexts/VerticalContext';
import {
  VERTICAL_CONFIGS,
  isVerticalKey,
  getVerticalConfig,
  DEFAULT_VERTICAL,
} from '../config/verticals';
import type { VerticalKey } from '../types/vertical';

describe('detectVerticalFromLocation', () => {
  it('detects vertical from URL query parameter with highest precedence', () => {
    const res = detectVerticalFromLocation({
      search: '?vertical=healthcare',
      pathname: '/legal',
      hostname: 'general.staging.resilai.org',
    });
    expect(res.vertical).toBe('healthcare');
    expect(res.source).toBe('query');
  });

  it('detects legal vertical from query parameter', () => {
    const res = detectVerticalFromLocation({
      search: '?vertical=legal',
      pathname: '/',
      hostname: 'staging.resilai.org',
    });
    expect(res.vertical).toBe('legal');
    expect(res.source).toBe('query');
  });

  it('detects general vertical from query parameter', () => {
    const res = detectVerticalFromLocation({
      search: '?vertical=general',
      pathname: '/healthcare',
      hostname: 'legal.staging.resilai.org',
    });
    expect(res.vertical).toBe('general');
    expect(res.source).toBe('query');
  });

  it('detects vertical from pathname when query param is absent', () => {
    const resHealthcare = detectVerticalFromLocation({
      search: '',
      pathname: '/healthcare',
      hostname: 'staging.resilai.org',
    });
    expect(resHealthcare.vertical).toBe('healthcare');
    expect(resHealthcare.source).toBe('path');

    const resLegal = detectVerticalFromLocation({
      search: '',
      pathname: '/legal/dashboard',
      hostname: 'staging.resilai.org',
    });
    expect(resLegal.vertical).toBe('legal');
    expect(resLegal.source).toBe('path');

    const resGeneral = detectVerticalFromLocation({
      search: '',
      pathname: '/general',
      hostname: 'staging.resilai.org',
    });
    expect(resGeneral.vertical).toBe('general');
    expect(resGeneral.source).toBe('path');
  });

  it('detects vertical from hostname subdomain when query and path are absent', () => {
    const resHealthcare = detectVerticalFromLocation({
      search: '',
      pathname: '/',
      hostname: 'healthcare.staging.resilai.org',
    });
    expect(resHealthcare.vertical).toBe('healthcare');
    expect(resHealthcare.source).toBe('subdomain');

    const resLegal = detectVerticalFromLocation({
      search: '',
      pathname: '/',
      hostname: 'legal.staging.resilai.org',
    });
    expect(resLegal.vertical).toBe('legal');
    expect(resLegal.source).toBe('subdomain');

    const resLocalhost = detectVerticalFromLocation({
      search: '',
      pathname: '/',
      hostname: 'healthcare.localhost',
    });
    expect(resLocalhost.vertical).toBe('healthcare');
    expect(resLocalhost.source).toBe('subdomain');
  });

  it('falls back to default general when no matching indicator is present', () => {
    const res = detectVerticalFromLocation({
      search: '',
      pathname: '/about',
      hostname: 'staging.resilai.org',
    });
    expect(res.vertical).toBe('general');
    expect(res.source).toBe('default');
  });

  it('ignores invalid query parameters and falls back to path or subdomain', () => {
    const res = detectVerticalFromLocation({
      search: '?vertical=unknown_industry',
      pathname: '/legal',
      hostname: 'healthcare.staging.resilai.org',
    });
    expect(res.vertical).toBe('legal');
    expect(res.source).toBe('path');
  });
});

describe('Static Configuration Registry', () => {
  it('contains valid and complete configurations for all 3 verticals', () => {
    const keys: VerticalKey[] = ['general', 'healthcare', 'legal'];

    keys.forEach((key) => {
      const config = VERTICAL_CONFIGS[key];
      expect(config).toBeDefined();
      expect(config.key).toBe(key);
      expect(config.displayName).toBeTruthy();
      expect(config.industryLabel).toBeTruthy();
      expect(config.tagline).toBeTruthy();
      expect(config.headline).toBeTruthy();
      expect(config.coreQuestion).toBeTruthy();
      expect(Array.isArray(config.focusAreas)).toBe(true);
      expect(config.focusAreas.length).toBeGreaterThanOrEqual(3);
      expect(config.demoOrgId).toBeTruthy();
      expect(config.demoOrgName).toBeTruthy();
      expect(config.demoPersonaName).toBeTruthy();
      expect(config.demoPersonaRole).toBeTruthy();
      expect(Array.isArray(config.criticalSystems)).toBe(true);
      expect(config.criticalSystems.length).toBeGreaterThanOrEqual(3);
    });
  });

  it('validates type guard isVerticalKey', () => {
    expect(isVerticalKey('general')).toBe(true);
    expect(isVerticalKey('healthcare')).toBe(true);
    expect(isVerticalKey('legal')).toBe(true);
    expect(isVerticalKey('finance')).toBe(false);
    expect(isVerticalKey(null)).toBe(false);
    expect(isVerticalKey(undefined)).toBe(false);
    expect(isVerticalKey(123)).toBe(false);
  });

  it('retrieves config via getVerticalConfig with fallback to default', () => {
    expect(getVerticalConfig('healthcare').displayName).toBe('ResilAI Healthcare');
    expect(getVerticalConfig('legal').displayName).toBe('ResilAI Legal');
    expect(getVerticalConfig('general').displayName).toBe('ResilAI');
    expect(getVerticalConfig('unknown' as any).key).toBe(DEFAULT_VERTICAL);
  });
});

// Component to test hook usage
const TestConsumer: React.FC = () => {
  const { currentVertical, config, setVertical, source } = useVertical();
  return (
    <div>
      <div data-testid="current-vertical">{currentVertical}</div>
      <div data-testid="source">{source}</div>
      <div data-testid="display-name">{config.displayName}</div>
      <div data-testid="headline">{config.headline}</div>
      <div data-testid="demo-org">{config.demoOrgName}</div>
      <button onClick={() => setVertical('legal')} data-testid="btn-set-legal">
        Switch to Legal
      </button>
      <button onClick={() => setVertical('healthcare')} data-testid="btn-set-healthcare">
        Switch to Healthcare
      </button>
    </div>
  );
};

describe('VerticalProvider & useVertical', () => {
  beforeEach(() => {
    // Dynamic fetch mock responding with appropriate vertical configuration
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      const match = typeof url === 'string' ? url.match(/vertical=([a-z]+)/) : null;
      const v = (match ? match[1] : 'general') as VerticalKey;
      const cfg = getVerticalConfig(v);
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            vertical_key: cfg.key,
            display_name: cfg.displayName,
            industry_label: cfg.industryLabel,
            headline: cfg.headline,
            core_question: cfg.coreQuestion,
            focus_areas: cfg.focusAreas,
            demo_org_id: cfg.demoOrgId,
            demo_org_name: cfg.demoOrgName,
          }),
      });
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('throws error when useVertical is called outside provider', () => {
    // Silence expected React error boundary console error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const renderOutside = () => render(<TestConsumer />);
    expect(renderOutside).toThrow('useVertical must be used within a VerticalProvider');
    consoleSpy.mockRestore();
  });

  it('provides default vertical context synchronously without flash of missing content', async () => {
    render(
      <VerticalProvider initialVertical="general">
        <TestConsumer />
      </VerticalProvider>
    );

    expect(screen.getByTestId('current-vertical').textContent).toBe('general');
    expect(screen.getByTestId('display-name').textContent).toBe('ResilAI');
    expect(screen.getByTestId('headline').textContent).toBe('ResilAI — AI Incident Readiness Platform');
    expect(screen.getByTestId('demo-org').textContent).toBe('Acme Technologies');

    // Wait for async fetch to finish
    await waitFor(() => {
      expect(screen.getByTestId('current-vertical').textContent).toBe('general');
    });
  });

  it('allows programmatic vertical switching via setVertical', async () => {
    render(
      <VerticalProvider initialVertical="general">
        <TestConsumer />
      </VerticalProvider>
    );

    expect(screen.getByTestId('current-vertical').textContent).toBe('general');

    await act(async () => {
      screen.getByTestId('btn-set-legal').click();
    });

    expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
    expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal');
    expect(screen.getByTestId('demo-org').textContent).toBe('Northstar & Cole LLP');

    await act(async () => {
      screen.getByTestId('btn-set-healthcare').click();
    });

    expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
    expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Healthcare');
    expect(screen.getByTestId('demo-org').textContent).toBe('Northstar Family Health');
  });

  it('initializes with specified initialVertical prop', async () => {
    render(
      <VerticalProvider initialVertical="healthcare">
        <TestConsumer />
      </VerticalProvider>
    );

    expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
    expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Healthcare');

    await waitFor(() => {
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
    });
  });
});

