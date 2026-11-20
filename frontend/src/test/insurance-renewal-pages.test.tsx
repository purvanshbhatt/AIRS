import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within } from '@testing-library/react';
import { renderWithRouter } from './utils/test-helpers';
import { ThemeProvider } from '../contexts/ThemeContext';
import { Footer } from '../components/layout/Footer';
import Contact from '../pages/Contact';
import InsuranceRenewalPage, { RENEWAL_CTA_TO, SAMPLE_PACK_HREF } from '../pages/InsuranceRenewal';
import DataAccessPage, { CONNECTOR_ROWS } from '../pages/DataAccess';
import appSource from '../App.tsx?raw';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    signInAsDemo: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
  }),
}));

function renderPublicPage(ui: React.ReactElement, options = {}) {
  return renderWithRouter(<ThemeProvider>{ui}</ThemeProvider>, options);
}

/** Text of the page body only: the shared navbar and footer are not this page's copy. */
function mainText(): string {
  return (screen.getByRole('main').textContent || '').replace(/\s+/g, ' ');
}

describe('Insurance renewal offer page (/insurance-renewal)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders one h1 that states the outcome in seven words or fewer', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const headings = screen.getAllByRole('heading', { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent('Answer your insurance renewal with proof');
    expect((headings[0].textContent || '').trim().split(/\s+/).length).toBeLessThanOrEqual(7);
  });

  it('sets the page title and meta description', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    expect(document.title).toBe('Answer your insurance renewal with proof | ResilAI');
    const meta = document.querySelector('meta[name="description"]') as HTMLMetaElement | null;
    expect(meta?.content).toMatch(/cyber-insurance application/i);
  });

  it('points every primary button at the contact form with the design-partner inquiry', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const buttons = screen.getAllByRole('link', { name: 'Send us one renewal' });
    expect(buttons).toHaveLength(2); // hero and final call to action
    for (const button of buttons) {
      expect(button).toHaveAttribute('href', RENEWAL_CTA_TO);
    }
    expect(RENEWAL_CTA_TO).toBe('/contact?tier=design-partner');
  });

  it('uses a query string the contact page really reads', () => {
    renderPublicPage(<Contact />, { initialEntries: [RENEWAL_CTA_TO] });
    const inquiry = screen.getByLabelText(/What would you like to discuss\?/i) as HTMLSelectElement;
    expect(inquiry.value).toBe('Design Partner Program');
  });

  it('links the sample answer pack PDF', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const samples = screen.getAllByRole('link', { name: /See a sample/i });
    expect(samples.length).toBeGreaterThanOrEqual(1);
    for (const sample of samples) {
      expect(sample).toHaveAttribute('href', SAMPLE_PACK_HREF);
    }
    expect(SAMPLE_PACK_HREF).toBe('/samples/insurance-answer-pack-sample.pdf');
  });

  it('labels the answer pack excerpt as sample data', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    expect(screen.getByTestId('sample-data-label')).toHaveTextContent('Sample data from a demo organisation');
  });

  it('shows the four answer states, with source and time on the evidenced answers', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const rows = screen.getAllByTestId(/^sample-answer-/);
    expect(rows.length).toBeGreaterThanOrEqual(3);
    expect(rows.length).toBeLessThanOrEqual(5);
    expect(new Set(rows.map((row) => row.getAttribute('data-value')))).toEqual(
      new Set(['yes', 'no', 'not_verified', 'human_only']),
    );

    const yes = rows.find((row) => row.getAttribute('data-value') === 'yes')!;
    expect(within(yes).getByText('Yes')).toBeInTheDocument();
    expect(yes).toHaveTextContent(/Evidence: Microsoft 365, as of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC/);

    const no = rows.find((row) => row.getAttribute('data-value') === 'no')!;
    expect(within(no).getByText('No')).toBeInTheDocument();
    expect(no).toHaveTextContent(/Evidence: .+, as of /);

    const notVerified = rows.find((row) => row.getAttribute('data-value') === 'not_verified')!;
    expect(within(notVerified).getByText('Not verified: answer manually')).toBeInTheDocument();
    expect(notVerified).not.toHaveTextContent('Evidence:');

    const humanOnly = rows.find((row) => row.getAttribute('data-value') === 'human_only')!;
    expect(within(humanOnly).getByText('You answer this')).toBeInTheDocument();
    expect(humanOnly).not.toHaveTextContent('Evidence:');
  });

  it('says plainly that the customer submits and ResilAI never does', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    expect(screen.getByTestId('never-submits')).toHaveTextContent(
      'You sign and submit the application. ResilAI never submits anything to an insurer.',
    );
  });

  it('states the design-partner offer, what is asked in return and the listed prices', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    expect(screen.getByTestId('design-partner-offer')).toHaveTextContent(
      'Send one client with a cyber-insurance renewal in the next 60 days. ResilAI fills the application from their live systems, with proof for each answer. Free for the first three design partners for 60 days.',
    );
    const text = mainText();
    expect(text).toContain('20-minute call each week for the 60 days');
    expect(text).toContain('only with your permission');
    expect(text).toContain('$149 per month');
    expect(text).toContain('$399 per month');
    expect(screen.getByRole('link', { name: 'See pricing' })).toHaveAttribute('href', '/pricing');
  });

  it('keeps the honest limits', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const text = mainText();
    expect(text).toContain('It is not legal or insurance advice');
    expect(text).toContain('It only sees what is connected');
    expect(text).toContain('No AI writes or rewrites an answer');
  });

  it('avoids the forbidden words', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const text = mainText();
    for (const word of ['telemetry', 'drift', 'deterministic', 'posture', 'leverage']) {
      expect(text).not.toMatch(new RegExp(word, 'i'));
    }
  });

  it('makes no "compliant" claim: the word appears once, inside the statement that it is never said', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    const text = mainText();
    expect(text.match(/compliant/gi) || []).toHaveLength(1);
    expect(text).toContain('It never says a practice "is compliant"');
    expect(text).not.toMatch(/HIPAA[- ]compliant|SOC ?2|ISO ?27001|HITRUST|certified by/i);
  });

  it('has no italic headings', () => {
    renderPublicPage(<InsuranceRenewalPage />);
    for (const heading of within(screen.getByRole('main')).getAllByRole('heading')) {
      expect(heading.className).not.toMatch(/\bitalic\b/);
      expect(heading.querySelector('em, i')).toBeNull();
    }
  });
});

describe('Trust page (/trust/data-access)', () => {
  it('renders one h1 with the page title', () => {
    renderPublicPage(<DataAccessPage />);
    const headings = screen.getAllByRole('heading', { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent('What ResilAI reads, and where it is kept');
    expect(document.title).toBe('What ResilAI reads, and where it is kept | ResilAI');
  });

  it('states where data is kept and how connection details are protected', () => {
    renderPublicPage(<DataAccessPage />);
    const text = mainText();
    expect(text).toContain('Google Cloud Run');
    expect(text).toContain('us-central1');
    expect(text).toContain('nam5');
    expect(text).toContain('AES-256-GCM');
  });

  it('lists each connector with what it reads and the access it asks for', () => {
    renderPublicPage(<DataAccessPage />);
    expect(CONNECTOR_ROWS.map((row) => row.id)).toEqual([
      'microsoft',
      'aws',
      'duo',
      'veeam',
      'wazuh',
      'splunk',
      'webhook',
    ]);
    for (const row of CONNECTOR_ROWS) {
      const element = screen.getByTestId(`connector-row-${row.id}`);
      expect(element).toHaveTextContent(row.name);
      for (const permission of row.permissions) {
        expect(within(element).getByText(permission)).toBeInTheDocument();
      }
    }

    const microsoft = screen.getByTestId('connector-row-microsoft');
    for (const scope of [
      'DeviceManagementManagedDevices.Read.All',
      'Policy.Read.All',
      'User.Read.All',
      'SecurityAlert.Read.All',
    ]) {
      expect(within(microsoft).getByText(scope)).toBeInTheDocument();
    }
    expect(microsoft).not.toHaveTextContent(/Mail\.Read|Files\.Read|Sites\.Read|ReadWrite/);

    expect(screen.getByTestId('connector-row-aws')).toHaveTextContent('SecurityAudit');
    expect(screen.getByTestId('connector-row-webhook')).toHaveTextContent(
      'It receives only what your own tools push to it',
    );
  });

  it('offers a business associate agreement on request, with a contact link', () => {
    renderPublicPage(<DataAccessPage />);
    expect(mainText()).toContain('We sign a business associate agreement with healthcare customers on request.');
    expect(screen.getByRole('link', { name: /Ask for a business associate agreement/i })).toHaveAttribute(
      'href',
      '/contact',
    );
  });

  it('says what removal erases and what it keeps', () => {
    renderPublicPage(<DataAccessPage />);
    const connector = screen.getByTestId('removal-connector');
    expect(connector).toHaveTextContent('its stored keys are erased');
    expect(connector).toHaveTextContent('Kept until you delete the organisation');
    const organisation = screen.getByTestId('removal-organisation');
    expect(organisation).toHaveTextContent('Everything that belongs to the organisation is erased');
    // The one thing that stays is named, not hidden.
    expect(organisation).toHaveTextContent('a marker holding the organisation\'s internal identifier');
  });

  it('claims no certification, test, uptime figure or insurance', () => {
    renderPublicPage(<DataAccessPage />);
    const text = mainText();
    expect(text).not.toMatch(
      /SOC ?2|ISO ?27001|HITRUST|penetration test|pen test|uptime|\d+(\.\d+)?%|HIPAA[- ]compliant|certified/i,
    );
  });
});

describe('Wiring', () => {
  it('registers both public routes before the app catch-all', () => {
    const renewal = appSource.indexOf('<Route path="/insurance-renewal" element={<InsuranceRenewalPage />} />');
    const trust = appSource.indexOf('<Route path="/trust/data-access" element={<DataAccessPage />} />');
    const catchAll = appSource.indexOf('<Route path="/*" element={<MainAppRoutes />} />');
    expect(renewal).toBeGreaterThan(-1);
    expect(trust).toBeGreaterThan(-1);
    expect(renewal).toBeLessThan(catchAll);
    expect(trust).toBeLessThan(catchAll);
  });

  it('links both pages from the footer', () => {
    renderPublicPage(<Footer />);
    expect(screen.getByRole('link', { name: 'Insurance renewal' })).toHaveAttribute('href', '/insurance-renewal');
    expect(screen.getByRole('link', { name: 'What we read' })).toHaveAttribute('href', '/trust/data-access');
  });
});
