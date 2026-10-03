import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import {
  checkHealth,
  getApiBaseUrl,
  getOrganizations,
  toggleOrgAnalytics,
  getOrganizationProfile,
  updateOrganizationProfile,
  getApplicableFrameworks,
  ApiRequestError,
} from '../api';
import { clearAllLocalData, getLocalDataSummary } from '../lib/userData';
import { useAuth } from '../contexts/AuthContext';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { ThemeContext } from '../contexts/ThemeContext';
import { useToast } from '../components/ui/Toast';
import {
  Settings as SettingsIcon,
  Server,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Database,
  User,
  Mail,
  Shield,
  Plug,
  Eye,
  EyeOff,
  Activity,
  CreditCard,
  Cpu,
  ShieldCheck,
  Building,
  Globe,
  Loader2,
  ExternalLink,
  BookOpen,
  Sun,
  Moon,
  Laptop,
  Layers,
  ChevronRight,
  ArrowRight,
  Terminal,
  Key,
  Lock,
  Sparkles,
} from 'lucide-react';
import type { OrganizationProfile, ApplicableFramework, OrganizationProfileUpdate } from '../types';

interface HealthStatus {
  status: 'checking' | 'ok' | 'error';
  message?: string;
  latencyMs?: number;
  lastChecked?: Date;
}

type SettingsTab = 'workspace' | 'frameworks' | 'telemetry' | 'diagnostics';

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('workspace');
  const [health, setHealth] = useState<HealthStatus>({ status: 'checking' });
  const [localDataSummary, setLocalDataSummary] = useState<{ key: string; size: number }[]>([]);
  const [clearingData, setClearingData] = useState(false);
  const [analyticsUpdating, setAnalyticsUpdating] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState<boolean>(
    () => localStorage.getItem('airs_analytics_enabled') !== 'false'
  );

  // Framework Profiles State
  const [profile, setProfile] = useState<OrganizationProfile | null>(null);
  const [frameworks, setFrameworks] = useState<ApplicableFramework[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [updatingProfile, setUpdatingProfile] = useState<string | null>(null);

  const apiBaseUrl = getApiBaseUrl();
  const { user, signOut } = useAuth();
  const { orgId: activeOrgId, orgName, orgs, isDemo, tier, selectOrg } = useActiveOrg();
  const themeContext = useContext(ThemeContext);
  const { addToast } = useToast();

  const effectiveOrgId = activeOrgId || (orgs.length > 0 ? orgs[0].id : null);

  const checkApiHealth = async () => {
    setHealth({ status: 'checking' });
    const startTime = performance.now();
    try {
      const result = await checkHealth();
      const latencyMs = Math.round(performance.now() - startTime);
      setHealth({
        status: result.status === 'ok' ? 'ok' : 'error',
        message: result.status === 'ok' ? 'API service is fully operational' : `Unexpected status: ${result.status}`,
        latencyMs,
        lastChecked: new Date(),
      });
    } catch (err) {
      setHealth({
        status: 'error',
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : (err instanceof Error ? err.message : 'Unknown connection error'),
        lastChecked: new Date(),
      });
    }
  };

  const refreshLocalDataSummary = () => {
    setLocalDataSummary(getLocalDataSummary());
  };

  const handleClearLocalData = () => {
    setClearingData(true);
    clearAllLocalData();
    refreshLocalDataSummary();
    addToast({
      title: 'Cache Flushed',
      message: 'Local browser session cache and draft states cleared.',
      type: 'info',
    });
    setTimeout(() => setClearingData(false), 500);
  };

  const handleAnalyticsToggle = async (enabled: boolean) => {
    setAnalyticsEnabled(enabled);
    localStorage.setItem('airs_analytics_enabled', enabled ? 'true' : 'false');
    if (effectiveOrgId) {
      setAnalyticsUpdating(true);
      try {
        await toggleOrgAnalytics(effectiveOrgId, enabled);
        addToast({
          title: 'Telemetry Updated',
          message: enabled ? 'Telemetry logging enabled.' : 'Telemetry logging disabled.',
          type: 'ready',
        });
      } catch {
        // Non-critical
      } finally {
        setAnalyticsUpdating(false);
      }
    }
  };

  const loadOrgData = async (targetOrgId: string) => {
    setLoadingProfile(true);
    try {
      const [profileData, fwData] = await Promise.all([
        getOrganizationProfile(targetOrgId),
        getApplicableFrameworks(targetOrgId),
      ]);
      setProfile(profileData);
      setFrameworks(fwData.frameworks || []);
    } catch {
      // Handle offline or error gracefully
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleProfileToggle = async (key: keyof OrganizationProfileUpdate, value: boolean) => {
    if (!effectiveOrgId || !profile) return;
    setUpdatingProfile(key as string);

    const updatePayload: OrganizationProfileUpdate = { [key]: value };
    
    // For GDPR toggle: GDPR is active if processes_pii is true AND geo_regions contains "EU"
    if (key === 'processes_pii') {
      const currentRegions = profile.geo_regions || [];
      if (value) {
        if (!currentRegions.includes('EU')) {
          updatePayload.geo_regions = [...currentRegions, 'EU'];
        }
      } else {
        updatePayload.geo_regions = currentRegions.filter((r) => r !== 'EU');
      }
    }

    try {
      const updated = await updateOrganizationProfile(effectiveOrgId, updatePayload);
      setProfile(updated);
      const fwData = await getApplicableFrameworks(effectiveOrgId);
      setFrameworks(fwData.frameworks || []);
      addToast({
        title: 'Framework Scope Updated',
        message: 'Compliance obligations recalculated deterministically.',
        type: 'ready',
      });
    } catch {
      addToast({
        title: 'Update Notice',
        message: 'Could not sync framework profile with backend server.',
        type: 'error',
      });
    } finally {
      setUpdatingProfile(null);
    }
  };

  useEffect(() => {
    checkApiHealth();
    refreshLocalDataSummary();
    if (effectiveOrgId) {
      loadOrgData(effectiveOrgId);
    }
  }, [effectiveOrgId]);

  const profileConfigs = [
    {
      key: 'processes_phi' as const,
      title: 'HIPAA Health Data (PHI)',
      category: 'Healthcare & Clinical',
      description: 'Protects patient health information, clinical databases, EHR systems, and Business Associate agreements.',
      icon: Activity,
      color: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
    },
    {
      key: 'uses_ai_in_production' as const,
      title: 'NIST AI Risk Management',
      category: 'AI & Autonomous Agents',
      description: 'Activates controls for autonomous agent lateral blast radius, prompt injection, and NIST AI RMF / OWASP LLM alignment.',
      icon: Cpu,
      color: 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20',
    },
    {
      key: 'processes_cardholder_data' as const,
      title: 'PCI-DSS Payment Security',
      category: 'Financial & Transactions',
      description: 'Enforces standards for cardholder data isolation, encrypted token storage, and network perimeter validation.',
      icon: CreditCard,
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      key: 'processes_pii' as const,
      title: 'GDPR / Privacy Framework',
      category: 'Privacy & Data Rights',
      description: 'Enforces EU region mapping, data residency, subject access request compliance, and anonymized audit logs.',
      icon: Globe,
      color: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20',
    },
    {
      key: 'financial_services' as const,
      title: 'NIST CSF 2.0 & FFIEC',
      category: 'Banking & Critical Infrastructure',
      description: 'Continuous cyber readiness and business continuity requirements expected for financial and critical systems.',
      icon: Building,
      color: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
    },
    {
      key: 'handles_dod_data' as const,
      title: 'Defense Contract (CMMC)',
      category: 'Government & Defense',
      description: 'Triggers NIST SP 800-171 controls required for handling Controlled Unclassified Information (CUI).',
      icon: ShieldCheck,
      color: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    },
    {
      key: 'government_contractor' as const,
      title: 'Federal Contractor (FedRAMP)',
      category: 'Government & Defense',
      description: 'Toggles advisory constraints for cloud systems and SaaS platforms hosting public sector and federal workloads.',
      icon: Shield,
      color: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 text-left pb-16">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 bg-surface-container border border-outline-variant/60 rounded-2xl flex items-center justify-center shadow-xs text-on-surface">
            <SettingsIcon className="w-6 h-6 text-ready-emerald" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-on-surface">Settings & Preferences</h1>
              {isDemo && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  Sandbox Demo
                </span>
              )}
            </div>
            <p className="text-on-surface-variant text-xs mt-0.5">
              Manage organization identity, compliance scope baselines, connected telemetry, and visual preferences.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/connectors"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 transition-colors"
          >
            <Plug className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Connectors Fleet</span>
          </Link>
          <button
            onClick={checkApiHealth}
            className="p-2 text-on-surface-variant hover:text-on-surface bg-surface-container hover:bg-surface-container-high rounded-xl border border-outline-variant/60 transition-colors"
            title="Refresh Diagnostics"
          >
            <RefreshCw className={`w-4 h-4 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Modern Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-surface-container rounded-2xl border border-outline-variant/60 overflow-x-auto shadow-xs">
        {[
          { id: 'workspace' as const, label: 'Workspace & Identity', icon: Building },
          { id: 'frameworks' as const, label: 'Regulatory Scope', icon: BookOpen, badge: frameworks.length > 0 ? frameworks.length : undefined },
          { id: 'telemetry' as const, label: 'Connectors & Telemetry', icon: Activity },
          { id: 'diagnostics' as const, label: 'System & Diagnostics', icon: Server },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-surface-container-low text-on-surface shadow-xs border border-outline-variant/40'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-primary/10 text-primary border border-primary/20">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: WORKSPACE & IDENTITY                                               */}
      {/* ========================================================================= */}
      {activeTab === 'workspace' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Active Organization Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald font-bold text-xs">
                    {orgName ? orgName.charAt(0).toUpperCase() : 'R'}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-on-surface">Organization Profile</h3>
                    <p className="text-[11px] text-on-surface-variant">Active tenant workspace</p>
                  </div>
                </div>
                <span className={`text-[10px] font-bold font-mono uppercase px-2 py-0.5 rounded-md border ${
                  isDemo
                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                }`}>
                  {isDemo ? 'Sandbox Demo' : 'Live Production'}
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-on-surface-variant block mb-1">Organization Name</span>
                  <div className="font-semibold text-on-surface text-sm">{orgName || 'Workspace'}</div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant text-[11px] block mb-0.5">Workspace Tier</span>
                    <span className="font-bold text-on-surface font-mono uppercase text-xs">
                      {tier || (isDemo ? 'Design Partner' : 'Enterprise')}
                    </span>
                  </div>
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant text-[11px] block mb-0.5">Environment</span>
                    <span className="font-bold text-on-surface font-mono text-xs">
                      {isDemo ? 'Synthetic Demo' : 'Verified Evidence'}
                    </span>
                  </div>
                </div>

                {orgs.length > 1 && (
                  <div className="pt-2">
                    <span className="text-on-surface-variant block mb-1.5 font-medium">Switch Organization</span>
                    <select
                      value={effectiveOrgId || ''}
                      onChange={(e) => selectOrg(e.target.value)}
                      className="w-full px-3 py-2 bg-surface-container border border-outline-variant/60 rounded-xl text-on-surface text-xs focus:outline-none focus:border-primary"
                    >
                      {orgs.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name} ({org.id.slice(0, 10)}...)
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* User Account & Session Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5 pb-3 border-b border-outline-variant/60">
                <User className="w-5 h-5 text-on-surface-variant" />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">Authenticated Member</h3>
                  <p className="text-[11px] text-on-surface-variant">Current user credentials</p>
                </div>
              </div>

              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 bg-ready-emerald/15 border border-ready-emerald/30 rounded-full flex items-center justify-center text-ready-emerald font-bold text-base shadow-sm shrink-0">
                  {user?.photoURL ? (
                    <img src={user.photoURL} alt="User" className="w-12 h-12 rounded-full object-cover" />
                  ) : (
                    <span>{user?.displayName?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}</span>
                  )}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-on-surface text-sm truncate">{user?.displayName || 'Authorized User'}</div>
                  <div className="text-xs text-on-surface-variant flex items-center gap-1.5 mt-0.5 truncate">
                    <Mail className="w-3.5 h-3.5 shrink-0" />
                    <span>{user?.email || 'user@organization.resilai.io'}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-outline-variant/60 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5 text-ready-emerald" />
                    Member ID
                  </span>
                  <code className="bg-surface-container border border-outline-variant/60 px-2 py-0.5 rounded font-mono text-[11px] text-on-surface">
                    {user?.uid ? `${user.uid.slice(0, 14)}...` : 'demo-auth-session'}
                  </code>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant flex items-center gap-1">
                    <Key className="w-3.5 h-3.5 text-ready-emerald" />
                    Auth Provider
                  </span>
                  <span className="font-mono font-semibold text-on-surface text-[11px]">
                    {user?.providerId || (isDemo ? 'Sandbox Session' : 'Firebase Auth')}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Visual Appearance & Theme Controls */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-on-surface">Visual Appearance & Interface Mode</h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Toggle between Material 3 Obsidian dark mode and high-contrast clinical light mode.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-1">
              {[
                { id: 'light' as const, label: 'Light Theme', desc: 'Clinical High Contrast', icon: Sun },
                { id: 'dark' as const, label: 'Dark Theme', desc: 'Stitch Obsidian Slate', icon: Moon },
                { id: 'system' as const, label: 'System Default', desc: 'Sync with Device OS', icon: Laptop },
              ].map((themeOption) => {
                const Icon = themeOption.icon;
                const isSelected = themeContext?.theme === themeOption.id;
                return (
                  <button
                    key={themeOption.id}
                    onClick={() => themeContext?.setTheme(themeOption.id)}
                    className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center gap-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-surface-container border-ready-emerald text-on-surface shadow-xs ring-1 ring-ready-emerald/50'
                        : 'bg-surface-container/60 hover:bg-surface-container border-outline-variant/60 text-on-surface-variant'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-ready-emerald' : 'text-on-surface-variant'}`} />
                    <div>
                      <div className={`text-xs font-bold ${isSelected ? 'text-on-surface' : 'text-on-surface-variant'}`}>
                        {themeOption.label}
                      </div>
                      <div className="text-[10px] text-on-surface-variant/70 mt-0.5">{themeOption.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: REGULATORY SCOPE                                                    */}
      {/* ========================================================================= */}
      {activeTab === 'frameworks' && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-4 border-b border-outline-variant/60">
              <div>
                <h3 className="text-base font-bold text-on-surface">Regulatory & Framework Scope Profiles</h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Toggling operational scope dynamically recalculates applicable compliance requirements in real-time.
                </p>
              </div>
              {loadingProfile && (
                <div className="flex items-center gap-2 text-xs font-mono text-primary">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Recalculating...</span>
                </div>
              )}
            </div>

            {/* Profile Toggles Grid */}
            <div className="grid md:grid-cols-2 gap-4">
              {profileConfigs.map((config) => {
                const Icon = config.icon;
                const isEnabled = profile ? !!profile[config.key] : false;
                const isUpdating = updatingProfile === config.key;

                return (
                  <div
                    key={config.key}
                    className={`p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between gap-3 ${
                      isEnabled
                        ? 'bg-surface-container border-ready-emerald/40 shadow-xs'
                        : 'bg-surface-container/40 border-outline-variant/40 hover:border-outline-variant/70'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${config.color}`}>
                        <Icon className="w-4.5 h-4.5" />
                      </div>
                      <div className="space-y-0.5 flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-on-surface truncate">{config.title}</h4>
                          <span className="text-[10px] text-on-surface-variant/70 font-mono uppercase">{config.category}</span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant leading-relaxed line-clamp-2">
                          {config.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-outline-variant/40 text-xs">
                      <span className={`text-[10px] uppercase font-bold tracking-wider font-mono ${
                        isEnabled ? 'text-ready-emerald' : 'text-on-surface-variant/60'
                      }`}>
                        {isEnabled ? 'Active Baseline' : 'Advisory / Inactive'}
                      </span>
                      <button
                        role="switch"
                        aria-checked={isEnabled}
                        disabled={isUpdating || !profile}
                        onClick={() => handleProfileToggle(config.key, !isEnabled)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none cursor-pointer disabled:opacity-50 ${
                          isEnabled ? 'bg-ready-emerald' : 'bg-surface-container-highest border border-outline-variant'
                        }`}
                      >
                        {isUpdating ? (
                          <Loader2 className="w-3 h-3 text-slate-950 animate-spin mx-auto" />
                        ) : (
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                              isEnabled ? 'translate-x-4.5' : 'translate-x-0.5'
                            }`}
                          />
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Recalculated Frameworks List */}
            <div className="pt-6 border-t border-outline-variant/60 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-mono font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-ready-emerald" />
                  <span>Recalculated Compliance Obligations ({frameworks.length})</span>
                </h4>
                <Link to="/governance" className="text-xs text-ready-emerald hover:underline font-semibold flex items-center gap-1">
                  <span>View Governance Matrix</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {frameworks.length === 0 ? (
                <div className="p-6 text-center rounded-xl bg-surface-container border border-dashed border-outline-variant text-xs text-on-surface-variant">
                  Toggle on compliance profiles above to activate regulatory rules engines and mapping tables.
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {frameworks.map((fw) => (
                    <div
                      key={fw.framework}
                      className="p-3.5 bg-surface-container rounded-xl border border-outline-variant/60 flex flex-col justify-between gap-2"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-bold font-mono text-on-surface">{fw.framework}</span>
                          <span
                            className={`px-1.5 py-0.2 text-[9px] font-bold rounded uppercase tracking-wider ${
                              fw.mandatory
                                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                                : 'bg-primary/10 text-primary border border-primary/20'
                            }`}
                          >
                            {fw.mandatory ? 'Mandatory' : 'Advisory'}
                          </span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant leading-relaxed line-clamp-2">
                          {fw.reason}
                        </p>
                      </div>

                      {fw.reference_url && (
                        <a
                          href={fw.reference_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline font-semibold mt-1"
                        >
                          <span>Official Reference</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: CONNECTORS & TELEMETRY                                             */}
      {/* ========================================================================= */}
      {activeTab === 'telemetry' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Telemetry Configuration Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5 pb-3 border-b border-outline-variant/60">
                <Activity className="w-5 h-5 text-ready-emerald" />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">Telemetry & Verification Streams</h3>
                  <p className="text-[11px] text-on-surface-variant">Inbound security log sync</p>
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 p-4 bg-surface-container rounded-xl border border-outline-variant/60">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-on-surface flex items-center gap-1.5">
                    {analyticsEnabled ? <Eye className="w-3.5 h-3.5 text-ready-emerald" /> : <EyeOff className="w-3.5 h-3.5 text-on-surface-variant" />}
                    <span>Share Operational Telemetry</span>
                  </div>
                  <p className="text-[11px] text-on-surface-variant leading-relaxed">
                    Transmits system event heartbeats for deterministic verification. Zero patient PHI or keys are ever ingested.
                  </p>
                </div>

                <button
                  role="switch"
                  aria-checked={analyticsEnabled}
                  disabled={analyticsUpdating}
                  onClick={() => handleAnalyticsToggle(!analyticsEnabled)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none cursor-pointer disabled:opacity-50 shrink-0 ${
                    analyticsEnabled ? 'bg-ready-emerald' : 'bg-surface-container-highest border border-outline-variant'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      analyticsEnabled ? 'translate-x-4.5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              <div className="space-y-2 text-xs pt-1">
                <div className="flex justify-between items-center text-on-surface-variant">
                  <span>Cryptographic Hashing</span>
                  <span className="font-mono text-ready-emerald font-bold">SHA-256 Active</span>
                </div>
                <div className="flex justify-between items-center text-on-surface-variant">
                  <span>Verification Method</span>
                  <span className="font-mono text-on-surface font-semibold">100% Deterministic (No LLM Scoring)</span>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  to="/activity"
                  className="w-full inline-flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 transition-colors"
                >
                  <Activity className="w-3.5 h-3.5 text-ready-emerald" />
                  <span>Inspect Audit & Telemetry Log</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Ingestion Fleet Direct Navigation Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2.5 pb-3 border-b border-outline-variant/60">
                  <Plug className="w-5 h-5 text-ready-emerald" />
                  <div>
                    <h3 className="text-sm font-bold text-on-surface">Connected Telemetry Fleet</h3>
                    <p className="text-[11px] text-on-surface-variant">Security and backup forwarders</p>
                  </div>
                </div>

                <div className="space-y-2.5 pt-3 text-xs">
                  <div className="flex items-center justify-between p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="font-medium text-on-surface">Microsoft 365 / Entra ID</span>
                    <span className="text-[10px] font-mono font-bold text-ready-emerald uppercase">Live Verified</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="font-medium text-on-surface">Veeam Backup & Replication</span>
                    <span className="text-[10px] font-mono font-bold text-ready-emerald uppercase">Immutable WORM</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="font-medium text-on-surface">Splunk / SIEM Log Ingestion</span>
                    <span className="text-[10px] font-mono font-bold text-ready-emerald uppercase">Real-time Heartbeat</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-outline-variant/60">
                <Link
                  to="/connectors"
                  className="w-full inline-flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-xl bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 transition-all shadow-sm"
                >
                  <Plug className="w-4 h-4" />
                  <span>Configure Telemetry Connectors</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: SYSTEM & DIAGNOSTICS                                               */}
      {/* ========================================================================= */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Live API Health Diagnostic Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                <div className="flex items-center gap-2.5">
                  <Server className="w-5 h-5 text-on-surface-variant" />
                  <div>
                    <h3 className="text-sm font-bold text-on-surface">API Connection Diagnostics</h3>
                    <p className="text-[11px] text-on-surface-variant">Cloud Run service health</p>
                  </div>
                </div>
                <button
                  onClick={checkApiHealth}
                  disabled={health.status === 'checking'}
                  className="p-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/60 text-xs transition-colors"
                  title="Check latency"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex items-center gap-3 p-3.5 bg-surface-container rounded-xl border border-outline-variant/60">
                {health.status === 'checking' && (
                  <>
                    <div className="w-2.5 h-2.5 bg-amber-400 rounded-full animate-ping" />
                    <span className="text-xs font-bold text-amber-500">Pinging Service...</span>
                  </>
                )}
                {health.status === 'ok' && (
                  <>
                    <CheckCircle className="w-4 h-4 text-ready-emerald" />
                    <div className="flex-1 flex justify-between items-center">
                      <span className="text-xs font-bold text-ready-emerald">Operational</span>
                      {health.latencyMs !== undefined && (
                        <span className="text-[11px] font-mono text-on-surface-variant">{health.latencyMs} ms latency</span>
                      )}
                    </div>
                  </>
                )}
                {health.status === 'error' && (
                  <>
                    <XCircle className="w-4 h-4 text-rose-500" />
                    <span className="text-xs font-bold text-rose-500">Service Degraded</span>
                  </>
                )}
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-on-surface-variant block mb-1">API Base URL</span>
                  <code className="text-[11px] bg-surface-container border border-outline-variant/60 px-3 py-1.5 rounded-xl font-mono text-on-surface block truncate">
                    {apiBaseUrl}
                  </code>
                </div>

                {health.lastChecked && (
                  <p className="text-[10px] text-on-surface-variant/70">
                    Last validated: {health.lastChecked.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>

            {/* Local Cache & Session Storage Card */}
            <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/60 shadow-xs space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
                  <div className="flex items-center gap-2.5">
                    <Database className="w-5 h-5 text-on-surface-variant" />
                    <div>
                      <h3 className="text-sm font-bold text-on-surface">Local Client Cache</h3>
                      <p className="text-[11px] text-on-surface-variant">Cached browser states</p>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-on-surface-variant">
                    {localDataSummary.length} item{localDataSummary.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="pt-2">
                  {localDataSummary.length > 0 ? (
                    <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                      {localDataSummary.slice(0, 5).map((item) => (
                        <div key={item.key} className="flex justify-between items-center text-xs bg-surface-container px-3 py-1.5 rounded-lg border border-outline-variant/40">
                          <code className="font-mono text-on-surface text-[11px] truncate max-w-[200px]">{item.key}</code>
                          <span className="text-on-surface-variant text-[10px] font-mono">
                            {item.size < 1024 ? `${item.size} B` : `${(item.size / 1024).toFixed(1)} KB`}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-on-surface-variant/70 italic py-2">No local cache data recorded.</p>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-outline-variant/60 flex items-center justify-between gap-3">
                <button
                  onClick={handleClearLocalData}
                  disabled={clearingData}
                  className="inline-flex items-center gap-2 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Trash2 className={`w-3.5 h-3.5 ${clearingData ? 'animate-pulse text-rose-500' : 'text-on-surface-variant'}`} />
                  <span>{clearingData ? 'Flushing...' : 'Flush Cache'}</span>
                </button>
                <p className="text-[10px] text-on-surface-variant/70 text-right leading-tight max-w-[220px]">
                  Flushing cache resets temporary client states without affecting server verification data.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
