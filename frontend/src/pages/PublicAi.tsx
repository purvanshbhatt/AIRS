import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ShieldCheck,
  Cpu,
  Layers,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Database,
  Lock,
  Code2,
  FileText,
  ShieldAlert,
  ArrowDown,
  Terminal,
  Activity,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';

export default function PublicAi() {
  const [activeTab, setActiveTab] = useState<'mfa' | 'backup' | 'edr'>('mfa');

  useEffect(() => {
    document.title = 'ResilAI AI — Business Impact Intelligence';
    window.scrollTo(0, 0);
  }, []);

  const examples = {
    mfa: {
      title: 'Privileged Identity MFA Enforcement',
      technical: 'Azure AD connector sync reports 4 global administrator accounts with SMS-only 2FA fallback. FIDO2 / WebAuthn enforcement rule [ID-MFA-004] triggered severity HIGH (-8.0 pts).',
      executive: 'Four administrator accounts lack modern hardware key protections. If an administrator is phished, attackers could move laterally across clinical systems and deploy ransomware.',
      action: 'Deploy hardware security keys to the 4 administrator accounts to prevent unauthorized lateral access.',
      scoreImpact: '-8.0 pts (Restores to 100% upon hardware key enrollment)',
    },
    backup: {
      title: 'Immutable Storage Verification',
      technical: 'Veeam & S3 telemetry verifies daily snapshot at 03:00 UTC with Object Lock legal hold enabled. Rule [REC-BKP-001] PASS (+15.0 pts). Maximum RTO calculated at 3.2 hours.',
      executive: 'Diagnostic and patient record backups are stored in write-once immutable cloud storage. Patient records can be restored within 4 hours without ransom payment.',
      action: 'Maintain automated daily snapshot schedule and quarterly disaster recovery drill.',
      scoreImpact: 'Fully verified (Zero data loss vulnerability)',
    },
    edr: {
      title: 'Endpoint Telemetry Heartbeat Lag',
      technical: 'Wazuh & CrowdStrike agent telemetry heartbeat exceeded 72 hours on 6 workstation nodes in the outpatient diagnostic wing. Rule [EDR-HB-002] MEDIUM (-4.0 pts).',
      executive: 'Six clinical workstations in outpatient care have stopped reporting security telemetry, creating an unmonitored blind spot where malware could run undetected.',
      action: 'Restart agent services on the 6 identified workstations to re-establish full visibility.',
      scoreImpact: '-4.0 pts (Restores upon active agent telemetry reception)',
    },
  };

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-primary-500/20 transition-colors duration-300">
      <PublicNavbar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-28 overflow-hidden border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-slate-50/70 via-white to-white dark:from-slate-900/50 dark:via-slate-950 dark:to-slate-950">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold uppercase tracking-wider bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800/60 shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
              <span>AI Architecture & Governance</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 leading-[1.15]">
              AI That Explains Security Risk.{' '}
              <span className="bg-gradient-to-r from-purple-600 to-primary-600 bg-clip-text text-transparent">
                Not AI That Invents It.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
              ResilAI decouples mathematical readiness scoring from generative language modeling. Telemetry determines the facts; Gemini explains the business impact.
            </p>
          </div>
        </section>

        {/* Dual-Layer Architecture Diagram & Breakdown */}
        <section className="py-16 lg:py-24 border-b border-slate-200/80 dark:border-slate-800/80">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                The Two-Layer Intelligence Architecture
              </h2>
              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                Why we strictly prevent generative AI models from calculating scores, evaluating compliance, or inventing risk data.
              </p>
            </div>

            {/* Architecture Flow Box */}
            <div className="space-y-6">
              {/* Layer 1 */}
              <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-900/70 border-2 border-emerald-500/40 space-y-6 shadow-md relative overflow-hidden">
                <div className="absolute top-0 right-0 px-4 py-1.5 rounded-bl-2xl bg-emerald-500 text-white text-xs font-mono font-bold uppercase tracking-wider">
                  Layer 1 • 100% Deterministic
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
                    <Database className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-50">
                      Layer 1: Deterministic Verification & Scoring Engine
                    </h3>
                    <p className="text-xs font-mono text-slate-500">Mathematical Verification — Zero LLM Involvement</p>
                  </div>
                </div>

                <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed">
                  Connector pipelines ingest live telemetry from Splunk, Wazuh, Microsoft Graph, and cloud stores. Evidence records are cryptographically SHA-256 hashed and evaluated against deterministic control rules.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Live Telemetry Ingestion</p>
                    <p className="text-slate-500 mt-1">SIEM, EDR, Okta, Active Directory, AWS, S3, Veeam</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Mathematical Scoring</p>
                    <p className="text-slate-500 mt-1">0–100% readiness formula. Traceable, repeatable, and audited.</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Cryptographic Ledger</p>
                    <p className="text-slate-500 mt-1">SHA-256 evidence hashing for verifiable auditor inspection.</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-mono text-emerald-700 dark:text-emerald-300">
                  <span className="flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> LLM never calculates scores</span>
                  <span className="flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> LLM never modifies findings</span>
                  <span className="flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> LLM never decides compliance</span>
                </div>
              </div>

              {/* Connecting Flow Arrow */}
              <div className="flex justify-center items-center py-2">
                <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-mono font-bold text-slate-600 dark:text-slate-300">
                  <span>Verified Findings & Deterministic Scores Flow into Translation Layer</span>
                  <ArrowDown className="w-3.5 h-3.5 text-primary-500 animate-bounce" />
                </div>
              </div>

              {/* Layer 2 */}
              <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-900/70 border-2 border-purple-500/40 space-y-6 shadow-md relative overflow-hidden">
                <div className="absolute top-0 right-0 px-4 py-1.5 rounded-bl-2xl bg-purple-600 text-white text-xs font-mono font-bold uppercase tracking-wider">
                  Layer 2 • Generative Intelligence
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-50">
                      Layer 2: Business Impact Intelligence (Gemini)
                    </h3>
                    <p className="text-xs font-mono text-slate-500">Plain-English Translation & Board-Level Contextualization</p>
                  </div>
                </div>

                <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed">
                  Using Gemini 2.5 / 3 Flash, ResilAI translates verified technical gaps into clear operational explanations. Leadership receives plain-English explanations of clinical downtime, financial exposure, and prioritized remediation actions.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Executive Briefing</p>
                    <p className="text-slate-500 mt-1">Converts CVSS/CVE codes into business language for leadership.</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Downtime & Financial Impact</p>
                    <p className="text-slate-500 mt-1">Explains ransomware propagation, patient care delays, or SLA breach risk.</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs">
                    <p className="font-mono font-bold text-slate-900 dark:text-slate-100">Actionable Remediation</p>
                    <p className="text-slate-500 mt-1">Suggests prioritized fix roadmaps with expected score recovery.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Interactive Translation Showcase */}
        <section className="py-16 lg:py-24 bg-slate-50/60 dark:bg-slate-900/30">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                See the AI Translation in Action
              </h2>
              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                Notice how the underlying technical ground truth remains 100% intact while the explanation adapts for executive leadership.
              </p>
            </div>

            {/* Selector Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              {(['mfa', 'backup', 'edr'] as const).map((key) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                    activeTab === key
                      ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-xs'
                      : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-200 dark:border-slate-800'
                  }`}
                >
                  {examples[key].title}
                </button>
              ))}
            </div>

            {/* Translation Comparison Card */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-lg">
              {/* Technical Feed (Layer 1) */}
              <div className="p-6 rounded-2xl bg-slate-950 text-slate-200 border border-slate-800 space-y-4 font-mono">
                <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-3">
                  <span className="flex items-center gap-1.5"><Terminal className="w-3.5 h-3.5 text-emerald-400" /> Layer 1: Deterministic Engine</span>
                  <span className="text-emerald-400">GROUND TRUTH</span>
                </div>
                <div className="space-y-3 text-xs">
                  <p className="text-slate-400 font-semibold">// Raw Telemetry & Finding</p>
                  <p className="text-slate-300 leading-relaxed bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
                    {examples[activeTab].technical}
                  </p>
                  <p className="text-slate-400 pt-2 font-semibold">// Mathematical Score Impact</p>
                  <p className="text-amber-400 font-bold">{examples[activeTab].scoreImpact}</p>
                </div>
              </div>

              {/* Executive Translation (Layer 2) */}
              <div className="p-6 rounded-2xl bg-purple-50/60 dark:bg-purple-950/20 text-slate-800 dark:text-slate-200 border border-purple-200 dark:border-purple-900/50 space-y-4">
                <div className="flex items-center justify-between text-xs text-purple-700 dark:text-purple-300 font-mono font-bold border-b border-purple-200 dark:border-purple-900/50 pb-3">
                  <span className="flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-purple-600" /> Layer 2: Gemini Translation</span>
                  <span>EXECUTIVE BRIEF</span>
                </div>
                <div className="space-y-3">
                  <p className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">What this means for the business</p>
                  <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                    {examples[activeTab].executive}
                  </p>
                  <p className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase pt-2">Recommended leadership action</p>
                  <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                    {examples[activeTab].action}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Banner */}
        <section className="py-20 bg-slate-900 text-white relative overflow-hidden">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight">
              Experience Deterministic AI Incident Readiness
            </h2>
            <p className="text-slate-300 text-base max-w-2xl mx-auto leading-relaxed">
              Explore how ResilAI provides continuous assurance for your critical systems without hallucinated scores or subjective checkboxes.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                to="/contact"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-sm shadow-lg hover:shadow-primary-500/25 transition-all"
              >
                <span>Talk to ResilAI</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/docs/methodology"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-all"
              >
                <span>Read Full Methodology</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
