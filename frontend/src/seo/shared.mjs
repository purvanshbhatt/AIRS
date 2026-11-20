// Shared by the React app and scripts/prerender-seo.mjs, so the tags a crawler
// reads in the static HTML are the same ones the app sets after it loads.
// Plain JavaScript on purpose: Node runs this file directly at build time.

/** Path without a trailing slash; the home page stays "/". */
export function normalisePath(pathname) {
  if (!pathname || pathname === '/') return '/';
  return pathname.replace(/\/+$/, '') || '/';
}

export function canonicalFor(data, path) {
  const clean = normalisePath(path);
  return clean === '/' ? `${data.site}/` : `${data.site}${clean}`;
}

export function findRoute(data, pathname) {
  const clean = normalisePath(pathname);
  return data.routes.find((route) => route.path === clean);
}

/** hreflang links for the home page and the regional pages; none for other pages. */
export function alternatesFor(data, route) {
  if (!route || !route.hreflangCluster) return [];
  return data.hreflang.map((entry) => ({
    hreflang: entry.hreflang,
    href: canonicalFor(data, entry.path),
  }));
}

export function headingFor(route) {
  return route.region ? route.region.h1 : route.h1;
}

function breadcrumb(data, route) {
  const items = [{ '@type': 'ListItem', position: 1, name: 'ResilAI', item: `${data.site}/` }];
  if (route.path !== '/') {
    items.push({
      '@type': 'ListItem',
      position: 2,
      name: route.region ? route.region.name : headingFor(route),
      item: canonicalFor(data, route.path),
    });
  }
  return { '@type': 'BreadcrumbList', itemListElement: items };
}

/** JSON-LD for one public route. */
export function schemaFor(data, route) {
  const url = canonicalFor(data, route.path);
  const page = {
    '@type': 'WebPage',
    '@id': `${url}#webpage`,
    url,
    name: route.title,
    description: route.description,
    inLanguage: 'en',
    isPartOf: { '@id': `${data.site}/#website` },
    publisher: { '@id': `${data.site}/#organization` },
    dateModified: data.lastmod,
  };
  const graph = [page, breadcrumb(data, route)];

  if (route.region) {
    graph.push({
      '@type': 'SoftwareApplication',
      name: 'ResilAI Incident Readiness Platform',
      applicationCategory: 'SecurityApplication',
      operatingSystem: 'Cloud, Web',
      url,
      description: route.description,
      areaServed: route.region.areaServed,
      offers: {
        '@type': 'AggregateOffer',
        priceCurrency: 'USD',
        lowPrice: '149',
        highPrice: '399',
        offerCount: 2,
        url: `${data.site}/pricing`,
      },
    });
    graph.push({
      '@type': 'FAQPage',
      mainEntity: route.region.faq.map((item) => ({
        '@type': 'Question',
        name: item.q,
        acceptedAnswer: { '@type': 'Answer', text: item.a },
      })),
    });
  }

  return { '@context': 'https://schema.org', '@graph': graph };
}
