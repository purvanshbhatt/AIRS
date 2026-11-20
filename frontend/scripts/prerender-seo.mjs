#!/usr/bin/env node
/**
 * Writes one static HTML file per public route after `vite build`.
 *
 * The site is a single-page app. Crawlers that do not run JavaScript, which
 * includes most AI crawlers, would otherwise read the home page's title and an
 * empty body on every URL. Each file written here carries the route's own
 * title, description, canonical link, hreflang links, structured data and a
 * plain-HTML copy of the page's main text. React replaces that text when it
 * mounts.
 *
 * Usage: node scripts/prerender-seo.mjs <dist-dir> [--public]
 *   --public  also refresh public/sitemap.xml so the dev server matches.
 *
 * Firebase Hosting serves `<route>.html` at `/<route>` because the marketing
 * target sets `cleanUrls: true`.
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { alternatesFor, canonicalFor, headingFor, schemaFor } from '../src/seo/shared.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const frontendDir = resolve(here, '..');
const data = JSON.parse(readFileSync(join(frontendDir, 'src/seo/publicRoutes.json'), 'utf8'));

const args = process.argv.slice(2);
const distArg = args.find((arg) => !arg.startsWith('--'));
if (!distArg) {
  console.error('Usage: node scripts/prerender-seo.mjs <dist-dir> [--public]');
  process.exit(1);
}
const distDir = resolve(frontendDir, distArg);

const esc = (text) =>
  String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

/** Replace one tag, and fail loudly if the template no longer has it. */
function replaceTag(html, pattern, replacement, label) {
  if (!pattern.test(html)) {
    throw new Error(`prerender-seo: index.html has no ${label} tag to replace`);
  }
  return html.replace(pattern, () => replacement);
}

function setMeta(html, attr, name, content) {
  const pattern = new RegExp(`<meta ${attr}="${name}" content="[^"]*"\\s*/?>`);
  return replaceTag(html, pattern, `<meta ${attr}="${name}" content="${esc(content)}" />`, `${attr}="${name}"`);
}

function headFor(template, route) {
  const url = canonicalFor(data, route.path);
  let html = template;

  html = replaceTag(html, /<title>[\s\S]*?<\/title>/, `<title>${esc(route.title)}</title>`, 'title');
  html = setMeta(html, 'name', 'description', route.description);
  html = setMeta(html, 'property', 'og:title', route.title);
  html = setMeta(html, 'property', 'og:description', route.description);
  html = setMeta(html, 'property', 'og:url', url);
  html = setMeta(html, 'name', 'twitter:title', route.title);
  html = setMeta(html, 'name', 'twitter:description', route.description);

  const keywordsPattern = /<meta name="keywords" content="[^"]*"\s*\/?>\s*/;
  if (route.keywords) {
    html = setMeta(html, 'name', 'keywords', route.keywords);
  } else if (route.path !== '/') {
    html = html.replace(keywordsPattern, '');
  }

  // The template may already carry the home page's hreflang links.
  html = html.replace(/\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*"\s*\/?>/g, '');
  const alternates = alternatesFor(data, route)
    .map((link) => `<link rel="alternate" hreflang="${esc(link.hreflang)}" href="${esc(link.href)}" />`)
    .join('\n    ');
  html = replaceTag(
    html,
    /<link rel="canonical" href="[^"]*"\s*\/?>/,
    `<link rel="canonical" href="${esc(url)}" />${alternates ? `\n    ${alternates}` : ''}`,
    'canonical',
  );

  // "<" is escaped so the JSON can never close the script tag early.
  const schema = JSON.stringify(schemaFor(data, route)).replace(/</g, '\\u003c');
  html = html.replace(
    '</head>',
    `  <script type="application/ld+json" id="resilai-page-jsonld">${schema}</script>\n  </head>`,
  );
  return html;
}

function bodyFor(route) {
  const parts = [`<h1>${esc(headingFor(route))}</h1>`];

  if (route.region) {
    const region = route.region;
    parts.push(`<p>${esc(region.intro)}</p>`);
    parts.push(`<h2>What ResilAI lists for ${esc(region.name)}</h2>`);
    parts.push(
      '<p>Each law is listed with the reason it applies to you and a link to the official source. ' +
        'ResilAI shows the evidence your systems give. It does not certify compliance or give legal advice.</p>',
    );
    parts.push(
      `<ul>${region.frameworks
        .map((item) => `<li><strong>${esc(item.name)}</strong>: ${esc(item.note)}</li>`)
        .join('')}</ul>`,
    );
    parts.push('<h2>What ResilAI checks every day</h2>');
    parts.push(
      `<ul>${data.dailyChecks
        .map((item) => `<li><strong>${esc(item.title)}</strong>: ${esc(item.text)}</li>`)
        .join('')}</ul>`,
    );
    parts.push(`<h2>Questions from ${esc(region.name)}</h2>`);
    parts.push(`<dl>${region.faq.map((item) => `<dt>${esc(item.q)}</dt><dd>${esc(item.a)}</dd>`).join('')}</dl>`);
  } else {
    for (const paragraph of route.summary || [route.description]) {
      parts.push(`<p>${esc(paragraph)}</p>`);
    }
  }

  const links = data.routes
    .filter((other) => other.path !== route.path)
    .map((other) => `<li><a href="${esc(other.path)}">${esc(other.region ? `ResilAI in ${other.region.name}` : headingFor(other))}</a></li>`)
    .join('');
  parts.push(`<nav aria-label="ResilAI pages"><ul>${links}</ul></nav>`);
  return parts.join('\n');
}

function sitemap() {
  const urls = data.routes
    .map((route) => {
      const alternates = alternatesFor(data, route)
        .map((link) => `    <xhtml:link rel="alternate" hreflang="${link.hreflang}" href="${link.href}" />`)
        .join('\n');
      return [
        '  <url>',
        `    <loc>${canonicalFor(data, route.path)}</loc>`,
        `    <lastmod>${data.lastmod}</lastmod>`,
        `    <changefreq>${route.changefreq}</changefreq>`,
        `    <priority>${route.priority}</priority>`,
        alternates,
        '  </url>',
      ]
        .filter(Boolean)
        .join('\n');
    })
    .join('\n');
  return (
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<!-- Generated by scripts/prerender-seo.mjs from src/seo/publicRoutes.json. Do not edit by hand. -->\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' +
    `${urls}\n</urlset>\n`
  );
}

// Strip what an earlier run added, so running the script twice on the same
// build gives the same files as running it once.
const template = readFileSync(join(distDir, 'index.html'), 'utf8')
  .replace(/\s*<script type="application\/ld\+json" id="resilai-page-jsonld">[\s\S]*?<\/script>/g, '')
  .replace(/\s*<noscript data-seo-static>[\s\S]*?<\/noscript>/g, '');
const rootOpen = '<div id="root">';
if (!template.includes(rootOpen)) {
  throw new Error('prerender-seo: index.html has no <div id="root">');
}

let written = 0;
for (const route of data.routes) {
  let html = headFor(template, route);
  const body = bodyFor(route);

  if (route.path === '/') {
    // index.html is also what the signed-in app loads on every app URL, so the
    // home text goes in <noscript>: crawlers read it, app users never see it.
    html = html.replace('</body>', `  <noscript data-seo-static>\n${body}\n    </noscript>\n  </body>`);
    writeFileSync(join(distDir, 'index.html'), html);
  } else {
    html = html.replace(
      rootOpen,
      `${rootOpen}\n<div id="seo-static" style="max-width:56rem;margin:0 auto;padding:2rem 1rem;line-height:1.6">\n${body}\n</div>`,
    );
    const target = join(distDir, `${route.path.slice(1)}.html`);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, html);
  }
  written += 1;
}

writeFileSync(join(distDir, 'sitemap.xml'), sitemap());
if (args.includes('--public')) {
  writeFileSync(join(frontendDir, 'public/sitemap.xml'), sitemap());
}

console.log(`prerender-seo: wrote ${written} pages and sitemap.xml to ${distArg}`);
