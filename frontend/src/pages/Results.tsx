import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  XCircle,
  Clock,
  Layers,
  Sparkles,
  Info,
  Lock,
  RotateCcw,
  FileCheck2,
  TrendingUp,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';

export default function Results() {
  const [selectedTab, setSelectedTab] = useState<'identity' | 'clinic'>('identity');

  useEffect(() => {
    document.title = 'ResilAI Results — From Security Evidence to Executive Readiness';
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-primary-500/20 transition-colors duration-300">
      <PublicNavbar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-28 overflow-hidden border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-slate-50/70 via-white to-white dark:from-slate-900/50 dark:via-slate-950 dark:to-slate-950">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 shadow-xs">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Measurable Outcomes</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 leading-[1.15]">
              From Security Telemetry to{' '}
              <span className="bg-gradient-to-r from-primary-600 to-emerald-500 bg-clip-text text-transparent">
                Executive Readiness
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
              How ResilAI converts thousands of disconnected alerts, logs, and connector telemetry into verifiable operational readiness and board-level risk clarity.
            </p>
          </div>
        </section>

        {/* The Transformation: Before vs With ResilAI */}
        <section className="py-16 lg:py-24 border-b border-slate-200/80 dark:border-slate-800/80">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                The Structural Transformation
              </h2>
              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                Moving from fragmented technical metrics to an evidence-backed continuous readiness operating model.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Before ResilAI Card */}
              <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-red-200/60 dark:border-red-900/40 space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 flex items-center justify-center font-bold">
                    <XCircle className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-50">Before ResilAI</h3>
                    <p className="text-xs font-mono text-slate-500">Fragmented Data & Subjective Surveys</p>
                  </div>
                </div>

                <ul className="space-y-3.5 text-sm text-slate-600 dark:text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-red-500 mt-2 shrink-0" />
                    <span><strong>Fragmented Silos:</strong> Security data scattered across SIEM, EDR, Okta, Active Directory, AWS, and backup appliances.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-red-500 mt-2 shrink-0" />
                    <span><strong>Alert Overload:</strong> Engineers analyze thousands of alerts, but leadership cannot determine if operations would survive an attack.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-red-500 mt-2 shrink-0" />
                    <span><strong>Self-Attestation Blindspots:</strong> Annual compliance spreadsheets rely on self-reported checkboxes without verifying live systems.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-red-500 mt-2 shrink-0" />
                    <span><strong>Unclear Business Impact:</strong> Technical vulnerabilities are presented as CVSS numbers without explaining clinic downtime or financial loss.</span>
                  </li>
                </ul>
              </div>

              {/* With ResilAI Card */}
              <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-emerald-200/80 dark:border-emerald-800/60 space-y-6 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
                    <CheckCircle className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-50">With ResilAI</h3>
                    <p className="text-xs font-mono text-emerald-600 dark:text-emerald-400">Deterministic Evidence & Board Understanding</p>
                  </div>
                </div>

                <ul className="space-y-3.5 text-sm text-slate-600 dark:text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 mt-2 shrink-0" />
                    <span><strong>Unified Evidence Ingestion:</strong> Continuous connectors ingest and cryptographically hash telemetry across identity, endpoints, and recovery.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 mt-2 shrink-0" />
                    <span><strong>Deterministic Mathematical Scoring:</strong> Transparent 0–100% readiness scores computed strictly by mathematical verification rules.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 mt-2 shrink-0" />
                    <span><strong>Executive Narrative Layer:</strong> Gemini translates verified gaps into plain-English business impact and executive briefings.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 mt-2 shrink-0" />
                    <span><strong>Verified Remediation:</strong> Fixes are tracked in an immutable ledger, proving the score change post-remediation.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Illustrative Results Showcase */}
        <section className="py-16 lg:py-24 bg-slate-50/60 dark:bg-slate-900/30">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-primary-600 dark:text-primary-400">
                  <FileCheck2 className="w-4 h-4" />
                  <span>Illustrative Results Output</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                  What ResilAI Produces
                </h2>
              </div>

              {/* Mandatory Illustrative Disclaimer Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30 shadow-xs">
                <Info className="w-3.5 h-3.5 text-amber-500" />
                <span>DEMO / ILLUSTRATIVE DATA</span>
              </div>
            </div>

            {/* Scenario Tabs */}
            <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
              <button
                onClick={() => setSelectedTab('identity')}
                className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                  selectedTab === 'identity'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-xs'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800'
                }`}
              >
                Scenario A: Identity Privilege Drift (82%)
              </button>
              <button
                onClick={() => setSelectedTab('clinic')}
                className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                  selectedTab === 'clinic'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-xs'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800'
                }`}
              >
                Scenario B: Multi-Facility Clinic Operations (94%)
              </button>
            </div>

            {/* Showcase Output Cards */}
            {selectedTab === 'identity' ? (
              <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 space-y-8 shadow-lg">
                {/* Header Readiness Summary */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
                  <div className="flex items-center gap-5">
                    <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border-2 border-amber-500/30 flex items-center justify-center shrink-0">
                      <span className="text-2xl font-extrabold text-amber-600 dark:text-amber-400">82%</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100">
                          ATTENTION REQUIRED: Identity Recovery Gaps
                        </h3>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                          DRIFT
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Core detection and recovery controls verified, but 4 privileged identities lack mandatory hardware MFA.
                      </p>
                    </div>
                  </div>
                </div>

                {/* 4-Tier Progressive Disclosure Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Tier 1: Technical Evidence */}
                  <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">
                      <Lock className="w-3.5 h-3.5 text-primary-500" />
                      <span>Tier 1 • Telemetry & Evidence</span>
                    </div>
                    <p className="text-xs font-mono text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                      Okta & Entra ID Connector Sync: 4 privileged domain accounts active with SMS-only 2FA fallback.
                    </p>
                  </div>

                  {/* Tier 2: Deterministic Finding */}
                  <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                      <span>Tier 2 • Deterministic Finding</span>
                    </div>
                    <p className="text-xs font-mono text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                      Rule ID [ID-MFA-004]: Severity HIGH (-8.0 points). Privileged identity MFA coverage is incomplete.
                    </p>
                  </div>

                  {/* Tier 3: Executive Business Impact */}
                  <div className="p-5 rounded-2xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-700 dark:text-amber-300 uppercase">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>Tier 3 • Executive Business Impact (Gemini Translation)</span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                      A compromised administrator credential allows lateral movement during a ransomware outbreak, exposing clinical data systems to unauthorized encryption.
                    </p>
                  </div>

                  {/* Tier 4: Recommended Action */}
                  <div className="p-5 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-700 dark:text-emerald-300 uppercase">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Tier 4 • Recommended Remediation</span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                      Enforce FIDO2 hardware keys on all 4 domain accounts to restore readiness score from 82% to 90%.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 space-y-8 shadow-lg">
                {/* Header Readiness Summary */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
                  <div className="flex items-center gap-5">
                    <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center shrink-0">
                      <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">94%</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100">
                          READY FOR TODAY: Digital Clinical Operations Verified
                        </h3>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                          VERIFIED
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
                        All 14 critical clinical feeds, immutable backup streams, and endpoint detection agents verified over the last 24 hours.
                      </p>
                    </div>
                  </div>
                </div>

                {/* 4-Tier Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">
                      <RotateCcw className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Tier 1 • Telemetry & Evidence</span>
                    </div>
                    <p className="text-xs font-mono text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                      Splunk MCP & Veeam: Immutable cloud backup snapshot completed at 03:00 UTC. Zero data corruption flags.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Tier 2 • Deterministic Finding</span>
                    </div>
                    <p className="text-xs font-mono text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                      Rule ID [REC-BKP-001]: PASS (100% control satisfaction). Maximum Recovery Time Objective (RTO) under 4 hours.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-700 dark:text-emerald-300 uppercase">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Tier 3 • Executive Business Impact</span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                      Electronic health records and diagnostic imaging systems can be fully restored without ransom payment in the event of primary infrastructure failure.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">
                      <Clock className="w-3.5 h-3.5 text-primary-500" />
                      <span>Tier 4 • Next Verification Cycle</span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                      Automated overnight verification scheduled to re-evaluate telemetry heartbeats at 04:00 UTC.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-slate-900 text-white relative overflow-hidden">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight">
              Test ResilAI with Your Operational Telemetry
            </h2>
            <p className="text-slate-300 text-base max-w-2xl mx-auto leading-relaxed">
              Explore our early access design partner program to establish continuous incident readiness visibility across your environment.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                to="/contact?tier=design-partner"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-sm shadow-lg hover:shadow-primary-500/25 transition-all"
              >
                <span>Become a Design Partner</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/ai"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-all"
              >
                <span>Explore AI Architecture</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
