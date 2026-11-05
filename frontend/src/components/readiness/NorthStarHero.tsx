import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, XCircle, HelpCircle, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { ReadinessStatus } from '../../types/readiness';

interface NorthStarHeroProps {
  status: ReadinessStatus;
  confidencePct: number;
  verifiedSystemsCount: number;
  morningBrief: string;
  trendText: string;
}

export function NorthStarHero({ 
  status, 
  confidencePct, 
  verifiedSystemsCount, 
  morningBrief, 
  trendText 
}: NorthStarHeroProps) {
  const [showPercentage, setShowPercentage] = useState(false);

  const getStatusConfig = () => {
    switch (status) {
      case 'safe_to_open':
        return {
          title: 'READY TODAY',
          color: 'text-emerald-600',
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/20',
          icon: ShieldCheck,
          gradient: 'from-emerald-500/10 via-emerald-500/5 to-transparent'
        };
      case 'action_needed':
        return {
          title: 'ACTION NEEDED',
          color: 'text-amber-600',
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/20',
          icon: AlertTriangle,
          gradient: 'from-amber-500/10 via-amber-500/5 to-transparent'
        };
      case 'critical_risk':
        return {
          title: 'CRITICAL RISK',
          color: 'text-red-600',
          bg: 'bg-red-500/10',
          border: 'border-red-500/20',
          icon: XCircle,
          gradient: 'from-red-500/10 via-red-500/5 to-transparent'
        };
      case 'unknown':
      default:
        return {
          title: 'UNABLE TO VERIFY',
          color: 'text-slate-600',
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/20',
          icon: HelpCircle,
          gradient: 'from-slate-500/10 via-slate-500/5 to-transparent'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const isHighConfidence = confidencePct >= 90;

  return (
    <div className={cn(
      "relative overflow-hidden rounded-3xl border bg-white p-8 md:p-12 transition-all duration-500",
      config.border
    )}>
      {/* Background Gradient */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br opacity-50",
        config.gradient
      )} />

      <div className="relative z-10 flex flex-col items-center text-center max-w-3xl mx-auto">
        <h2 className="text-xl md:text-2xl font-medium text-slate-600 mb-6">Good Morning.</h2>
        
        <div className="flex flex-col items-center justify-center gap-4 mb-6">
          <div className={cn("p-4 rounded-full", config.bg, config.color)}>
            <Icon className="w-12 h-12 md:w-16 md:h-16 stroke-[1.5]" />
          </div>
          <h1 className={cn("text-4xl md:text-6xl font-bold tracking-tight", config.color)}>
            {config.title}
          </h1>
        </div>

        {/* Confidence interactive pill */}
        <button 
          onClick={() => setShowPercentage(!showPercentage)}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100/80 hover:bg-slate-200/80 text-slate-700 text-sm font-medium transition-colors mb-8 group"
        >
          {status === 'unknown' ? (
            <span>Readiness may be lower than shown</span>
          ) : (
            <>
              <span className="flex items-center gap-1.5">
                <span className={cn("w-2 h-2 rounded-full", isHighConfidence ? "bg-emerald-500" : "bg-amber-500")} />
                {showPercentage ? `${confidencePct}% Confidence` : 'High Confidence'}
              </span>
              <span className="text-slate-400">·</span>
              <span>Verified {verifiedSystemsCount} systems</span>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </>
          )}
        </button>

        {/* Morning Brief Narrative */}
        <p className="text-lg md:text-xl text-slate-600 leading-relaxed font-light">
          {status === 'unknown' 
            ? "We couldn't verify critical systems this morning. Please check your data connectors." 
            : morningBrief}
        </p>

        {/* Trend */}
        <div className="mt-8 inline-flex items-center gap-2 text-sm text-slate-500">
          <span className="font-medium text-slate-700">{trendText}</span>
        </div>
      </div>
    </div>
  );
}
