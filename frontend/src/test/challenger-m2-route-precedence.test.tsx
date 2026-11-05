/**
 * Challenger Adversarial Test Suite — Milestone 2: Route Resolution & Precedence Stress-Testing
 * 
 * Target Components: Landing.tsx, App.tsx, PublicNavbar.tsx, VerticalContext.tsx
 * Scope:
 *  1. Route path resolution under /healthcare, /legal, /general, /
 *  2. Precedence: query param ?vertical=legal on /healthcare path must display Legal vertical copy
 *  3. Invalid vertical query params (?vertical=invalid) on /healthcare must gracefully display Healthcare copy (path fallback)
 *  4. Dynamic prop overrides (defaultVertical) and failure mode identification
 *  5. Interactive demo sandbox seeding under conflicting parameters
 *  6. Client-side dynamic route navigation transitions
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';

import Landing from '../pages/Landing';
import { VerticalProvider, useVertical } from '../contexts/VerticalContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import App from '../App';

// Mock AuthContext so signInAsDemo resolves without network dependencies
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual<any>('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      user: null,
      loading: false,
      error: null,
      isConfigured: true,
      hasOrganizations: false,
      signInAsDemo: vi.fn().mockResolvedValue(undefined),
      clearError: vi.fn(),
      getToken: vi.fn().mockResolvedValue(null),
      signOut: vi.fn().mockResolvedValue(undefined),
    }),
  };
});

// Mock api module
vi.mock('../api', async () => {
  const actual = await vi.importActual<any>('../api');
  return {
    ...actual,
    setUnauthorizedHandler: vi.fn(),
    isApiConfigured: true,
    getSystemStatus: vi.fn().mockResolvedValue({}),
  };
});

// Polyfill IntersectionObserver for Framer Motion viewport features in jsdom
class MockIntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  takeRecords = vi.fn().mockReturnValue([]);
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});
Object.defineProperty(global, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});

describe('Challenger M2 Stress-Test: Route Resolution & Precedence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    // Mock global fetch to prevent unhandled node socket timeouts
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
      return {
        ok: false,
        status: 404,
        json: async () => ({}),
        text: async () => '',
      } as any;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // Suite 1: Route Path Resolution under /, /healthcare, /legal, /general
  // ============================================================================
  describe('Suite 1: Route Path Resolution in <App /> & <Landing />', () => {
    it('C1.01: <App /> at root route / resolves to General vertical copy', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent('If a security or AI incident happens tomorrow, are you actually ready?');
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification · AI Incident Readiness');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Acme Technologies/i);
      });
    });

    it('C1.02: <App /> at /healthcare resolves to Healthcare vertical copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent("If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?");
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification for Healthcare');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C1.03: <App /> at /legal resolves to Legal vertical copy', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent('If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?');
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification for Law Firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C1.04: <App /> at /general resolves to General vertical copy', async () => {
      render(
        <MemoryRouter initialEntries={['/general']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Acme Technologies/i);
      });
    });

    it('C1.05: <Landing /> in isolation detects path /healthcare without defaultVertical prop', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
      });
    });

    it('C1.06: <Landing /> in isolation detects path /legal without defaultVertical prop', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
      });
    });

    it('C1.07: Trailing slash on path /healthcare/ resolves to Healthcare copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare/']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
      });
    });

    it('C1.08: Trailing slash on path /legal/ resolves to Legal copy', async () => {
      render(
        <MemoryRouter initialEntries={['/legal/']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
      });
    });
  });

  // ============================================================================
  // Suite 2: Precedence — Query Parameter Overrides Route Path
  // ============================================================================
  describe('Suite 2: Query Parameter Precedence over Route Path', () => {
    it('C2.01: Query param ?vertical=legal on /healthcare path MUST display Legal copy in <Landing />', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=legal']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical="healthcare" />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent('If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?');
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification for Law Firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C2.02: Query param ?vertical=legal on /healthcare path MUST display Legal copy in full <App />', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/protect client data/i);
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C2.03: Query param ?vertical=healthcare on /legal path MUST display Healthcare copy in <App />', async () => {
      render(
        <MemoryRouter initialEntries={['/legal?vertical=healthcare']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/ransomware hits your clinic/i);
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C2.04: Query param ?vertical=general on /healthcare path MUST display General copy in <App />', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=general']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Acme Technologies/i);
      });
    });

    it('C2.05: Multiple query params preserve precedence: /healthcare?ref=partner&vertical=legal&src=web', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?ref=partner&vertical=legal&src=web']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C2.06: Case-insensitive query param /healthcare?vertical=LEGAL displays Legal copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=LEGAL']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C2.07: Mixed-case query param /legal?vertical=HeAlThCaRe displays Healthcare copy', async () => {
      render(
        <MemoryRouter initialEntries={['/legal?vertical=HeAlThCaRe']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });
  });

  // ============================================================================
  // Suite 3: Graceful Path Fallback on Invalid Query Parameters
  // ============================================================================
  describe('Suite 3: Graceful Path Fallback on Invalid Query Parameters', () => {
    it('C3.01: ?vertical=invalid on /healthcare MUST gracefully display Healthcare copy (not General)', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=invalid']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/ransomware hits your clinic/i);
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification for Healthcare');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C3.02: ?vertical=invalid on /healthcare in standalone <Landing /> displays Healthcare copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=invalid']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical="healthcare" />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C3.03: ?vertical=unknown on /legal MUST gracefully display Legal copy (not General)', async () => {
      render(
        <MemoryRouter initialEntries={['/legal?vertical=unknown']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/protect client data/i);
        expect(screen.getByTestId('hero-badge')).toHaveTextContent('Deterministic Verification for Law Firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C3.04: Empty query param ?vertical= on /healthcare gracefully falls back to Healthcare copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C3.05: Numeric/nonsense query param ?vertical=99999 on /healthcare gracefully falls back to Healthcare', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=99999']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
      });
    });

    it('C3.06: ?vertical=invalid on root / falls back to General copy', async () => {
      render(
        <MemoryRouter initialEntries={['/?vertical=invalid']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Acme Technologies/i);
      });
    });
  });

  // ============================================================================
  // Suite 4: Dynamic Prop Overrides (defaultVertical) & Failure Mode Audit
  // ============================================================================
  describe('Suite 4: Dynamic Prop Overrides (defaultVertical)', () => {
    it('C4.01: <Landing defaultVertical="healthcare" /> at root route / renders Healthcare copy', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical="healthcare" />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });

    it('C4.02: <Landing defaultVertical="legal" /> at root route / renders Legal copy', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical="legal" />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C4.03: Conflicting dynamic prop defaultVertical vs route path resolves cleanly without re-render ping-pong cycle', () => {
      // When defaultVertical differs from the URL route path, Landing sets VerticalContext to defaultVertical,
      // and passes currentVertical={effectiveVertical} to PublicNavbar without triggering a ping-pong loop.
      function LoopSpy({ onTransition }: { onTransition: (v: string) => void }) {
        const { currentVertical } = useVertical();
        React.useEffect(() => {
          onTransition(currentVertical);
        }, [currentVertical, onTransition]);
        return null;
      }

      const transitions: string[] = [];
      let detectedInfiniteLoop = false;

      try {
        render(
          <MemoryRouter initialEntries={['/healthcare']}>
            <ThemeProvider>
              <VerticalProvider>
                <LoopSpy onTransition={(v) => {
                  transitions.push(v);
                  if (transitions.length > 20) {
                    detectedInfiniteLoop = true;
                    throw new Error('INFINITE_PING_PONG_DETECTED');
                  }
                }} />
                <Landing defaultVertical="legal" />
              </VerticalProvider>
            </ThemeProvider>
          </MemoryRouter>
        );
      } catch (err: any) {
        if (err.message === 'INFINITE_PING_PONG_DETECTED') {
          detectedInfiniteLoop = true;
        }
      }

      // Assert that the infinite ping-pong loop is eliminated and transitions settle cleanly
      expect(detectedInfiniteLoop).toBe(false);
      expect(transitions).toEqual(['general', 'legal']);
      expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
    });

    it('C4.04: Query param ?vertical=legal OVERRIDES defaultVertical="healthcare" at root /', async () => {
      render(
        <MemoryRouter initialEntries={['/?vertical=legal']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical="healthcare" />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C4.05: Invalid defaultVertical prop gracefully falls back to root general', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <ThemeProvider>
            <VerticalProvider>
              <Landing defaultVertical={"nonsense" as any} />
            </VerticalProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
      });
    });
  });

  // ============================================================================
  // Suite 5: Interactive Sandbox Seeding under Precedence & Edge Cases
  // ============================================================================
  describe('Suite 5: Interactive Sandbox Seeding under Precedence', () => {
    it('C5.01: Clicking hero CTA under /healthcare?vertical=legal seeds Legal org (Northstar & Cole LLP)', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=legal']}>
          <App />
        </MemoryRouter>
      );

      const heroCta = await screen.findByTestId('hero-demo-cta');
      expect(heroCta).toHaveTextContent(/Northstar & Cole LLP/i);

      fireEvent.click(heroCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-cole');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('C5.02: Clicking hero CTA under /healthcare?vertical=invalid seeds Healthcare org (Northstar Family Health)', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=invalid']}>
          <App />
        </MemoryRouter>
      );

      const heroCta = await screen.findByTestId('hero-demo-cta');
      expect(heroCta).toHaveTextContent(/Northstar Family Health/i);

      fireEvent.click(heroCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('C5.03: Clicking bottom CTA under /legal?vertical=healthcare seeds Healthcare org', async () => {
      render(
        <MemoryRouter initialEntries={['/legal?vertical=healthcare']}>
          <App />
        </MemoryRouter>
      );

      const bottomCta = await screen.findByTestId('bottom-demo-cta');
      expect(bottomCta).toHaveTextContent(/Northstar Family Health/i);

      fireEvent.click(bottomCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('C5.04: Value pillars and personas reflect Legal vertical when /healthcare?vertical=legal', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Managing Partner \(L1\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Practice Director \(L2\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Legal IT \/ MSP \(L3\)/i)).toBeInTheDocument();
      });
    });

    it('C5.05: Report preview reflects Legal vertical when /healthcare?vertical=legal', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare?vertical=legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Firm & Client Confidentiality Audits')).toBeInTheDocument();
        expect(screen.getByText(/NetDocuments Vault/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Suite 6: Dynamic Client-Side Router Navigation Transitions in <App />
  // ============================================================================
  describe('Suite 6: Dynamic Client-Side Router Navigation Transitions', () => {
    function NavTestController() {
      const navigate = useNavigate();
      return (
        <div data-testid="nav-controller">
          <button data-testid="go-healthcare" onClick={() => navigate('/healthcare')}>Go Healthcare</button>
          <button data-testid="go-legal" onClick={() => navigate('/legal')}>Go Legal</button>
          <button data-testid="go-override-legal" onClick={() => navigate('/healthcare?vertical=legal')}>Go Healthcare With Legal Param</button>
          <button data-testid="go-invalid-param" onClick={() => navigate('/healthcare?vertical=invalid_token')}>Go Healthcare With Invalid Param</button>
          <button data-testid="go-general" onClick={() => navigate('/')}>Go Root</button>
        </div>
      );
    }

    it('C6.01: Transition from /healthcare to /legal dynamically updates copy', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <NavTestController />
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
      });

      // Navigate to /legal
      act(() => {
        fireEvent.click(screen.getByTestId('go-legal'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C6.02: Transition from /healthcare to /healthcare?vertical=legal dynamically switches to Legal', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <NavTestController />
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
      });

      // Navigate to /healthcare?vertical=legal
      act(() => {
        fireEvent.click(screen.getByTestId('go-override-legal'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar & Cole LLP/i);
      });
    });

    it('C6.03: Transition to invalid param gracefully preserves /healthcare path copy', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <NavTestController />
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
      });

      // Navigate to /healthcare?vertical=invalid_token
      act(() => {
        fireEvent.click(screen.getByTestId('go-invalid-param'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');
        expect(screen.getByTestId('hero-demo-cta')).toHaveTextContent(/Northstar Family Health/i);
      });
    });
  });
});
