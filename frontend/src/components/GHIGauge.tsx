/**
 * GHI Gauge — Governance Health Index focal-point component.
 *
 * Displays the composite GHI grade (A–F) with a circular gauge,
 * pulsing AI-status indicator, and dimension breakdown.
 */

import { ShieldCheck, Sparkles, TrendingUp, Server, Scale, FileCheck, Info } from 'lucide-react';
import type { GHIResponse } from '../api';
import { Tooltip } from './ui';

/* ── colour + label map per grade ──────────────────────────────── */
const GRADE_META: Record<string, { ring: string; bg: string; text: string; label: string }> = {
  A: { ring: 'stroke-success-500', bg: 'bg-success-50 dark:bg-success-900/20', text: 'text-success-700 dark:text-success-400', label: 'Excellent' },
  B: { ring: 'stroke-primary-500', bg: 'bg-primary-50 dark:bg-primary-900/20', text: 'text-primary-700 dark:text-primary-400', label: 'Good' },
  C: { ring: 'stroke-warning-500', bg: 'bg-warning-50 dark:bg-warning-900/20', text: 'text-warning-700 dark:text-warning-400', label: 'Fair' },
  D: { ring: 'stroke-warning-600', bg: 'bg-warning-50 dark:bg-warning-900/20', text: 'text-warning-700 dark:text-warning-400', label: 'At Risk' },
  F: { ring: 'stroke-danger-500', bg: 'bg-danger-50 dark:bg-danger-900/20', text: 'text-danger-700 dark:text-danger-400', label: 'Critical' },
};

const DIMENSION_ICONS: Record<string, typeof ShieldCheck> = {
  audit: FileCheck,
  lifecycle: Server,
  sla: TrendingUp,
  compliance: Scale,
};

const DIMENSION_LABELS: Record<string, string> = {
  audit: 'Audit Readiness',
  lifecycle: 'Lifecycle Health',
  sla: 'SLA Compliance',
  compliance: 'Framework Coverage',
};

const DIMENSION_TOOLTIPS: Record<string, string> = {
  audit: 'Score = 100 − (Critical×15) − (High×8) − (Medium×3). Based on open findings severity.',
  lifecycle: 'Deductions: EOL component = −25, Deprecated = −15, Outdated (2+ major versions) = −5.',
  sla: 'Compares your SLA target against standard uptime tiers (99.0%–99.99%).',
  compliance: 'Normalized from mandatory + recommended framework count for your governance profile.',
};

interface GHIGaugeProps {
  data: GHIResponse;
}

export default function GHIGauge({ data }: GHIGaugeProps) {
  const meta = GRADE_META[data.grade] || GRADE_META.F;
  const pct = Math.min(data.ghi, 100);

  // SVG circular gauge (radius ~54, circumference ≈ 339.3)
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className={`rounded-3xl border ${meta.bg} border-slate-200 dark:border-slate-800 p-8 animate-fade-up`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h2 className="text-title text-slate-900 dark:text-slate-100 font-extrabold tracking-tight">Security Posture</h2>
        </div>
        {/* Pulsing SIEM indicator */}
        <div className="flex items-center gap-2 bg-slate-100/50 dark:bg-slate-900/40 px-2.5 py-1 rounded-full border border-slate-200/50 dark:border-slate-800/40">
          <span className="relative flex h-2 w-2">
            <span className="animate-pulse-siem absolute inline-flex h-full w-full rounded-full bg-primary-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
          </span>
          <span className="text-[10px] font-bold font-mono text-slate-500 dark:text-slate-400 tracking-wider">
            VERIFIED_VIA_SIEM
          </span>
        </div>
      </div>
 
      <div className="flex flex-col lg:flex-row items-center gap-8">
        {/* Circular gauge */}
        <div className="relative flex-shrink-0">
          <svg width="140" height="140" viewBox="0 0 140 140" className="transform -rotate-90">
            {/* Outer Tick Ring */}
            <circle
              cx="70" cy="70" r="64"
              fill="none"
              strokeWidth="1"
              strokeDasharray="1, 4"
              className="stroke-slate-400 dark:stroke-slate-600 opacity-60"
            />
            {/* Compass Ticks */}
            <line x1="70" y1="2" x2="70" y2="7" stroke="currentColor" className="text-primary-500/60" strokeWidth="1.5" />
            <line x1="70" y1="133" x2="70" y2="138" stroke="currentColor" className="text-primary-500/60" strokeWidth="1.5" />
            <line x1="2" y1="70" x2="7" y2="70" stroke="currentColor" className="text-primary-500/60" strokeWidth="1.5" />
            <line x1="133" y1="70" x2="138" y2="70" stroke="currentColor" className="text-primary-500/60" strokeWidth="1.5" />
            
            {/* Background ring */}
            <circle
              cx="70" cy="70" r={radius}
              fill="none"
              strokeWidth="8"
              className="stroke-slate-200 dark:stroke-slate-800"
            />
            {/* Progress ring */}
            <circle
              cx="70" cy="70" r={radius}
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className={`${meta.ring} transition-[stroke-dashoffset] duration-1000 ease-out`}
            />
            {/* Inner grid ring */}
            <circle
              cx="70" cy="70" r="44"
              fill="none"
              strokeWidth="0.5"
              strokeDasharray="2, 6"
              className="stroke-slate-350 dark:stroke-slate-700 opacity-40"
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center mt-1">
            <Tooltip
              content="GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1). Deterministic — no LLM."
              placement="bottom"
            >
              <span className={`text-3xl font-extrabold font-mono tracking-tighter ${meta.text} cursor-help`}>{data.grade}</span>
            </Tooltip>
            <span className="text-[10px] font-mono font-bold text-slate-500 dark:text-slate-400 mt-0.5">{data.ghi.toFixed(1)}%</span>
            <span className="text-[8px] font-mono text-primary-600 dark:text-primary-400 mt-0.5 uppercase tracking-wider scale-90">SECURE_SYNC</span>
          </div>
        </div>
 
        {/* Dimension breakdown */}
        <div className="flex-1 w-full grid grid-cols-2 gap-4">
          {Object.entries(data.dimensions).map(([key, score]) => {
            const Icon = DIMENSION_ICONS[key] || ShieldCheck;
            const label = DIMENSION_LABELS[key] || key;
            const weight = data.weights[key as keyof typeof data.weights];
            const barPct = Math.min(score, 100);
            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center gap-1.5">
                  <Icon className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  <span className="text-caption text-slate-500 dark:text-slate-400">{label}</span>
                  <Tooltip content={DIMENSION_TOOLTIPS[key] || ''} placement="top">
                    <Info className="w-3 h-3 text-slate-400 dark:text-slate-600 cursor-help" />
                  </Tooltip>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden relative flex items-center">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ease-out ${
                        score >= 80 ? 'bg-success-500' : score >= 60 ? 'bg-warning-500' : 'bg-danger-500'
                      }`}
                      style={{ width: `${barPct}%` }}
                    />
                    {/* High-precision LED segments grid (10 blocks) */}
                    <div className="absolute inset-0 flex justify-between pointer-events-none px-0.5">
                      {Array.from({ length: 9 }).map((_, i) => (
                        <div key={i} className="w-[1.5px] h-full bg-white dark:bg-slate-950/80 opacity-40" />
                      ))}
                    </div>
                  </div>
                  <span className="text-caption text-slate-700 dark:text-slate-300 w-10 text-right tabular-nums">
                    {score.toFixed(0)}%
                  </span>
                </div>
                <span className="text-overline text-slate-400 dark:text-slate-500">
                  Weight: {((weight ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
 
      {/* Footer status */}
      <div className="mt-6 flex items-center justify-between border-t border-slate-200/50 dark:border-slate-800/40 pt-4">
        <span className={`text-body font-bold ${meta.text}`}>
          {meta.label} — GHI {data.grade}
        </span>
        {data.issues.length > 0 && (
          <span className="text-caption text-slate-500 dark:text-slate-400 font-mono">
            {data.issues.length} ISSUE{data.issues.length !== 1 ? 'S' : ''}_DETECTED
          </span>
        )}
      </div>
    </div>
  );
}
