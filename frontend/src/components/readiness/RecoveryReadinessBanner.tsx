import React from 'react';
import { ShieldAlert, ArrowRight, Server, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';
import { TrustBadge } from './TrustBadge';

interface RecoveryReadinessBannerProps {
  canRecoverToday: boolean;
  estimatedRecoveryHours: number;
  lastBackupVerifiedAt: string;
}

export function RecoveryReadinessBanner({
  canRecoverToday,
  estimatedRecoveryHours,
  lastBackupVerifiedAt
}: RecoveryReadinessBannerProps) {
  return (
    <div className={cn(
      "rounded-3xl border p-8 flex flex-col md:flex-row md:items-center justify-between gap-8",
      canRecoverToday 
        ? "bg-emerald-900 text-white border-emerald-800" 
        : "bg-red-900 text-white border-red-800"
    )}>
      <div className="flex-1 space-y-4">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-emerald-400" />
          <span className="text-emerald-400/90 font-medium tracking-wide text-sm uppercase">Recovery Readiness</span>
        </div>
        <h2 className="text-3xl md:text-4xl font-semibold">
          If today goes wrong...<br/>Can your business continue?
        </h2>
        <div className="flex items-center gap-3 mt-4">
          <span className={cn(
            "text-2xl font-bold px-4 py-1.5 rounded-full",
            canRecoverToday ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
          )}>
            {canRecoverToday ? 'YES' : 'NO'}
          </span>
          <TrustBadge status="verified" text={`Verified ${lastBackupVerifiedAt}`} className="bg-emerald-950 border-emerald-800/50 text-emerald-400" />
        </div>
      </div>

      <div className="flex flex-col gap-4 bg-black/20 p-6 rounded-2xl md:min-w-[300px]">
        <div className="flex justify-between items-center pb-4 border-b border-white/10">
          <div className="flex items-center gap-2 text-emerald-100/70">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Estimated Recovery</span>
          </div>
          <span className="font-semibold">{estimatedRecoveryHours} hours</span>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 text-emerald-100/70">
            <Server className="w-4 h-4" />
            <span className="text-sm">Critical Systems</span>
          </div>
          <span className="font-semibold text-emerald-400">Protected</span>
        </div>

        <button className="w-full mt-4 flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 transition-colors py-2.5 rounded-xl font-medium text-sm">
          View Continuity Plan <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
