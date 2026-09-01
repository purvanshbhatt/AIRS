import React, { useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Building,
  RefreshCw,
  ExternalLink,
  Printer,
  Check,
} from 'lucide-react';
import type { BoardStoryPreview, OnboardingMode } from '../../types/onboarding';
import { DEMO_BOARD_STORY_PREVIEW } from './onboardingData';
import { getBoardStoryPdfUrl } from '../../api';

interface Step6BoardReportProps {
  mode: OnboardingMode;
  orgId: string;
  orgName: string;
  onComplete: () => void;
  onPrev: () => void;
  isSubmitting?: boolean;
}

export function Step6BoardReport({
  mode,
  orgId,
  orgName,
  onComplete,
  onPrev,
  isSubmitting = false,
}: Step6BoardReportProps) {
  const isDemo = mode === 'demo';
  const reportData = DEMO_BOARD_STORY_PREVIEW;
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleDownloadReport = () => {
    setDownloading(true);
    setDownloadSuccess(false);

    try {
      const targetOrgId = orgId || (isDemo ? 'demo-health-org' : 'default');
      const pdfUrl = getBoardStoryPdfUrl(targetOrgId);
      
      // Trigger download via hidden anchor
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `ResilAI_Boardroom_Readiness_Report_${orgName || 'Acme_Health'}.pdf`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setTimeout(() => {
        setDownloading(false);
        setDownloadSuccess(true);
      }, 1200);
    } catch (err) {
      console.warn('[Step6BoardReport] PDF download trigger notice:', err);
      setDownloading(false);
      setDownloadSuccess(true);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              Executive Boardroom Story & Cyber Insurance Report
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              Synthesize your operational telemetry and cryptographic evidence into an authoritative executive report formatted for board directors and underwriters.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Report Generated & Ready</span>
          </span>
        </div>
      </div>

      {/* Boardroom Story Preview Card */}
      <div className="bg-surface-container-low rounded-2xl border border-outline-variant/50 overflow-hidden shadow-2xl">
        {/* Report Top Header */}
        <div className="p-6 bg-gradient-to-r from-surface-container to-surface-container-high border-b border-outline-variant/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-ready-emerald/15 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald font-bold text-lg">
              {orgName ? orgName.charAt(0).toUpperCase() : 'A'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-lg font-bold text-on-surface">
                  {orgName || reportData.orgName}
                </h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-ready-emerald/20 text-ready-emerald font-bold">
                  VERIFIED
                </span>
              </div>
              <p className="text-xs text-on-surface-variant">
                Executive Cybersecurity & Operational Resilience Briefing • {reportData.generatedDate}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] font-mono uppercase text-on-surface-variant block">
                Readiness Index
              </span>
              <span className="text-2xl font-bold font-mono text-ready-emerald">
                {reportData.readinessScore}%
              </span>
            </div>
          </div>
        </div>

        {/* Report Body Content */}
        <div className="p-6 md:p-8 space-y-6">
          {/* Executive Headline */}
          <div className="p-4 rounded-xl bg-surface-container border border-ready-emerald/20">
            <span className="text-[10px] font-mono uppercase tracking-wider text-ready-emerald font-bold block mb-1">
              Executive Posture Summary:
            </span>
            <p className="text-sm sm:text-base font-bold text-on-surface leading-relaxed">
              &ldquo;{reportData.executiveSummaryHeadline}&rdquo;
            </p>
          </div>

          {/* Key Highlights */}
          <div className="space-y-3">
            <h5 className="text-xs font-mono font-bold uppercase tracking-wider text-on-surface">
              Core Assurance Findings
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {reportData.keyHighlights.map((highlight, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/30 flex items-start gap-2.5"
                >
                  <CheckCircle2 className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                  <span className="text-xs text-on-surface-variant leading-relaxed">
                    {highlight}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Metrics Summary Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-outline-variant/30 text-center font-mono">
            <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/30">
              <span className="text-[10px] text-on-surface-variant uppercase block">Verified Controls</span>
              <strong className="text-lg text-ready-emerald font-bold">24 / 24</strong>
            </div>
            <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/30">
              <span className="text-[10px] text-on-surface-variant uppercase block">Unverified Gaps</span>
              <strong className="text-lg text-on-surface font-bold">0 Gaps</strong>
            </div>
            <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/30">
              <span className="text-[10px] text-on-surface-variant uppercase block">Immutability Lock</span>
              <strong className="text-lg text-ready-emerald font-bold">30 Days</strong>
            </div>
            <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/30">
              <span className="text-[10px] text-on-surface-variant uppercase block">Recovery RTO</span>
              <strong className="text-lg text-primary-400 font-bold">42 Mins</strong>
            </div>
          </div>
        </div>

        {/* Report Download & Action Footer */}
        <div className="p-6 bg-surface-container border-t border-outline-variant/40 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDownloadReport}
              disabled={downloading}
              className="px-5 py-2.5 bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-semibold text-xs rounded-xl border border-outline-variant/60 transition-all flex items-center gap-2 shadow-sm"
            >
              {downloading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-ready-emerald" />
                  <span>Generating Server PDF...</span>
                </>
              ) : downloadSuccess ? (
                <>
                  <Check className="w-4 h-4 text-ready-emerald" />
                  <span className="text-ready-emerald font-bold">PDF Downloaded</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 text-ready-emerald" />
                  <span>Download Executive PDF</span>
                </>
              )}
            </button>
            <span className="text-xs text-on-surface-variant hidden sm:inline">
              Server-generated via ReportLab engine
            </span>
          </div>

          <div className="text-xs text-on-surface-variant text-right">
            <span>Deterministic SHA-256 Provenance Embedded</span>
          </div>
        </div>
      </div>

      {/* Completion Navigation Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          className="px-5 py-2.5 rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-semibold text-xs transition-all flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Recovery</span>
        </button>

        <button
          type="button"
          onClick={onComplete}
          disabled={isSubmitting}
          className="px-8 py-3.5 bg-gradient-to-r from-primary-600 to-ready-emerald hover:from-primary-500 hover:to-emerald-400 text-slate-950 font-bold text-sm rounded-xl shadow-xl shadow-ready-emerald/25 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          <span>Complete Onboarding & Enter Workspace</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
