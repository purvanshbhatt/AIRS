import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { ReadinessStatus } from '../../types/readiness';

interface TimelineDay {
  date: string; // e.g. "Today", "Yesterday", "Monday", "Sunday"
  status: ReadinessStatus;
}

interface ReadinessHistoryTimelineProps {
  history: TimelineDay[];
}

export function ReadinessHistoryTimeline({ history }: ReadinessHistoryTimelineProps) {
  const getStatusVisuals = (status: ReadinessStatus) => {
    switch (status) {
      case 'safe_to_open':
        return { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50', label: 'READY' };
      case 'action_needed':
        return { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50', label: 'ACTION NEEDED' };
      case 'critical_risk':
        return { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50', label: 'CRITICAL RISK' };
      case 'unknown':
      default:
        return { icon: HelpCircle, color: 'text-slate-400', bg: 'bg-slate-50', label: 'UNKNOWN' };
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-6">Readiness History</h3>
      
      <div className="space-y-4">
        {history.map((day, index) => {
          const isLast = index === history.length - 1;
          const { icon: Icon, color, bg, label } = getStatusVisuals(day.status);
          
          return (
            <div key={index} className="relative flex items-start gap-4">
              {!isLast && (
                <div className="absolute top-8 left-4 bottom-[-16px] w-0.5 bg-slate-100" />
              )}
              <div className={cn("relative z-10 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center", bg, color)}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 pb-4">
                <p className="text-sm font-medium text-slate-900">{day.date}</p>
                <p className={cn("text-xs font-bold mt-0.5", color)}>{label}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
