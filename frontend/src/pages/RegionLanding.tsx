import { useMemo } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Globe2, Scale } from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { SEOHead } from '../components/common/SEOHead';
import { alternatesFor, canonicalFor, findPublicRoute, regionRoutes, schemaFor, seoData } from '../seo';

/** What ResilAI checks every day. The same in every region. */
const DAILY_CHECKS: Array<{ title: string; text: string }> = seoData.dailyChecks;

export interface RegionLandingProps {
  /** Route path of the region, for example "/europe". */
  path: string;
}

export default function RegionLanding({ path }: RegionLandingProps) {
  const route = findPublicRoute(path);
  const schema = useMemo(() => (route ? schemaFor(route) : undefined), [route]);
  const alternates = useMemo(() => alternatesFor(route), [route]);

  if (!route || !route.region) {
    return <Navigate to="/" replace />;
  }

  const region = route.region;
  const otherRegions = regionRoutes.filter((other) => other.path !== route.path);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-ready-emerald/20">
      <SEOHead
        title={route.title}
        description={route.description}
        keywords={route.keywords}
        canonicalUrl={canonicalFor(route.path)}
        schema={schema}
        alternates={alternates}
      />

      <PublicNavbar />

      <section className="pt-16 pb-16 border-b border-slate-200 dark:border-slate-800/80 bg-gradient-to-b from-white via-slate-50 to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-ready-emerald/15 text-on-surface border border-ready-emerald/40">
            <Globe2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{region.eyebrow}</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
            {region.h1}
          </h1>

          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            {region.intro}
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/pilot"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 shadow-sm transition-colors flex items-center justify-center gap-2"
            >
              <span>Join the pilot</span>
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link
              to="/pricing"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-semibold text-sm bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition-colors flex items-center justify-center"
            >
              See pricing
            </Link>
          </div>
        </div>
      </section>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-14 space-y-16 w-full">
        <section className="space-y-4" aria-labelledby="region-frameworks">
          <div className="flex items-center gap-2 text-ready-emerald text-xs font-mono font-bold uppercase tracking-wider">
            <Scale className="w-4 h-4" aria-hidden="true" />
            <span>Laws and frameworks</span>
          </div>
          <h2 id="region-frameworks" className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            What ResilAI lists for {region.name}
          </h2>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
            Each law is listed with the reason it applies to you and a link to the official source.
            ResilAI shows the evidence your systems give. It does not certify compliance or give legal advice.
          </p>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {region.frameworks.map((framework) => (
              <li
                key={framework.name}
                className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2"
              >
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">{framework.name}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{framework.note}</p>
              </li>
            ))}
          </ul>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            See the full list in the{' '}
            <Link to="/docs/frameworks" className="font-medium text-ready-emerald hover:underline">
              framework mappings
            </Link>
            .
          </p>
        </section>

        <section className="space-y-4" aria-labelledby="region-checks">
          <h2 id="region-checks" className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            What ResilAI checks every day
          </h2>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {DAILY_CHECKS.map((check) => (
              <li key={check.title} className="flex gap-3">
                <CheckCircle2 className="w-5 h-5 text-ready-emerald shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">{check.title}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{check.text}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Read{' '}
            <Link to="/trust/data-access" className="font-medium text-ready-emerald hover:underline">
              what ResilAI reads and where it is kept
            </Link>
            .
          </p>
        </section>

        <section className="space-y-4" aria-labelledby="region-faq">
          <h2 id="region-faq" className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Questions from {region.name}
          </h2>
          <dl className="space-y-4">
            {region.faq.map((item) => (
              <div
                key={item.q}
                className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
              >
                <dt className="font-semibold text-slate-900 dark:text-slate-100">{item.q}</dt>
                <dd className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{item.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <nav className="space-y-3" aria-labelledby="region-others">
          <h2 id="region-others" className="text-lg font-bold text-slate-900 dark:text-white">
            ResilAI in other regions
          </h2>
          <ul className="flex flex-wrap gap-3">
            {otherRegions.map((other) => (
              <li key={other.path}>
                <Link
                  to={other.path}
                  className="inline-flex px-4 py-2 rounded-full text-sm font-medium bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  {other.region?.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </main>

      <Footer />
    </div>
  );
}
