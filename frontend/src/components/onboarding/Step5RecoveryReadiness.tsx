import React from 'react';
import {
  RotateCcw,
  HardDrive,
  Lock,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Zap,
  Server,
  FileCheck,
} from 'lucide-react';
import type { RecoveryReadinessPreview, OnboardingMode } from '../../types/onboarding';
import { DEMO_RECOVERY_PREVIEW } from './onboardingData';

interface Step5RecoveryReadinessProps {
  mode: OnboardingMode;
  onNext: () => void;
  onPrev: () => void;
}

export function Step5RecoveryReadiness({
  mode,
  onNext,
  onPrev,
}: Step5RecoveryReadinessProps) {
  const isDemo = mode === 'demo';
  const recovery = DEMO_RECOVERY_PREVIEW;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
            <RotateCcw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              Incident Recovery Readiness & Backup Immutability Assurance
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              When ransomware strikes, your only true safety net is mathematically proven backup immutability and verified restoration speed.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            <span>30-Day WORM Immutability Active</span>
          </span>
        </div>
      </div>

      {/* Main Recovery Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Immutability Lock */}
        <div className="p-5 rounded-2xl bg-surface-container-low border border-ready-emerald/30 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ready-emerald font-bold">
                Anti-Ransomware Shield
              </span>
              <div className="w-8 h-8 rounded-lg bg-ready-emerald/15 text-ready-emerald flex items-center justify-center">
                <Lock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-ready-emerald mb-1">
              30-Day Locked
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Immutable Object Lock verified via Veeam & S3 API. Backups cannot be encrypted or deleted by compromised admin credentials.
            </p>
          </div>
          <div className="pt-3 mt-4 border-t border-outline-variant/30 text-[11px] font-mono text-ready-emerald flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Air-Gap Cryptographically Proven</span>
          </div>
        </div>

        {/* Metric 2: Clinical Recovery RTO */}
        <div className="p-5 rounded-2xl bg-surface-container-low border border-outline-variant/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-primary-400 font-bold">
                Recovery Time Objective (RTO)
              </span>
              <div className="w-8 h-8 rounded-lg bg-primary-500/15 text-primary-400 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-on-surface mb-1">
              42 Minutes
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Estimated time to restore all core Electronic Health Record (EHR) databases and clinical scheduling systems.
            </p>
          </div>
          <div className="pt-3 mt-4 border-t border-outline-variant/30 text-[11px] font-mono text-on-surface-variant flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-primary-400" />
            <span>Exceeds HIPAA 2-hour SLA standard</span>
          </div>
        </div>

        {/* Metric 3: Recovery Point Objective (RPO) */}
        <div className="p-5 rounded-2xl bg-surface-container-low border border-outline-variant/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface font-bold">
                Recovery Point (RPO)
              </span>
              <div className="w-8 h-8 rounded-lg bg-surface-container-high text-on-surface flex items-center justify-center">
                <Server className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-on-surface mb-1">
              15 Minutes
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Maximum potential transaction gap in event of immediate catastrophic failover. Last continuous log sync was 14m ago.
            </p>
          </div>
          <div className="pt-3 mt-4 border-t border-outline-variant/30 text-[11px] font-mono text-on-surface-variant flex items-center gap-1.5">
            <FileCheck className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Continuous WAL shipping active</span>
          </div>
        </div>
      </div>

      {/* Narrative Scenario Box */}
      <div className="p-6 rounded-2xl bg-surface-container border border-outline-variant/50 relative overflow-hidden">
        <h4 className="text-sm font-bold text-on-surface mb-2 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-ready-emerald" />
          <span>Executive Business Continuity Assessment</span>
        </h4>
        <p className="text-sm text-on-surface font-medium leading-relaxed mb-4">
          &ldquo;{recovery.readinessNarrative}&rdquo;
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30">
            <span className="text-[10px] font-mono uppercase text-on-surface-variant block mb-1">Primary Backup Target:</span>
            <strong className="text-on-surface font-mono">{recovery.backupSource}</strong>
          </div>
          <div className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30">
            <span className="text-[10px] font-mono uppercase text-on-surface-variant block mb-1">Last Validated Snapshot:</span>
            <strong className="text-ready-emerald font-mono">{recovery.lastSuccessfulSnapshot}</strong>
          </div>
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          className="px-5 py-2.5 rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-semibold text-xs transition-all flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Triage</span>
        </button>

        <button
          type="button"
          onClick={onNext}
          className="px-6 py-3 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          <span>Continue to Step 6: Executive Board Report</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
