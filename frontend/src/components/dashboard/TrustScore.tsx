import { Shield, Sparkles, CheckCircle2, FileEdit } from 'lucide-react';
import { Card, CardContent } from '../ui';

interface TrustScoreProps {
  score: number;
  verifiedTelemetryPct: number;
  selfAttestedPct: number;
}

export default function TrustScore({
  score,
  verifiedTelemetryPct,
  selfAttestedPct,
}: TrustScoreProps) {
  return (
    <Card className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300">
      <CardContent className="p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Left section: Score text and main description */}
          <div className="space-y-4 max-w-xl text-left">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-[#00C853]/10 text-[#00C853] rounded-xl border border-[#00C853]/20">
                <Shield className="w-5 h-5" />
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                ResilAI Mathematical Scoring Engine
              </span>
            </div>
            
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-snug">
              Audit Confidence Index
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-semibold">
              This index represents the verified maturity of your AI and systems security posture. It differentiates between self-attested documentation (manual questionnaire baselines) and deterministic telemetry collected continuously from active endpoints, APIs, and logs.
            </p>
          </div>

          {/* Right section: High-density numeric score display */}
          <div className="flex items-center gap-6 shrink-0 bg-slate-50/50 dark:bg-slate-900/30 p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800/40">
            <div className="relative flex items-center justify-center w-24 h-24 rounded-full border-4 border-[#00C853] bg-emerald-500/5 shadow-inner">
              <div className="text-center">
                <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tighter">
                  {score}
                </span>
                <span className="text-xs font-bold text-slate-500 dark:text-slate-450 block -mt-1">
                  / 100
                </span>
              </div>
            </div>
            
            <div className="space-y-1.5 text-left">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-[#00C853] animate-pulse" />
                <span className="text-xs font-extrabold text-[#00C853] uppercase tracking-wider">
                  Verified Readiness
                </span>
              </div>
              <p className="text-2xl font-black text-slate-800 dark:text-slate-200 tracking-tight">
                {score >= 80 ? 'Resilient' : score >= 60 ? 'Managed' : 'Critical'}
              </p>
              <p className="text-[10px] text-slate-450 font-bold">
                RECALCULATED SECONDS AGO
              </p>
            </div>
          </div>
        </div>

        {/* Dynamic breakdown bar */}
        <div className="mt-8 pt-6 border-t border-slate-200/60 dark:border-slate-800/60 text-left">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider mb-2.5">
            <div className="flex items-center gap-1 text-slate-500">
              <span>Control Weight Allocation</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[#00C853] flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded bg-[#00C853] inline-block"></span>
                {verifiedTelemetryPct}% Telemetry-Verified
              </span>
              <span className="text-[#D97706] flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded bg-[#D97706] inline-block"></span>
                {selfAttestedPct}% Self-Attested
              </span>
            </div>
          </div>

          {/* Stacked indicator bar */}
          <div className="w-full h-3 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden flex border border-slate-200/30 dark:border-slate-800/20">
            <div 
              style={{ width: `${verifiedTelemetryPct}%` }}
              className="h-full bg-gradient-to-r from-emerald-500 to-[#00C853] transition-all duration-500"
            />
            <div 
              style={{ width: `${selfAttestedPct}%` }}
              className="h-full bg-gradient-to-r from-amber-500 to-[#D97706] transition-all duration-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 text-[11px] text-slate-500 font-semibold leading-relaxed">
            <div className="flex gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#00C853] shrink-0 mt-0.5" />
              <span>
                <strong className="text-slate-700 dark:text-slate-300">Continuous Telemetry:</strong> Inbound events from Wazuh agents, Splunk logging configurations, and secure API gateways verify these controls deterministically.
              </span>
            </div>
            <div className="flex gap-2">
              <FileEdit className="w-4 h-4 text-[#D97706] shrink-0 mt-0.5" />
              <span>
                <strong className="text-slate-700 dark:text-slate-300">Self-Attestation:</strong> Questionnaire assessment submissions define the baseline for these controls. These are subject to audit verification before transition.
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
