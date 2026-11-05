import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Sparkles, Shield, RotateCcw } from 'lucide-react';
import type {
  OnboardingStepNumber,
  OnboardingMode,
  OnboardingOrgProfile,
  SecurityConnectorState,
} from '../../types/onboarding';
import {
  INITIAL_DEMO_PROFILE,
  INITIAL_REAL_PROFILE,
  DEFAULT_CONNECTORS,
  getOnboardingStep,
  setOnboardingStep,
  setOnboardingCompleted,
} from './onboardingData';
import { GettingStartedStepper } from './GettingStartedStepper';
import { Step1OrgProfile } from './Step1OrgProfile';
import { Step2Connectors } from './Step2Connectors';
import { Step3EvidenceLedger } from './Step3EvidenceLedger';
import { Step4NeedsAttention } from './Step4NeedsAttention';
import { Step5RecoveryReadiness } from './Step5RecoveryReadiness';
import { Step6BoardReport } from './Step6BoardReport';

interface GettingStartedModalProps {
  isOpen: boolean;
  onClose: () => void;
  orgId?: string;
  orgName?: string;
  initialMode?: OnboardingMode;
  onCompleted?: () => void;
}

export function GettingStartedModal({
  isOpen,
  onClose,
  orgId,
  orgName,
  initialMode,
  onCompleted,
}: GettingStartedModalProps) {
  const effectiveOrgId = orgId || 'demo-health-org';
  const [mode, setMode] = useState<OnboardingMode>(
    initialMode || (effectiveOrgId === 'demo-health-org' ? 'demo' : 'real')
  );

  const [currentStep, setCurrentStep] = useState<OnboardingStepNumber>(1);
  const [completedSteps, setCompletedSteps] = useState<OnboardingStepNumber[]>([]);
  const [profile, setProfile] = useState<OnboardingOrgProfile>(
    mode === 'demo' ? INITIAL_DEMO_PROFILE : { ...INITIAL_REAL_PROFILE, name: orgName || '' }
  );
  const [connectors, setConnectors] = useState<SecurityConnectorState[]>(DEFAULT_CONNECTORS);

  // Synchronize initial step and mode when opened
  useEffect(() => {
    if (!isOpen) return;

    const savedStep = getOnboardingStep(effectiveOrgId);
    const validStep = (savedStep >= 1 && savedStep <= 6 ? savedStep : 1) as OnboardingStepNumber;
    setCurrentStep(validStep);

    // Populate completed steps up to saved step
    const completedArr: OnboardingStepNumber[] = [];
    for (let i = 1; i < validStep; i++) {
      completedArr.push(i as OnboardingStepNumber);
    }
    setCompletedSteps(completedArr);

    if (mode === 'demo') {
      setProfile(INITIAL_DEMO_PROFILE);
    } else {
      setProfile((prev) => ({ ...prev, name: orgName || prev.name }));
    }
  }, [isOpen, effectiveOrgId, mode, orgName]);

  // Handle escape key and scroll lock
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === 'undefined') return null;

  const handleSelectStep = (step: OnboardingStepNumber) => {
    setCurrentStep(step);
    setOnboardingStep(effectiveOrgId, step);
  };

  const handleNextStep = () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps((prev) => [...prev, currentStep]);
    }
    if (currentStep < 6) {
      const next = (currentStep + 1) as OnboardingStepNumber;
      setCurrentStep(next);
      setOnboardingStep(effectiveOrgId, next);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      const prev = (currentStep - 1) as OnboardingStepNumber;
      setCurrentStep(prev);
      setOnboardingStep(effectiveOrgId, prev);
    }
  };

  const handleUpdateProfile = (updated: Partial<OnboardingOrgProfile>) => {
    setProfile((prev) => ({ ...prev, ...updated }));
  };

  const handleUpdateConnector = (
    connectorId: string,
    updated: Partial<SecurityConnectorState>
  ) => {
    setConnectors((prev) =>
      prev.map((c) => (c.id === connectorId ? { ...c, ...updated } : c))
    );
  };

  const handleToggleMode = () => {
    const nextMode = mode === 'demo' ? 'real' : 'demo';
    setMode(nextMode);
    if (nextMode === 'demo') {
      setProfile(INITIAL_DEMO_PROFILE);
    } else {
      setProfile({ ...INITIAL_REAL_PROFILE, name: orgName || '' });
    }
  };

  const handleFinishOnboarding = () => {
    setOnboardingCompleted(effectiveOrgId, true);
    setOnboardingStep(effectiveOrgId, 6);
    if (onCompleted) {
      onCompleted();
    }
    onClose();
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4 md:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      aria-modal="true"
      role="dialog"
      aria-label="Getting Started with ResilAI 6-Step Guide"
    >
      <div
        className="bg-surface-container-lowest text-on-surface rounded-3xl max-w-5xl w-full max-h-[92vh] flex flex-col border border-outline-variant/50 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Floating App Bar inside Modal */}
        <div className="px-6 py-3.5 border-b border-outline-variant/30 flex items-center justify-between bg-surface-container-low shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-ready-emerald/15 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald font-bold text-xs">
              6
            </div>
            <div>
              <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
                <span>Getting Started with ResilAI</span>
                <span className="text-[10px] font-mono text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/30 px-2 py-0.2 rounded">
                  Interactive Guide
                </span>
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
              title="Close guide (progress is automatically saved)"
            >
              Resume Later
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 hover:bg-surface-container-highest rounded-full text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 6-Step Horizontal Progress Stepper */}
        <GettingStartedStepper
          currentStep={currentStep}
          completedSteps={completedSteps}
          onSelectStep={handleSelectStep}
          mode={mode}
          onToggleMode={handleToggleMode}
          allowModeSwitch={true}
        />

        {/* Step Body Content Scroll Area */}
        <div className="p-4 sm:p-6 md:p-8 overflow-y-auto flex-1 bg-surface-container-lowest">
          {currentStep === 1 && (
            <Step1OrgProfile
              profile={profile}
              onChangeProfile={handleUpdateProfile}
              mode={mode}
              onNext={handleNextStep}
            />
          )}

          {currentStep === 2 && (
            <Step2Connectors
              connectors={connectors}
              onUpdateConnector={handleUpdateConnector}
              mode={mode}
              onNext={handleNextStep}
              onPrev={handlePrevStep}
            />
          )}

          {currentStep === 3 && (
            <Step3EvidenceLedger
              mode={mode}
              onNext={handleNextStep}
              onPrev={handlePrevStep}
            />
          )}

          {currentStep === 4 && (
            <Step4NeedsAttention
              mode={mode}
              onNext={handleNextStep}
              onPrev={handlePrevStep}
            />
          )}

          {currentStep === 5 && (
            <Step5RecoveryReadiness
              mode={mode}
              onNext={handleNextStep}
              onPrev={handlePrevStep}
            />
          )}

          {currentStep === 6 && (
            <Step6BoardReport
              mode={mode}
              orgId={effectiveOrgId}
              orgName={profile.name || orgName || 'Acme Health Systems'}
              onComplete={handleFinishOnboarding}
              onPrev={handlePrevStep}
            />
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
