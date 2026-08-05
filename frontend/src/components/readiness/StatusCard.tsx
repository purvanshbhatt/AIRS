import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, FileCode, PlayCircle, Loader2, Sparkles, Server, CheckCircle2, XCircle } from 'lucide-react';
import { TrustBadge } from './TrustBadge';
import { AIDrawer } from './AIDrawer';
import { cn } from '../../lib/utils';
import { tokens } from '../../lib/design-tokens';
import type { ActionCard } from '../../types/readiness';

interface StatusCardProps {
  variant: 'hero' | 'story' | 'technical' | 'compact';
  action: ActionCard;
  onFix?: (id: string) => Promise<void>;
  onViewEvidence?: (id: string) => void;
}

export function StatusCard({ variant, action, onFix, onViewEvidence }: StatusCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [isFixed, setIsFixed] = useState(false);
  const [aiDrawerOpen, setAiDrawerOpen] = useState(false);

  const handleFix = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!onFix) return;
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
  
  const statusColors = action.severity === 'critical' ? tokens.status.error :
                       action.severity === 'high' ? tokens.status.warning :
                       tokens.status.ready;

  const StatusIcon = action.severity === 'critical' || action.severity === 'high' ? AlertTriangle : CheckCircle2;

  // Render Compact Variant (Used in grids, small summaries)
  if (variant === 'compact') {
    return (
      <div className={cn(tokens.surface.base, "p-4 flex items-center justify-between", tokens.interaction.hover)}>
        <div className="flex items-center gap-3">
          <div className={cn("w-8 h-8 rounded-full flex items-center justify-center", statusColors.bg, statusColors.text)}>
            <StatusIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className={cn(tokens.typography.cardTitle, "text-sm")}>{action.title}</h3>
            <p className={tokens.typography.small}>Verified {action.last_verified_at}</p>
          </div>
        </div>
      </div>
    );
  }

  // Render Hero Variant (Top level "Today" page header block)
  if (variant === 'hero') {
    return (
      <div className={cn(tokens.surface.base, "p-8 md:p-10 text-center")}>
        <div className={cn("mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-6", statusColors.bg, statusColors.text)}>
          <StatusIcon className="w-8 h-8" />
        </div>
        <h2 className={tokens.typography.hero}>{action.title}</h2>
        <p className={cn(tokens.typography.body, "mt-4 max-w-2xl mx-auto")}>{action.impact_narrative}</p>
        
        {onFix && (
          <div className="mt-8">
            <button 
              onClick={handleFix}
              disabled={isFixing || isFixed}
              className={cn(tokens.button.primary, isFixed && "bg-emerald-500 hover:bg-emerald-600")}
            >
              {isFixed ? "Resolved" : isFixing ? <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Fixing...</> : "Take Action"}
            </button>
          </div>
        )}
      </div>
    );
  }

  // Render Story Variant (Default interactive card with progressive disclosure)
  // This incorporates the AI Explain drawer
  return (
    <>
      <div className={cn(
        tokens.surface.base,
        "overflow-hidden transition-all duration-300",
        expanded ? "shadow-md border-slate-300 dark:border-slate-700" : tokens.interaction.hover
      )}>
        {/* Top Level Summary (Card) */}
        <div 
          className="p-5 flex items-start gap-4 cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex-shrink-0 mt-1">
            <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", statusColors.bg, statusColors.text)}>
              <StatusIcon className="w-5 h-5" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-1">
              <h3 className={cn(tokens.typography.cardTitle, "truncate pr-4")}>
                {action.title}
              </h3>
              <div className="flex items-center gap-2">
                <button 
                  onClick={(e) => { e.stopPropagation(); setAiDrawerOpen(true); }}
                  className={tokens.button.aiExplain}
                >
                  <Sparkles className="w-3 h-3" /> Explain
                </button>
                {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
              </div>
            </div>
            
            <div className="flex items-center gap-3 flex-wrap">
              <TrustBadge 
                status="verified" 
                text={isHighConfidence ? "High Confidence" : "Needs Review"} 
              />
              <span className={tokens.typography.small}>
                Verified {action.last_verified_at}
              </span>
            </div>
          </div>
        </div>

        {/* Expanded Content (Progressive Disclosure inline) */}
        {expanded && (
          <div className="border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
            
            {/* The Story */}
            <div className="p-6 border-b border-slate-200/60 dark:border-slate-800">
              <p className={tokens.typography.body}>
                {action.impact_narrative}
              </p>
            </div>

            {/* The Action */}
            {onFix && (
              <div className="p-6 bg-white dark:bg-slate-900">
                <h4 className="text-xs font-bold tracking-wider text-indigo-400 uppercase mb-3">Recommendation</h4>
                <p className="text-slate-800 dark:text-slate-200 font-medium leading-relaxed mb-6">
                  {action.recommendation}
                </p>
                
                <div className="flex items-center gap-4">
                  <button 
                    onClick={handleFix}
                    disabled={isFixing || isFixed}
                    className={cn(
                      tokens.button.primary,
                      isFixed ? "bg-emerald-500 hover:bg-emerald-600 border-none" : "bg-indigo-600 hover:bg-indigo-700"
                    )}
                  >
                    {isFixed ? (
                      <>Resolved</>
                    ) : isFixing ? (
                      <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Applying Fix...</>
                    ) : (
                      <><PlayCircle className="w-4 h-4 mr-2" /> Fix Now</>
                    )}
                  </button>
                  {action.can_be_undone && (
                    <span className={tokens.typography.small}>This action can be undone later.</span>
                  )}
                </div>
              </div>
            )}

            {/* Technical Variant (Native embedding of raw evidence) */}
            {variant === 'technical' && (
              <div className="p-6 bg-slate-950 border-t border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2 text-slate-300">
                    <Server className="w-4 h-4" />
                    <span className="text-sm font-medium">Technical Evidence</span>
                  </div>
                  <span className="text-xs font-mono text-slate-500">Method: {action.verification_method}</span>
                </div>
                <div className="overflow-x-auto rounded-lg border border-slate-800 bg-black/50 p-4">
                  <pre className="text-emerald-400/90 text-xs font-mono whitespace-pre-wrap">
                    {action.evidence}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <AIDrawer 
        isOpen={aiDrawerOpen}
        onClose={() => setAiDrawerOpen(false)}
        title={action.title}
        explanation={{
          whatChanged: action.impact_narrative,
          howWeKnow: `Verified using ${action.verification_method}.`,
          confidence: action.confidence_pct,
          rawEvidencePreview: action.evidence.substring(0, 200) + '...'
        }}
        onViewFullEvidence={() => {
          setAiDrawerOpen(false);
          if (onViewEvidence) onViewEvidence(action.id);
        }}
      />
    </>
  );
}
