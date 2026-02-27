/**
 * ComplianceDrift.tsx — Compliance Drift & Shadow AI Dashboard
 *
 * Staging-only page providing:
 *   - Drift Timeline visualization (GHI over time with risk flags)
 *   - Drift Alerts Panel (active signals grouped by category)
 *   - Drift Impact Score (DIS) gauge
 *   - Compliance Sustainability Index (CSI) / Audit Failure Probability
 *   - Shadow AI governance violations
 *   - Baseline management controls
 *
 * Gated: only renders when systemStatus.environment === 'staging'
 */

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  Activity,
  AlertTriangle,
  BarChart3,
  BookmarkCheck,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  FileWarning,
  Gauge,
  RefreshCw,
  Shield,
  ShieldAlert,
  Target,
  TrendingDown,
  TrendingUp,
  XCircle,
  Zap,
} from 'lucide-react';
import {
  getOrganizations,
  createDriftBaseline,
  getDriftAnalysis,
  getDriftTimeline,
  checkShadowAI,
  getSustainabilityIndex,
} from '../api';
import { useDemoMode, useIsReadOnly } from '../contexts';
import type {
  Organization,
  DriftResult,
  DriftSignal,
  DriftTimelineEntry,
  DriftTimelineResponse,
  ShadowAIResponse,
  SustainabilityResponse,
} from '../types';


// ═══════════════════════════════════════════════════════════════════════
// Staging Gate
// ═══════════════════════════════════════════════════════════════════════

function StagingGate({ children }: { children: React.ReactNode }) {
  const { systemStatus, isLoading } = useDemoMode();

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-b-2 border-blue-500 rounded-full" />
      </div>
    );
  }

  if (systemStatus?.environment !== 'staging') {
    return (
      <div className="p-8 text-center">
        <ShieldAlert className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-400">
          Feature Not Available
        </h2>
        <p className="text-gray-500 dark:text-gray-500 mt-2">
          Compliance Drift Detection is only available in staging environments.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}


// ═══════════════════════════════════════════════════════════════════════
// Sub-components
// ═══════════════════════════════════════════════════════════════════════

const BAND_COLORS: Record<string, string> = {
  green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  gray: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800',
  high: 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-800',
  low: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800',
};

const SIGNAL_ICONS: Record<string, React.ReactNode> = {
  control_regression: <TrendingDown className="h-4 w-4" />,
  risk_escalation: <TrendingUp className="h-4 w-4" />,
  sla_breach: <Clock className="h-4 w-4" />,
  evidence_expiry: <FileWarning className="h-4 w-4" />,
  tech_risk: <AlertTriangle className="h-4 w-4" />,
  audit_proximity: <Target className="h-4 w-4" />,
  shadow_ai: <Brain className="h-4 w-4" />,
};

const SIGNAL_LABELS: Record<string, string> = {
  control_regression: 'Control Regression',
  risk_escalation: 'Risk Escalation',
  sla_breach: 'SLA Breach',
  evidence_expiry: 'Evidence Expiry',
  tech_risk: 'Tech Risk Drift',
  audit_proximity: 'Audit Proximity',
  shadow_ai: 'Shadow AI',
};


// ── DIS Gauge ───────────────────────────────────────────────────────

function DISGauge({ score, band, color }: { score: number; band: string; color: string }) {
  const rotation = (score / 100) * 180;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-20 overflow-hidden">
        {/* Background arc */}
        <div className="absolute inset-0 border-8 border-b-0 rounded-t-full border-gray-200 dark:border-gray-700" />
        {/* Filled arc */}
        <div
          className="absolute bottom-0 left-1/2 w-1 h-16 origin-bottom transition-transform duration-1000"
          style={{
            transform: `rotate(${rotation - 90}deg)`,
            backgroundColor: color === 'green' ? '#22c55e' : color === 'yellow' ? '#eab308' : color === 'orange' ? '#f97316' : '#ef4444',
          }}
        />
        {/* Center point */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-gray-600 dark:bg-gray-400" />
      </div>
      <div className="mt-2 text-center">
        <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">{score}</span>
        <span className="text-sm text-gray-500 dark:text-gray-400 ml-1">/ 100</span>
      </div>
      <Badge className={`mt-1 ${BAND_COLORS[color] || BAND_COLORS.gray}`}>
        {band}
      </Badge>
    </div>
  );
}


// ── Drift Timeline ──────────────────────────────────────────────────

function DriftTimeline({ entries }: { entries: DriftTimelineEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 py-8">
        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>No baseline history yet. Create a baseline to start tracking drift.</p>
      </div>
    );
  }

  const maxGhi = Math.max(...entries.map(e => e.ghi), 100);
  const minGhi = Math.min(...entries.map(e => e.ghi), 0);
  const range = maxGhi - minGhi || 1;

  return (
    <div className="space-y-2">
      {/* Chart area */}
      <div className="relative h-48 flex items-end gap-1 px-2">
        {entries.map((entry, idx) => {
          const height = ((entry.ghi - minGhi) / range) * 100;
          const barColor = entry.band_color === 'red' ? 'bg-red-500' :
            entry.band_color === 'orange' ? 'bg-orange-500' :
            entry.band_color === 'yellow' ? 'bg-yellow-500' : 'bg-green-500';

          return (
            <div key={idx} className="flex-1 flex flex-col items-center group relative">
              {/* Tooltip */}
              <div className="hidden group-hover:block absolute bottom-full mb-2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                <div>GHI: {entry.ghi.toFixed(1)}</div>
                <div>Drift: {entry.drift_score.toFixed(1)}</div>
                <div>Signals: {entry.signals_count}</div>
                <div>{new Date(entry.date).toLocaleDateString()}</div>
              </div>
              {/* Red flag for critical */}
              {entry.band_color === 'red' && (
                <div className="text-red-500 mb-1">
                  <AlertTriangle className="h-3 w-3" />
                </div>
              )}
              {/* Bar */}
              <div
                className={`w-full rounded-t ${barColor} transition-all duration-300 min-h-[4px]`}
                style={{ height: `${Math.max(height, 2)}%` }}
              />
            </div>
          );
        })}
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between px-2 text-xs text-gray-500 dark:text-gray-400">
        {entries.length > 0 && (
          <>
            <span>{new Date(entries[0].date).toLocaleDateString()}</span>
            <span>{new Date(entries[entries.length - 1].date).toLocaleDateString()}</span>
          </>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-3 justify-center text-xs">
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-green-500" /> Stable</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-yellow-500" /> Mild</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-orange-500" /> Elevated</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-red-500" /> Critical</span>
      </div>
    </div>
  );
}


// ── Signal Card ─────────────────────────────────────────────────────

function SignalCard({ signal }: { signal: DriftSignal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border rounded-lg p-3 ${SEVERITY_COLORS[signal.severity] || SEVERITY_COLORS.low} cursor-pointer transition-all`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {SIGNAL_ICONS[signal.signal_type] || <AlertTriangle className="h-4 w-4" />}
          <div>
            <span className="font-medium text-sm">{signal.title}</span>
            <Badge className="ml-2 text-xs" variant="outline">
              {signal.severity.toUpperCase()}
            </Badge>
          </div>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 flex-shrink-0" /> : <ChevronDown className="h-4 w-4 flex-shrink-0" />}
      </div>
      {expanded && (
        <div className="mt-2 text-sm opacity-90">
          <p>{signal.description}</p>
          {signal.delta != null && (
            <p className="mt-1 font-mono text-xs">Delta: {signal.delta > 0 ? '+' : ''}{signal.delta.toFixed(1)}</p>
          )}
          <p className="mt-1 text-xs opacity-70">{new Date(signal.detected_at).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════

function ComplianceDriftContent() {
  const [searchParams] = useSearchParams();
  const isReadOnly = useIsReadOnly();

  // State
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [loading, setLoading] = useState(true);
  const [driftResult, setDriftResult] = useState<DriftResult | null>(null);
  const [timeline, setTimeline] = useState<DriftTimelineEntry[]>([]);
  const [shadowAI, setShadowAI] = useState<ShadowAIResponse | null>(null);
  const [sustainability, setSustainability] = useState<SustainabilityResponse | null>(null);
  const [baselineCreating, setBaselineCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'shadow-ai'>('overview');

  // Load orgs
  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      })
      .catch(() => setOrganizations([]))
      .finally(() => setLoading(false));
  }, []);

  // Load drift data when org changes
  useEffect(() => {
    if (!selectedOrgId) return;
    loadDriftData();
  }, [selectedOrgId]);

  const loadDriftData = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);

    try {
      const [driftRes, timelineRes, shadowRes, sustainRes] = await Promise.allSettled([
        getDriftAnalysis(selectedOrgId),
        getDriftTimeline(selectedOrgId),
        checkShadowAI(selectedOrgId),
        getSustainabilityIndex(selectedOrgId),
      ]);

      if (driftRes.status === 'fulfilled') setDriftResult(driftRes.value);
      if (timelineRes.status === 'fulfilled') setTimeline(timelineRes.value.entries);
      if (shadowRes.status === 'fulfilled') setShadowAI(shadowRes.value);
      if (sustainRes.status === 'fulfilled') setSustainability(sustainRes.value);
    } catch (err) {
      setError('Failed to load drift data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBaseline = async () => {
    if (!selectedOrgId || isReadOnly) return;
    setBaselineCreating(true);
    try {
      await createDriftBaseline(selectedOrgId);
      await loadDriftData();
    } catch {
      setError('Failed to create baseline');
    } finally {
      setBaselineCreating(false);
    }
  };

  // Group signals by type
  const signalsByType = useMemo(() => {
    if (!driftResult?.signals) return {};
    const grouped: Record<string, DriftSignal[]> = {};
    for (const signal of driftResult.signals) {
      const key = signal.signal_type;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(signal);
    }
    return grouped;
  }, [driftResult]);

  // Merge shadow AI signals
  const allSignals = useMemo(() => {
    const signals = [...(driftResult?.signals || [])];
    if (shadowAI?.shadow_ai_signals) {
      signals.push(...shadowAI.shadow_ai_signals);
    }
    return signals;
  }, [driftResult, shadowAI]);

  const criticalCount = allSignals.filter(s => s.severity === 'critical').length;
  const highCount = allSignals.filter(s => s.severity === 'high').length;

  if (loading && organizations.length === 0) {
    return <div className="space-y-4 p-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Activity className="h-7 w-7 text-blue-500" />
            Compliance Drift Detection
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Continuous Control Integrity Monitoring — track posture deviation over time
          </p>
        </div>

        {/* Staging badge */}
        <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border border-purple-300">
          <Zap className="h-3 w-3 mr-1" />
          STAGING ONLY
        </Badge>
      </div>

      {/* Org selector + baseline button */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Organization
              </label>
              <select
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
              >
                <option value="">Select organization...</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 mt-5">
              <Button
                onClick={handleCreateBaseline}
                disabled={!selectedOrgId || baselineCreating || isReadOnly}
                className="flex items-center gap-1"
              >
                <BookmarkCheck className="h-4 w-4" />
                {baselineCreating ? 'Creating...' : 'Create Baseline'}
              </Button>
              <Button
                onClick={loadDriftData}
                disabled={!selectedOrgId || loading}
                variant="outline"
                className="flex items-center gap-1"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-800 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Summary Cards Row */}
      {driftResult && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* DIS Card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Gauge className="h-4 w-4" />
                Drift Impact Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DISGauge
                score={driftResult.drift_impact_score}
                band={driftResult.drift_band}
                color={driftResult.drift_band_color}
              />
            </CardContent>
          </Card>

          {/* GHI Delta */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Activity className="h-4 w-4" />
                GHI Change
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {driftResult.current_ghi.toFixed(1)}
              </div>
              <div className={`text-sm font-medium mt-1 ${
                driftResult.ghi_delta > 0 ? 'text-green-600' : driftResult.ghi_delta < 0 ? 'text-red-600' : 'text-gray-500'
              }`}>
                {driftResult.ghi_delta > 0 ? '+' : ''}{driftResult.ghi_delta.toFixed(1)} from baseline
              </div>
              {driftResult.baseline_date && (
                <div className="text-xs text-gray-400 mt-1">
                  Baseline: {new Date(driftResult.baseline_date).toLocaleDateString()}
                </div>
              )}
            </CardContent>
          </Card>

          {/* CSI */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Shield className="h-4 w-4" />
                Sustainability Index
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              {sustainability ? (
                <>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {sustainability.compliance_sustainability_index.toFixed(0)}
                  </div>
                  <Badge className={`mt-1 ${
                    sustainability.csi_band === 'Excellent' ? 'bg-green-100 text-green-700' :
                    sustainability.csi_band === 'Good' ? 'bg-blue-100 text-blue-700' :
                    sustainability.csi_band === 'Fair' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {sustainability.csi_band}
                  </Badge>
                </>
              ) : <span className="text-gray-400">—</span>}
            </CardContent>
          </Card>

          {/* Audit Failure Probability */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Target className="h-4 w-4" />
                Audit Failure Probability
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              {sustainability ? (
                <>
                  <div className={`text-3xl font-bold ${
                    sustainability.audit_failure_probability <= 20 ? 'text-green-600' :
                    sustainability.audit_failure_probability <= 50 ? 'text-yellow-600' :
                    sustainability.audit_failure_probability <= 75 ? 'text-orange-600' :
                    'text-red-600'
                  }`}>
                    {sustainability.audit_failure_probability.toFixed(0)}%
                  </div>
                  <Badge className={`mt-1 ${
                    sustainability.afp_band === 'Low Risk' ? 'bg-green-100 text-green-700' :
                    sustainability.afp_band === 'Moderate' ? 'bg-yellow-100 text-yellow-700' :
                    sustainability.afp_band === 'High Risk' ? 'bg-orange-100 text-orange-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {sustainability.afp_band}
                  </Badge>
                </>
              ) : <span className="text-gray-400">—</span>}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alert Summary Banner */}
      {(criticalCount > 0 || highCount > 0) && (
        <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
          <ShieldAlert className="h-6 w-6 text-red-600 flex-shrink-0" />
          <div>
            <span className="font-semibold text-red-800 dark:text-red-300">
              {criticalCount + highCount} Active Alert{criticalCount + highCount !== 1 ? 's' : ''}
            </span>
            <span className="text-red-600 dark:text-red-400 text-sm ml-2">
              {criticalCount > 0 && `${criticalCount} Critical`}
              {criticalCount > 0 && highCount > 0 && ' · '}
              {highCount > 0 && `${highCount} High`}
            </span>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-4">
          {[
            { key: 'overview', label: 'Overview', icon: <BarChart3 className="h-4 w-4" /> },
            { key: 'signals', label: `Drift Signals (${allSignals.length})`, icon: <AlertTriangle className="h-4 w-4" /> },
            { key: 'shadow-ai', label: `Shadow AI (${shadowAI?.count || 0})`, icon: <Brain className="h-4 w-4" /> },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as typeof activeTab)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Drift Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                Drift Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DriftTimeline entries={timeline} />
            </CardContent>
          </Card>

          {/* Signal Summary by Category */}
          {driftResult && Object.keys(driftResult.signal_counts).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-purple-500" />
                  Drift Signal Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(driftResult.signal_counts).map(([type, count]) => (
                    <div key={type} className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                      <div className="flex justify-center mb-1 text-gray-600 dark:text-gray-400">
                        {SIGNAL_ICONS[type]}
                      </div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{count}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{SIGNAL_LABELS[type] || type}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Forecast summary */}
          {driftResult?.forecast_summary && (
            <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-sm text-blue-800 dark:text-blue-300">
              <strong>Forecast:</strong> {driftResult.forecast_summary}
            </div>
          )}
        </div>
      )}

      {activeTab === 'signals' && (
        <div className="space-y-3">
          {allSignals.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-green-500" />
              <p className="text-lg font-medium">No Drift Signals Detected</p>
              <p className="text-sm mt-1">Your compliance posture is stable relative to baseline.</p>
            </div>
          ) : (
            <>
              {/* Group by type */}
              {Object.entries(
                allSignals.reduce<Record<string, DriftSignal[]>>((acc, s) => {
                  const key = s.signal_type;
                  if (!acc[key]) acc[key] = [];
                  acc[key].push(s);
                  return acc;
                }, {})
              ).map(([type, signals]) => (
                <div key={type}>
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                    {SIGNAL_ICONS[type]}
                    {SIGNAL_LABELS[type] || type}
                    <Badge variant="outline" className="text-xs">{signals.length}</Badge>
                  </h3>
                  <div className="space-y-2 mb-4">
                    {signals.map((signal, idx) => (
                      <SignalCard key={`${type}-${idx}`} signal={signal} />
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {activeTab === 'shadow-ai' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-500" />
                Shadow AI Governance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Detects unsanctioned AI models in the tech stack. Models with HIGH data sensitivity
                and UNSANCTIONED tier generate CRITICAL governance violations.
              </p>

              {shadowAI && shadowAI.count > 0 ? (
                <div className="space-y-3">
                  {shadowAI.has_critical && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2">
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="text-red-800 dark:text-red-300 font-semibold">
                        CRITICAL: Unsanctioned AI processing sensitive data detected
                      </span>
                    </div>
                  )}
                  {shadowAI.shadow_ai_signals.map((signal, idx) => (
                    <SignalCard key={idx} signal={signal} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-green-500" />
                  <p className="text-lg font-medium">No Shadow AI Violations</p>
                  <p className="text-sm mt-1">
                    All AI models in the tech stack are properly classified.
                    Add items with category &quot;AI Model&quot; to enable governance checks.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Model Tier Reference */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">AI Model Governance Tiers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                  <div className="font-semibold text-green-800 dark:text-green-300">Sanctioned</div>
                  <p className="text-green-700 dark:text-green-400 text-xs mt-1">Approved for production — vetted by security team</p>
                </div>
                <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
                  <div className="font-semibold text-yellow-800 dark:text-yellow-300">Conditional</div>
                  <p className="text-yellow-700 dark:text-yellow-400 text-xs mt-1">Approved with restrictions — requires data classification review</p>
                </div>
                <div className="p-3 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800">
                  <div className="font-semibold text-orange-800 dark:text-orange-300">Unsanctioned</div>
                  <p className="text-orange-700 dark:text-orange-400 text-xs mt-1">Not approved — requires security review before deployment</p>
                </div>
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <div className="font-semibold text-red-800 dark:text-red-300">Banned</div>
                  <p className="text-red-700 dark:text-red-400 text-xs mt-1">Explicitly prohibited — violates organizational policy</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Export — wrapped with staging gate
// ═══════════════════════════════════════════════════════════════════════

export default function ComplianceDrift() {
  return (
    <StagingGate>
      <ComplianceDriftContent />
    </StagingGate>
  );
}
