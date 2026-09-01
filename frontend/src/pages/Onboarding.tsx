import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { createOrganization, getOrganizations } from '../api';
import {
  Building2,
  Users,
  AlertCircle,
  LogOut,
  Sparkles,
  Shield,
  ArrowRight,
} from 'lucide-react';
import type {
  OnboardingStepNumber,
  OnboardingMode,
  OnboardingOrgProfile,
  SecurityConnectorState,
} from '../types/onboarding';
import {
  INITIAL_DEMO_PROFILE,
  INITIAL_REAL_PROFILE,
  DEFAULT_CONNECTORS,
  setOnboardingCompleted,
  setOnboardingStep,
  getOnboardingStep,
} from '../components/onboarding/onboardingData';
import { GettingStartedStepper } from '../components/onboarding/GettingStartedStepper';
import { Step1OrgProfile } from '../components/onboarding/Step1OrgProfile';
import { Step2Connectors } from '../components/onboarding/Step2Connectors';
import { Step3EvidenceLedger } from '../components/onboarding/Step3EvidenceLedger';
import { Step4NeedsAttention } from '../components/onboarding/Step4NeedsAttention';
import { Step5RecoveryReadiness } from '../components/onboarding/Step5RecoveryReadiness';
import { Step6BoardReport } from '../components/onboarding/Step6BoardReport';

export default function Onboarding() {
  const navigate = useNavigate();
  const { user, signOut, loading: authLoading, refreshAuth, signInAsDemo } = useAuth();

  const isExplicitDemo =
    typeof window !== 'undefined' &&
    (localStorage.getItem('resilai_demo_user') === 'true' ||
      window.location.search.includes('mode=demo') ||
      window.location.search.includes('env=demo'));

  const [mode, setMode] = useState<OnboardingMode>(isExplicitDemo ? 'demo' : 'real');
  const [currentStep, setCurrentStep] = useState<OnboardingStepNumber>(1);
  const [completedSteps, setCompletedSteps] = useState<OnboardingStepNumber[]>([]);
  const [profile, setProfile] = useState<OnboardingOrgProfile>(
    isExplicitDemo ? INITIAL_DEMO_PROFILE : INITIAL_REAL_PROFILE
  );
  const [connectors, setConnectors] = useState<SecurityConnectorState[]>(DEFAULT_CONNECTORS);
  const [createdOrgId, setCreatedOrgId] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if organization already exists on load
  useEffect(() => {
    if (!authLoading && user && mode === 'real') {
      const isExplicitNew = window.location.search.includes('new=true');
      if (isExplicitNew) {
        return; // Allow creating another org
      }

      getOrganizations()
        .then((orgs) => {
          if (orgs && orgs.length > 0) {
            const savedOrgId = localStorage.getItem('resilai_selected_org_id');
            const targetId = savedOrgId && orgs.find((o) => o.id === savedOrgId) ? savedOrgId : orgs[0].id;
            setCreatedOrgId(targetId);
            setProfile((prev) => ({
              ...prev,
              name: prev.name || orgs[0].name || '',
            }));
          }
        })
        .catch((err) => console.warn('[Onboarding] Org check warning:', err));
    }
  }, [authLoading, user, mode]);

  const handleSelectStep = (step: OnboardingStepNumber) => {
    setCurrentStep(step);
    if (createdOrgId) {
      setOnboardingStep(createdOrgId, step);
    }
  };

  const handleNextStep = async () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps((prev) => [...prev, currentStep]);
    }

    // If moving from Step 1 to Step 2 in Real mode, ensure org is created or updated
    if (currentStep === 1 && mode === 'real' && !createdOrgId && profile.name.trim()) {
      try {
        setSubmitting(true);
        setError(null);
        const org = await createOrganization({
          name: profile.name.trim(),
          industry: profile.industry.trim() || undefined,
          size: profile.size.trim() || undefined,
          country: profile.country.trim() || undefined,
          region_state: profile.regionState.trim() || undefined,
        });

        setCreatedOrgId(org.id);
        localStorage.setItem('resilai_selected_org_id', org.id);
        localStorage.setItem('resilai_operating_profile', profile.industry);

        if (refreshAuth) {
          await refreshAuth();
        }
      } catch (err: any) {
        console.warn('[Onboarding] Org creation notice:', err);
        // If already exists or error, use fallback id
        const fallbackId = 'org_' + Date.now();
        setCreatedOrgId(fallbackId);
        localStorage.setItem('resilai_selected_org_id', fallbackId);
      } finally {
        setSubmitting(false);
      }
    }

    if (currentStep < 6) {
      const next = (currentStep + 1) as OnboardingStepNumber;
      setCurrentStep(next);
      if (createdOrgId) {
        setOnboardingStep(createdOrgId, next);
      }
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      const prev = (currentStep - 1) as OnboardingStepNumber;
      setCurrentStep(prev);
      if (createdOrgId) {
        setOnboardingStep(createdOrgId, prev);
      }
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
      setProfile(INITIAL_REAL_PROFILE);
    }
  };

  const handleCompleteAndEnter = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const effectiveOrgId = createdOrgId || (mode === 'demo' ? 'demo-health-org' : 'default-org');
      setOnboardingCompleted(effectiveOrgId, true);
      setOnboardingStep(effectiveOrgId, 6);

      if (mode === 'demo') {
        await signInAsDemo();
      }

      navigate('/morning-brief', { replace: true });
    } catch (err: any) {
      console.error('[Onboarding] Final enter error:', err);
      navigate('/morning-brief', { replace: true });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login', { replace: true });
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-on-surface-variant text-sm font-mono">
          Initializing ResilAI Environment...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col justify-between selection:bg-ready-emerald/30 selection:text-ready-emerald">
      {/* Top Navbar */}
      <header className="h-16 border-b border-outline-variant/40 bg-surface-container-low/90 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between z-30">
        <div className="flex items-center gap-3">
          <img src="/logo_header.svg" alt="ResilAI" className="h-7 w-auto" />
          <span className="hidden sm:inline-block h-4 w-[1px] bg-outline-variant/50" />
          <span className="hidden sm:inline-block text-xs font-mono font-bold uppercase tracking-wider text-ready-emerald">
            Getting Started Guided Setup
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleToggleMode}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-outline-variant/60 hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all flex items-center gap-1.5"
          >
            {mode === 'demo' ? (
              <>
                <Shield className="w-3.5 h-3.5 text-ready-emerald" />
                <span className="hidden sm:inline">Switch to Live Setup</span>
                <span className="sm:hidden">Live Mode</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-drift-amber" />
                <span className="hidden sm:inline">Switch to Acme Demo</span>
                <span className="sm:hidden">Demo Mode</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleCompleteAndEnter}
            className="text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:underline px-2 py-1"
          >
            Skip to Dashboard
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 md:p-8 flex flex-col">
        {error && (
          <div className="mb-6 p-4 bg-critical-red/10 border border-critical-red/30 rounded-2xl text-critical-red text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* 6-Step Stepper Header */}
        <div className="bg-surface-container-low rounded-3xl border border-outline-variant/40 overflow-hidden shadow-2xl flex-1 flex flex-col">
          <GettingStartedStepper
            currentStep={currentStep}
            completedSteps={completedSteps}
            onSelectStep={handleSelectStep}
            mode={mode}
            onToggleMode={handleToggleMode}
            allowModeSwitch={true}
          />

          {/* Active Step Workspace */}
          <div className="p-4 sm:p-6 md:p-8 flex-1">
            {currentStep === 1 && (
              <Step1OrgProfile
                profile={profile}
                onChangeProfile={handleUpdateProfile}
                mode={mode}
                onNext={handleNextStep}
                isSubmitting={submitting}
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
                orgId={createdOrgId || (mode === 'demo' ? 'demo-health-org' : 'default')}
                orgName={profile.name || 'Acme Health Systems'}
                onComplete={handleCompleteAndEnter}
                onPrev={handlePrevStep}
                isSubmitting={submitting}
              />
            )}
          </div>
        </div>
      </main>

      {/* Footer Info */}
      <footer className="h-14 border-t border-outline-variant/30 px-6 flex items-center justify-between text-xs text-on-surface-variant bg-surface-container-lowest">
        <div className="flex items-center gap-2">
          <span>Signed in as: <strong className="text-on-surface">{user?.email || 'Demo Executive'}</strong></span>
        </div>

        <button
          type="button"
          onClick={handleSignOut}
          className="hover:text-critical-red flex items-center gap-1.5 transition-colors font-medium"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </footer>
    </div>
  );
}
