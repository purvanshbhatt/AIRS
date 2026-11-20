import data from './publicRoutes.json';
import {
  alternatesFor as sharedAlternatesFor,
  canonicalFor as sharedCanonicalFor,
  findRoute as sharedFindRoute,
  schemaFor as sharedSchemaFor,
} from './shared.mjs';

export interface RegionFramework {
  name: string;
  note: string;
}

export interface RegionFaq {
  q: string;
  a: string;
}

export interface RegionContent {
  code: string;
  name: string;
  areaServed: string[];
  eyebrow: string;
  h1: string;
  intro: string;
  frameworks: RegionFramework[];
  faq: RegionFaq[];
}

export interface PublicRoute {
  path: string;
  title: string;
  description: string;
  keywords?: string;
  h1?: string;
  summary?: string[];
  priority: string;
  changefreq: string;
  /** True when the page sets no tags of its own and RouteSEO must do it. */
  managed?: boolean;
  hreflangCluster?: boolean;
  region?: RegionContent;
}

export interface HreflangLink {
  hreflang: string;
  href: string;
}

export const seoData = data;
export const publicRoutes = data.routes as PublicRoute[];
export const regionRoutes = publicRoutes.filter((route) => route.region);
export const DEFAULT_OG_IMAGE: string = data.defaultImage;

export function findPublicRoute(pathname: string): PublicRoute | undefined {
  return sharedFindRoute(data, pathname);
}

export function canonicalFor(path: string): string {
  return sharedCanonicalFor(data, path);
}

export function alternatesFor(route: PublicRoute | undefined): HreflangLink[] {
  return sharedAlternatesFor(data, route);
}

export function schemaFor(route: PublicRoute): Record<string, unknown> {
  return sharedSchemaFor(data, route);
}
