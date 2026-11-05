/**
 * Adversarial Stress & Isolation Test Suite: Milestone 2
 * Author: teamwork_preview_challenger_m2_r5_2
 * 
 * Objectives:
 * 1. Stress-test PublicNavbar with and without ThemeProvider (SafeThemeToggle isolation).
 * 2. Stress-test Landing across responsive viewports (mobile 375px, tablet 768px, desktop 1280px).
 * 3. Stress-test rapid-fire demo CTA clicks (concurrency and race condition resilience).
 * 4. Stress-test terminal tabs, copy functionality, and timer unmounting.
 * 5. Stress-test malformed props and query parameter edge cases.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useNavigate } from 'react-router-dom';

import Landing from '../pages/Landing';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { VerticalProvider } from '../contexts/VerticalContext';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import type { VerticalKey } from '../types/vertical';

// Mock AuthContext for demo auth resilience
const mockSignInAsDemo = vi.fn().mockResolvedValue(undefined);
const mockClearError = vi.fn();

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
      signInAsDemo: mockSignInAsDemo,
      clearError: mockClearError,
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
  };
});

// Polyfill MockIntersectionObserver for jsdom
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

describe('Adversarial Challenger Suite — Milestone 2 UI & Isolation Stress', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    window.innerWidth = 1024;
    window.innerHeight = 768;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ==========================================================================
  // CHALLENGE 1: PublicNavbar & SafeThemeToggle Context Isolation
  // ==========================================================================
  describe('Challenge 1: PublicNavbar SafeThemeToggle Isolation', () => {
    it('renders PublicNavbar completely WITHOUT ThemeProvider ancestor without throwing', () => {
      // Intentionally omit ThemeProvider
      expect(() => {
        render(
          <MemoryRouter initialEntries={['/']}>
            <PublicNavbar />
          </MemoryRouter>
        );
      }).not.toThrow();

      // Verify theme buttons exist inside SafeThemeToggle in both desktop and mobile containers
      const lightBtns = screen.getAllByRole('button', { name: /Switch to Light theme/i });
      const darkBtns = screen.getAllByRole('button', { name: /Switch to Dark theme/i });
      const systemBtns = screen.getAllByRole('button', { name: /Switch to System theme/i });

      expect(lightBtns.length).toBeGreaterThanOrEqual(2);
      expect(darkBtns.length).toBeGreaterThanOrEqual(2);
      expect(systemBtns.length).toBeGreaterThanOrEqual(2);
    });

    it('interacts with SafeThemeToggle buttons without ThemeProvider ancestor without crashing', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <PublicNavbar />
        </MemoryRouter>
      );

      const darkBtns = screen.getAllByRole('button', { name: /Switch to Dark theme/i });
      const lightBtns = screen.getAllByRole('button', { name: /Switch to Light theme/i });

      // Click dark theme on desktop toggle
      expect(() => fireEvent.click(darkBtns[0])).not.toThrow();
      expect(localStorage.getItem('resilai-theme')).toBe('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);

      // Click light theme on desktop toggle
      expect(() => fireEvent.click(lightBtns[0])).not.toThrow();
      expect(localStorage.getItem('resilai-theme')).toBe('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('seamlessly adopts outer ThemeProvider when one is provided', () => {
      function ThemeConsumer() {
        const { theme } = useTheme();
        return <div data-testid="current-outer-theme">{theme}</div>;
      }

      render(
        <MemoryRouter initialEntries={['/']}>
          <ThemeProvider defaultTheme="light">
            <PublicNavbar />
            <ThemeConsumer />
          </ThemeProvider>
        </MemoryRouter>
      );

      expect(screen.getByTestId('current-outer-theme')).toHaveTextContent('light');

      // Click dark theme in navbar
      const darkBtns = screen.getAllByRole('button', { name: /Switch to Dark theme/i });
      fireEvent.click(darkBtns[0]);

      // Outer consumer reflects theme change because SafeThemeToggle used outer context
      expect(screen.getByTestId('current-outer-theme')).toHaveTextContent('dark');
    });

    it('renders PublicNavbar outside VerticalProvider with safe fallback', () => {
      // Intentionally omit VerticalProvider
      expect(() => {
        render(
          <MemoryRouter initialEntries={['/healthcare']}>
            <PublicNavbar />
          </MemoryRouter>
        );
      }).not.toThrow();

      // Should still detect vertical from location pathname
      expect(screen.getByTestId('navbar-vertical-badge')).toHaveTextContent('Healthcare & Clinics');
    });
  });

  // ==========================================================================
  // CHALLENGE 2: Responsive Viewports & Mobile Menu Navigation
  // ==========================================================================
  describe('Challenge 2: Responsive Viewport Stress', () => {
    it('handles mobile viewport (375x667) and toggles mobile drawer', async () => {
      window.innerWidth = 375;
      window.innerHeight = 667;

      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <PublicNavbar />
          </VerticalProvider>
        </MemoryRouter>
      );

      // Mobile hamburger button
      const toggleBtn = screen.getByRole('button', { name: /Open navigation menu/i });
      expect(toggleBtn).toBeInTheDocument();
      expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');

      // Open drawer
      fireEvent.click(toggleBtn);
      expect(toggleBtn).toHaveAttribute('aria-expanded', 'true');

      // Mobile demo CTA in drawer
      const mobileDemoCta = screen.getByTestId('navbar-mobile-demo-cta');
      expect(mobileDemoCta).toBeInTheDocument();
      expect(mobileDemoCta).toHaveTextContent(/Explore Demo Sandbox \(Northstar Family Health\)/i);

      // Click mobile demo CTA
      fireEvent.click(mobileDemoCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });

      // Drawer closes upon CTA click
      expect(screen.queryByTestId('navbar-mobile-demo-cta')).toBeNull();
    });

    it('renders on tablet viewport (768x1024) across verticals', () => {
      window.innerWidth = 768;
      window.innerHeight = 1024;

      const { unmount } = render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');
      expect(screen.getByTestId('landing-focus-areas')).toHaveTextContent('Client data protection');
      unmount();
    });

    it('renders on widescreen viewport (1920x1080) across verticals', () => {
      window.innerWidth = 1920;
      window.innerHeight = 1080;

      const { unmount } = render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
      unmount();
    });
  });

  // ==========================================================================
  // CHALLENGE 3: Rapid Concurrent Demo CTA Clicks (Stress Harness)
  // ==========================================================================
  describe('Challenge 3: Rapid Demo CTA Clicks Stress Harness', () => {
    it('endures 25 rapid-fire clicks on Hero Demo CTA without unhandled rejections', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const heroCta = screen.getByTestId('hero-demo-cta');

      // Hammer the CTA 25 times in a synchronous loop
      for (let i = 0; i < 25; i++) {
        fireEvent.click(heroCta);
      }

      await waitFor(() => {
        expect(mockSignInAsDemo).toHaveBeenCalled();
        expect(mockClearError).toHaveBeenCalled();
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('endures 25 rapid-fire clicks on Bottom Demo CTA without failure', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const bottomCta = screen.getByTestId('bottom-demo-cta');

      for (let i = 0; i < 25; i++) {
        fireEvent.click(bottomCta);
      }

      await waitFor(() => {
        expect(mockSignInAsDemo).toHaveBeenCalled();
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-cole');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('endures rapid switching between Hero CTA and Navbar CTA', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      const heroCta = screen.getByTestId('hero-demo-cta');
      const navbarCta = screen.getByTestId('navbar-demo-cta');

      for (let i = 0; i < 10; i++) {
        fireEvent.click(heroCta);
        fireEvent.click(navbarCta);
      }

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-acme-technologies');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });
  });

  // ==========================================================================
  // CHALLENGE 4: Terminal Widget & Tab Rapid Switching Stress
  // ==========================================================================
  describe('Challenge 4: Terminal Widget Stress & Clipboard Resilience', () => {
    it('endures 30 rapid tab switches between Live Stream, cURL, and JSON', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      const liveStreamTab = screen.getByRole('button', { name: /Live Stream/i });
      const curlTab = screen.getByRole('button', { name: /cURL/i });
      const jsonTab = screen.getByRole('button', { name: /JSON/i });

      for (let i = 0; i < 10; i++) {
        fireEvent.click(curlTab);
        fireEvent.click(jsonTab);
        fireEvent.click(liveStreamTab);
      }

      // Live stream is still visible and operational
      expect(screen.getByText('ENGINE ACTIVE')).toBeInTheDocument();
    });

    it('handles copy button safely with clipboard API mock', async () => {
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      const copyBtn = screen.getByTitle('Copy to clipboard');

      for (let i = 0; i < 5; i++) {
        fireEvent.click(copyBtn);
      }

      expect(writeTextMock).toHaveBeenCalled();
    });

    it('cleans up interval timer safely on unmount without warnings', () => {
      const { unmount } = render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      // Unmounting should clear interval cleanly
      expect(() => unmount()).not.toThrow();
    });
  });

  // ==========================================================================
  // CHALLENGE 5: Edge Cases, Malformed Verticals & Precedence
  // ==========================================================================
  describe('Challenge 5: Edge Cases and Precedence Under Stress', () => {
    it('handles completely invalid defaultVertical prop gracefully falling back to general', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <Landing defaultVertical={'nonexistent_vertical' as any} />
        </MemoryRouter>
      );

      expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
    });

    it('handles bizarre query parameters safely without crash', () => {
      render(
        <MemoryRouter initialEntries={['/?vertical=???&&foo=bar&vertical=&&']}>
          <Landing />
        </MemoryRouter>
      );

      expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');
    });

    it('handles rapid sequential route switches across all 3 verticals', async () => {
      const { unmount, rerender } = render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing defaultVertical="general" />
          </VerticalProvider>
        </MemoryRouter>
      );
      expect(screen.getByTestId('landing-headline')).toHaveTextContent('ResilAI — AI Incident Readiness Platform');

      rerender(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );
      expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for healthcare organizations');

      rerender(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );
      expect(screen.getByTestId('landing-headline')).toHaveTextContent('Incident readiness for law firms');

      unmount();
    });
  });
});
