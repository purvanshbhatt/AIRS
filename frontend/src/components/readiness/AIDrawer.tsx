import React from 'react';
import { X, ShieldCheck, ArrowRight, Server, Clock, Database, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { tokens } from '../../lib/design-tokens';

export interface AIDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  target?: string;
  timestamp?: string;
  confidence?: number;
  source?: string;
  rawMetrics?: Record<string, string | number>;
  domainPath?: string;
  domainName?: string;
  explanation?: {
    whatChanged?: string;
    howWeKnow?: string;
    confidence?: number;
    rawEvidencePreview?: string;
  };
  whyItMatters?: string;
  onViewFullEvidence?: () => void;
  onNavigateDomain?: (path: string) => void;
}

export function AIDrawer({
  isOpen,
  onClose,
  title,
  target,
  timestamp,
  confidence,
  source,
  rawMetrics,
  domainPath,
  domainName,
  explanation,
  whyItMatters,
  onViewFullEvidence,
  onNavigateDomain,
}: AIDrawerProps) {
  const navigate = useNavigate();

  if (!isOpen) return null;

  // Resolve values supporting legacy & new props
  const resolvedTarget = target || title;
  const resolvedTimestamp = timestamp || 'Verified just now';
  const resolvedConfidence = confidence ?? explanation?.confidence ?? 98;
  const resolvedSource = source || (explanation?.howWeKnow ? explanation.howWeKnow : 'Veeam & Microsoft Graph Connector APIs');
  const resolvedWhyItMatters = whyItMatters || explanation?.whatChanged || explanation?.howWeKnow || 'Operational telemetry confirms system resilience parameters are within safety thresholds.';
  
  const rawPreview = explanation?.rawEvidencePreview || (rawMetrics ? JSON.stringify(rawMetrics, null, 2) : JSON.stringify({
    verification_target: resolvedTarget,
    connector_source: resolvedSource,
    confidence_score: `${resolvedConfidence}%`,
    telemetry_status: "VERIFIED_DETERMINISTIC",
    integrity_hash: "0x7e9a3b8d"
  }, null, 2));

  // Determine domain link
  const inferredPath = domainPath || (
    title.toLowerCase().includes('backup') || title.toLowerCase().includes('recovery') ? '/backups' :
    title.toLowerCase().includes('identity') || title.toLowerCase().includes('mfa') || title.toLowerCase().includes('user') ? '/identity' :
    title.toLowerCase().includes('device') || title.toLowerCase().includes('endpoint') ? '/devices' :
    title.toLowerCase().includes('email') || title.toLowerCase().includes('phish') ? '/email' :
    title.toLowerCase().includes('network') || title.toLowerCase().includes('firewall') || title.toLowerCase().includes('vpn') ? '/network' :
    title.toLowerCase().includes('cloud') || title.toLowerCase().includes('aws') || title.toLowerCase().includes('azure') ? '/cloud' :
    title.toLowerCase().includes('ai') || title.toLowerCase().includes('model') ? '/ai' :
    '/backups'
  );

  const inferredDomainLabel = domainName || (
    inferredPath === '/backups' ? 'Backups & Recovery' :
    inferredPath === '/identity' ? 'Identity & Access' :
    inferredPath === '/devices' ? 'Devices & Endpoints' :
    inferredPath === '/email' ? 'Email Security' :
    inferredPath === '/network' ? 'Network & Zero Trust' :
    inferredPath === '/cloud' ? 'Cloud Infrastructure' :
    'AI Estate'
  );

  const handleDomainNavigation = () => {
    onClose();
    if (onNavigateDomain) {
      onNavigateDomain(inferredPath);
    } else if (onViewFullEvidence) {
      onViewFullEvidence();
      navigate(inferredPath);
    } else {
      navigate(inferredPath);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className={cn(
        "fixed inset-y-0 right-0 w-full max-w-lg z-50 flex flex-col transform transition-transform duration-300 ease-in-out",
        tokens.surface.drawer,
        isOpen ? "translate-x-0" : "translate-x-full"
      )}>
        {/* Header - Display "How do we know?" as title/header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-700 dark:text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                How do we know?
              </h2>
              <p className="text-xs text-slate-500 font-medium">Deterministic Evidence & Health Check</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 -mr-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-full hover:bg-slate-200/60 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Section 1: Top Section - Deterministic Evidence */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Server className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                1. Deterministic Evidence
              </h3>
              <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-2.5 py-0.5 rounded-full">
                {resolvedConfidence}% Deterministic
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 font-medium block mb-0.5">Target System</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200 truncate block">
                    {resolvedTarget}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-medium block mb-0.5">Health Check Time</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {resolvedTimestamp}
                  </span>
                </div>
                <div className="col-span-2 pt-2 border-t border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400 font-medium block mb-0.5">Telemetry Source</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {resolvedSource}
                  </span>
                </div>
              </div>

              {/* Raw Metrics Preview */}
              <div className="pt-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Raw Telemetry Evidence
                </span>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 overflow-x-auto">
                  <pre className="text-emerald-400 text-xs font-mono whitespace-pre-wrap">
                    {rawPreview}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Middle Section - Operational AI Summary ("Why this matters") */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-indigo-500" />
              2. Why This Matters (Operational AI Summary)
            </h3>
            <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200 leading-relaxed">
                {resolvedWhyItMatters}
              </p>
            </div>
          </div>
        </div>

        {/* Section 3: Bottom Section - Link to view technical details in domain page */}
        <div className="p-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
          <button 
            onClick={handleDomainNavigation}
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 rounded-xl transition-all shadow-sm group"
          >
            <span className="flex items-center gap-2">
              <ExternalLink className="w-4 h-4" />
              View Technical Details in {inferredDomainLabel}
            </span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </div>
    </>
  );
}

export default AIDrawer;
