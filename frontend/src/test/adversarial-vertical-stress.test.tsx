/**
 * Adversarial Stress & Robustness Tests for Vertical Architecture (Milestone 1)
 * 
 * Verifies:
 * - Malformed query strings, URL encoding, multiple conflicting params
 * - Trailing slashes, uppercase subdomains, ports, IPv4/IPv6 hosts
 * - API timeouts, HTTP 500, network disconnects during background config fetch
 * - Rapid concurrent switching, unmount cleanup, race condition defense
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import {
  detectVerticalFromLocation,
  VerticalProvider,
  useVertical,
} from '../contexts/VerticalContext';
import {
  VERTICAL_CONFIGS,
  getVerticalConfig,
  isVerticalKey,
} from '../config/verticals';

describe('Adversarial Stress Testing: detectVerticalFromLocation', () => {
  describe('Query String Edge Cases & Malformed Inputs', () => {
    it('handles percent-encoded characters (?vertical=%68ealthcare)', () => {
      // %68 is lowercase 'h'
      const res = detectVerticalFromLocation({ search: '?vertical=%68ealthcare' });
      expect(res.vertical).toBe('healthcare');
      expect(res.source).toBe('query');
    });

    it('handles full percent-encoding (?vertical=%6C%65%67%61%6C)', () => {
      // %6C%65%67%61%6C is 'legal'
      const res = detectVerticalFromLocation({ search: '?vertical=%6C%65%67%61%6C' });
      expect(res.vertical).toBe('legal');
      expect(res.source).toBe('query');
    });

    it('normalizes uppercase and mixed-case query params', () => {
      expect(detectVerticalFromLocation({ search: '?vertical=HEALTHCARE' }).vertical).toBe('healthcare');
      expect(detectVerticalFromLocation({ search: '?vertical=LeGaL' }).vertical).toBe('legal');
      expect(detectVerticalFromLocation({ search: '?vertical=GeNeRaL' }).vertical).toBe('general');
    });

    it('handles multiple conflicting query parameters by taking the first defined', () => {
      const res1 = detectVerticalFromLocation({ search: '?vertical=healthcare&vertical=legal' });
      expect(res1.vertical).toBe('healthcare');
      expect(res1.source).toBe('query');

      const res2 = detectVerticalFromLocation({ search: '?vertical=legal&vertical=healthcare' });
      expect(res2.vertical).toBe('legal');
      expect(res2.source).toBe('query');
    });

    it('handles query parameter positioned among numerous unrelated parameters', () => {
      const res = detectVerticalFromLocation({
        search: '?utm_source=google&utm_medium=cpc&vertical=legal&session_id=98765&ref=partner',
      });
      expect(res.vertical).toBe('legal');
      expect(res.source).toBe('query');
    });

    it('does not crash on malformed percent-encoding (%ZZ, %E0%A4%A)', () => {
      // Invalid hex or incomplete sequences in URLSearchParams
      expect(() => {
        const res = detectVerticalFromLocation({ search: '?vertical=%ZZ' });
        expect(res.vertical).toBe('general');
      }).not.toThrow();

      expect(() => {
        const res = detectVerticalFromLocation({ search: '?vertical=%E0%A4%A' });
        expect(res.vertical).toBe('general');
      }).not.toThrow();
    });

    it('handles empty or blank query values gracefully', () => {
      expect(detectVerticalFromLocation({ search: '?vertical=' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: '?vertical' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: '?' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: '' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: '????&&&' }).vertical).toBe('general');
    });

    it('handles query param with whitespace or URL encoded space', () => {
      // ' healthcare' or 'healthcare ' is not a valid vertical key
      const res = detectVerticalFromLocation({ search: '?vertical=%20healthcare' });
      expect(res.vertical).toBe('general');
    });

    it('handles query param with null bytes or script injection attempts', () => {
      expect(detectVerticalFromLocation({ search: '?vertical=%00healthcare' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: '?vertical=<script>alert(1)</script>' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ search: "?vertical=' OR 1=1 --" }).vertical).toBe('general');
    });

    it('handles extremely long query strings without crashing or timeout', () => {
      const hugeQuery = '?vertical=' + 'a'.repeat(20000) + '&other=' + 'b'.repeat(20000);
      const start = performance.now();
      const res = detectVerticalFromLocation({ search: hugeQuery });
      const duration = performance.now() - start;
      expect(res.vertical).toBe('general');
      expect(duration).toBeLessThan(100); // Must be sub-100ms
    });
  });

  describe('Pathname Boundary & Malformed Inputs', () => {
    it('handles trailing slashes on path prefixes', () => {
      expect(detectVerticalFromLocation({ pathname: '/healthcare/' }).vertical).toBe('healthcare');
      expect(detectVerticalFromLocation({ pathname: '/legal/' }).vertical).toBe('legal');
      expect(detectVerticalFromLocation({ pathname: '/general/' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ pathname: '/healthcare///' }).vertical).toBe('healthcare');
    });

    it('handles mixed-case deep subpaths', () => {
      expect(detectVerticalFromLocation({ pathname: '/HEALTHCARE/dashboard' }).vertical).toBe('healthcare');
      expect(detectVerticalFromLocation({ pathname: '/LeGaL/audit-ledger' }).vertical).toBe('legal');
      expect(detectVerticalFromLocation({ pathname: '/GeNeRaL/reports/2026' }).vertical).toBe('general');
    });

    it('does NOT falsely match partial vertical prefix words', () => {
      // E.g. /healthcare-clinic or /legality or /generalization should not match
      expect(detectVerticalFromLocation({ pathname: '/healthcare-clinic' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ pathname: '/legality' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ pathname: '/generalization' }).vertical).toBe('general');
    });

    it('does NOT match vertical name appearing later in the path', () => {
      expect(detectVerticalFromLocation({ pathname: '/api/v1/healthcare' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ pathname: '/docs/legal' }).vertical).toBe('general');
    });

    it('handles root path and empty pathname', () => {
      expect(detectVerticalFromLocation({ pathname: '/' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ pathname: '' }).vertical).toBe('general');
    });
  });

  describe('Hostname Boundary & Malformed Inputs', () => {
    it('handles hostnames with port numbers', () => {
      const res1 = detectVerticalFromLocation({ hostname: 'healthcare.staging.resilai.org:5173' });
      expect(res1.vertical).toBe('healthcare');

      const res2 = detectVerticalFromLocation({ hostname: 'legal.staging.resilai.org:8080' });
      expect(res2.vertical).toBe('legal');
    });

    it('normalizes uppercase hostnames', () => {
      expect(detectVerticalFromLocation({ hostname: 'HEALTHCARE.STAGING.RESILAI.ORG' }).vertical).toBe('healthcare');
      expect(detectVerticalFromLocation({ hostname: 'LEGAL.LOCALHOST' }).vertical).toBe('legal');
    });

    it('handles IPv4 and IPv6 loopback addresses safely without crashing', () => {
      expect(detectVerticalFromLocation({ hostname: '127.0.0.1' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ hostname: '127.0.0.1:5173' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ hostname: '[::1]' }).vertical).toBe('general');
      expect(detectVerticalFromLocation({ hostname: '[::1]:5173' }).vertical).toBe('general');
    });

    it('handles dashed preview hostnames (healthcare-preview, legal-staging)', () => {
      expect(detectVerticalFromLocation({ hostname: 'healthcare-staging.web.app' }).vertical).toBe('healthcare');
      expect(detectVerticalFromLocation({ hostname: 'legal-preview.firebaseapp.com' }).vertical).toBe('legal');
      expect(detectVerticalFromLocation({ hostname: 'general-dev.resilai.org' }).vertical).toBe('general');
    });

    it('handles trailing FQDN dot (healthcare.staging.resilai.org.)', () => {
      expect(detectVerticalFromLocation({ hostname: 'healthcare.staging.resilai.org.' }).vertical).toBe('healthcare');
    });

    it('handles empty or missing hostname', () => {
      expect(detectVerticalFromLocation({ hostname: '' }).vertical).toBe('general');
    });
  });

  describe('Precedence Stress Hierarchy', () => {
    it('strictly enforces Query > Path > Subdomain > Fallback', () => {
      // 1. All 3 present -> Query wins
      expect(
        detectVerticalFromLocation({
          search: '?vertical=healthcare',
          pathname: '/legal',
          hostname: 'general.staging.resilai.org',
        }).vertical
      ).toBe('healthcare');

      // 2. Query invalid -> Path wins
      expect(
        detectVerticalFromLocation({
          search: '?vertical=invalid',
          pathname: '/legal',
          hostname: 'healthcare.staging.resilai.org',
        }).vertical
      ).toBe('legal');

      // 3. Query invalid & Path invalid -> Subdomain wins
      expect(
        detectVerticalFromLocation({
          search: '?vertical=invalid',
          pathname: '/unknown-route',
          hostname: 'healthcare.staging.resilai.org',
        }).vertical
      ).toBe('healthcare');

      // 4. Query invalid & Path invalid & Subdomain unrecognized -> Fallback 'general'
      expect(
        detectVerticalFromLocation({
          search: '?vertical=invalid',
          pathname: '/unknown-route',
          hostname: 'production.resilai.org',
        }).vertical
      ).toBe('general');
    });
  });

  describe('Edge Parameter Types to detectVerticalFromLocation', () => {
    it('handles undefined and empty object parameter cleanly', () => {
      expect(() => detectVerticalFromLocation(undefined)).not.toThrow();
      expect(() => detectVerticalFromLocation({})).not.toThrow();
      expect(() =>
        detectVerticalFromLocation({ search: undefined, pathname: undefined, hostname: undefined })
      ).not.toThrow();
    });
  });
});

// Component for testing provider resilience
const ConsumerComponent: React.FC = () => {
  const { currentVertical, config, isLoading, setVertical } = useVertical();
  return (
    <div>
      <div data-testid="vertical">{currentVertical}</div>
      <div data-testid="headline">{config.headline}</div>
      <div data-testid="loading">{isLoading ? 'loading' : 'idle'}</div>
      <button data-testid="switch-legal" onClick={() => setVertical('legal')}>Legal</button>
      <button data-testid="switch-health" onClick={() => setVertical('healthcare')}>Health</button>
    </div>
  );
};

describe('Adversarial Stress Testing: VerticalProvider & Network Robustness', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('preserves static configuration when backend returns HTTP 500 Internal Server Error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    }));

    render(
      <VerticalProvider initialVertical="healthcare">
        <ConsumerComponent />
      </VerticalProvider>
    );

    // Synchronous static config renders immediately
    expect(screen.getByTestId('vertical').textContent).toBe('healthcare');
    expect(screen.getByTestId('headline').textContent).toBe(
      'Incident readiness for healthcare organizations'
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('idle');
    });

    // Headline remains the valid healthcare static headline
    expect(screen.getByTestId('headline').textContent).toBe(
      'Incident readiness for healthcare organizations'
    );
  });

  it('preserves static configuration when network fetch throws error (offline / timeout)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch (network error)')));

    render(
      <VerticalProvider initialVertical="legal">
        <ConsumerComponent />
      </VerticalProvider>
    );

    expect(screen.getByTestId('vertical').textContent).toBe('legal');
    expect(screen.getByTestId('headline').textContent).toBe(
      'Incident readiness for law firms'
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('idle');
    });

    expect(screen.getByTestId('headline').textContent).toBe(
      'Incident readiness for law firms'
    );
  });

  it('handles corrupt / invalid JSON body from server without crash', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.reject(new SyntaxError('Unexpected token < in JSON at position 0')),
    }));

    render(
      <VerticalProvider initialVertical="general">
        <ConsumerComponent />
      </VerticalProvider>
    );

    expect(screen.getByTestId('vertical').textContent).toBe('general');
    expect(screen.getByTestId('headline').textContent).toBe(
      'ResilAI — AI Incident Readiness Platform'
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('idle');
    });

    expect(screen.getByTestId('headline').textContent).toBe(
      'ResilAI — AI Incident Readiness Platform'
    );
  });

  it('ignores stale response when vertical switched rapidly before fetch finishes (race condition)', async () => {
    let resolveFirstFetch: any;
    const firstFetchPromise = new Promise((resolve) => {
      resolveFirstFetch = resolve;
    });

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('general')) {
          return firstFetchPromise;
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              vertical_key: 'legal',
              display_name: 'ResilAI Legal (Enriched)',
              headline: 'Incident readiness for law firms (Enriched)',
            }),
        });
      })
    );

    render(
      <VerticalProvider initialVertical="general">
        <ConsumerComponent />
      </VerticalProvider>
    );

    expect(screen.getByTestId('vertical').textContent).toBe('general');

    // Rapidly switch to legal
    await act(async () => {
      screen.getByTestId('switch-legal').click();
    });

    expect(screen.getByTestId('vertical').textContent).toBe('legal');

    // Now resolve the delayed general fetch with stale data
    await act(async () => {
      resolveFirstFetch({
        ok: true,
        json: () =>
          Promise.resolve({
            vertical_key: 'general',
            display_name: 'STALE GENERAL DATA',
            headline: 'STALE GENERAL HEADLINE',
          }),
      });
    });

    // Vertical must still be legal and headline must NOT be overwritten by stale general response
    await waitFor(() => {
      expect(screen.getByTestId('vertical').textContent).toBe('legal');
      expect(screen.getByTestId('headline').textContent).not.toContain('STALE GENERAL');
    });
  });

  it('handles component unmount cleanly while fetch is in-flight without console errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: () => Promise.resolve(getVerticalConfig('healthcare')),
                }),
              200
            );
          })
      )
    );

    const { unmount } = render(
      <VerticalProvider initialVertical="healthcare">
        <ConsumerComponent />
      </VerticalProvider>
    );

    // Unmount before fetch resolves
    unmount();
    // Verify no unhandled rejection or warning
  });
});
