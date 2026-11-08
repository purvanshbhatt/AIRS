import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { ArrowRight, X } from 'lucide-react';
import type { OnboardingMode } from '../../types/onboarding';
import { FIRST_RUN_COPY } from './onboardingData';

interface GettingStartedModalProps {
  isOpen: boolean;
  onClose: () => void;
  orgId?: string;
  orgName?: string;
  initialMode?: OnboardingMode;
  onCompleted?: () => void;
}

const ITEMS = [FIRST_RUN_COPY.connect, FIRST_RUN_COPY.verdict, FIRST_RUN_COPY.report];

/**
 * Small "first steps" reminder opened from the readiness header. Same three
 * items as the FirstRunChecklist on the morning brief, without live state.
 */
export function GettingStartedModal({ isOpen, onClose, orgName }: GettingStartedModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === 'undefined') return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Getting started with ResilAI"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg bg-surface-container-low rounded-3xl border border-outline-variant/40 shadow-2xl p-6 sm:p-8 space-y-5"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-on-surface">Getting started with ResilAI</h2>
            <p className="text-xs text-on-surface-variant mt-1">
              Three steps{orgName ? ` for ${orgName}` : ''}. Most practices finish in a week.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <ol className="space-y-3">
          {ITEMS.map((item, index) => (
            <li key={item.href} className="p-4 rounded-2xl bg-surface-container border border-outline-variant/40 flex items-start gap-3">
              <span className="w-6 h-6 rounded-full bg-ready-emerald/15 text-ready-emerald text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {index + 1}
              </span>
              <div className="min-w-0">
                <Link to={item.href} onClick={onClose} className="text-sm font-bold text-on-surface hover:text-ready-emerald inline-flex items-center gap-1.5">
                  {item.title}
                  <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                </Link>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">{item.caption}</p>
              </div>
            </li>
          ))}
        </ol>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
