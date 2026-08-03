import React from 'react';
import { CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { cn } from '../../lib/utils'; // Assuming this exists, typically standard in these stacks.

interface TrustBadgeProps {
  status: 'verified' | 'unverified' | 'unknown';
  text: string;
  className?: string;
}

export function TrustBadge({ status, text, className }: TrustBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium tracking-wide",
        status === 'verified' && "bg-emerald-50 text-emerald-700 border border-emerald-200/50",
        status === 'unverified' && "bg-amber-50 text-amber-700 border border-amber-200/50",
        status === 'unknown' && "bg-slate-100 text-slate-600 border border-slate-200",
        className
      )}
    >
      {status === 'verified' && <CheckCircle2 className="w-3.5 h-3.5" />}
      {status === 'unverified' && <AlertCircle className="w-3.5 h-3.5" />}
      {status === 'unknown' && <HelpCircle className="w-3.5 h-3.5" />}
      {text}
    </div>
  );
}
