import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useIsReadOnly } from '../contexts';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  CardSkeleton,
} from '../components/ui';
import {
  Shield,
  Save,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  Link2,
  Copy,
  Sparkles,
} from 'lucide-react';
import {
  getOrganizations,
  getOrganizationProfile,
  updateOrganizationProfile,
  getApplicableFrameworks,
  getUptimeAnalysis,
  generateAuditorLink,
  getGovernanceForecast,
  GovernanceForecast,
  ApiRequestError,
} from '../api';
import type {
  Organization,
  OrganizationProfile as ProfileType,
  OrganizationProfileUpdate,
  ApplicableFramework,
  UptimeTierAnalysis,
} from '../types';

const REVENUE_BANDS = ['<$10M', '$10M-$50M', '$50M-$250M', '$250M-$1B', '>$1B'];
const GEO_OPTIONS = ['US', 'EU', 'UK', 'APAC', 'LATAM', 'MEA', 'Canada', 'Global'];
const TIER_OPTIONS = [
  { value: 'tier_1', label: 'Tier 1', sla: '99.99%' },
  { value: 'tier_2', label: 'Tier 2', sla: '99.9%' },
  { value: 'tier_3', label: 'Tier 3', sla: '99.5%' },
  { value: 'tier_4', label: 'Tier 4', sla: '99.0%' },
];

export default function GovernanceProfile() {
  const [searchParams] = useSearchParams();
  const isReadOnly = useIsReadOnly();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [frameworks, setFrameworks] = useState<ApplicableFramework[]>([]);
  const [uptimeAnalysis, setUptimeAnalysis] = useState<UptimeTierAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [form, setForm] = useState<OrganizationProfileUpdate>({});
  const [auditorLink, setAuditorLink] = useState<string | null>(null);
  const [auditorCopied, setAuditorCopied] = useState(false);
  const [forecast, setForecast] = useState<GovernanceForecast | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);

    Promise.all([
      getOrganizationProfile(selectedOrgId).catch(() => null),
      getApplicableFrameworks(selectedOrgId).catch(() => null),
      getUptimeAnalysis(selectedOrgId).catch(() => null),
    ]).then(([p, f, u]) => {
      if (p) {
        setProfile(p);
        setForm({
          revenue_band: p.revenue_band || undefined,
          employee_count: p.employee_count || undefined,
          geo_regions: p.geo_regions || [],
          processes_pii: p.processes_pii,
          processes_phi: p.processes_phi,
          processes_cardholder_data: p.processes_cardholder_data,
          handles_dod_data: p.handles_dod_data,
          uses_ai_in_production: p.uses_ai_in_production,
          government_contractor: p.government_contractor,
          financial_services: p.financial_services,
          application_tier: p.application_tier || undefined,
          sla_target: p.sla_target || undefined,
        });
      }
      if (f) setFrameworks(f.frameworks);
      if (u) setUptimeAnalysis(u);
      setLoading(false);
    });
  }, [selectedOrgId]);

  const handleSave = async () => {
    if (!selectedOrgId) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await updateOrganizationProfile(selectedOrgId, form);
      setProfile(updated);

      // Refresh frameworks & uptime after profile update
      const [f, u] = await Promise.all([
        getApplicableFrameworks(selectedOrgId).catch(() => null),
        getUptimeAnalysis(selectedOrgId).catch(() => null),
      ]);
      if (f) setFrameworks(f.frameworks);
      if (u) setUptimeAnalysis(u);

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.toDisplayMessage()
          : 'Failed to save profile'
      );
    } finally {
      setSaving(false);
    }
  };

  const toggleGeo = (region: string) => {
    const current = form.geo_regions || [];
    const updated = current.includes(region)
      ? current.filter((r) => r !== region)
      : [...current, region];
    setForm({ ...form, geo_regions: updated });
  };

  if (loading && organizations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        <CardSkeleton />
        <CardSkeleton />
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-50 dark:bg-indigo-950/30 rounded-xl flex items-center justify-center border border-indigo-200 dark:border-indigo-900/40 shadow-sm">
            <Shield className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Governance Profile
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">
              Define your compliance attributes to unlock framework recommendations
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all font-medium"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
          {!isReadOnly && (
            <Button onClick={handleSave} disabled={saving} className="gap-2 rounded-xl font-bold hover:scale-[1.01] transition-all">
              {saved ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Profile'}
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Card className="border-red-200 dark:border-red-900/30 bg-red-50/20 dark:bg-red-950/10 shadow-sm">
          <CardContent className="py-3">
            <p className="text-sm text-red-600 dark:text-red-400 font-semibold">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
            <CardHeader>
              <CardTitle className="text-slate-900 dark:text-slate-100 font-bold">Organization Details</CardTitle>
            </CardHeader>
             <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    Revenue Band
                  </label>
                  <select
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-medium"
                    value={form.revenue_band || ''}
                    onChange={(e) => setForm({ ...form, revenue_band: e.target.value || undefined })}
                  >
                    <option value="">Select...</option>
                    {REVENUE_BANDS.map((b) => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    Employee Count
                  </label>
                  <input
                    type="number"
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-medium"
                    value={form.employee_count || ''}
                    onChange={(e) =>
                      setForm({ ...form, employee_count: e.target.value ? parseInt(e.target.value) : undefined })
                    }
                    placeholder="e.g., 500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Geographic Regions
                </label>
                <div className="flex flex-wrap gap-2">
                  {GEO_OPTIONS.map((region) => (
                    <button
                      key={region}
                      type="button"
                      onClick={() => toggleGeo(region)}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-200 ${
                        (form.geo_regions || []).includes(region)
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-950/40 dark:border-indigo-800 dark:text-indigo-300 shadow-sm'
                          : 'bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700'
                      }`}
                    >
                      {region}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
            <CardHeader>
              <CardTitle className="text-slate-900 dark:text-slate-100 font-bold">Data & Regulatory Attributes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { key: 'processes_pii', label: 'Processes PII (Personal Data)' },
                  { key: 'processes_phi', label: 'Processes PHI (Health Data)' },
                  { key: 'processes_cardholder_data', label: 'Processes Cardholder Data' },
                  { key: 'handles_dod_data', label: 'Handles DoD/CUI Data' },
                  { key: 'uses_ai_in_production', label: 'Uses AI in Production' },
                  { key: 'government_contractor', label: 'Government Contractor' },
                  { key: 'financial_services', label: 'Financial Services' },
                ].map(({ key, label }) => (
                  <label
                    key={key}
                    className="flex items-center gap-3 p-3 rounded-xl border border-slate-100 dark:border-slate-800/80 hover:bg-slate-50 dark:hover:bg-slate-900/30 cursor-pointer transition-all duration-200"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean((form as Record<string, unknown>)[key])}
                      onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                      className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500/20 focus:ring-2 dark:bg-slate-950 dark:checked:bg-indigo-600"
                    />
                    <span className="text-sm text-slate-800 dark:text-slate-200 font-semibold">{label}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
            <CardHeader>
              <CardTitle className="text-slate-900 dark:text-slate-100 font-bold">Uptime & SLA Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    Application Tier
                  </label>
                  <select
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-medium"
                    value={form.application_tier || ''}
                    onChange={(e) => setForm({ ...form, application_tier: e.target.value || undefined })}
                  >
                    <option value="">Select tier...</option>
                    {TIER_OPTIONS.map((t) => (
                      <option key={t.value} value={t.value}>{t.label} ({t.sla})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    Your SLA Target (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-medium"
                    value={form.sla_target ?? ''}
                    onChange={(e) =>
                      setForm({ ...form, sla_target: e.target.value ? parseFloat(e.target.value) : undefined })
                    }
                    placeholder="e.g., 99.95"
                  />
                </div>
              </div>

              {uptimeAnalysis && (
                <div
                  className={`p-4 rounded-xl border transition-all duration-300 ${
                    uptimeAnalysis.status === 'on_track'
                      ? 'bg-green-50/20 border-green-200 dark:bg-green-950/20 dark:border-green-900/40 text-green-700 dark:text-green-400'
                      : uptimeAnalysis.status === 'at_risk'
                        ? 'bg-amber-50/20 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/40 text-amber-700 dark:text-amber-400'
                        : uptimeAnalysis.status === 'unrealistic'
                          ? 'bg-red-50/20 border-red-200 dark:bg-red-950/20 dark:border-red-900/40 text-red-700 dark:text-red-400'
                          : 'bg-slate-50/20 border-slate-200 dark:bg-slate-900/20 dark:border-slate-800 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <p className="text-sm font-extrabold text-slate-900 dark:text-slate-100">
                    {uptimeAnalysis.status === 'on_track' && '✅ '}
                    {uptimeAnalysis.status === 'at_risk' && '⚠️ '}
                    {uptimeAnalysis.status === 'unrealistic' && '🔴 '}
                    Uptime Analysis
                  </p>
                  <p className="text-sm mt-1 leading-relaxed opacity-95">
                    {uptimeAnalysis.message}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar — Applicable Frameworks */}
        <div className="space-y-6">
          <Card className="shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
            <CardHeader>
              <CardTitle className="text-lg text-slate-900 dark:text-slate-100 font-bold">Applicable Frameworks</CardTitle>
            </CardHeader>
            <CardContent>
              {frameworks.length === 0 ? (
                <p className="text-sm text-slate-500 dark:text-slate-400 italic">
                  Complete your governance profile to see applicable frameworks.
                </p>
              ) : (
                <div className="space-y-3">
                  {frameworks.map((fw) => (
                    <div
                      key={fw.framework}
                      className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-900/10"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                          {fw.framework}
                        </span>
                        <Badge
                          variant={fw.mandatory ? 'danger' : 'default'}
                          className="rounded-lg px-2.5 py-0.5 text-xs font-extrabold border border-indigo-200 dark:border-indigo-900/40"
                        >
                          {fw.mandatory ? 'Mandatory' : 'Recommended'}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
                        {fw.reason}
                      </p>
                      {fw.reference_url && (
                        <a
                          href={fw.reference_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline mt-1.5 inline-flex items-center gap-1 font-bold"
                        >
                          Learn more <ChevronRight className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Governance Forecast (Gemini AI) */}
          <Card className="border-purple-200 dark:border-purple-900/30 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md bg-purple-50/10 dark:bg-purple-950/5">
            <CardHeader>
              <CardTitle className="text-lg text-slate-900 dark:text-slate-100 font-bold flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-500" />
                Governance Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              {forecast ? (
                <div className="space-y-3">
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                    {forecast.forecast}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 font-semibold">
                    <span className="px-2.5 py-0.5 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 rounded-lg font-bold border border-purple-200/50 dark:border-purple-900/40">
                      {forecast.focus_area}
                    </span>
                    <span>Confidence: {forecast.confidence}</span>
                    {forecast.llm_generated && (
                      <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400">
                        <Sparkles className="w-3 h-3" /> AI
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <button
                  onClick={async () => {
                    setForecastLoading(true);
                    try {
                      const result = await getGovernanceForecast(selectedOrgId);
                      setForecast(result);
                    } catch {
                      setError('Failed to generate forecast');
                    } finally {
                      setForecastLoading(false);
                    }
                  }}
                  disabled={forecastLoading || !selectedOrgId}
                  className="w-full p-3 rounded-xl border border-purple-200 dark:border-purple-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all duration-200 text-sm text-purple-700 dark:text-purple-300 flex items-center justify-center gap-2 disabled:opacity-50 font-bold"
                >
                  {forecastLoading ? (
                    <>Generating forecast...</>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate SOC 2 CC7.1 Forecast
                    </>
                  )}
                </button>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
            <CardHeader>
              <CardTitle className="text-lg text-slate-900 dark:text-slate-100 font-bold">Quick Links</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5">
              <Link
                to={`/dashboard/audit-calendar?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-all duration-200"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300 font-bold">Audit Calendar</span>
                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              </Link>
              <Link
                to={`/dashboard/tech-stack?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-all duration-200"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300 font-bold">Tech Stack Registry</span>
                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              </Link>
              <Link
                to={`/dashboard/ai-attack-simulation-lab?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-all duration-200"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300 font-bold">AI Threat Lab</span>
                <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              </Link>

              {/* Auditor Link Generator */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-semibold">Share read-only access with auditors</p>
                {auditorLink ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        readOnly
                        value={auditorLink}
                        className="flex-1 text-xs p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl font-mono text-slate-800 dark:text-slate-200 focus:outline-none"
                      />
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(auditorLink);
                          setAuditorCopied(true);
                          setTimeout(() => setAuditorCopied(false), 2000);
                        }}
                        className="p-2 text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                        title="Copy link"
                      >
                        {auditorCopied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">Expires in 72 hours</p>
                  </div>
                ) : (
                  <button
                    onClick={async () => {
                      try {
                        const result = await generateAuditorLink(selectedOrgId);
                        const link = `${window.location.origin}/auditor?token=${result.token}`;
                        setAuditorLink(link);
                      } catch {
                        setError('Failed to generate auditor link');
                      }
                    }}
                    className="flex items-center gap-2 w-full p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-all duration-200 text-sm text-slate-700 dark:text-slate-300 font-bold"
                  >
                    <Link2 className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                    Generate Auditor Link
                  </button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}
