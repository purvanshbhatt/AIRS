import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  ArrowRight,
  ArrowLeft,
  X,
  Sparkles,
  Calendar,
  AlertTriangle,
  RotateCcw,
  FileText,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export interface TourStop {
  id: string;
  route: string;
  title: string;
  subtitle: string;
  description: string;
  highlightAction: string;
  badge: string;
}

export const TOUR_STOPS: TourStop[] = [
  {
    id: 'tour-today',
    route: '/morning-brief',
    title: '1. Morning Brief & Readiness Score',
    subtitle: 'Answers "Are we ready for today?" in 5 seconds',
    description: 'The executive briefing answers whether critical systems are safe to operate today. Built on 100% deterministic control evidence—no hallucinated scores.',
    highlightAction: 'View Macro Readiness Score & Overnight Verification Delta',
    badge: 'Today Briefing',
  },
  {
    id: 'tour-triage',
    route: '/needs-attention',
    title: '2. Needs Attention & Incident Triage',
    subtitle: 'Plain-English clinical risk ranking',
    description: 'Prioritizes active technical gaps by patient care disruption risk and provides 1-click remediation actions for IT operators.',
    highlightAction: 'Triage Gaps by Clinical Severity & Disruption Risk',
    badge: 'Needs Attention',
  },
  {
    id: 'tour-recovery',
    route: '/recovery',
    title: '3. Incident Recovery & Immutability',
    subtitle: 'Ransomware safety net & RTO assurance',
    description: 'Verifies 30-day immutable backup locks and calculates realistic Recovery Time Objectives before an incident occurs.',
    highlightAction: 'Check Immutable Lock Status & 42-Min EHR Recovery RTO',
    badge: 'Recovery Posture',
  },
  {
    id: 'tour-documents',
    route: '/documents',
    title: '4. Evidence Vault & Board Reports',
    subtitle: 'Audit-ready folders & executive stories',
    description: 'Download the authoritative Boardroom Security Posture Story PDF or export cryptographic proof packages for HIPAA audits and insurance underwriting.',
    highlightAction: 'Download Executive Boardroom PDF & Audit Packages',
    badge: 'Evidence Vault',
  },
  {
    id: 'tour-governance',
    route: '/governance',
    title: '5. Framework Alignment',
    subtitle: 'Readiness evidence aligned to NIST, CIS, HIPAA',
    description: 'Continuously maps operational evidence to NIST CSF 2.0, NIST AI RMF, CIS Controls, SOC 2, ISO 27001, and HIPAA without claiming unverified certification.',
    highlightAction: 'Inspect Framework Alignment & Telemetry Coverage',
    badge: 'Frameworks',
  },
  {
    id: 'tour-connectors',
    route: '/connectors',
    title: '6. Telemetry Connectors',
    subtitle: 'Microsoft 365, Veeam, CrowdStrike, SentinelOne',
    description: 'Manage read-only API connectors and MCP telemetry forwarders that harvest cryptographic proof around the clock.',
    highlightAction: 'Manage Live Connectors & Sync Status',
    badge: 'Connectors',
  },
];

interface GettingStartedTourProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GettingStartedTour({ isOpen, onClose }: GettingStartedTourProps) {
  const navigate = useNavigate();
  const [currentStopIndex, setCurrentStopIndex] = useState(0);

  if (!isOpen) return null;

  const currentStop = TOUR_STOPS[currentStopIndex];
  const isFirst = currentStopIndex === 0;
  const isLast = currentStopIndex === TOUR_STOPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      onClose();
    } else {
      const nextIndex = currentStopIndex + 1;
      setCurrentStopIndex(nextIndex);
      navigate(TOUR_STOPS[nextIndex].route);
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      const prevIndex = currentStopIndex - 1;
      setCurrentStopIndex(prevIndex);
      navigate(TOUR_STOPS[prevIndex].route);
    }
  };

  const handleNavigateDirect = (index: number) => {
    setCurrentStopIndex(index);
    navigate(TOUR_STOPS[index].route);
  };

  return (
    <div className="fixed bottom-20 right-6 md:bottom-8 md:right-8 z-50 max-w-md w-full animate-in slide-in-from-bottom-6 duration-300 pointer-events-auto">
      <div className="bg-surface-container-high/95 backdrop-blur-xl border border-ready-emerald/40 rounded-3xl p-5 shadow-2xl shadow-black/60 text-on-surface ring-1 ring-ready-emerald/20">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-ready-emerald/20 border border-ready-emerald/40 text-ready-emerald flex items-center justify-center text-xs font-mono font-bold">
              {currentStopIndex + 1}
            </span>
            <span className="text-xs font-mono font-bold text-ready-emerald uppercase tracking-wider">
              {currentStop.badge}
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1 text-on-surface-variant hover:text-on-surface rounded-full hover:bg-surface-container transition-colors"
            aria-label="Exit Guided Tour"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-2 mb-4">
          <h4 className="text-sm font-bold text-on-surface">
            {currentStop.title}
          </h4>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            {currentStop.description}
          </p>
          <div className="pt-2 text-[11px] font-mono text-ready-emerald">
            💡 {currentStop.highlightAction}
          </div>
        </div>

        {/* Stop indicators & Navigation actions */}
        <div className="flex items-center justify-between pt-3 border-t border-outline-variant/30">
          <div className="flex items-center gap-1.5">
            {TOUR_STOPS.map((stop, idx) => (
              <button
                key={stop.id}
                type="button"
                onClick={() => handleNavigateDirect(idx)}
                className={`w-2.5 h-2.5 rounded-full transition-all ${
                  idx === currentStopIndex
                    ? 'bg-ready-emerald w-5'
                    : 'bg-surface-container-highest hover:bg-on-surface-variant'
                }`}
                title={stop.title}
                aria-label={`Jump to ${stop.title}`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                type="button"
                onClick={handlePrev}
                className="px-3 py-1.5 rounded-xl border border-outline-variant/50 text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-all flex items-center gap-1"
              >
                <ArrowLeft className="w-3 h-3" />
                <span>Prev</span>
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              className="px-4 py-1.5 bg-ready-emerald text-slate-950 font-bold text-xs rounded-xl hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-1 shadow-md shadow-ready-emerald/20"
            >
              <span>{isLast ? 'Finish Tour' : 'Next Stop'}</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
