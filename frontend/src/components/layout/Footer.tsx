import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Github, FileText, Lock, Shield, Activity, Mail, ShieldCheck, ArrowUpRight, ExternalLink } from 'lucide-react';
import { getSystemStatus } from '../../api';
import type { SystemStatus } from '../../types';
import { COMPANY_INFO } from '../../config/company';

export function Footer() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    getSystemStatus()
      .then(setSystemStatus)
      .catch(() => {
        setSystemStatus(null);
      });
  }, []);

  const host = typeof window !== 'undefined' ? window.location.hostname : '';
  const isStaging =
    systemStatus?.environment === 'staging' ||
    host.includes('staging') ||
    import.meta.env.MODE === 'staging';

  const isDemo =
    systemStatus?.environment === 'demo' ||
    host.includes('demo') ||
    import.meta.env.MODE === 'demo';

  return (
    <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950 text-slate-600 dark:text-slate-400 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        {/* Environment Status Notice (Staging / Demo) */}
        {(isStaging || isDemo) && (
          <div className="mb-10 p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4 transition-all duration-300 shadow-xs">
            <div className="flex items-center gap-3">
              <div className="relative flex h-3 w-3">
                <span
                  className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${
                    isStaging ? 'bg-amber-400' : isDemo ? 'bg-blue-400' : 'bg-emerald-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-3 w-3 ${
                    isStaging ? 'bg-amber-500' : isDemo ? 'bg-blue-500' : 'bg-emerald-500'
                  }`}
                />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-slate-800 dark:text-slate-200 uppercase">
                  {isStaging ? 'Staging Environment' : isDemo ? 'Demo Environment' : 'Production Instance'}
                </span>
                <span className="hidden sm:inline text-slate-300 dark:text-slate-700">|</span>
                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                  {isStaging ? 'staging.resilai.org' : isDemo ? 'demo.resilai.org' : 'resilai.org'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span>Deterministic Scoring Engine: Active</span>
              </div>
              <span className="text-slate-300 dark:text-slate-700">|</span>
              <div className="text-slate-500 dark:text-slate-400">
                <span>Latency: {isStaging ? '35ms' : '18ms'}</span>
              </div>
            </div>
          </div>
        )}

        {/* Main 4-Column Startup Navigation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 lg:gap-8 pb-12 border-b border-slate-200 dark:border-slate-800/80">
          {/* Brand & Mission Column (Spans 2 cols on desktop) */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="inline-block">
              <img
                src="/logo_footer_and github.svg"
                alt="ResilAI Brand Logo"
                className="h-12 w-auto dark:brightness-0 dark:invert transition-all duration-300"
              />
            </Link>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-sm leading-relaxed">
              Continuous AI & cybersecurity incident readiness for healthcare and enterprise organizations. Transform fragmented telemetry into verifiable executive understanding and operational resilience.
            </p>
            <div className="pt-2 flex items-center gap-3">
              <a
                href={COMPANY_INFO.socials.maidensail}
                rel="dofollow"
                target="_blank"
                className="inline-flex items-center transition-opacity hover:opacity-90"
                title="Featured on Maidensail"
              >
                <img
                  src="https://maidensail.com/badge/resilai.svg?theme=dark"
                  alt="Featured on Maidensail"
                  height="40"
                  className="rounded-lg"
                />
              </a>
              <a
                href={COMPANY_INFO.socials.github}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
                aria-label="ResilAI GitHub Repository"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product Column */}
          <div className="space-y-3">
            <p className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-200">
              Product
            </p>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/#how-it-works" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Overview & Loop
                </Link>
              </li>
              <li>
                <Link to="/results" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Results & Evidence
                </Link>
              </li>
              <li>
                <Link to="/ai" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  AI Architecture
                </Link>
              </li>
              <li>
                <Link to="/pricing" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Pricing & Tiers
                </Link>
              </li>
              <li>
                <Link to="/status" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  System Status
                </Link>
              </li>
            </ul>
          </div>

          {/* Company Column */}
          <div className="space-y-3">
            <p className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-200">
              Company
            </p>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/about" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/about#team" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  The Team
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link to="/pilot" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Design Partner Program
                </Link>
              </li>
              <li>
                <Link to="/security" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Security Posture
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources & Trust Column */}
          <div className="space-y-3">
            <p className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-200">
              Resources & Trust
            </p>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/docs/methodology" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Scoring Methodology
                </Link>
              </li>
              <li>
                <Link to="/docs/frameworks" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Framework Alignment
                </Link>
              </li>
              <li>
                <Link to="/docs/api" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  API & Verification
                </Link>
              </li>
              <li>
                <Link to="/docs/security#privacy" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <a
                  href={COMPANY_INFO.founder.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
                >
                  <span>Founder LinkedIn</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Legal Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-500">
          <p>
            &copy; {new Date().getFullYear()} {COMPANY_INFO.name}. Founded {COMPANY_INFO.foundedYear}. Open source under GNU AGPL-3.0 license.
          </p>
          <div className="flex items-center gap-4">
            <Link to="/security" className="hover:underline">
              Responsible Disclosure
            </Link>
            <span>•</span>
            <Link to="/docs/methodology" className="hover:underline">
              Trust Invariants
            </Link>
            <span>•</span>
            <a href={`mailto:${COMPANY_INFO.contactEmail}`} className="hover:underline">
              {COMPANY_INFO.contactEmail}
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
