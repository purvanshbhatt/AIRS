/**
 * Adversarial State & Concurrency Verification Test Suite
 * 
 * Target: Milestone 1 (Host- and Route-Aware Vertical Architecture)
 * Scope:
 * 1. Popstate browser navigation events across verticals (forward/back history, no stale closures)
 * 2. Rapid vertical switching and async race conditions (cancellation token, out-of-order responses)
 * 3. Precedence boundaries and invalid input hardening
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import React from 'react';
import {
  VerticalProvider,
  useVertical,
  detectVerticalFromLocation,
} from '../contexts/VerticalContext';
import { VERTICAL_CONFIGS } from '../config/verticals';
import type { VerticalKey } from '../types/vertical';

// Helper consumer component to expose context state to DOM
const VerticalStateInspector: React.FC<{
  onStateChange?: (state: ReturnType<typeof useVertical>) => void;
}> = ({ onStateChange }) => {
  const context = useVertical();

  React.useEffect(() => {
    onStateChange?.(context);
  }, [context, onStateChange]);

  return (
    <div data-testid="vertical-inspector">
      <span data-testid="current-vertical">{context.currentVertical}</span>
      <span data-testid="display-name">{context.config.displayName}</span>
      <span data-testid="config-key">{context.config.key}</span>
      <span data-testid="demo-org-id">{context.config.demoOrgId}</span>
      <span data-testid="headline">{context.config.headline}</span>
      <span data-testid="source">{context.source}</span>
      <span data-testid="is-loading">{context.isLoading ? 'loading' : 'idle'}</span>
      <button
        data-testid="set-healthcare"
        onClick={() => context.setVertical('healthcare')}
      >
        Set Healthcare
      </button>
      <button
        data-testid="set-legal"
        onClick={() => context.setVertical('legal')}
      >
        Set Legal
      </button>
      <button
        data-testid="set-general"
        onClick={() => context.setVertical('general')}
      >
        Set General
      </button>
      <button
        data-testid="set-invalid"
        onClick={() => (context.setVertical as any)('invalid-vertical')}
      >
        Set Invalid
      </button>
    </div>
  );
};

describe('Adversarial Verification: Popstate Reactivity & State Concurrency', () => {
  const originalLocation = window.location;
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock fetch to return 404 or clean fallback so background fetch doesn't interfere unless mocked
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: false,
        status: 404,
        json: async () => ({}),
      } as Response)
    );
  });

  afterEach(() => {
    global.fetch = originalFetch;
    window.history.pushState({}, '', '/');
  });

  // =========================================================================
  // SUITE 1: Popstate Browser Navigation & History Traversal
  // =========================================================================
  describe('Suite 1: Popstate Navigation & History Events', () => {
    it('1.1 dynamically reacts to popstate navigation across all 3 verticals without page reload', async () => {
      // Start at root '/' (general)
      window.history.pushState({}, '', '/');
      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('general');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI');

      // Navigate to /healthcare via pushState + popstate
      await act(async () => {
        window.history.pushState({}, '', '/healthcare');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
      expect(screen.getByTestId('config-key').textContent).toBe('healthcare');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Healthcare');
      expect(screen.getByTestId('demo-org-id').textContent).toBe('demo-northstar-health');
      expect(screen.getByTestId('source').textContent).toBe('path');

      // Navigate to /legal via pushState + popstate
      await act(async () => {
        window.history.pushState({}, '', '/legal');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
      expect(screen.getByTestId('config-key').textContent).toBe('legal');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal');
      expect(screen.getByTestId('demo-org-id').textContent).toBe('demo-northstar-cole');
      expect(screen.getByTestId('source').textContent).toBe('path');

      // Navigate back to root / via pushState + popstate
      await act(async () => {
        window.history.pushState({}, '', '/');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('general');
      expect(screen.getByTestId('config-key').textContent).toBe('general');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI');
      expect(screen.getByTestId('source').textContent).toBe('default');
    });

    it('1.2 handles simulated browser back and forward history traversal sequence without stale closures', async () => {
      window.history.pushState({}, '', '/');
      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      // Simulation history stack:
      // 0: /
      // 1: /healthcare
      // 2: /legal
      // 3: /?vertical=healthcare

      // Step 1: Forward to /healthcare
      await act(async () => {
        window.history.pushState({}, '', '/healthcare');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');

      // Step 2: Forward to /legal
      await act(async () => {
        window.history.pushState({}, '', '/legal');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');

      // Step 3: Forward to query param ?vertical=healthcare
      await act(async () => {
        window.history.pushState({}, '', '/?vertical=healthcare');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
      expect(screen.getByTestId('source').textContent).toBe('query');

      // Step 4: User clicks BACK -> to /legal
      await act(async () => {
        window.history.pushState({}, '', '/legal');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
      expect(screen.getByTestId('source').textContent).toBe('path');

      // Step 5: User clicks BACK -> to /healthcare
      await act(async () => {
        window.history.pushState({}, '', '/healthcare');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
      expect(screen.getByTestId('source').textContent).toBe('path');

      // Step 6: User clicks BACK -> to /
      await act(async () => {
        window.history.pushState({}, '', '/');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('general');
      expect(screen.getByTestId('source').textContent).toBe('default');
    });

    it('1.3 survives a rapid burst of popstate events without desynchronization or crashes', async () => {
      window.history.pushState({}, '', '/');
      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      // Rapidly trigger 12 popstate events in immediate succession
      const targets = [
        '/healthcare',
        '/legal',
        '/?vertical=general',
        '/healthcare/deep-link',
        '/?vertical=legal',
        '/general',
        '/legal',
        '/healthcare',
        '/?vertical=legal',
        '/healthcare',
        '/',
        '/legal',
      ];

      await act(async () => {
        for (const target of targets) {
          window.history.pushState({}, '', target);
          window.dispatchEvent(new PopStateEvent('popstate'));
        }
      });

      // Must cleanly settle on the final target ('/legal')
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
      expect(screen.getByTestId('config-key').textContent).toBe('legal');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal');
    });

    it('1.4 removes popstate event listener upon unmount cleanly (no memory leak or ghost updates)', async () => {
      window.history.pushState({}, '', '/');
      const addListenerSpy = vi.spyOn(window, 'addEventListener');
      const removeListenerSpy = vi.spyOn(window, 'removeEventListener');

      let unmountFn: () => void;
      await act(async () => {
        const res = render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
        unmountFn = res.unmount;
      });

      expect(addListenerSpy).toHaveBeenCalledWith('popstate', expect.any(Function));

      // Unmount provider
      await act(async () => {
        unmountFn!();
      });

      expect(removeListenerSpy).toHaveBeenCalledWith('popstate', expect.any(Function));

      // Dispatching popstate after unmount must not throw or update unmounted components
      expect(() => {
        window.history.pushState({}, '', '/healthcare');
        window.dispatchEvent(new PopStateEvent('popstate'));
      }).not.toThrow();
    });
  });

  // =========================================================================
  // SUITE 2: Rapid Vertical Switching & Async Race Conditions
  // =========================================================================
  describe('Suite 2: Rapid State Updates & Async Race Conditions', () => {
    it('2.1 handles rapid sequential setVertical() calls and guarantees final state consistency', async () => {
      window.history.pushState({}, '', '/');
      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('general');

      // Rapidly fire setVertical calls in immediate succession
      await act(async () => {
        screen.getByTestId('set-healthcare').click();
        screen.getByTestId('set-legal').click();
        screen.getByTestId('set-general').click();
        screen.getByTestId('set-healthcare').click();
        screen.getByTestId('set-legal').click();
      });

      // The final state must be strictly 'legal'
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
      expect(screen.getByTestId('config-key').textContent).toBe('legal');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal');
      expect(screen.getByTestId('demo-org-id').textContent).toBe('demo-northstar-cole');
    });

    it('2.2 protects against out-of-order async API responses (cancellation token / race guard)', async () => {
      window.history.pushState({}, '', '/');

      // Simulate a scenario where 'healthcare' request is slow (resolves late)
      // and 'legal' request is fast (resolves early).
      let resolveHealthcare: (val: any) => void;
      let resolveLegal: (val: any) => void;

      const healthcarePromise = new Promise((resolve) => {
        resolveHealthcare = resolve;
      });
      const legalPromise = new Promise((resolve) => {
        resolveLegal = resolve;
      });

      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('vertical=healthcare')) {
          return healthcarePromise;
        }
        if (url.includes('vertical=legal')) {
          return legalPromise;
        }
        return Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({}),
        });
      });

      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      // 1. Switch to healthcare (slow request started)
      await act(async () => {
        screen.getByTestId('set-healthcare').click();
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');

      // 2. Immediately switch to legal (fast request started)
      await act(async () => {
        screen.getByTestId('set-legal').click();
      });
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');

      // 3. Resolve legal FIRST with enriched legal data
      await act(async () => {
        resolveLegal!({
          ok: true,
          status: 200,
          json: async () => ({
            vertical_key: 'legal',
            display_name: 'ResilAI Legal — Enriched Edition',
            industry_label: 'Law Firms & Legal',
            headline: 'Enriched Legal Headline',
            core_question: 'Enriched Legal Question?',
            focus_areas: ['Privileged Data Protection'],
            demo_org_id: 'demo-northstar-cole',
            demo_org_name: 'Northstar & Cole LLP',
          }),
        });
      });

      await waitFor(() => {
        expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal — Enriched Edition');
      });

      // 4. Resolve healthcare LATER with obsolete healthcare data
      await act(async () => {
        resolveHealthcare!({
          ok: true,
          status: 200,
          json: async () => ({
            vertical_key: 'healthcare',
            display_name: 'OLD STALE HEALTHCARE DATA',
            industry_label: 'Healthcare',
            headline: 'OLD STALE HEADLINE',
            core_question: 'OLD STALE QUESTION?',
            focus_areas: ['Old EHR'],
            demo_org_id: 'demo-northstar-health',
            demo_org_name: 'Northstar Family Health',
          }),
        });
      });

      // 5. CRUCIAL ASSERTION: The stale healthcare response must NOT overwrite active legal state!
      expect(screen.getByTestId('current-vertical').textContent).toBe('legal');
      expect(screen.getByTestId('config-key').textContent).toBe('legal');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Legal — Enriched Edition');
      expect(screen.getByTestId('display-name').textContent).not.toBe('OLD STALE HEALTHCARE DATA');
    });

    it('2.3 survives network 500 error and exception during setVertical() without dropping state', async () => {
      window.history.pushState({}, '', '/');

      // Fetch will reject with network failure
      global.fetch = vi.fn().mockRejectedValue(new Error('500 Internal Server Error: Telemetry Offline'));

      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      // Switch to healthcare while network is throwing errors
      await act(async () => {
        screen.getByTestId('set-healthcare').click();
      });

      // State must still synchronously switch to healthcare using static fallback config
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
      expect(screen.getByTestId('config-key').textContent).toBe('healthcare');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Healthcare');
      expect(screen.getByTestId('demo-org-id').textContent).toBe('demo-northstar-health');

      // isLoading must cleanly reset back to idle
      await waitFor(() => {
        expect(screen.getByTestId('is-loading').textContent).toBe('idle');
      });
    });

    it('2.4 safely rejects invalid vertical keys without corrupting current state', async () => {
      window.history.pushState({}, '', '/healthcare');
      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector />
          </VerticalProvider>
        );
      });

      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');

      // Attempt to set invalid vertical key
      await act(async () => {
        screen.getByTestId('set-invalid').click();
      });

      // Must retain healthcare state without error
      expect(screen.getByTestId('current-vertical').textContent).toBe('healthcare');
      expect(screen.getByTestId('config-key').textContent).toBe('healthcare');
      expect(screen.getByTestId('display-name').textContent).toBe('ResilAI Healthcare');
    });
  });

  // =========================================================================
  // SUITE 3: Invariant Consistency & Boundary Precedence
  // =========================================================================
  describe('Suite 3: Invariants & Precedence Integrity', () => {
    it('3.1 guarantees currentVertical === config.key at all times across transitions', async () => {
      window.history.pushState({}, '', '/');
      let capturedStates: Array<{ currentVertical: VerticalKey; configKey: string }> = [];

      await act(async () => {
        render(
          <VerticalProvider>
            <VerticalStateInspector
              onStateChange={(state) => {
                capturedStates.push({
                  currentVertical: state.currentVertical,
                  configKey: state.config.key,
                });
              }}
            />
          </VerticalProvider>
        );
      });

      await act(async () => {
        screen.getByTestId('set-healthcare').click();
        screen.getByTestId('set-legal').click();
        screen.getByTestId('set-general').click();
      });

      // Verify invariant across every captured render: vertical key must always equal config key
      expect(capturedStates.length).toBeGreaterThan(0);
      for (const st of capturedStates) {
        expect(st.currentVertical).toBe(st.configKey);
      }
    });

    it('3.2 correctly prioritizes query param over conflicting pathname and subdomain', () => {
      const result = detectVerticalFromLocation({
        search: '?vertical=legal',
        pathname: '/healthcare',
        hostname: 'general.staging.resilai.org',
      });

      expect(result.vertical).toBe('legal');
      expect(result.source).toBe('query');
    });

    it('3.3 correctly prioritizes pathname over conflicting subdomain when query param is absent', () => {
      const result = detectVerticalFromLocation({
        search: '',
        pathname: '/healthcare',
        hostname: 'legal.staging.resilai.org',
      });

      expect(result.vertical).toBe('healthcare');
      expect(result.source).toBe('path');
    });

    it('3.4 defaults cleanly when given unusual or malformed location inputs', () => {
      // Empty location
      expect(detectVerticalFromLocation({})).toEqual({ vertical: 'general', source: 'default' });

      // Malformed path and query
      expect(detectVerticalFromLocation({ search: '?vertical=unknown-123', pathname: '/api/v1/scores' })).toEqual({
        vertical: 'general',
        source: 'default',
      });

      // Special characters in query
      expect(detectVerticalFromLocation({ search: '?vertical=%20healthcare%20' })).toEqual({
        vertical: 'general',
        source: 'default',
      });
    });
  });
});
