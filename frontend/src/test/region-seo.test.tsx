import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithRouter } from './utils/test-helpers';
import { ThemeProvider } from '../contexts/ThemeContext';
import RegionLanding from '../pages/RegionLanding';
import { RouteSEO } from '../components/common/RouteSEO';
import { alternatesFor, canonicalFor, findPublicRoute, publicRoutes, regionRoutes, schemaFor } from '../seo';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: null, signInAsDemo: vi.fn().mockResolvedValue(undefined), clearError: vi.fn() }),
}));

function renderPage(ui: React.ReactElement, options = {}) {
  return renderWithRouter(<ThemeProvider>{ui}</ThemeProvider>, options);
}

const hreflangTags = () =>
  Array.from(document.querySelectorAll('link[rel="alternate"][hreflang]')) as HTMLLinkElement[];

afterEach(() => {
  hreflangTags().forEach((tag) => tag.remove());
  document.getElementById('resilai-page-jsonld')?.remove();
});

describe('regional pages', () => {
  it('has one page each for the US, Europe, the Gulf and Australia', () => {
    expect(regionRoutes.map((route) => route.path)).toEqual(['/us', '/europe', '/gulf', '/australia']);
  });

  it.each(regionRoutes.map((route) => [route.path, route] as const))(
    '%s shows its heading, every listed law and every question',
    (path, route) => {
      renderPage(<RegionLanding path={path} />);
      const region = route.region!;
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(region.h1);
      region.frameworks.forEach((framework) => {
        expect(screen.getByRole('heading', { name: framework.name })).toBeInTheDocument();
      });
      region.faq.forEach((item) => {
        expect(screen.getByText(item.q)).toBeInTheDocument();
        expect(screen.getByText(item.a)).toBeInTheDocument();
      });
    },
  );

  it('says plainly that it does not certify compliance', () => {
    renderPage(<RegionLanding path="/gulf" />);
    expect(screen.getAllByText(/does not certify compliance or give legal advice/i).length).toBeGreaterThan(0);
  });

  it('links to the other three regions', () => {
    renderPage(<RegionLanding path="/australia" />);
    const nav = screen.getByRole('navigation', { name: /other regions/i });
    expect(nav.querySelectorAll('a')).toHaveLength(3);
  });

  it('sets the canonical link, hreflang links and FAQ structured data', async () => {
    renderPage(<RegionLanding path="/europe" />);
    await waitFor(() => expect(document.title).toMatch(/EU & UK/));
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe('https://resilai.org/europe');
    const byLang = Object.fromEntries(hreflangTags().map((tag) => [tag.hreflang, tag.href]));
    expect(byLang['en-GB']).toBe('https://resilai.org/europe');
    expect(byLang['en-AE']).toBe('https://resilai.org/gulf');
    expect(byLang['en-AU']).toBe('https://resilai.org/australia');
    expect(byLang['en-US']).toBe('https://resilai.org/us');
    expect(byLang['x-default']).toBe('https://resilai.org/');
    const schema = JSON.parse(document.getElementById('resilai-page-jsonld')!.textContent || '{}');
    const types = schema['@graph'].map((node: { '@type': string }) => node['@type']);
    expect(types).toEqual(expect.arrayContaining(['WebPage', 'BreadcrumbList', 'SoftwareApplication', 'FAQPage']));
  });
});

describe('public route data', () => {
  it('keeps titles and descriptions inside search-result lengths', () => {
    publicRoutes.forEach((route) => {
      expect(route.title.length, route.path).toBeLessThanOrEqual(80);
      expect(route.description.length, route.path).toBeGreaterThanOrEqual(90);
      expect(route.description.length, route.path).toBeLessThanOrEqual(190);
    });
  });

  it('has no duplicate paths or titles', () => {
    expect(new Set(publicRoutes.map((route) => route.path)).size).toBe(publicRoutes.length);
    expect(new Set(publicRoutes.map((route) => route.title)).size).toBe(publicRoutes.length);
  });

  it('gives the home page the same hreflang links as the regional pages', () => {
    expect(alternatesFor(findPublicRoute('/'))).toEqual(alternatesFor(findPublicRoute('/gulf')));
    expect(alternatesFor(findPublicRoute('/pricing'))).toEqual([]);
  });

  it('ignores a trailing slash', () => {
    expect(findPublicRoute('/europe/')?.path).toBe('/europe');
    expect(canonicalFor('/europe/')).toBe('https://resilai.org/europe');
    expect(canonicalFor('/')).toBe('https://resilai.org/');
  });

  it('lists the served countries on the regional structured data', () => {
    const app = (schemaFor(findPublicRoute('/gulf')!)['@graph'] as Array<Record<string, unknown>>).find(
      (node) => node['@type'] === 'SoftwareApplication',
    );
    expect(app?.areaServed).toEqual(['AE', 'SA', 'QA', 'BH', 'KW', 'OM']);
  });
});

describe('RouteSEO', () => {
  it('sets tags for a public page that has none of its own', async () => {
    renderPage(<RouteSEO />, { initialEntries: ['/about'] });
    await waitFor(() => expect(document.title).toMatch(/About ResilAI/));
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe('https://resilai.org/about');
  });

  it('leaves pages that set their own tags alone', () => {
    document.title = 'unchanged';
    renderPage(<RouteSEO />, { initialEntries: ['/pricing'] });
    expect(document.title).toBe('unchanged');
  });
});
