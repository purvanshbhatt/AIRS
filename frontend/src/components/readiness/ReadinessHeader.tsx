import { Search, Bell, Menu, HelpCircle, BookOpen, LogOut, ChevronDown, UserCheck, Shield, Sparkles, Building, RefreshCw, Compass } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ProductGuideModal } from '../layout/ProductGuideModal';
import { GettingStartedModal } from '../onboarding/GettingStartedModal';
import { getOnboardingCompleted, getOnboardingStep } from '../onboarding/onboardingData';
import { useAuth } from '../../contexts/AuthContext';
import { useActiveOrg } from '../../hooks/useActiveOrg';

interface ReadinessHeaderProps {
  onMenuClick: () => void;
  orgName?: string;
  isDemoMode?: boolean;
  isMspTenant?: boolean;
}

export function ReadinessHeader({ onMenuClick, isMspTenant = false }: ReadinessHeaderProps) {
  const navigate = useNavigate();
  const { user, signOut, signInAsDemo } = useAuth();
  const { orgName, orgId, isDemo, orgs, selectOrg } = useActiveOrg();

  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [isGettingStartedOpen, setIsGettingStartedOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isOnboardingDone, setIsOnboardingDone] = useState(true);
  const [onboardingCurrentStep, setOnboardingCurrentStep] = useState(1);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Check onboarding completion state for the current active organization
  useEffect(() => {
    const effectiveOrgId = orgId || (isDemo ? 'demo-health-org' : '');
    const completed = getOnboardingCompleted(effectiveOrgId);
    const step = getOnboardingStep(effectiveOrgId);
    setIsOnboardingDone(completed);
    setOnboardingCurrentStep(step);
  }, [orgId, isDemo, isGettingStartedOpen]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    setIsUserMenuOpen(false);
    await signOut();
    navigate('/login', { replace: true });
  };

  const handleExitDemoAndLogin = async () => {
    setIsUserMenuOpen(false);
    await signOut();
    navigate('/login', { replace: true });
  };

  const handleSwitchToDemo = async () => {
    setIsUserMenuOpen(false);
    await signInAsDemo();
    navigate('/morning-brief', { replace: true });
  };

  return (
    <header className="h-20 bg-background/90 dark:bg-background/90 backdrop-blur-md border-b border-outline-variant/40 flex items-center justify-between px-4 md:px-8 z-40 sticky top-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 text-on-surface-variant hover:text-on-surface rounded-lg"
          aria-label="Toggle menu"
        >
          <Menu className="w-6 h-6" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald font-bold text-sm shadow-sm">
            {orgName ? orgName.charAt(0).toUpperCase() : 'R'}
          </div>
          <div>
            <h2 className="text-sm font-bold text-on-surface flex items-center gap-2">
              <span className="truncate max-w-[200px] sm:max-w-[280px]">{orgName || 'Workspace'}</span>
              
              {isDemo ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1.5 shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                  DEMO WORKSPACE (SIMULATED DATA)
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  LIVE WORKSPACE
                </span>
              )}

              {isMspTenant && (
                <span className="hidden sm:flex px-2 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase bg-surface-container-high text-on-surface-variant border border-outline-variant/30 items-center gap-1">
                  MSP Managed
                </span>
              )}
            </h2>
            <p className="text-[11px] text-on-surface-variant hidden sm:block">
              {isDemo ? 'This workspace uses synthetic security data to demonstrate ResilAI.' : 'Continuous mathematical evidence verification'}
            </p>
          </div>
        </div>
      </div>

      {/* Global Ask ResilAI / Search Bar */}
      <div className="flex-1 max-w-md mx-6 hidden lg:flex items-center relative">
        <Search className="w-4 h-4 absolute left-3.5 text-on-surface-variant/60" />
        <input
          type="text"
          placeholder="Ask ResilAI or search telemetry..."
          className="w-full bg-surface-container-high text-sm text-on-surface rounded-full py-2 pl-10 pr-4 border border-outline-variant/50 focus:outline-none focus:ring-2 focus:ring-ready-emerald/50 placeholder-on-surface-variant/50 transition-all"
        />
      </div>

      {/* Header Actions & User Profile Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Persistent Getting Started 6-Step Guide Launcher */}
        <button
          onClick={() => setIsGettingStartedOpen(true)}
          className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm ${
            !isOnboardingDone
              ? 'bg-ready-emerald/20 border-ready-emerald/50 text-ready-emerald hover:bg-ready-emerald hover:text-slate-950 animate-pulse'
              : 'bg-surface-container-high hover:bg-surface-container-highest border-outline-variant/60 text-on-surface'
          }`}
          aria-label="Getting Started 6-Step Guide"
          title="Getting Started with ResilAI 6-Step Guide"
        >
          <Compass className="w-4 h-4 text-ready-emerald shrink-0" />
          <span className="hidden sm:inline">
            {!isOnboardingDone ? `Getting Started (${onboardingCurrentStep}/6)` : 'Getting Started'}
          </span>
          <span className="sm:hidden">Start</span>
        </button>

        {/* Quick Exit Demo CTA */}
        {isDemo && (
          <button
            onClick={handleExitDemoAndLogin}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 bg-ready-emerald/15 border border-ready-emerald/30 text-ready-emerald hover:bg-ready-emerald hover:text-on-primary-container text-xs font-semibold rounded-xl transition-all shadow-sm"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Sign In / Real Mode</span>
          </button>
        )}

        {/* Scoring Methodology Docs Link */}
        <Link
          to="/docs/methodology"
          className="p-2 text-on-surface-variant hover:text-ready-emerald hover:bg-surface-container-high rounded-full transition-colors flex items-center gap-1.5 text-xs font-medium"
          title="Scoring Methodology & Trust Contract"
        >
          <BookOpen className="w-4 h-4" />
          <span className="hidden md:inline">Docs</span>
        </Link>

        {/* Product Guide Modal Trigger */}
        <button 
          onClick={() => setIsGuideOpen(true)}
          className="p-2 text-on-surface-variant hover:text-ready-emerald hover:bg-surface-container-high rounded-full transition-colors flex items-center gap-1.5 text-xs font-medium"
          aria-label="Product Guide"
          title="How ResilAI Works"
        >
          <HelpCircle className="w-4 h-4" />
          <span className="hidden md:inline">Guide</span>
        </button>

        {/* User Profile & Account Dropdown */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex items-center gap-2 p-1.5 rounded-full hover:bg-surface-container-high transition-all border border-outline-variant/40"
            aria-label="User Account Menu"
          >
            {user?.photoURL ? (
              <img
                src={user.photoURL}
                alt={user.displayName || 'User Avatar'}
                className="w-8 h-8 rounded-full object-cover border border-ready-emerald/40"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container font-bold text-xs flex items-center justify-center shadow-sm">
                {user?.displayName
                  ? user.displayName.charAt(0).toUpperCase()
                  : user?.email
                  ? user.email.charAt(0).toUpperCase()
                  : isDemo
                  ? 'D'
                  : 'U'}
              </div>
            )}
            <ChevronDown className="w-3.5 h-3.5 text-on-surface-variant hidden sm:block mr-1" />
          </button>

          {/* Popover Dropdown Menu */}
          {isUserMenuOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-surface-container-low dark:bg-surface-container-low border border-outline-variant/50 rounded-2xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
              {/* User Identity Box */}
              <div className="p-3 bg-surface-container rounded-xl border border-surface-bright mb-2">
                <div className="flex items-center gap-3 mb-1">
                  {user?.photoURL ? (
                    <img src={user.photoURL} alt="" className="w-10 h-10 rounded-full object-cover" />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-ready-emerald/20 border border-ready-emerald/40 text-ready-emerald font-bold text-sm flex items-center justify-center">
                      {(user?.displayName || user?.email || 'D').charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-on-surface truncate">
                      {user?.displayName || (isDemo ? 'Dr. Evelyn Reed (Demo CMO)' : 'Authenticated User')}
                    </p>
                    <p className="text-xs text-on-surface-variant truncate">
                      {user?.email || (isDemo ? 'executive@acme-health.resilai.io' : 'No email')}
                    </p>
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-outline-variant/30 flex items-center justify-between text-[10px] font-mono text-on-surface-variant">
                  <span>Workspace:</span>
                  <span className="font-semibold text-ready-emerald truncate max-w-[140px]">{orgName}</span>
                </div>
              </div>

              {/* Navigation Items */}
              <div className="space-y-0.5 text-xs text-on-surface font-medium">
                {/* Switch Organizations (if multiple) */}
                {orgs.length > 1 && (
                  <div className="px-2 py-1.5 text-[11px] text-on-surface-variant font-semibold uppercase tracking-wider">
                    Switch Organization
                  </div>
                )}
                {orgs.length > 1 && orgs.map(o => (
                  <button
                    key={o.id}
                    onClick={() => {
                      selectOrg(o.id);
                      setIsUserMenuOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg flex items-center justify-between ${
                      o.id === orgId ? 'bg-ready-emerald/15 text-ready-emerald font-semibold' : 'hover:bg-surface-container'
                    }`}
                  >
                    <span className="truncate">{o.name}</span>
                    {o.id === orgId && <span className="text-[10px] font-mono font-bold">ACTIVE</span>}
                  </button>
                ))}

                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    setIsGettingStartedOpen(true);
                  }}
                  className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-container transition-colors text-ready-emerald font-semibold"
                >
                  <Compass className="w-4 h-4 text-ready-emerald" />
                  <span>Launch 6-Step Guided Setup</span>
                </button>

                <Link
                  to="/onboarding?new=true"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-container transition-colors"
                >
                  <Building className="w-4 h-4 text-on-surface-variant" />
                  <span>+ Create / Onboard Organization</span>
                </Link>

                <Link
                  to="/connectors"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-container transition-colors"
                >
                  <RefreshCw className="w-4 h-4 text-on-surface-variant" />
                  <span>Manage Telemetry Connectors</span>
                </Link>

                {isDemo ? (
                  <button
                    onClick={handleExitDemoAndLogin}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-ready-emerald hover:bg-ready-emerald/10 transition-colors font-semibold"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>Sign In to Real Account</span>
                  </button>
                ) : (
                  <button
                    onClick={handleSwitchToDemo}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-amber-500 hover:bg-amber-500/10 transition-colors"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Explore Demo Sandbox</span>
                  </button>
                )}

                <div className="my-1 border-t border-outline-variant/30" />

                <button
                  onClick={handleSignOut}
                  className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-critical-red hover:bg-critical-red/10 transition-colors font-semibold"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Product Guide Modal */}
      <ProductGuideModal 
        isOpen={isGuideOpen} 
        onClose={() => setIsGuideOpen(false)} 
      />

      {/* 6-Step Guided Onboarding Modal */}
      <GettingStartedModal
        isOpen={isGettingStartedOpen}
        onClose={() => setIsGettingStartedOpen(false)}
        orgId={orgId}
        orgName={orgName}
      />
    </header>
  );
}
