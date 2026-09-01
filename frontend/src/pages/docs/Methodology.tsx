import { useState } from 'react';
import { 
  Plug, 
  ShieldCheck, 
  Calculator, 
  Sparkles, 
  TrendingUp, 
  CheckCircle2, 
  Activity, 
  FileText, 
  Layers, 
  RotateCcw, 
  Lock,
  ArrowRight,
  Target
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DocsMethodology() {
  const [activePersona, setActivePersona] = useState<'exec' | 'it'>('exec');

  return (
    <div className="space-y-12 max-w-5xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 mb-3">
          <ShieldCheck className="w-5 h-5" />
          <span className="text-xs font-bold font-mono tracking-wider uppercase">Operating Methodology</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight mb-4">
          How ResilAI Works
        </h1>
        <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl leading-relaxed">
          ResilAI replaces subjective questionnaires and point-in-time compliance audits with continuous, mathematical verification of whether your organization's critical security controls actually work.
        </p>
      </div>

      {/* Non-Negotiable Trust Invariant */}
      <div className="p-6 sm:p-8 bg-emerald-500/10 border border-emerald-500/30 rounded-3xl space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              The ResilAI Trust Invariant
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">Core architectural guarantees enforced in every evaluation</p>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-2 bg-slate-900/40 p-4 rounded-2xl border border-slate-800/80">
            <p className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-2 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" /> 100% Deterministic Mathematical Scoring
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              <strong>LLMs never calculate readiness scores.</strong> All scoring is derived strictly from verified telemetry, weighted mathematical rubrics, and automated rule execution.
            </p>
          </div>
          <div className="space-y-2 bg-slate-900/40 p-4 rounded-2xl border border-slate-800/80">
            <p className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-2 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" /> Strict Evidence Invariant
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              <strong>No evidence → Not Yet Verified.</strong> ResilAI never assumes readiness when evidence is missing. Telemetry gaps produce honest unverified states, not fabricated positive scores.
            </p>
          </div>
        </div>
      </div>

      {/* 5-Step Continuous Verification Loop */}
      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            The 5-Stage Verification Operating Model
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            From raw security system telemetry to clear executive decisions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            {
              step: '01',
              title: 'Connect',
              icon: Plug,
              desc: 'Connect the security and operational systems your organization already uses (M365, Splunk, CrowdStrike, Veeam, AWS).',
            },
            {
              step: '02',
              title: 'Verify',
              icon: ShieldCheck,
              desc: 'ResilAI inspects actual system configurations, event streams, and cryptographic proof rather than trusting self-reported claims.',
            },
            {
              step: '03',
              title: 'Measure',
              icon: Calculator,
              desc: 'Readiness is calculated using deterministic scoring rules and weighted rubrics—never generative AI opinions.',
            },
            {
              step: '04',
              title: 'Explain',
              icon: Sparkles,
              desc: 'Technical findings are translated into plain-English business impact: clinical downtime risk, patient care continuity, and compliance drift.',
            },
            {
              step: '05',
              title: 'Improve',
              icon: TrendingUp,
              desc: 'Executives and IT teams receive clear, prioritized remediation actions to restore readiness before an incident occurs.',
            },
          ].map((s) => (
            <div
              key={s.step}
              className="p-5 bg-slate-900/40 rounded-2xl border border-slate-800/80 flex flex-col justify-between space-y-4 hover:border-emerald-500/30 transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-mono font-bold text-emerald-500">{s.step}</span>
                  <s.icon className="w-4 h-4 text-slate-400" />
                </div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">{s.title}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tailored Perspectives: Executives vs IT/Security */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              One Truth, Translated for Every Stakeholder
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Select a persona to see how ResilAI presents readiness without compromising technical rigor.
            </p>
          </div>

          <div className="inline-flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setActivePersona('exec')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activePersona === 'exec'
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              For Healthcare Executives
            </button>
            <button
              onClick={() => setActivePersona('it')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activePersona === 'it'
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              For IT & Security Teams
            </button>
          </div>
        </div>

        {activePersona === 'exec' ? (
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-500" />
                What is my current readiness?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                A single daily readiness score reflecting whether critical operations can withstand a security disruption today, based strictly on verified control telemetry.
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <Activity className="w-4 h-4 text-amber-500" />
                What needs attention?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                A prioritized list of critical gaps explained in terms of operational impact, such as clinical workstation exposure or backup recovery windows.
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-blue-500" />
                What would happen if an incident occurred tomorrow?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Clear recovery readiness projections and tested Recovery Time Objectives (RTO) so leaders know how fast clinics can resume patient appointments.
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                What should we fix first?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Recommended, high-leverage fixes with estimated score recovery deltas to maximize resilience with minimal administrative overhead.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-500" />
                Telemetry & Cryptographic Evidence
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                SHA-256 hashes generated over raw log events and configuration snapshots, providing non-repudiation and verifiable audit trails for cyber insurers.
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <Plug className="w-4 h-4 text-blue-500" />
                Pre-Built Connectors
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Zero-agent connectors for Microsoft Graph / Entra ID, Splunk MCP, Wazuh SIEM, Veeam Backup, and generic syslog webhooks with sub-second health checks.
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-500" />
                Rule-Based Control Verification
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Deterministic policy evaluations mapping to NIST CSF 2.0 and HIPAA Security Rule safeguard requirements (e.g. 100% MFA enforcement on admin roles).
              </p>
            </div>

            <div className="p-6 bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                <FileText className="w-4 h-4 text-amber-500" />
                Readiness Ledger & Compliance Drift
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                An append-only time-series ledger documenting exact scoring changes, telemetry delta causality, and automated remediation event tracking.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Maturity Levels */}
      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            Readiness Maturity Levels
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Standardized maturity benchmarks based on deterministic telemetry scores.
          </p>
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-800">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-900 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Level</th>
                <th className="px-5 py-3.5">Name</th>
                <th className="px-5 py-3.5">Score</th>
                <th className="px-5 py-3.5">Evidence Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950 text-xs sm:text-sm">
              {[
                { level: 1, name: 'Initial', range: '0–20%', desc: 'Unverified or ad-hoc security controls with significant telemetry gaps.' },
                { level: 2, name: 'Developing', range: '21–40%', desc: 'Basic telemetry connected; key controls (MFA, immutable backups) unverified.' },
                { level: 3, name: 'Defined', range: '41–60%', desc: 'Core systems monitored; incident playbooks and alerting established.' },
                { level: 4, name: 'Managed', range: '61–80%', desc: 'Proactive control verification with automated gap detection.' },
                { level: 5, name: 'Optimized', range: '81–100%', desc: 'Continuous automated verification across all domains with proven recovery.' },
              ].map((l) => (
                <tr key={l.level} className="hover:bg-slate-900/50 transition-colors">
                  <td className="px-5 py-4 font-mono font-bold text-emerald-500">L{l.level}</td>
                  <td className="px-5 py-4 font-semibold text-slate-200">{l.name}</td>
                  <td className="px-5 py-4 font-mono text-slate-300 font-semibold">{l.range}</td>
                  <td className="px-5 py-4 text-slate-400 text-xs">{l.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Navigation Footer */}
      <div className="pt-6 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <Link
          to="/morning-brief"
          className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-500 hover:text-emerald-400 transition-colors"
        >
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Return to Morning Operations</span>
        </Link>
        <Link
          to="/docs/frameworks"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition-colors"
        >
          <span>View Framework Mappings (NIST CSF 2.0 / HIPAA)</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}

