import { ShieldCheck, AlertTriangle, HelpCircle, ShieldAlert } from 'lucide-react';
import type { VerdictTone } from '../PlainLanguage';

/**
 * Large readiness ring for the V2 hero. The score is the report's
 * clinic_health_pct; nothing is interpolated or estimated here.
 */
export function ReadinessRing({
  score,
  tone,
  className = '',
}: {
  /** 0..100 from the report, or null when nothing has been checked yet. */
  score: number | null;
  tone: VerdictTone;
  className?: string;
}) {
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const pct = score === null ? 0 : Math.min(100, Math.max(0, score));
  const offset = circumference - (circumference * pct) / 100;

  const stroke: Record<VerdictTone, string> = {
    ready: 'text-ready-emerald',
    warning: 'text-drift-amber',
    critical: 'text-critical-red',
    unknown: 'text-outline-variant',
  };
  const Icon = tone === 'ready' ? ShieldCheck : tone === 'warning' ? AlertTriangle : tone === 'critical' ? ShieldAlert : HelpCircle;
  const label = tone === 'ready' ? 'All clear' : tone === 'warning' ? 'Needs attention' : tone === 'critical' ? 'Not protected' : 'Not checked';

  return (
    <div
      className={`relative w-48 h-48 sm:w-56 sm:h-56 lg:w-64 lg:h-64 shrink-0 ${className}`}
      role="img"
      aria-label={score === null ? 'Readiness score not available yet' : `Readiness score ${pct} percent, ${label}`}
      data-testid="readiness-ring"
    >
      <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle className="text-surface-container-highest" cx="50" cy="50" r={radius} fill="none" stroke="currentColor" strokeWidth="5" />
        <circle
          className={`transition-[stroke-dashoffset] duration-1000 ease-out ${stroke[tone]}`}
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <Icon className={`w-6 h-6 sm:w-7 sm:h-7 mb-1 ${stroke[tone]}`} aria-hidden="true" />
        <div className="flex items-baseline justify-center leading-none">
          <span className="text-5xl sm:text-6xl font-extrabold tracking-tight text-on-surface" data-testid="readiness-score">
            {score === null ? '--' : pct}
          </span>
          {score !== null && <span className={`ml-0.5 text-base font-mono font-bold ${stroke[tone]}`}>%</span>}
        </div>
        <span className="mt-1.5 text-[10px] sm:text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant">
          {label}
        </span>
      </div>
    </div>
  );
}
