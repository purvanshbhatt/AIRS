import React from 'react';
import { Check, Sparkles, Shield, ChevronRight } from 'lucide-react';
import type { OnboardingStepNumber, OnboardingMode } from '../../types/onboarding';
import { ONBOARDING_STEPS_METADATA } from './onboardingData';

interface GettingStartedStepperProps {
  currentStep: OnboardingStepNumber;
  completedSteps: OnboardingStepNumber[];
  onSelectStep: (step: OnboardingStepNumber) => void;
  mode: OnboardingMode;
  onToggleMode?: () => void;
  allowModeSwitch?: boolean;
}

export function GettingStartedStepper({
  currentStep,
  completedSteps,
  onSelectStep,
  mode,
  onToggleMode,
  allowModeSwitch = false,
}: GettingStartedStepperProps) {
  const currentStepMeta = ONBOARDING_STEPS_METADATA.find((s) => s.step === currentStep);
  const progressPct = Math.round(((completedSteps.length) / 6) * 100);

  return (
    <div className="w-full bg-surface-container-low/95 border-b border-outline-variant/40 p-4 md:px-8 shrink-0">
      {/* Top Header Bar inside Stepper */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/30 px-2.5 py-0.5 rounded-full">
              {currentStepMeta?.badge || `Step ${currentStep} of 6`}
            </span>
            {mode === 'demo' ? (
              <span className="text-[11px] font-mono font-bold uppercase tracking-wide text-amber-500 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-500" />
                Demo Telemetry
              </span>
            ) : (
              <span className="text-[11px] font-mono font-bold uppercase tracking-wide text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Shield className="w-3 h-3 text-emerald-400" />
                Live Setup Mode
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-on-surface mt-1">
            {currentStepMeta?.title}
          </h2>
          <p className="text-xs text-on-surface-variant line-clamp-1">
            {currentStepMeta?.subtitle}
          </p>
        </div>

        {/* Right side controls: Mode toggle & Progress */}
        <div className="flex items-center gap-4">
          {allowModeSwitch && onToggleMode && (
            <button
              type="button"
              onClick={onToggleMode}
              className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-outline-variant/60 hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all flex items-center gap-1.5"
            >
              {mode === 'demo' ? (
                <>
                  <Shield className="w-3.5 h-3.5 text-ready-emerald" />
                  <span>Switch to Real Org</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-drift-amber" />
                  <span>Switch to Acme Demo</span>
                </>
              )}
            </button>
          )}

          <div className="text-right">
            <div className="text-[11px] font-mono text-on-surface-variant">
              Progress: <strong className="text-on-surface">{progressPct}%</strong>
            </div>
            <div className="w-28 sm:w-36 h-2 bg-surface-container-highest rounded-full overflow-hidden mt-1 border border-outline-variant/30">
              <div
                className="h-full bg-gradient-to-r from-primary-600 to-ready-emerald transition-all duration-500 rounded-full"
                style={{ width: `${Math.max(8, progressPct)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 6-Step Horizontal Navigator */}
      <div className="grid grid-cols-6 gap-2 sm:gap-3">
        {ONBOARDING_STEPS_METADATA.map((meta) => {
          const isCurrent = meta.step === currentStep;
          const isCompleted = completedSteps.includes(meta.step);
          const isAccessible = isCompleted || meta.step === currentStep || meta.step <= Math.max(1, ...completedSteps, currentStep);

          return (
            <button
              key={meta.step}
              type="button"
              onClick={() => onSelectStep(meta.step)}
              disabled={!isAccessible}
              className={`group flex flex-col items-center sm:items-start p-2 sm:p-2.5 rounded-xl border text-left transition-all relative overflow-hidden ${
                isCurrent
                  ? 'bg-ready-emerald/10 border-ready-emerald text-on-surface shadow-md shadow-ready-emerald/5 ring-1 ring-ready-emerald/40'
                  : isCompleted
                  ? 'bg-surface-container border-outline-variant/50 text-on-surface hover:border-ready-emerald/40'
                  : 'bg-surface-container-low border-outline-variant/30 text-on-surface-variant/60 opacity-60 cursor-not-allowed'
              }`}
              title={meta.title}
              aria-current={isCurrent ? 'step' : undefined}
            >
              <div className="flex items-center gap-2 w-full">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0 transition-colors ${
                    isCurrent
                      ? 'bg-ready-emerald text-slate-950 shadow-sm'
                      : isCompleted
                      ? 'bg-ready-emerald/20 text-ready-emerald border border-ready-emerald/40'
                      : 'bg-surface-container-highest text-on-surface-variant'
                  }`}
                >
                  {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : meta.step}
                </div>
                <span className="hidden lg:inline text-xs font-bold truncate">
                  {meta.shortTitle}
                </span>
              </div>
              <span className="hidden sm:block lg:hidden text-[10px] font-semibold mt-1 truncate w-full text-center sm:text-left">
                {meta.shortTitle}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
