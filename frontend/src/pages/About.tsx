import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  BarChart3,
  Lock,
  Layers,
  CheckCircle,
  ArrowRight,
  ShieldCheck,
  Building2,
  Calendar,
  Linkedin,
  Github,
  Mail,
  Scale,
  Sparkles,
  ArrowUpRight,
  Cpu,
  Fingerprint,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { COMPANY_INFO, getCompanyLeadership } from '../config/company';

export default function About() {
  const leaders = getCompanyLeadership();
  useEffect(() => {
    document.title = 'About ResilAI — AI Incident Readiness';
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-primary-500/20 transition-colors duration-300">
      <PublicNavbar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-28 overflow-hidden border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-slate-50/70 via-white to-white dark:from-slate-900/50 dark:via-slate-950 dark:to-slate-950">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold uppercase tracking-wider bg-primary-50 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800/60 shadow-xs">
              <ShieldCheck className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400" />
              <span>Company & Mission</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 leading-[1.15]">
              Bridging the Gap Between Cybersecurity Telemetry and{' '}
              <span className="bg-gradient-to-r from-primary-600 to-emerald-500 bg-clip-text text-transparent">
                Executive Decision-Making
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
              Security teams generate gigabytes of telemetry, alerts, findings, and controls every day. Yet executives and clinic managing partners still struggle to answer one fundamental question:
              <span className="font-semibold text-slate-900 dark:text-slate-100 block mt-2 text-lg sm:text-xl">
                “If a cyber or AI incident happens tomorrow morning, are we actually ready?”
              </span>
            </p>
          </div>
        </section>

        {/* Company Quick Facts / Founded Bar */}
        <section className="py-8 bg-slate-50/80 dark:bg-slate-900/40 border-b border-slate-200/80 dark:border-slate-800/80">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
                <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Founded
                </p>
                <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                  {COMPANY_INFO.foundedYear}
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
                <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Mission Focus
                </p>
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
                  Incident Readiness
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
                <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Core Invariant
                </p>
                <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  Deterministic Scoring
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
                <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  AI Architecture
                </p>
                <p className="text-lg font-bold text-primary-600 dark:text-primary-400 mt-1">
                  Gemini Narrative Layer
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Our Story Section */}
        <section className="py-16 lg:py-24">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-primary-600 dark:text-primary-400">
                <Building2 className="w-4 h-4" />
                <span>Our Story</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                Why We Built ResilAI
              </h2>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none text-base sm:text-lg text-slate-600 dark:text-slate-300 space-y-6 leading-relaxed">
              <p>
                Modern cybersecurity is caught in an uncomfortable paradox. Organizations invest heavily in security information and event management (SIEM), endpoint detection and response (EDR), identity providers, and cloud access tools. These systems output hundreds of thousands of events, security alerts, and technical metrics every week.
              </p>
              <p>
                Yet when executive leadership, clinic managing partners, or board directors ask whether their organization can withstand a targeted ransomware attack or recover from an identity compromise, they are handed either static, self-attested compliance questionnaires or dense engineering spreadsheets.
              </p>
              <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900/70 border-l-4 border-primary-500 border-y border-r border-slate-200 dark:border-slate-800 not-italic">
                <p className="font-semibold text-slate-900 dark:text-slate-100 text-base sm:text-lg mb-0">
                  ResilAI was created to bridge this divide with two fundamental principles:
                  <br />
                  <span className="text-primary-600 dark:text-primary-400 block mt-2">
                    1. Telemetry and evidence must deterministically establish the ground truth.
                  </span>
                  <span className="text-emerald-600 dark:text-emerald-400 block mt-1">
                    2. AI should be used to translate technical security reality into executive business decisions — never to invent scores or fabricate readiness.
                  </span>
                </p>
              </div>
              <p>
                By connecting directly to existing operational systems (Splunk, Wazuh, Microsoft Graph, and cloud identity stores) and cryptographically hashing the evidence, ResilAI calculates mathematical readiness scores and generates clear, actionable leadership briefings without subjective guesswork.
              </p>
            </div>
          </div>
        </section>

        {/* The Team Section */}
        <section id="team" className="py-16 lg:py-24 bg-slate-50/60 dark:bg-slate-900/30 border-t border-slate-200/80 dark:border-slate-800/80 scroll-mt-20">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-primary-600 dark:text-primary-400">
                <Fingerprint className="w-4 h-4" />
                <span>Leadership</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                The Team Behind ResilAI
              </h2>
              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                ResilAI is led by security engineers dedicated to audit integrity, deterministic evaluation, and operational resilience.
              </p>
            </div>

            {/* Leadership Cards */}
            <div className={leaders.length > 1 ? "grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto" : "max-w-2xl mx-auto"}>
              {leaders.map((person) => {
                const initials = person.name.split(' ').map(n => n[0]).join('').substring(0, 2);
                const badgeText = person.role.includes('Co-Founder') ? 'Co-Founder' : 'Founder';

                return (
                  <div key={person.name} className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 sm:p-10 shadow-lg hover:border-primary-500/40 transition-all duration-300 flex flex-col justify-between">
                    <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
                      {/* Avatar */}
                      <div className="relative shrink-0">
                        {person.avatarUrl ? (
                          <img
                            src={person.avatarUrl}
                            alt={person.name}
                            className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl object-cover shadow-md border-2 border-white dark:border-slate-800"
                          />
                        ) : (
                          <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-gradient-to-br from-primary-600 to-emerald-500 flex items-center justify-center text-white font-extrabold text-3xl shadow-md border-2 border-white dark:border-slate-800">
                            <span>{initials}</span>
                          </div>
                        )}
                        <div className="absolute -bottom-2 -right-2 px-2 py-0.5 rounded-full bg-emerald-500 text-white text-[10px] font-mono font-bold uppercase tracking-wider shadow-xs">
                          {badgeText}
                        </div>
                      </div>

                      {/* Details */}
                      <div className="space-y-3 flex-1">
                        <div>
                          <h3 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-50">
                            {person.name}
                          </h3>
                          <p className="text-sm font-semibold text-primary-600 dark:text-primary-400">
                            {person.role}
                          </p>
                        </div>

                        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                          {person.bio}
                        </p>

                        <div className="pt-2 flex flex-wrap items-center justify-center sm:justify-start gap-3">
                          <a
                            href={person.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-primary-50 dark:hover:bg-primary-950/50 hover:text-primary-600 dark:hover:text-primary-400 border border-slate-200 dark:border-slate-700 transition-colors"
                          >
                            <Linkedin className="w-3.5 h-3.5 text-[#0A66C2]" />
                            <span>LinkedIn Profile</span>
                            <ArrowUpRight className="w-3 h-3 opacity-60" />
                          </a>
                          {person.github && (
                            <a
                              href={person.github}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-colors"
                            >
                              <Github className="w-3.5 h-3.5" />
                              <span>GitHub</span>
                            </a>
                          )}
                          {person.email && (
                            <a
                              href={`mailto:${person.email}`}
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-colors"
                            >
                              <Mail className="w-3.5 h-3.5" />
                              <span>Email</span>
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Our Trust Principles */}
        <section className="py-16 lg:py-24 border-t border-slate-200/80 dark:border-slate-800/80">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                <Shield className="w-4 h-4" />
                <span>Our Principles</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                The Non-Negotiable Trust Contract
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
                  1
                </div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100">
                  LLMs Never Calculate Scores
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  A hallucinated readiness score destroys trust. Readiness percentages and finding severities are calculated through transparent, deterministic mathematical formulas.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-primary-500/10 text-primary-600 dark:text-primary-400 flex items-center justify-center font-bold">
                  2
                </div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100">
                  Telemetry Beats Questionnaires
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  Self-attested surveys mask operational failure. We evaluate live connector telemetry from SIEM, EDR, and identity providers rather than relying on human memory.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
                  3
                </div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100">
                  Cryptographic Provenance
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  Every finding links back to a SHA-256 evidence record, connector source, and timestamp, giving auditors and IT operators full auditability.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Banner */}
        <section className="py-20 bg-slate-900 text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-primary-900/30 to-emerald-900/30 pointer-events-none" />
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6 relative z-10">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight">
              Ready to Explore Verifiable Incident Readiness?
            </h2>
            <p className="text-slate-300 text-base max-w-2xl mx-auto leading-relaxed">
              Connect with our team to discuss your organization's resilience requirements, explore design partnership opportunities, or test our live demo environment.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                to="/contact"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-sm shadow-lg hover:shadow-primary-500/25 transition-all"
              >
                <span>Contact Us</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/pricing"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-all"
              >
                <span>View Pricing & Tiers</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
