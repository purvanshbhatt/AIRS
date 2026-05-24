import { useState, useEffect } from 'react';
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
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
} from '../components/ui';
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
} from 'lucide-react';

interface HealthStatus {
  status: 'checking' | 'ok' | 'error';
  message?: string;
  lastChecked?: Date;
}

export default function Settings() {
  const [health, setHealth] = useState<HealthStatus>({ status: 'checking' });
  const [localDataSummary, setLocalDataSummary] = useState<{ key: string; size: number }[]>([]);
  const [clearingData, setClearingData] = useState(false);
  const [currentOrgId, setCurrentOrgId] = useState<string | null>(null);
  const [analyticsUpdating, setAnalyticsUpdating] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState<boolean>(
    () => localStorage.getItem('airs_analytics_enabled') !== 'false'
  );

  // Framework Profiles State
  const [profile, setProfile] = useState<import('../types').OrganizationProfile | null>(null);
  const [frameworks, setFrameworks] = useState<import('../types').ApplicableFramework[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [updatingProfile, setUpdatingProfile] = useState<string | null>(null);

  const apiBaseUrl = getApiBaseUrl();
  const { user } = useAuth();

  const handleAnalyticsToggle = async (enabled: boolean) => {
    setAnalyticsEnabled(enabled);
    localStorage.setItem('airs_analytics_enabled', enabled ? 'true' : 'false');
    if (currentOrgId) {
      setAnalyticsUpdating(true);
      try {
        await toggleOrgAnalytics(currentOrgId, enabled);
      } catch {
        // Non-critical
      } finally {
        setAnalyticsUpdating(false);
      }
    }
  };

  const refreshLocalDataSummary = () => {
    setLocalDataSummary(getLocalDataSummary());
  };

  const handleClearLocalData = () => {
    setClearingData(true);
    clearAllLocalData();
    refreshLocalDataSummary();
    setTimeout(() => setClearingData(false), 500);
  };

  const checkApiHealth = async () => {
    setHealth({ status: 'checking' });
    try {
      const result = await checkHealth();
      setHealth({
        status: result.status === 'ok' ? 'ok' : 'error',
        message: result.status === 'ok' ? 'API is responding' : `Unexpected status: ${result.status}`,
        lastChecked: new Date(),
      });
    } catch (err) {
      setHealth({
        status: 'error',
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : (err instanceof Error ? err.message : 'Unknown error'),
        lastChecked: new Date(),
      });
    }
  };

  const loadOrgData = async (orgId: string) => {
    setLoadingProfile(true);
    try {
      const [profileData, fwData] = await Promise.all([
        getOrganizationProfile(orgId),
        getApplicableFrameworks(orgId),
      ]);
      setProfile(profileData);
      setFrameworks(fwData.frameworks);
    } catch {
      // Handle offline or error gracefully
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleProfileToggle = async (key: keyof import('../types').OrganizationProfileUpdate, value: boolean) => {
    if (!currentOrgId || !profile) return;
    setUpdatingProfile(key as string);

    // Prepare update payload
    const updatePayload: import('../types').OrganizationProfileUpdate = { [key]: value };
    
    // For GDPR toggle: GDPR is active if processes_pii is true AND geo_regions contains "EU"
    if (key === 'processes_pii') {
      const currentRegions = profile.geo_regions || [];
      if (value) {
        if (!currentRegions.includes('EU')) {
          updatePayload.geo_regions = [...currentRegions, 'EU'];
        }
      } else {
        updatePayload.geo_regions = currentRegions.filter(r => r !== 'EU');
      }
    }

    try {
      const updated = await updateOrganizationProfile(currentOrgId, updatePayload);
      setProfile(updated);
      const fwData = await getApplicableFrameworks(currentOrgId);
      setFrameworks(fwData.frameworks);
    } catch {
      // Revert in case of API failure
    } finally {
      setUpdatingProfile(null);
    }
  };

  useEffect(() => {
    checkApiHealth();
    refreshLocalDataSummary();
    getOrganizations()
      .then((orgs) => {
        if (orgs.length > 0) {
          setCurrentOrgId(orgs[0].id);
          if (typeof orgs[0].analytics_enabled === 'boolean') {
            setAnalyticsEnabled(orgs[0].analytics_enabled);
            localStorage.setItem('airs_analytics_enabled', orgs[0].analytics_enabled ? 'true' : 'false');
          }
          loadOrgData(orgs[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const profileConfigs = [
    {
      key: 'processes_phi' as const,
      title: 'HIPAA Health Data Profile',
      description: 'Protects health datasets. Enforces regulations governing Protected Health Information (PHI).',
      icon: Activity,
      color: 'text-rose-500 bg-rose-50 dark:bg-rose-950/30',
    },
    {
      key: 'processes_cardholder_data' as const,
      title: 'PCI-DSS Payment Security',
      description: 'Enforces standards for credit card handling, storage, and transaction isolation.',
      icon: CreditCard,
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30',
    },
    {
      key: 'uses_ai_in_production' as const,
      title: 'NIST AI Risk Management',
      description: 'Activates controls for algorithmic bias, training safety, and generative weights governance.',
      icon: Cpu,
      color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-950/30',
    },
    {
      key: 'handles_dod_data' as const,
      title: 'Defense Contract (CMMC)',
      description: 'Triggers NIST 800-171 controls required for handling Controlled Unclassified Information (CUI).',
      icon: ShieldCheck,
      color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/30',
    },
    {
      key: 'processes_pii' as const,
      title: 'GDPR / Privacy Framework',
      description: 'Enforces EU region mapping, data subject access rights, and anonymized logging controls.',
      icon: Globe,
      color: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-950/30',
    },
    {
      key: 'financial_services' as const,
      title: 'NIST CSF & FFIEC Profile',
      description: 'Implements cyber readiness structures expected for banking and credit systems.',
      icon: Building,
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/30',
    },
    {
      key: 'government_contractor' as const,
      title: 'Federal Contractor (FedRAMP)',
      description: 'Toggles advisory constraints for SaaS applications hosting government workloads.',
      icon: Shield,
      color: 'text-purple-500 bg-purple-50 dark:bg-purple-950/30',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 text-left pb-16">
      <div className="flex items-center gap-3.5 mb-2">
        <div className="w-12 h-12 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center justify-center shadow-inner">
          <SettingsIcon className="w-6 h-6 text-slate-700 dark:text-slate-300" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-50">Settings</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">Configure compliance targets, local caches, and API states.</p>
        </div>
      </div>

      {/* Compliance Framework Section */}
      <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 rounded-3xl overflow-hidden shadow-sm">
        <CardHeader className="border-b border-slate-100 dark:border-slate-900">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-50">Compliance Framework Profiles</CardTitle>
              <CardDescription className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Toggle organizational scope attributes. Changes dynamically recalculate frameworks in real-time.
              </CardDescription>
            </div>
            {loadingProfile && (
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            )}
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-8">
          {/* Grid of Toggles */}
          <div className="grid md:grid-cols-2 gap-5">
            {profileConfigs.map((config) => {
              const Icon = config.icon;
              const isEnabled = profile ? !!profile[config.key] : false;
              const isUpdating = updatingProfile === config.key;

              return (
                <div
                  key={config.key}
                  className={`p-5 rounded-2xl border transition-all duration-300 flex flex-col justify-between gap-4 ${
                    isEnabled
                      ? 'bg-slate-50/60 dark:bg-slate-900/40 border-blue-400/30 dark:border-blue-500/20 shadow-sm'
                      : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-900 hover:border-slate-300 dark:hover:border-slate-800'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${config.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-tight">
                        {config.title}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                        {config.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-900/60">
                    <span className="text-[10px] uppercase font-bold text-slate-400">
                      {isEnabled ? 'Active Target' : 'Not Active'}
                    </span>
                    <button
                      role="switch"
                      aria-checked={isEnabled}
                      disabled={isUpdating || !profile}
                      onClick={() => handleProfileToggle(config.key, !isEnabled)}
                      className={`relative inline-flex h-5.5 w-10.5 items-center rounded-full transition-colors focus:outline-none disabled:opacity-60 ${
                        isEnabled
                          ? 'bg-blue-600'
                          : 'bg-slate-200 dark:bg-slate-800'
                      }`}
                    >
                      {isUpdating ? (
                        <Loader2 className="w-3.5 h-3.5 text-white animate-spin mx-auto" />
                      ) : (
                        <span
                          className={`inline-block h-4.5 w-4.5 transform rounded-full bg-white shadow transition-transform ${
                            isEnabled ? 'translate-x-5' : 'translate-x-0.5'
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
          <div className="pt-6 border-t border-slate-100 dark:border-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              Recalculated Compliance Obligations ({frameworks.length})
            </h3>
            {frameworks.length === 0 ? (
              <div className="p-5 text-center rounded-2xl bg-slate-50 dark:bg-slate-900/40 border border-dashed border-slate-200 dark:border-slate-800/80">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Toggle on compliance profiles above to activate regulatory rules engines.
                </p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {frameworks.map((fw) => (
                  <div
                    key={fw.framework}
                    className="p-4 bg-slate-50/50 dark:bg-slate-900/30 border border-slate-200/80 dark:border-slate-800 rounded-2xl flex flex-col justify-between gap-3 text-left"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-bold font-mono text-slate-900 dark:text-slate-100">
                          {fw.framework}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 text-[9px] font-bold rounded-md uppercase tracking-wider ${
                            fw.mandatory
                              ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/20 dark:text-rose-450 border border-rose-100 dark:border-rose-900/30'
                              : 'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-450 border border-blue-100 dark:border-blue-900/30'
                          }`}
                        >
                          {fw.mandatory ? 'Mandatory' : 'Advisory'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                        {fw.reason}
                      </p>
                    </div>

                    {fw.reference_url && (
                      <a
                        href={fw.reference_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] text-blue-600 dark:text-blue-400 hover:underline mt-1 font-semibold"
                      >
                        Official Reference
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Grid: Profile, API Status */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Profile Card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900">
            <div className="flex items-center gap-2.5">
              <User className="h-5 w-5 text-slate-500 dark:text-slate-400" />
              <CardTitle className="text-lg font-bold">Profile</CardTitle>
            </div>
            <CardDescription className="text-xs">Your account information</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-500 rounded-full flex items-center justify-center shadow">
                {user?.photoURL ? (
                  <img
                    src={user.photoURL}
                    alt="Profile"
                    className="w-14 h-14 rounded-full object-cover"
                  />
                ) : (
                  <span className="text-xl font-bold text-white">
                    {user?.displayName?.charAt(0).toUpperCase() ||
                      user?.email?.charAt(0).toUpperCase() ||
                      'U'}
                  </span>
                )}
              </div>
              <div className="text-left">
                <p className="text-base font-bold text-slate-900 dark:text-slate-50">
                  {user?.displayName || 'User'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                  <Mail className="w-3.5 h-3.5" />
                  {user?.email || 'Not signed in'}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-slate-900 space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5" />
                  User ID
                </span>
                <code className="bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 px-2 py-0.5 rounded font-mono text-[10px] text-slate-700 dark:text-slate-300">
                  {user?.uid ? `${user.uid.slice(0, 10)}...` : 'N/A'}
                </code>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Status Card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Server className="h-5 w-5 text-slate-500 dark:text-slate-400" />
                <CardTitle className="text-lg font-bold">API Connection</CardTitle>
              </div>
              <button
                onClick={checkApiHealth}
                disabled={health.status === 'checking'}
                className="p-1.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 disabled:opacity-50"
                title="Refresh status"
              >
                <RefreshCw className={`h-4 w-4 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <CardDescription className="text-xs">Connection diagnostic</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center gap-3">
              {health.status === 'checking' && (
                <>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" />
                  <span className="text-yellow-600 dark:text-yellow-400 font-bold text-xs">Checking Connectivity...</span>
                </>
              )}
              {health.status === 'ok' && (
                <>
                  <div className="w-3 h-3 bg-emerald-500 rounded-full animate-ping" />
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold text-xs">Operational</span>
                </>
              )}
              {health.status === 'error' && (
                <>
                  <XCircle className="w-5 h-5 text-rose-500" />
                  <span className="text-rose-600 dark:text-rose-450 font-bold text-xs">Service Offline</span>
                </>
              )}
            </div>

            {health.status === 'error' && health.message && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl text-rose-700 dark:text-rose-350 text-xs">
                {health.message}
              </div>
            )}

            <div className="pt-3 border-t border-slate-100 dark:border-slate-900 text-left">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">API Base URL</p>
              <code className="text-xs bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 px-2 py-1 rounded-lg font-mono text-slate-700 dark:text-slate-300 block overflow-x-auto">
                {apiBaseUrl}
              </code>
            </div>

            {health.lastChecked && (
              <p className="text-[10px] text-slate-400 dark:text-slate-500">
                Last checked: {health.lastChecked.toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Grid: Integrations, Privacy, local data */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900">
            <div className="flex items-center gap-2">
              <Plug className="h-5 w-5 text-slate-500" />
              <CardTitle className="text-base font-bold">API Integrations</CardTitle>
            </div>
            <CardDescription className="text-xs">Outbound keys</CardDescription>
          </CardHeader>
          <CardContent className="p-5">
            <Link to="/dashboard/integrations">
              <Button variant="outline" className="w-full text-xs rounded-xl">Open Integrations</Button>
            </Link>
          </CardContent>
        </Card>

        {/* Telemetry card */}
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden col-span-2">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900">
            <div className="flex items-center gap-2">
              {analyticsEnabled
                ? <Eye className="h-5 w-5 text-blue-500" />
                : <EyeOff className="h-5 w-5 text-slate-500" />}
              <CardTitle className="text-base font-bold">Privacy &amp; Telemetry</CardTitle>
            </div>
            <CardDescription className="text-xs">Anonymised usage metrics</CardDescription>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="text-left">
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  Share telemetry logs
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Helps prioritize compliance tools. No audit text or credentials are ever sent.
                </p>
              </div>
              <button
                role="switch"
                aria-checked={analyticsEnabled}
                disabled={analyticsUpdating}
                onClick={() => handleAnalyticsToggle(!analyticsEnabled)}
                className={`relative inline-flex h-5.5 w-10.5 items-center rounded-full transition-colors focus:outline-none disabled:opacity-60 ${
                  analyticsEnabled
                    ? 'bg-blue-600'
                    : 'bg-slate-200 dark:bg-slate-800'
                }`}
              >
                <span
                  className={`inline-block h-4.5 w-4.5 transform rounded-full bg-white shadow transition-transform ${
                    analyticsEnabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Local Storage details */}
      <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
        <CardHeader className="border-b border-slate-100 dark:border-slate-900">
          <div className="flex items-center gap-2.5">
            <Database className="h-5 w-5 text-slate-500" />
            <CardTitle className="text-lg font-bold">Local Cache Storage</CardTitle>
          </div>
          <CardDescription className="text-xs">Clear cookies and local session states.</CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4 text-left">
          {localDataSummary.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">Cached elements:</p>
              {localDataSummary.map((item) => (
                <div key={item.key} className="flex justify-between items-center text-xs bg-slate-50 dark:bg-slate-900 px-3.5 py-2 rounded-xl border border-slate-100 dark:border-slate-800">
                  <code className="font-mono text-slate-700 dark:text-slate-300">{item.key}</code>
                  <span className="text-slate-500 dark:text-slate-400 text-[10px] font-semibold">
                    {item.size < 1024
                      ? `${item.size} B`
                      : `${(item.size / 1024).toFixed(1)} KB`}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No local cache data recorded.</p>
          )}

          <div className="pt-4 border-t border-slate-100 dark:border-slate-900 flex flex-wrap items-center justify-between gap-3">
            <Button
              variant="outline"
              onClick={handleClearLocalData}
              disabled={clearingData || localDataSummary.length === 0}
              className="flex items-center gap-2 rounded-xl text-xs"
            >
              <Trash2 className={`h-4 w-4 ${clearingData ? 'animate-pulse' : ''}`} />
              {clearingData ? 'Purging Cache...' : 'Flush Cache'}
            </Button>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 max-w-sm">
              Clearing cache will remove draft assessments. Active database assessments are stored safely in cloud firestore.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
