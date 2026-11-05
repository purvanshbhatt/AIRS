import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  FileCode,
  KeyRound,
  HardDrive,
  Copy,
  Check,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  ExternalLink,
  HelpCircle,
  Database,
  Layers,
} from 'lucide-react';
import type { EvidenceLedgerItem, OnboardingMode } from '../../types/onboarding';
import { DEMO_EVIDENCE_ITEMS } from './onboardingData';

interface Step3EvidenceLedgerProps {
  mode: OnboardingMode;
  onNext: () => void;
  onPrev: () => void;
}

export function Step3EvidenceLedger({
  mode,
  onNext,
  onPrev,
}: Step3EvidenceLedgerProps) {
  const isDemo = mode === 'demo';
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<EvidenceLedgerItem>(DEMO_EVIDENCE_ITEMS[0]);

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              Deterministic Health Checks & Cryptographic Evidence Ledger
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              Every readiness score is backed by cryptographic evidence harvested from connected security platforms. If evidence is missing, confidence is 0%—never guessed.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30">
            100% Cryptographically Verified
          </span>
        </div>
      </div>

      {/* Main Evidence Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: List of Verified Controls in Evidence Ledger */}
        <div className="lg:col-span-7 space-y-3">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-ready-emerald mb-2">
            Active Verified Controls in Ledger ({DEMO_EVIDENCE_ITEMS.length})
          </h4>

          {DEMO_EVIDENCE_ITEMS.map((item) => {
            const isSelected = selectedItem.id === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-ready-emerald/10 border-ready-emerald ring-1 ring-ready-emerald/40 shadow-sm'
                    : 'bg-surface-container-low border-outline-variant/40 hover:border-outline-variant hover:bg-surface-container'
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-surface-container-high text-on-surface border border-outline-variant/40">
                      {item.controlCode}
                    </span>
                    <span className="text-xs font-bold text-on-surface truncate max-w-[280px]">
                      {item.title}
                    </span>
                  </div>

                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30 font-bold shrink-0 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Verified
                  </span>
                </div>

                <p className="text-xs text-on-surface-variant line-clamp-2 leading-relaxed mb-3">
                  {item.plainEnglishExplanation}
                </p>

                <div className="flex items-center justify-between text-[11px] font-mono text-on-surface-variant/80 pt-2 border-t border-outline-variant/30">
                  <span className="text-ready-emerald font-semibold">{item.sourceConnector}</span>
                  <span>Verified {item.lastVerifiedAt}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Cryptographic Inspection Panel */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-surface-container p-6 rounded-2xl border border-outline-variant/50 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-ready-emerald uppercase">
                <FileCode className="w-4 h-4" />
                <span>Evidence Provenance</span>
              </div>
              <span className="text-[10px] font-mono bg-ready-emerald/15 text-ready-emerald px-2 py-0.5 rounded-full font-bold">
                SHA-256 Verified
              </span>
            </div>

            <div>
              <h5 className="text-sm font-bold text-on-surface mb-1">
                {selectedItem.title}
              </h5>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                {selectedItem.plainEnglishExplanation}
              </p>
            </div>

            {/* Cryptographic Hash Inspector */}
            <div className="p-3.5 bg-surface-container-lowest rounded-xl border border-outline-variant/50 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-on-surface-variant">
                <span className="font-mono font-bold text-ready-emerald uppercase">SHA-256 Fingerprint:</span>
                <button
                  type="button"
                  onClick={() => handleCopyHash(selectedItem.evidenceHash)}
                  className="hover:text-ready-emerald flex items-center gap-1 transition-colors"
                  title="Copy full cryptographic hash"
                >
                  {copiedHash === selectedItem.evidenceHash ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-ready-emerald" />
                      <span className="text-ready-emerald font-semibold">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-[11px] font-mono text-ready-emerald break-all bg-surface-container p-2 rounded-lg border border-ready-emerald/20 select-all">
                {selectedItem.evidenceHash}
              </p>
            </div>

            {/* Raw Telemetry Payload */}
            <div className="p-3.5 bg-surface-container-lowest rounded-xl border border-outline-variant/50 space-y-1.5">
              <span className="text-[10px] font-mono uppercase text-on-surface-variant font-bold block">
                Telemetry Signature & Source:
              </span>
              <p className="text-[11px] font-mono text-on-surface bg-surface-container p-2 rounded-lg border border-outline-variant/40 break-words leading-relaxed">
                {selectedItem.technicalTelemetry}
              </p>
            </div>

            <div className="p-3 bg-ready-emerald/10 border border-ready-emerald/30 rounded-xl text-xs text-on-surface flex items-start gap-2.5">
              <HelpCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
              <p className="text-[11px] text-on-surface-variant leading-relaxed">
                <strong className="text-on-surface">Auditor-Ready Guarantee:</strong> This SHA-256 fingerprint can be independently audited by cyber insurance underwriters or HIPAA compliance officers to prove control execution.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          className="px-5 py-2.5 rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-semibold text-xs transition-all flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Connectors</span>
        </button>

        <button
          type="button"
          onClick={onNext}
          className="px-6 py-3 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          <span>Continue to Step 4: Understand What Matters</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
