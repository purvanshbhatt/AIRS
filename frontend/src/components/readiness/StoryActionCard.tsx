import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, FileCode, PlayCircle, Loader2 } from 'lucide-react';
import { TrustBadge } from './TrustBadge';
import { cn } from '../../lib/utils';
import type { ActionCard } from '../../types/readiness';

interface StoryActionCardProps {
  action: ActionCard;
  onFix: (id: string) => Promise<void>;
}

export function StoryActionCard({ action, onFix }: StoryActionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [isFixed, setIsFixed] = useState(false);

  const handleFix = async () => {
    setIsFixing(true);
    try {
      await onFix(action.id);
      setIsFixed(true);
    } catch (e) {
      console.error(e);
    } finally {
      setIsFixing(false);
    }
  };

  const isHighConfidence = action.confidence_pct >= 90;

  return (
    <div className={cn(
      "border rounded-2xl bg-white overflow-hidden transition-all duration-300",
      expanded ? "shadow-md border-slate-300" : "shadow-sm border-slate-200 hover:border-slate-300"
    )}>
      {/* Top Level Summary */}
      <div 
        className="p-5 flex items-start gap-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-shrink-0 mt-1">
          <div className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center",
            action.severity === 'critical' ? "bg-red-50 text-red-600" :
            action.severity === 'high' ? "bg-amber-50 text-amber-600" :
            "bg-blue-50 text-blue-600"
          )}>
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-base font-semibold text-slate-900 truncate pr-4">
              {action.title}
            </h3>
            {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
          </div>
          
          <div className="flex items-center gap-3 flex-wrap">
            <TrustBadge 
              status="verified" 
              text={isHighConfidence ? "High Confidence" : "Needs Review"} 
            />
            <span className="text-sm text-slate-500">
              Verified {action.last_verified_at}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded Content (Progressive Disclosure) */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/50">
          
          {/* Level 1: Facts (Problem & Impact) */}
          <div className="p-6 border-b border-slate-200/60">
            <h4 className="text-xs font-bold tracking-wider text-slate-400 uppercase mb-3">The Facts</h4>
            <p className="text-slate-700 leading-relaxed mb-4">
              {action.impact_narrative}
            </p>
          </div>

          {/* Level 2: Recommendation */}
          <div className="p-6 border-b border-slate-200/60 bg-white">
            <h4 className="text-xs font-bold tracking-wider text-blue-400 uppercase mb-3">Recommendation</h4>
            <p className="text-slate-800 font-medium leading-relaxed mb-6">
              {action.recommendation}
            </p>
            
            <div className="flex items-center gap-4">
              <button 
                onClick={(e) => { e.stopPropagation(); handleFix(); }}
                disabled={isFixing || isFixed}
                className={cn(
                  "flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-colors",
                  isFixed ? "bg-emerald-500 text-white" : "bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                )}
              >
                {isFixed ? (
                  <>Resolved</>
                ) : isFixing ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Applying Fix...</>
                ) : (
                  <><PlayCircle className="w-4 h-4" /> Fix Now</>
                )}
              </button>
              {action.can_be_undone && (
                <span className="text-sm text-slate-500">This action can be undone later.</span>
              )}
            </div>
          </div>

          {/* Level 3 & 4: How We Know & Technical Details (Inside a sub-disclosure) */}
          <details className="group">
            <summary className="p-4 cursor-pointer text-sm font-medium text-slate-500 hover:text-slate-700 flex items-center gap-2 bg-slate-50">
              <FileCode className="w-4 h-4" />
              How We Know & Technical Evidence
            </summary>
            <div className="p-4 pt-0 bg-slate-50">
              <div className="bg-slate-900 rounded-xl p-4 mt-2 overflow-x-auto">
                <div className="text-slate-400 text-xs mb-2">Source: {action.verification_method}</div>
                <pre className="text-emerald-400 text-sm font-mono whitespace-pre-wrap">
                  {action.evidence}
                </pre>
              </div>
            </div>
          </details>

        </div>
      )}
    </div>
  );
}
