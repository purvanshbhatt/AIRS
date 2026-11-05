import React, { useState } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Activity,
  CheckCircle2,
  Wrench,
  Clock,
  Eye,
  Info,
} from 'lucide-react';
import type { NeedsAttentionPreviewItem, OnboardingMode } from '../../types/onboarding';
import { DEMO_NEEDS_ATTENTION_ITEMS } from './onboardingData';

interface Step4NeedsAttentionProps {
  mode: OnboardingMode;
  onNext: () => void;
  onPrev: () => void;
}

export function Step4NeedsAttention({
  mode,
  onNext,
  onPrev,
}: Step4NeedsAttentionProps) {
  const isDemo = mode === 'demo';
  const [activeItem, setActiveItem] = useState<string>(DEMO_NEEDS_ATTENTION_ITEMS[0].id);
  const [viewMode, setViewMode] = useState<'executive' | 'technical'>('executive');
  const [fixedItems, setFixedItems] = useState<string[]>([]);

  const handleTriggerRemediation = (id: string) => {
    setFixedItems((prev) => [...prev, id]);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              Needs Attention Triage & Clinical Risk Ranking
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              ResilAI cuts through alarm fatigue by ranking incidents based on patient care disruption and clinical risk, translated into plain English for healthcare leadership.
            </p>
          </div>
        </div>

        {/* Dual Mode Switcher: Executive View vs Technical View */}
        <div className="flex items-center gap-1.5 p-1 bg-surface-container-high rounded-xl border border-outline-variant/50 shrink-0">
          <button
            type="button"
            onClick={() => setViewMode('executive')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'executive'
                ? 'bg-ready-emerald text-slate-950 shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Executive Translation
          </button>
          <button
            type="button"
            onClick={() => setViewMode('technical')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'technical'
                ? 'bg-ready-emerald text-slate-950 shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Technical Telemetry
          </button>
        </div>
      </div>

      {/* Main Triage Items List */}
      <div className="space-y-4">
        {DEMO_NEEDS_ATTENTION_ITEMS.map((item) => {
          const isFixed = fixedItems.includes(item.id);
          const isExpanded = activeItem === item.id;

          return (
            <div
              key={item.id}
              className={`p-6 rounded-2xl border transition-all ${
                isFixed
                  ? 'bg-surface-container/50 border-ready-emerald/30 opacity-75'
                  : item.severity === 'critical'
                  ? 'bg-surface-container-low border-critical-red/30 shadow-md shadow-critical-red/5'
                  : 'bg-surface-container-low border-drift-amber/30'
              }`}
            >
              {/* Header Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider ${
                      item.severity === 'critical'
                        ? 'bg-critical-red/15 text-critical-red border border-critical-red/30'
                        : 'bg-drift-amber/15 text-drift-amber border border-drift-amber/30'
                    }`}
                  >
                    {item.severity} Risk
                  </span>
                  <h4 className="text-base font-bold text-on-surface">
                    {item.title}
                  </h4>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] font-mono uppercase text-on-surface-variant block">
                      Clinical Risk Rating
                    </span>
                    <span className="text-sm font-mono font-bold text-critical-red">
                      {item.clinicalRiskScore} / 100
                    </span>
                  </div>

                  <span className="text-xs font-mono px-2.5 py-1 bg-surface-container-high rounded-lg text-on-surface-variant border border-outline-variant/40">
                    {item.system}
                  </span>
                </div>
              </div>

              {/* Dynamic Presentation Mode */}
              {viewMode === 'executive' ? (
                /* Executive Plain English View */
                <div className="space-y-3 bg-surface-container p-4 rounded-xl border border-outline-variant/40">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-ready-emerald font-bold block mb-1">
                      Plain English Executive Summary:
                    </span>
                    <p className="text-sm text-on-surface font-medium leading-relaxed">
                      {item.executiveSummary}
                    </p>
                  </div>

                  <div className="p-3 bg-surface-container-lowest rounded-lg border border-drift-amber/20 flex items-start gap-2.5">
                    <Activity className="w-4 h-4 text-drift-amber shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-xs text-on-surface block mb-0.5">Clinical Operations Impact:</strong>
                      <p className="text-xs text-on-surface-variant leading-relaxed">
                        {item.clinicalImpactSummary}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                /* Technical Deep Dive View */
                <div className="space-y-3 bg-surface-container-lowest p-4 rounded-xl border border-outline-variant/40 font-mono text-xs">
                  <div>
                    <span className="text-[10px] uppercase text-on-surface-variant font-bold block mb-1">
                      Technical Control Finding:
                    </span>
                    <p className="text-on-surface bg-surface-container p-2.5 rounded border border-outline-variant/40 break-words">
                      {item.technicalFinding}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-on-surface-variant">
                    <span>Evidence Fingerprint:</span>
                    <span className="text-ready-emerald truncate max-w-[280px]">
                      {item.evidenceHash}
                    </span>
                  </div>
                </div>
              )}

              {/* Recommended Action & 1-Click Remediation */}
              <div className="mt-4 pt-4 border-t border-outline-variant/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs text-on-surface">
                  <Wrench className="w-4 h-4 text-ready-emerald shrink-0" />
                  <span>
                    <strong className="font-semibold">Recommended Fix:</strong> {item.recommendedAction}
                  </span>
                </div>

                {isFixed ? (
                  <span className="px-4 py-2 rounded-xl bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30 font-bold text-xs flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Remediation Triggered
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleTriggerRemediation(item.id)}
                    className="px-4 py-2 bg-ready-emerald/15 hover:bg-ready-emerald text-ready-emerald hover:text-slate-950 font-bold text-xs rounded-xl border border-ready-emerald/30 transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <span>1-Click Trigger Fix</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          className="px-5 py-2.5 rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-semibold text-xs transition-all flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Evidence Ledger</span>
        </button>

        <button
          type="button"
          onClick={onNext}
          className="px-6 py-3 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          <span>Continue to Step 5: Incident Recovery Readiness</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
