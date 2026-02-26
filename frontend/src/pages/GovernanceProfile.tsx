import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
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
      <div className="space-y-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">
              Governance Profile
            </h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">
              Define your compliance attributes to unlock framework recommendations
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            className="rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 min-w-[220px]"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
          <Button onClick={handleSave} disabled={saving} className="gap-2">
            {saved ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Profile'}
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="py-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Revenue Band
                  </label>
                  <select
                    className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Employee Count
                  </label>
                  <input
                    type="number"
                    className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                    value={form.employee_count || ''}
                    onChange={(e) =>
                      setForm({ ...form, employee_count: e.target.value ? parseInt(e.target.value) : undefined })
                    }
                    placeholder="e.g., 500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Geographic Regions
                </label>
                <div className="flex flex-wrap gap-2">
                  {GEO_OPTIONS.map((region) => (
                    <button
                      key={region}
                      type="button"
                      onClick={() => toggleGeo(region)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                        (form.geo_regions || []).includes(region)
                          ? 'bg-indigo-100 border-indigo-300 text-indigo-700 dark:bg-indigo-900/40 dark:border-indigo-600 dark:text-indigo-300'
                          : 'bg-gray-50 border-gray-200 text-gray-600 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400 hover:border-gray-300'
                      }`}
                    >
                      {region}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data & Regulatory Attributes</CardTitle>
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
                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean((form as Record<string, unknown>)[key])}
                      onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-slate-300">{label}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Uptime & SLA Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Application Tier
                  </label>
                  <select
                    className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Your SLA Target (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
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
                  className={`p-4 rounded-lg border ${
                    uptimeAnalysis.status === 'on_track'
                      ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
                      : uptimeAnalysis.status === 'at_risk'
                        ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800'
                        : uptimeAnalysis.status === 'unrealistic'
                          ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                          : 'bg-gray-50 border-gray-200 dark:bg-slate-800 dark:border-slate-700'
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-slate-100">
                    {uptimeAnalysis.status === 'on_track' && '✅ '}
                    {uptimeAnalysis.status === 'at_risk' && '⚠️ '}
                    {uptimeAnalysis.status === 'unrealistic' && '🔴 '}
                    Uptime Analysis
                  </p>
                  <p className="text-sm text-gray-700 dark:text-slate-300 mt-1">
                    {uptimeAnalysis.message}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar — Applicable Frameworks */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Applicable Frameworks</CardTitle>
            </CardHeader>
            <CardContent>
              {frameworks.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-slate-400 italic">
                  Complete your governance profile to see applicable frameworks.
                </p>
              ) : (
                <div className="space-y-3">
                  {frameworks.map((fw) => (
                    <div
                      key={fw.framework}
                      className="p-3 rounded-lg border border-gray-100 dark:border-slate-800"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900 dark:text-slate-100">
                          {fw.framework}
                        </span>
                        <Badge
                          variant={fw.mandatory ? 'danger' : 'default'}
                        >
                          {fw.mandatory ? 'Mandatory' : 'Recommended'}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-400">
                        {fw.reason}
                      </p>
                      {fw.reference_url && (
                        <a
                          href={fw.reference_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-indigo-600 hover:underline mt-1 inline-flex items-center gap-1"
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
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-500" />
                Governance Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              {forecast ? (
                <div className="space-y-3">
                  <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">
                    {forecast.forecast}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span className="px-2 py-0.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded">
                      {forecast.focus_area}
                    </span>
                    <span>Confidence: {forecast.confidence}</span>
                    {forecast.llm_generated && (
                      <span className="flex items-center gap-1">
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
                  className="w-full p-3 rounded-lg border border-purple-200 dark:border-purple-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors text-sm text-purple-700 dark:text-purple-300 flex items-center justify-center gap-2 disabled:opacity-50"
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

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Links</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link
                to={`/dashboard/audit-calendar?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
              >
                <span className="text-sm text-gray-700 dark:text-slate-300">Audit Calendar</span>
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </Link>
              <Link
                to={`/dashboard/tech-stack?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
              >
                <span className="text-sm text-gray-700 dark:text-slate-300">Tech Stack Registry</span>
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </Link>
              <Link
                to={`/dashboard/pilot-program?org=${selectedOrgId}`}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
              >
                <span className="text-sm text-gray-700 dark:text-slate-300">Pilot Program</span>
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </Link>

              {/* Auditor Link Generator */}
              <div className="pt-3 border-t border-gray-100 dark:border-slate-800">
                <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">Share read-only access with auditors</p>
                {auditorLink ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        readOnly
                        value={auditorLink}
                        className="flex-1 text-xs p-2 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded font-mono"
                      />
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(auditorLink);
                          setAuditorCopied(true);
                          setTimeout(() => setAuditorCopied(false), 2000);
                        }}
                        className="p-2 text-gray-500 hover:text-blue-600 transition"
                        title="Copy link"
                      >
                        {auditorCopied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-400">Expires in 72 hours</p>
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
                    className="flex items-center gap-2 w-full p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors text-sm text-gray-700 dark:text-slate-300"
                  >
                    <Link2 className="w-4 h-4" />
                    Generate Auditor Link
                  </button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
