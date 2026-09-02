import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithRouter } from './utils/test-helpers';
import { ThemeProvider } from '../contexts/ThemeContext';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import About from '../pages/About';
import Results from '../pages/Results';
import PublicAi from '../pages/PublicAi';
import Pricing from '../pages/Pricing';
import Contact from '../pages/Contact';
import { COMPANY_INFO } from '../config/company';

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    signInAsDemo: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
  }),
}));

function renderPublicPage(ui: React.ReactElement, options = {}) {
  return renderWithRouter(
    <ThemeProvider>
      {ui}
    </ThemeProvider>,
    options
  );
}

describe('Public Website Expansion & Google for Startups Review Readiness', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('1. Public Navigation (PublicNavbar)', () => {
    it('renders all required public navigation links', () => {
      renderPublicPage(<PublicNavbar />);
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Results')).toBeInTheDocument();
      expect(screen.getByText('AI Architecture')).toBeInTheDocument();
      expect(screen.getByText('Pricing')).toBeInTheDocument();
      expect(screen.getByText('About Us')).toBeInTheDocument();
      expect(screen.getByText('Contact')).toBeInTheDocument();
      expect(screen.getByText('Docs')).toBeInTheDocument();
      expect(screen.getByText('Sign In')).toBeInTheDocument();
      expect(screen.getByText('Get Started')).toBeInTheDocument();
    });

    it('toggles mobile menu on button click', () => {
      renderPublicPage(<PublicNavbar />);
      const toggleButton = screen.getByLabelText('Open navigation menu');
      expect(toggleButton).toBeInTheDocument();
      fireEvent.click(toggleButton);
      expect(screen.getByText('Sign In to Organization')).toBeInTheDocument();
    });
  });

  describe('2. About Us Page (/about) - Google for Startups Criteria', () => {
    it('renders company mission and problem statement', () => {
      renderPublicPage(<About />);
      expect(screen.getByText(/Bridging the Gap Between Cybersecurity Telemetry/i)).toBeInTheDocument();
      expect(screen.getByText(/Why We Built ResilAI/i)).toBeInTheDocument();
    });

    it('renders foundation year prominently', () => {
      renderPublicPage(<About />);
      expect(screen.getByText(String(COMPANY_INFO.foundedYear))).toBeInTheDocument();
    });

    it('renders founder profile with Purvansh Bhatt, role, and LinkedIn link', () => {
      renderPublicPage(<About />);
      expect(screen.getByText(COMPANY_INFO.founder.name)).toBeInTheDocument();
      expect(screen.getByText(COMPANY_INFO.founder.role)).toBeInTheDocument();
      const linkedinLink = screen.getByRole('link', { name: /LinkedIn Profile/i });
      expect(linkedinLink).toHaveAttribute('href', COMPANY_INFO.founder.linkedin);
    });

    it('renders core non-negotiable trust invariants', () => {
      renderPublicPage(<About />);
      expect(screen.getByText(/LLMs Never Calculate Scores/i)).toBeInTheDocument();
      expect(screen.getByText(/Telemetry Beats Questionnaires/i)).toBeInTheDocument();
      expect(screen.getByText(/Cryptographic Provenance/i)).toBeInTheDocument();
    });
  });

  describe('3. Results Page (/results)', () => {
    it('renders transformation from fragmented data to executive readiness', () => {
      renderPublicPage(<Results />);
      expect(screen.getByText(/From Security Telemetry to/i)).toBeInTheDocument();
      expect(screen.getByText('Before ResilAI')).toBeInTheDocument();
      expect(screen.getByText('With ResilAI')).toBeInTheDocument();
    });

    it('renders illustrative data disclaimer badge', () => {
      renderPublicPage(<Results />);
      expect(screen.getByText('DEMO / ILLUSTRATIVE DATA')).toBeInTheDocument();
    });

    it('allows switching between illustrative scenarios', () => {
      renderPublicPage(<Results />);
      expect(screen.getByText(/Scenario A: Identity Privilege Drift/i)).toBeInTheDocument();
      const clinicTab = screen.getByText(/Scenario B: Multi-Facility Clinic Operations/i);
      fireEvent.click(clinicTab);
      expect(screen.getByText(/READY FOR TODAY: Digital Clinical Operations Verified/i)).toBeInTheDocument();
    });
  });

  describe('4. AI Architecture Page (/ai)', () => {
    it('renders dual-layer architecture explanation', () => {
      renderPublicPage(<PublicAi />);
      expect(screen.getByText(/AI That Explains Security Risk/i)).toBeInTheDocument();
      expect(screen.getByText(/Not AI That Invents It/i)).toBeInTheDocument();
      expect(screen.getByText(/Layer 1: Deterministic Verification & Scoring Engine/i)).toBeInTheDocument();
      expect(screen.getByText(/Layer 2: Business Impact Intelligence \(Gemini\)/i)).toBeInTheDocument();
    });

    it('highlights deterministic invariants (LLM never scores)', () => {
      renderPublicPage(<PublicAi />);
      expect(screen.getByText(/LLM never calculates scores/i)).toBeInTheDocument();
      expect(screen.getByText(/LLM never modifies findings/i)).toBeInTheDocument();
    });

    it('allows toggling interactive translation examples', () => {
      renderPublicPage(<PublicAi />);
      const backupTab = screen.getByRole('button', { name: /Immutable Storage Verification/i });
      fireEvent.click(backupTab);
      expect(screen.getByText(/Veeam & S3 telemetry verifies daily snapshot/i)).toBeInTheDocument();
    });
  });

  describe('5. Pricing Page (/pricing)', () => {
    it('renders Design Partner, Growth, and Enterprise tiers', () => {
      renderPublicPage(<Pricing />);
      expect(screen.getByRole('heading', { name: 'Design Partner Program' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Growth' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Enterprise' })).toBeInTheDocument();
      expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    });

    it('renders transparent call-to-actions linking to contact flow', () => {
      renderPublicPage(<Pricing />);
      const cta = screen.getByRole('link', { name: /Become a Design Partner/i });
      expect(cta).toHaveAttribute('href', '/contact?tier=design-partner');
    });
  });

  describe('6. Contact Us Page (/contact)', () => {
    it('renders contact form with all required fields', () => {
      renderPublicPage(<Contact />);
      expect(screen.getByLabelText(/Full Name \*/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Work Email \*/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Organization \/ Clinic Name \*/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/What would you like to discuss\?/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Talk to ResilAI/i })).toBeInTheDocument();
    });

    it('pre-selects inquiry type from URL search params', () => {
      renderPublicPage(<Contact />, { initialEntries: ['/contact?tier=design-partner'] });
      const inquirySelect = screen.getByLabelText(/What would you like to discuss\?/i) as HTMLSelectElement;
      expect(inquirySelect.value).toBe('Design Partner Program');
    });

    it('shows validation error when required fields are missing', async () => {
      renderPublicPage(<Contact />);
      const submitBtn = screen.getByRole('button', { name: /Talk to ResilAI/i });
      fireEvent.click(submitBtn);
      expect(await screen.findByText('Please enter your full name.')).toBeInTheDocument();
    });

    it('successfully submits valid contact form with confirmation feedback', async () => {
      renderPublicPage(<Contact />);
      fireEvent.change(screen.getByLabelText(/Full Name \*/i), { target: { value: 'Dr. John Doe' } });
      fireEvent.change(screen.getByLabelText(/Work Email \*/i), { target: { value: 'jdoe@clinic.org' } });
      fireEvent.change(screen.getByLabelText(/Organization \/ Clinic Name \*/i), { target: { value: 'Metro Health' } });

      const submitBtn = screen.getByRole('button', { name: /Talk to ResilAI/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText('Message Received')).toBeInTheDocument();
      expect(screen.getByText(/Thank you for reaching out to ResilAI/i)).toBeInTheDocument();
    });
  });

  describe('7. Upgraded Public Footer (Footer)', () => {
    it('renders 4-column structure with company, product, resources, and Maidensail badge', () => {
      renderPublicPage(<Footer />);
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Company')).toBeInTheDocument();
      expect(screen.getByText('Resources & Trust')).toBeInTheDocument();
      expect(screen.getByAltText('Featured on Maidensail')).toBeInTheDocument();
      expect(screen.getByText(new RegExp(`Founded ${COMPANY_INFO.foundedYear}`, 'i'))).toBeInTheDocument();
    });
  });
});
