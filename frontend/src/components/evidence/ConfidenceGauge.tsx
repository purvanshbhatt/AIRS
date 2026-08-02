import React from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';

interface ConfidenceGaugeProps {
  /** Aggregate confidence score 0-100, or null when no data is available. */
  score: number | null;
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export function ConfidenceGauge({ score, size = 'md', isLoading = false }: ConfidenceGaugeProps) {
  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-emerald-500';
    if (s >= 50) return 'text-amber-500';
    return 'text-red-500';
  };

  const getStrokeColor = (s: number) => {
    if (s >= 80) return '#00C853';
    if (s >= 50) return '#D97706';
    return '#EF4444';
  };

  const sizeClasses = {
    sm: { container: 'h-14 w-14', svg: 56, strokeWidth: 4, text: 'text-xs' },
    md: { container: 'h-24 w-24', svg: 96, strokeWidth: 6, text: 'text-base font-extrabold' },
    lg: { container: 'h-36 w-36', svg: 144, strokeWidth: 8, text: 'text-2xl font-black' },
  }[size];

  const radius = (sizeClasses.svg - sizeClasses.strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;

  if (isLoading) {
    return (
      <div className={`${sizeClasses.container} flex items-center justify-center`}>
        <svg className="animate-spin h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>
    );
  }

  // S1.8-AUDIT-FIX-P01: ScoreUnavailableState — render dashed ring + em-dash when data not yet available.
  // Prevents any numeric fabrication fallback (PRODUCT_MOAT #4 invariant).
  if (score === null || score === undefined) {
    return (
      <div className="relative flex flex-col items-center justify-center">
        <div className={`${sizeClasses.container} relative flex items-center justify-center`}>
          <svg width={sizeClasses.svg} height={sizeClasses.svg} className="transform -rotate-90">
            <circle
              cx={sizeClasses.svg / 2}
              cy={sizeClasses.svg / 2}
              r={radius}
              stroke="rgba(156, 163, 175, 0.15)"
              strokeWidth={sizeClasses.strokeWidth}
              fill="transparent"
              strokeDasharray="4 4"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className={`${sizeClasses.text} text-slate-400 tracking-tight`}>—</span>
            {size === 'lg' && (
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider mt-0.5">
                No Data
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center justify-center">
      <div className={`${sizeClasses.container} relative flex items-center justify-center`}>
        <svg
          width={sizeClasses.svg}
          height={sizeClasses.svg}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={sizeClasses.svg / 2}
            cy={sizeClasses.svg / 2}
            r={radius}
            stroke="rgba(156, 163, 175, 0.1)"
            strokeWidth={sizeClasses.strokeWidth}
            fill="transparent"
          />
          {/* Active progress arc */}
          <circle
            cx={sizeClasses.svg / 2}
            cy={sizeClasses.svg / 2}
            r={radius}
            stroke={getStrokeColor(score)}
            strokeWidth={sizeClasses.strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        {/* Score text overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className={`${sizeClasses.text} ${getScoreColor(score)} tracking-tight`}>
            {score.toFixed(0)}%
          </span>
          {size === 'lg' && (
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider mt-0.5">
              Confidence
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConfidenceGauge;
