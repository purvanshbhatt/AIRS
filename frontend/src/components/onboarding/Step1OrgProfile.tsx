import React from 'react';
import { Building2, Users, MapPin, Activity, ShieldCheck, Sparkles, Shield, Info, ArrowRight } from 'lucide-react';
import type { OnboardingOrgProfile, OnboardingMode } from '../../types/onboarding';

interface Step1OrgProfileProps {
  profile: OnboardingOrgProfile;
  onChangeProfile: (updated: Partial<OnboardingOrgProfile>) => void;
  mode: OnboardingMode;
  onNext: () => void;
  isSubmitting?: boolean;
}

const INDUSTRY_PROFILES = [
  {
    id: 'Healthcare',
    label: 'Healthcare & Clinical Operations',
    description: 'Prioritizes patient safety, EHR database integrity (Epic/Cerner), and HIPAA safeguard evidence.',
    icon: Activity,
  },
  {
    id: 'Financial Services',
    label: 'Financial Services & Banking',
    description: 'Prioritizes transactional integrity, audit trail persistence, and SOC 2 / GLBA controls.',
    icon: ShieldCheck,
  },
  {
    id: 'SaaS / Technology',
    label: 'SaaS & Cloud Infrastructure',
    description: 'Focuses on cloud configuration drifts, IAM least privilege, and API security telemetry.',
    icon: Shield,
  },
  {
    id: 'Enterprise',
    label: 'Enterprise & Manufacturing',
    description: 'Balanced posture covering endpoint hygiene, supply chain controls, and disaster recovery.',
    icon: Building2,
  },
];

export function Step1OrgProfile({
  profile,
  onChangeProfile,
  mode,
  onNext,
  isSubmitting = false,
}: Step1OrgProfileProps) {
  const isDemo = mode === 'demo';

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner explaining Step 1 */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              {isDemo ? 'Acme Health Systems — Baseline Readiness Profile' : 'Configure Your Organization Profile'}
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              ResilAI uses your organizational profile to establish strict deterministic thresholds for incident readiness, backup immutability, and clinical risk ranking.
            </p>
          </div>
        </div>

        {isDemo && (
          <div className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 text-xs font-mono font-semibold shrink-0 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Pre-Loaded Demo Data</span>
          </div>
        )}
      </div>

      {/* Main Profile Form & Baseline Card Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Organization Details Form */}
        <div className="lg:col-span-7 space-y-5 bg-surface-container-low p-6 rounded-2xl border border-outline-variant/40">
          <h4 className="text-sm font-bold text-on-surface uppercase tracking-wider text-xs font-mono text-ready-emerald">
            1. Core Identity & Location
          </h4>

          {/* Org Name */}
          <div>
            <label className="block text-xs font-semibold text-on-surface mb-1.5">
              Organization Name *
            </label>
            <div className="relative">
              <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                value={profile.name}
                onChange={(e) => onChangeProfile({ name: e.target.value })}
                placeholder="e.g. Acme Health Systems"
                disabled={isDemo || isSubmitting}
                className="w-full pl-10 pr-4 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all placeholder-on-surface-variant/50"
              />
            </div>
            {isDemo && (
              <p className="text-[11px] text-amber-500/90 mt-1 flex items-center gap-1">
                <Info className="w-3 h-3 inline" /> Preloaded with simulated Acme Health Systems profile.
              </p>
            )}
          </div>

          {/* Company Size & Country */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-on-surface mb-1.5">
                Company Size
              </label>
              <div className="relative">
                <Users className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
                <select
                  value={profile.size}
                  onChange={(e) => onChangeProfile({ size: e.target.value })}
                  disabled={isDemo || isSubmitting}
                  className="w-full pl-10 pr-8 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all appearance-none"
                >
                  <option value="1-50">1-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-1000">201-1000 employees</option>
                  <option value="1000+">1000+ employees</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface mb-1.5">
                Country / Jurisdiction
              </label>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
                <select
                  value={profile.country}
                  onChange={(e) => onChangeProfile({ country: e.target.value })}
                  disabled={isDemo || isSubmitting}
                  className="w-full pl-10 pr-8 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all appearance-none"
                >
                  <option value="United States">United States (HIPAA / NIST)</option>
                  <option value="Canada">Canada (PIPEDA)</option>
                  <option value="United Kingdom">United Kingdom (NHS DSPT)</option>
                  <option value="European Union">European Union (GDPR / NIS2)</option>
                  <option value="Other">Other Global</option>
                </select>
              </div>
            </div>
          </div>

          {/* Region / State */}
          <div>
            <label className="block text-xs font-semibold text-on-surface mb-1.5">
              Region / State
            </label>
            <input
              type="text"
              value={profile.regionState}
              onChange={(e) => onChangeProfile({ regionState: e.target.value })}
              placeholder="e.g. California, New York, Ontario"
              disabled={isDemo || isSubmitting}
              className="w-full px-4 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all placeholder-on-surface-variant/50"
            />
          </div>

          {/* Operating Profile Selection */}
          <div className="pt-2">
            <label className="block text-xs font-semibold text-on-surface mb-2">
              Operating Profile & Clinical Baseline
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {INDUSTRY_PROFILES.map((ind) => {
                const Icon = ind.icon;
                const isSelected = profile.industry.toLowerCase().includes(ind.id.toLowerCase());
                return (
                  <button
                    key={ind.id}
                    type="button"
                    onClick={() => onChangeProfile({ industry: ind.label })}
                    disabled={isDemo || isSubmitting}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'border-ready-emerald bg-ready-emerald/10 text-on-surface shadow-sm ring-1 ring-ready-emerald/40'
                        : 'border-outline-variant/40 bg-surface-container hover:border-outline-variant text-on-surface-variant'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`w-4 h-4 ${isSelected ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
                      <span className="text-xs font-bold text-on-surface">{ind.id}</span>
                    </div>
                    <p className="text-[11px] text-on-surface-variant leading-relaxed line-clamp-2">
                      {ind.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Mathematical Verification Baseline Explanation */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-gradient-to-br from-surface-container to-surface-container-high p-6 rounded-2xl border border-ready-emerald/20 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-ready-emerald/5 rounded-full blur-2xl pointer-events-none" />
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-ready-emerald uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Deterministic Trust Contract</span>
            </div>
            <h4 className="text-base font-bold text-on-surface mb-2">
              How ResilAI Computes Incident Readiness
            </h4>
            <p className="text-xs text-on-surface-variant leading-relaxed mb-4">
              Unlike legacy compliance checklists that rely on subjective questionnaires or unverified self-attestations, ResilAI operates on mathematical control verification.
            </p>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-surface-container-lowest/80 rounded-xl border border-outline-variant/40 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-ready-emerald/20 text-ready-emerald font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">1</span>
                <div>
                  <strong className="text-on-surface block mb-0.5">Continuous Verification</strong>
                  <span className="text-on-surface-variant">Telemetry is polled directly from identity, backup, and endpoint systems every few minutes.</span>
                </div>
              </div>

              <div className="p-3 bg-surface-container-lowest/80 rounded-xl border border-outline-variant/40 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-ready-emerald/20 text-ready-emerald font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">2</span>
                <div>
                  <strong className="text-on-surface block mb-0.5">Zero Hallucination Guarantee</strong>
                  <span className="text-on-surface-variant">Scores are 100% mathematical. Frontend never invents scores and LLMs never evaluate raw risk numbers.</span>
                </div>
              </div>

              <div className="p-3 bg-surface-container-lowest/80 rounded-xl border border-outline-variant/40 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">3</span>
                <div>
                  <strong className="text-on-surface block mb-0.5">Missing Telemetry = 0% Score</strong>
                  <span className="text-on-surface-variant">If a security connector stops feeding evidence, confidence immediately drops to &quot;Unable to verify&quot;.</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/40 text-xs text-on-surface-variant flex items-center justify-between">
            <div>
              <span className="text-on-surface font-semibold block">Next Step:</span>
              <span>Connect your security systems (Microsoft 365, Veeam, CrowdStrike, SentinelOne)</span>
            </div>
            <ArrowRight className="w-4 h-4 text-ready-emerald shrink-0" />
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="pt-4 border-t border-outline-variant/30 flex justify-end">
        <button
          type="button"
          onClick={onNext}
          disabled={!profile.name.trim() || isSubmitting}
          className="px-6 py-3 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Continue to Step 2: Connect Security Systems</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
