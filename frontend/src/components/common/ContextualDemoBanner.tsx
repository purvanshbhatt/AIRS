import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Shield,
  Info,
  ArrowRight,
  X,
  Compass,
  CheckCircle2,
  Lock,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { useActiveOrg } from '../../hooks/useActiveOrg';

export type DemoContextSection =
  | 'today'
  | 'needs-attention'
  | 'recovery'
  | 'documents'
  | 'governance'
  | 'connectors'
  | 'activity'
  | 'operations'
  | 'generic';

interface ContextualDemoBannerProps {
  section?: DemoContextSection;
  customHeadline?: string;
  customDescription?: string;
  onOpenGettingStarted?: () => void;
  dismissible?: boolean;
}

const SECTION_GUIDANCE: Record<
  DemoContextSection,
  {
    tag: string;
    headline: string;
    description: string;
    tip: string;
  }
> = {
  today: {
    tag: 'Simulated Morning Briefing',
    headline: 'Acme Health Systems — Illustrative Executive Briefing',
    description:
      'This dashboard renders synthetic security telemetry demonstrating how ResilAI answers "Are we ready for today?" in under 5 seconds using 100% deterministic verification.',
    tip: 'Notice: No LLM hallucinates scores. In production, scores are calculated purely from live connector evidence.',
  },
  'needs-attention': {
    tag: 'Simulated Clinical Triage',
    headline: 'Active Incident Gaps Ranked by Clinical Disruption Risk',
    description:
      'Instead of hundreds of raw IT alerts, ResilAI prioritizes issues based on clinical workflow and patient care impact with plain-English leadership summaries.',
    tip: 'Click "Explain for Leadership" on any card to see how technical findings are translated for executive decision-makers.',
  },
  recovery: {
    tag: 'Simulated Incident Recovery',
    headline: 'Continuous Backup Immutability & Disaster Recovery Posture',
    description:
      'Simulating verified 30-day write-once (WORM) storage locks and an automated 42-minute recovery SLA for Acme Health Systems EHR databases.',
    tip: 'Production mode queries Veeam Enterprise Manager and AWS S3 Object Lock directly to confirm air-gap guarantees.',
  },
  documents: {
    tag: 'Simulated Evidence Vault',
    headline: 'Evidence-Backed Readiness Vault & Executive Boardroom Story',
    description:
      'Download server-generated PDF Boardroom Stories and audit-ready evidence packages formatted for healthcare leadership and cyber underwriters.',
    tip: 'Click "Download Executive PDF" to preview the ReportLab server-rendered boardroom summary.',
  },
  governance: {
    tag: 'Simulated Framework Alignment',
    headline: 'Readiness Evidence Aligned to Major Security Frameworks',
    description:
      'Continuously maps operational evidence to NIST CSF 2.0, NIST AI RMF, CIS Controls, SOC 2, ISO 27001, and HIPAA without claiming unverified certification.',
    tip: 'Evidence is categorized as "Readiness evidence aligned to..." ensuring zero audit overclaims.',
  },
  connectors: {
    tag: 'Simulated Connector Fleet',
    headline: 'Pre-Integrated Telemetry Connectors Fleet',
    description:
      'Acme Health Systems uses simulated telemetry forwarders for Microsoft 365, Veeam, CrowdStrike, and SentinelOne.',
    tip: 'You can test connecting real credentials at any time in Live Workspace mode.',
  },
  activity: {
    tag: 'Simulated Audit Timeline',
    headline: 'Deterministic Evidence Log & Overnight Deltas',
    description:
      'Tracks SHA-256 cryptographic evidence hashes, connector sync heartbeats, and overnight configuration changes.',
    tip: 'Every entry includes an immutable SHA-256 hash verifying when and how evidence was harvested.',
  },
  operations: {
    tag: 'Simulated Technical Operations',
    headline: 'Deep Domain Mini-Products & Technical Telemetry',
    description:
      'Explore domain-level telemetry for Identity, Backups, Devices, Email, and Cloud Infrastructure.',
    tip: 'Technical metrics remain subordinate to operational context and plain-English answers.',
  },
  generic: {
    tag: 'Demo Sandbox Active',
    headline: 'Interactive Demonstration Environment',
    description:
      'You are exploring ResilAI with synthetic healthcare clinic telemetry (Acme Health Systems).',
    tip: 'All interactions are fully functional and safe to test.',
  },
};

export function ContextualDemoBanner({
  section = 'generic',
  customHeadline,
  customDescription,
  onOpenGettingStarted,
  dismissible = false,
}: ContextualDemoBannerProps) {
  const { isDemo } = useActiveOrg();
  const [dismissed, setDismissed] = useState(false);

  // Only display in Demo mode
  if (!isDemo || dismissed) return null;

  const guidance = SECTION_GUIDANCE[section] || SECTION_GUIDANCE.generic;
  const headline = customHeadline || guidance.headline;
  const description = customDescription || guidance.description;

  return (
    <aside
      aria-label="Demo environment simulation notice"
      className="mb-6 rounded-2xl bg-gradient-to-r from-amber-500/10 via-surface-container-high to-surface-container border border-amber-500/30 p-4 sm:p-5 shadow-lg shadow-black/20 animate-in fade-in duration-300"
    >
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        {/* Left Icon & Text */}
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-500 shrink-0 mt-0.5 shadow-sm">
            <Sparkles className="w-5 h-5" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1.5 shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                DEMO ENVIRONMENT (SIMULATED DATA)
              </span>
              <span className="text-[11px] font-mono text-on-surface-variant">
                • {guidance.tag}
              </span>
            </div>

            <h3 className="text-sm font-bold text-on-surface">
              {headline}
            </h3>

            <p className="text-xs text-on-surface-variant mt-0.5 leading-relaxed max-w-3xl">
              {description}
            </p>

            <div className="mt-2 text-[11px] font-mono text-amber-500/90 flex items-center gap-1">
              <span>💡</span>
              <span>{guidance.tip}</span>
            </div>
          </div>
        </div>

        {/* Right CTA Actions */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-end lg:self-center">
          {onOpenGettingStarted && (
            <button
              type="button"
              onClick={onOpenGettingStarted}
              className="px-3.5 py-1.5 bg-ready-emerald text-slate-950 font-bold text-xs rounded-xl shadow-md shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-1.5"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Launch 6-Step Guide</span>
            </button>
          )}

          <Link
            to="/login"
            className="px-3.5 py-1.5 bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-semibold text-xs rounded-xl border border-outline-variant/60 transition-all flex items-center gap-1.5"
          >
            <Shield className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Sign In to Live Org</span>
          </Link>

          {dismissible && (
            <button
              type="button"
              onClick={() => setDismissed(true)}
              className="p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
              aria-label="Dismiss banner for session"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
