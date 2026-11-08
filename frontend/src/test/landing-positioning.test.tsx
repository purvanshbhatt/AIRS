/**
 * Unit & Integration Test Suite: Milestone 2 (Three Distinct Landing & Positioning Experiences)
 * 
 * Validates Requirement R2 across:
 * - 1. General Platform Landing Experience (Headline, Question, Focus Areas, Demo CTA)
 * - 2. Healthcare Landing Experience (Headline, Question, Focus Areas, Demo CTA, EHR & Backups)
 * - 3. Legal Landing Experience (Headline, Question, Focus Areas, Demo CTA, Client Data & Vaults)
 * - 4. PublicNavbar Vertical Context Preservation (Badges, Links, Demo CTA)
 * - 5. App Routing Integration (/healthcare, /legal, /)
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import Landing from '../pages/Landing';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { VerticalProvider } from '../contexts/VerticalContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import { VERTICAL_CONFIGS } from '../config/verticals';
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

// Mock api module to prevent unintended network calls
vi.mock('../api', async () => {
  const actual = await vi.importActual<any>('../api');
  return {
    ...actual,
    setUnauthorizedHandler: vi.fn(),
    isApiConfigured: true,
  };
});

// Polyfill IntersectionObserver for Framer Motion viewport features
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

function renderWithProviders(ui: React.ReactElement, initialRoute = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <ThemeProvider>
        {ui}
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Milestone 2: Three Distinct Landing & Positioning Experiences', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // 1. General Platform Landing Positioning
  // ============================================================================
  describe('1. General Platform Landing Experience', () => {
    it('renders the universal general headline and core question', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      const headline = screen.getByTestId('landing-headline');
      expect(headline).toHaveTextContent('prove your ransomware readiness');

      const coreQuestion = screen.getByTestId('landing-core-question');
      expect(coreQuestion).toHaveTextContent('If a security or AI incident happens tomorrow, are you actually ready?');

      const badge = screen.getByTestId('hero-badge');
      expect(badge).toHaveTextContent('Non-LLM Readiness Scoring');
    });

    it('renders general three-persona value section (focus-areas section removed in landing overhaul)', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Executive\ \(L1\)/)).toBeInTheDocument();
      expect(screen.getByText(/Are\ we\ ready\ for\ an\ incident\?/)).toBeInTheDocument();
      expect(screen.getByText(/IT\ \&\ Security\ \(L3\)/)).toBeInTheDocument();
    });

    it('seeds Acme Technologies demo organization on CTA click', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <Landing />
          </VerticalProvider>
        </MemoryRouter>
      );

      const heroCta = screen.getByTestId('hero-demo-cta');
      expect(heroCta).toHaveTextContent(/Live Sandbox Demo/i);

      fireEvent.click(heroCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-acme-technologies');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });
  });

  // ============================================================================
  // 2. Healthcare Vertical Landing Positioning
  // ============================================================================
  describe('2. Healthcare Vertical Landing Experience', () => {
    it('renders healthcare-specific headline and clinic ransomware question', () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const headline = screen.getByTestId('landing-headline');
      expect(headline).toHaveTextContent("clinic's ransomware readiness");

      const coreQuestion = screen.getByTestId('landing-core-question');
      expect(coreQuestion).toHaveTextContent("If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?");

      const badge = screen.getByTestId('hero-badge');
      expect(badge).toHaveTextContent('HIPAA Verified');
    });

    it('renders healthcare persona questions (focus-areas section removed in landing overhaul)', () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Can\ we\ treat\ patients\ and\ stay\ open\?/)).toBeInTheDocument();
      expect(screen.getByText(/Clinical\ IT\ \/\ MSP\ \(L3\)/)).toBeInTheDocument();
    });

    it('seeds Northstar Family Health demo organization on CTA click', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const heroCta = screen.getByTestId('hero-demo-cta');
      expect(heroCta).toHaveTextContent(/Live Sandbox Demo/i);

      fireEvent.click(heroCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('adapts persona section and hero badge to healthcare (report-preview section removed in landing overhaul)', () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <Landing defaultVertical="healthcare" />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/What\ EHR\ or\ backup\ controls\ drifted\?/)).toBeInTheDocument();
      expect(screen.getByTestId('hero-badge')).toHaveTextContent('Clinical Continuity');
    });
  });

  // ============================================================================
  // 3. Legal Vertical Landing Positioning
  // ============================================================================
  describe('3. Legal Vertical Landing Experience', () => {
    it('renders legal headline and law firm client data core question', () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const headline = screen.getByTestId('landing-headline');
      expect(headline).toHaveTextContent("firm's ransomware resilience");

      const coreQuestion = screen.getByTestId('landing-core-question');
      expect(coreQuestion).toHaveTextContent('If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?');

      const badge = screen.getByTestId('hero-badge');
      expect(badge).toHaveTextContent('ABA 477R Verified');
    });

    it('renders legal persona questions (focus-areas section removed in landing overhaul)', () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Is\ client\ confidentiality\ protected\?/)).toBeInTheDocument();
      expect(screen.getByText(/Managing\ Partner\ \(L1\)/)).toBeInTheDocument();
    });

    it('seeds Northstar & Cole LLP demo organization on CTA click', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      const heroCta = screen.getByTestId('hero-demo-cta');
      expect(heroCta).toHaveTextContent(/Live Sandbox Demo/i);

      fireEvent.click(heroCta);

      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-cole');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('adapts persona section and hero badge to legal (report-preview section removed in landing overhaul)', () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <Landing defaultVertical="legal" />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/What\ evidence\ proves\ ABA\ compliance\?/)).toBeInTheDocument();
      expect(screen.getByTestId('hero-badge')).toHaveTextContent('Document Vault Protection');
    });
  });

  // ============================================================================
  // 4. PublicNavbar Vertical Navigation & Context Preservation
  // ============================================================================
  describe('4. PublicNavbar Vertical Navigation', () => {
    it('does not display vertical badge in general vertical', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <VerticalProvider initialVertical="general">
            <PublicNavbar />
          </VerticalProvider>
        </MemoryRouter>
      );

      expect(screen.queryByTestId('navbar-vertical-badge')).toBeNull();
      const brandLink = screen.getByTestId('navbar-brand-link');
      expect(brandLink).toHaveAttribute('href', '/');
    });

    it('displays Healthcare badge and preserves vertical in links and demo CTA', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <PublicNavbar />
          </VerticalProvider>
        </MemoryRouter>
      );

      const badge = screen.getByTestId('navbar-vertical-badge');
      expect(badge).toHaveTextContent('Healthcare & Clinics');

      const brandLink = screen.getByTestId('navbar-brand-link');
      expect(brandLink).toHaveAttribute('href', '/healthcare');

      const resultsLink = screen.getByRole('link', { name: /Results/i });
      expect(resultsLink).toHaveAttribute('href', '/results?vertical=healthcare');

      const navbarDemoBtn = screen.getByTestId('navbar-demo-cta');
      expect(navbarDemoBtn).toHaveAttribute('title', expect.stringContaining('Northstar Family Health'));

      fireEvent.click(navbarDemoBtn);
      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-health');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });

    it('displays Legal badge and preserves vertical in links and demo CTA', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <VerticalProvider initialVertical="legal">
            <PublicNavbar />
          </VerticalProvider>
        </MemoryRouter>
      );

      const badge = screen.getByTestId('navbar-vertical-badge');
      expect(badge).toHaveTextContent('Law Firms & Legal');

      const brandLink = screen.getByTestId('navbar-brand-link');
      expect(brandLink).toHaveAttribute('href', '/legal');

      const resultsLink = screen.getByRole('link', { name: /Results/i });
      expect(resultsLink).toHaveAttribute('href', '/results?vertical=legal');

      const navbarDemoBtn = screen.getByTestId('navbar-demo-cta');
      expect(navbarDemoBtn).toHaveAttribute('title', expect.stringContaining('Northstar & Cole LLP'));

      fireEvent.click(navbarDemoBtn);
      await waitFor(() => {
        expect(localStorage.getItem('resilai_selected_org_id')).toBe('demo-northstar-cole');
        expect(localStorage.getItem('resilai_demo_user')).toBe('true');
      });
    });
  });

  // ============================================================================
  // 5. App Routing Integration
  // ============================================================================
  describe('5. App Routing Integration', () => {
    it('navigates to Healthcare Landing on route /healthcare', async () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent("clinic's ransomware readiness");
      });
    });

    it('navigates to Legal Landing on route /legal', async () => {
      render(
        <MemoryRouter initialEntries={['/legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent("firm's ransomware resilience");
      });
    });

    it('renders General Landing on root route /', async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent('prove your ransomware readiness');
      });
    });

    it('switches vertical dynamically when visiting /?vertical=healthcare', async () => {
      render(
        <MemoryRouter initialEntries={['/?vertical=healthcare']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent("clinic's ransomware readiness");
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/ransomware hits your clinic/i);
      });
    });

    it('switches vertical dynamically when visiting /?vertical=legal', async () => {
      render(
        <MemoryRouter initialEntries={['/?vertical=legal']}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('landing-headline')).toHaveTextContent("firm's ransomware resilience");
        expect(screen.getByTestId('landing-core-question')).toHaveTextContent(/protect client data/i);
      });
    });
  });

  // ============================================================================
  // 6. Overhauled page structure: CTAs, FAQ, SEO head, no fabricated numbers
  // ============================================================================
  describe('6. Landing page structure (post-overhaul)', () => {
    const renderVertical = (v: 'general' | 'healthcare' | 'legal') =>
      render(
        <MemoryRouter initialEntries={[v === 'general' ? '/' : `/${v}`]}>
          <VerticalProvider initialVertical={v}>
            <Landing defaultVertical={v} />
          </VerticalProvider>
        </MemoryRouter>
      );

    it('primary CTA links to /login, carrying the vertical when not general', () => {
      const { unmount } = renderVertical('general');
      const general = screen.getAllByRole('link', { name: /Start Free Readiness Scan/i });
      expect(general.length).toBeGreaterThan(0);
      general.forEach((a) => expect(a).toHaveAttribute('href', '/login'));
      unmount();

      renderVertical('legal');
      screen
        .getAllByRole('link', { name: /Start Free Readiness Scan/i })
        .forEach((a) => expect(a).toHaveAttribute('href', '/login?vertical=legal'));
    });

    it('navbar Pricing link points to /pricing (vertical-aware)', () => {
      render(
        <MemoryRouter initialEntries={['/healthcare']}>
          <VerticalProvider initialVertical="healthcare">
            <PublicNavbar />
          </VerticalProvider>
        </MemoryRouter>
      );
      expect(screen.getByRole('link', { name: /Pricing/i })).toHaveAttribute('href', '/pricing?vertical=healthcare');
    });

    it('renders the FAQ and expands an item on click', () => {
      renderVertical('general');
      expect(screen.getByRole('heading', { name: /Frequently asked questions/i })).toBeInTheDocument();
      const item = screen.getByRole('button', { name: /Do we need to install software agents/i });
      expect(item).toHaveAttribute('aria-expanded', 'false');
      fireEvent.click(item);
      expect(item).toHaveAttribute('aria-expanded', 'true');
    });

    it('SEOHead sets a document title and vertical-specific description', async () => {
      renderVertical('general');
      await waitFor(() => expect(document.title).toMatch(/ResilAI/));
      expect(document.querySelector('meta[name="description"]')?.getAttribute('content')).toBeTruthy();
    });

    it('does not display fabricated customer counts or testimonial-style stats', () => {
      renderVertical('general');
      const text = document.body.textContent ?? '';
      expect(text).not.toMatch(/\b\d[\d,]*\+?\s+(customers|clients|organizations|companies|users)\b/i);
      expect(text).not.toMatch(/trusted by \d/i);
    });
  });
});
