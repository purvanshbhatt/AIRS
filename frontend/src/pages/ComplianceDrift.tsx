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
import { motion } from 'framer-motion';
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
          className="absolute bottom-0 left-1/2 w-1.5 h-16 origin-bottom transition-transform duration-1000"
          style={{
            transform: `rotate(${rotation - 90}deg)`,
            backgroundColor: color === 'green' ? '#10b981' : color === 'yellow' ? '#f59e0b' : color === 'orange' ? '#f97316' : '#ef4444',
          }}
        />
        {/* Center point */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-slate-600 dark:bg-slate-400 border border-white dark:border-slate-900 shadow-sm" />
      </div>
      <div className="mt-2 text-center">
        <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">{score}</span>
        <span className="text-sm text-slate-500 dark:text-slate-400 ml-1">/ 105</span>
      </div>
      <span className={`mt-1.5 ${BAND_COLORS[color] || BAND_COLORS.gray}`}>
        {band}
      </span>
    </div>
  );
}


// ── Drift Timeline ──────────────────────────────────────────────────

function DriftTimeline({ entries }: { entries: DriftTimelineEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className="text-center text-slate-500 dark:text-slate-400 py-12">
        <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-40 text-slate-400" />
        <p className="font-semibold">No baseline history yet. Create a baseline to start tracking drift.</p>
      </div>
    );
  }

  const maxGhi = Math.max(...entries.map(e => e.ghi), 100);
  const minGhi = Math.min(...entries.map(e => e.ghi), 0);
  const range = maxGhi - minGhi || 1;

  return (
    <div className="space-y-4">
      {/* Chart area */}
      <div className="relative h-48 flex items-end gap-1.5 px-2">
        {entries.map((entry, idx) => {
          const height = ((entry.ghi - minGhi) / range) * 100;
          const barColor = entry.band_color === 'red' ? 'bg-red-500' :
            entry.band_color === 'orange' ? 'bg-orange-500' :
            entry.band_color === 'yellow' ? 'bg-amber-500' : 'bg-green-500';

          return (
            <div key={idx} className="flex-1 flex flex-col items-center group relative">
              {/* Tooltip */}
              <div className="hidden group-hover:block absolute bottom-full mb-3 bg-slate-900 dark:bg-slate-950 text-slate-100 dark:text-slate-200 text-xs rounded-xl shadow-lg border border-slate-700/50 p-2.5 whitespace-nowrap z-10">
                <div className="font-bold text-slate-200">GHI: {entry.ghi.toFixed(1)}</div>
                <div className="font-medium mt-0.5">Drift: {entry.drift_score.toFixed(1)}</div>
                <div className="font-medium">Signals: {entry.signals_count}</div>
                <div className="text-[10px] text-slate-400 mt-1 font-semibold">{new Date(entry.date).toLocaleDateString()}</div>
              </div>
              {/* Red flag for critical */}
              {entry.band_color === 'red' && (
                <div className="text-red-500 mb-1 animate-bounce">
                  <AlertTriangle className="h-3.5 w-3.5" />
                </div>
              )}
              {/* Bar */}
              <div
                className={`w-full rounded-t-lg ${barColor} transition-all duration-300 hover:brightness-110 min-h-[6px]`}
                style={{ height: `${Math.max(height, 3)}%` }}
              />
            </div>
          );
        })}
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between px-2 text-xs font-semibold text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800/60 pt-2">
        {entries.length > 0 && (
          <>
            <span>{new Date(entries[0].date).toLocaleDateString()}</span>
            <span>{new Date(entries[entries.length - 1].date).toLocaleDateString()}</span>
          </>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-4 justify-center text-xs font-semibold text-slate-600 dark:text-slate-400">
        <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-green-500" /> Stable</span>
        <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-amber-500" /> Mild</span>
        <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-orange-500" /> Elevated</span>
        <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500" /> Critical</span>
      </div>
    </div>
  );
}


// ── Signal Card ─────────────────────────────────────────────────────

function SignalCard({ signal }: { signal: DriftSignal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border rounded-2xl p-4 ${SEVERITY_COLORS[signal.severity] || SEVERITY_COLORS.low} cursor-pointer transition-all duration-300 hover:scale-[1.005] hover:shadow-md`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1 rounded-lg bg-white/40 dark:bg-black/10">
            {SIGNAL_ICONS[signal.signal_type] || <AlertTriangle className="h-4 w-4" />}
          </div>
          <div>
            <span className="font-bold text-sm tracking-wide">{signal.title}</span>
            <Badge className="ml-2.5 text-xs font-bold" variant="outline">
              {signal.severity.toUpperCase()}
            </Badge>
          </div>
        </div>
        {expanded ? <ChevronUp className="h-4.5 w-4.5 flex-shrink-0" /> : <ChevronDown className="h-4.5 w-4.5 flex-shrink-0" />}
      </div>
      {expanded && (
        <div className="mt-3.5 text-sm leading-relaxed opacity-95 pl-7 border-t border-slate-200/40 dark:border-slate-800/40 pt-2 transition-all duration-300">
          <p className="font-medium">{signal.description}</p>
          {signal.delta != null && (
            <p className="mt-1.5 font-mono text-xs font-semibold opacity-75">Delta: {signal.delta > 0 ? '+' : ''}{signal.delta.toFixed(1)}</p>
          )}
          <p className="mt-2 text-xs font-medium opacity-60">{new Date(signal.detected_at).toLocaleString()}</p>
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
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-4 p-4"
      >
        <CardSkeleton />
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
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Activity className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
            Compliance Drift Detection
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-medium">
            Continuous Control Integrity Monitoring — track posture deviation over time
          </p>
        </div>

        {/* Staging badge */}
        <span className="inline-flex items-center gap-1.5 bg-purple-55/10 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800/40 rounded-xl px-3 py-1.5 text-xs font-bold shadow-sm">
          <Zap className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
          STAGING ONLY
        </span>
      </div>

      {/* Org selector + baseline button */}
      <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
        <CardContent className="p-5">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                Organization
              </label>
              <select
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all font-semibold"
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
              >
                <option value="" className="text-slate-500">Select organization...</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-2.5 mt-5">
              <Button
                onClick={handleCreateBaseline}
                disabled={!selectedOrgId || baselineCreating || isReadOnly}
                className="flex items-center gap-1.5 rounded-xl transition-all duration-205 hover:scale-[1.01] shadow-sm hover:shadow-md font-bold"
              >
                <BookmarkCheck className="h-4 w-4" />
                {baselineCreating ? 'Creating...' : 'Create Baseline'}
              </Button>
              <Button
                onClick={loadDriftData}
                disabled={!selectedOrgId || loading}
                variant="outline"
                className="flex items-center gap-1.5 rounded-xl border-slate-200 dark:border-slate-800 transition-all duration-200 hover:bg-slate-50 dark:hover:bg-slate-900/30 hover:scale-[1.01] font-bold text-slate-700 dark:text-slate-300"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-50/20 dark:bg-red-950/10 border border-red-200 dark:border-red-900/40 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm font-semibold shadow-sm transition-all duration-300">
          {error}
        </div>
      )}

      {/* Summary Cards Row */}
      {driftResult && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* DIS Card */}
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Gauge className="h-4 w-4 text-slate-400" />
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
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="h-4 w-4 text-slate-400" />
                GHI Change
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                {driftResult.current_ghi.toFixed(1)}
              </div>
              <div className={`text-sm font-bold mt-1.5 ${
                driftResult.ghi_delta > 0 ? 'text-green-600 dark:text-green-400' : driftResult.ghi_delta < 0 ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'
              }`}>
                {driftResult.ghi_delta > 0 ? '+' : ''}{driftResult.ghi_delta.toFixed(1)} from baseline
              </div>
              {driftResult.baseline_date && (
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-2">
                  Baseline: {new Date(driftResult.baseline_date).toLocaleDateString()}
                </div>
              )}
            </CardContent>
          </Card>

          {/* CSI */}
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Shield className="h-4 w-4 text-slate-400" />
                Sustainability Index
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              {sustainability ? (
                <>
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                    {sustainability.compliance_sustainability_index.toFixed(0)}
                  </div>
                  <span className={`inline-block mt-2.5 ${
                    sustainability.csi_band === 'Excellent' ? 'bg-green-55/10 text-green-800 border border-green-200 dark:bg-green-950/30 dark:text-green-300 dark:border-green-800/40' :
                    sustainability.csi_band === 'Good' ? 'bg-blue-50/10 text-blue-800 border border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-800/40' :
                    sustainability.csi_band === 'Fair' ? 'bg-yellow-55/10 text-yellow-800 border border-yellow-200 dark:bg-yellow-950/30 dark:text-yellow-300 dark:border-yellow-800/40' :
                    'bg-red-50/10 text-red-800 border border-red-200 dark:bg-red-950/20 dark:text-red-300 dark:border-red-800/40'
                  } font-bold text-xs px-2.5 py-1.5 rounded-xl`}>
                    {sustainability.csi_band}
                  </span>
                </>
              ) : <span className="text-slate-400 dark:text-slate-600 font-semibold">—</span>}
            </CardContent>
          </Card>

          {/* Audit Failure Probability */}
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="h-4 w-4 text-slate-400" />
                Audit Failure Probability
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              {sustainability ? (
                <>
                  <div className={`text-3xl font-extrabold ${
                    sustainability.audit_failure_probability <= 20 ? 'text-green-600 dark:text-green-400' :
                    sustainability.audit_failure_probability <= 50 ? 'text-yellow-600 dark:text-yellow-400' :
                    sustainability.audit_failure_probability <= 75 ? 'text-orange-600 dark:text-orange-400' :
                    'text-red-600 dark:text-red-400'
                  }`}>
                    {sustainability.audit_failure_probability.toFixed(0)}%
                  </div>
                  <span className={`inline-block mt-2.5 ${
                    sustainability.afp_band === 'Low Risk' ? 'bg-green-55/10 text-green-800 border border-green-200 dark:bg-green-950/30 dark:text-green-300 dark:border-green-800/40' :
                    sustainability.afp_band === 'Moderate' ? 'bg-yellow-55/10 text-yellow-800 border border-yellow-200 dark:bg-yellow-950/30 dark:text-yellow-300 dark:border-yellow-800/40' :
                    sustainability.afp_band === 'High Risk' ? 'bg-orange-55/10 text-orange-800 border border-orange-200 dark:bg-orange-950/30 dark:text-orange-300 dark:border-orange-800/40' :
                    'bg-red-50/10 text-red-800 border border-red-200 dark:bg-red-950/20 dark:text-red-300 dark:border-red-800/40'
                  } font-bold text-xs px-2.5 py-1.5 rounded-xl`}>
                    {sustainability.afp_band}
                  </span>
                </>
              ) : <span className="text-slate-400 dark:text-slate-600 font-semibold">—</span>}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alert Summary Banner */}
      {(criticalCount > 0 || highCount > 0) && (
        <div className="bg-red-50/20 dark:bg-red-950/10 border border-red-200 dark:border-red-900/40 rounded-2xl p-4 flex items-center gap-3 shadow-sm transition-all duration-300">
          <ShieldAlert className="h-6 w-6 text-red-600 dark:text-red-400 flex-shrink-0" />
          <div>
            <span className="font-extrabold text-red-900 dark:text-red-300">
              {criticalCount + highCount} Active Alert{criticalCount + highCount !== 1 ? 's' : ''}
            </span>
            <span className="text-red-750 dark:text-red-400 text-sm ml-2.5 font-bold">
              {criticalCount > 0 && `${criticalCount} Critical`}
              {criticalCount > 0 && highCount > 0 && ' · '}
              {highCount > 0 && `${highCount} High`}
            </span>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-800/80">
        <nav className="flex space-x-4">
          {[
            { key: 'overview', label: 'Overview', icon: <BarChart3 className="h-4 w-4" /> },
            { key: 'signals', label: `Drift Signals (${allSignals.length})`, icon: <AlertTriangle className="h-4 w-4" /> },
            { key: 'shadow-ai', label: `Shadow AI (${shadowAI?.count || 0})`, icon: <Brain className="h-4 w-4" /> },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as typeof activeTab)}
              className={`flex items-center gap-1.5 px-3.5 py-3 text-sm font-bold border-b-2 transition-all duration-200 ${
                activeTab === tab.key
                  ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
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
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-slate-100 text-lg font-bold">
                <BarChart3 className="h-5 w-5 text-indigo-605" />
                Drift Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DriftTimeline entries={timeline} />
            </CardContent>
          </Card>

          {/* Signal Summary by Category */}
          {driftResult && Object.keys(driftResult.signal_counts).length > 0 && (
            <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-slate-100 text-lg font-bold">
                  <Activity className="h-5 w-5 text-purple-600" />
                  Drift Signal Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(driftResult.signal_counts).map(([type, count]) => (
                    <div key={type} className="text-center p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800/40 hover:scale-[1.02] transition-transform duration-200">
                      <div className="flex justify-center mb-1.5 text-slate-400 dark:text-slate-500">
                        {SIGNAL_ICONS[type]}
                      </div>
                      <div className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">{count}</div>
                      <div className="text-xs font-bold text-slate-500 dark:text-slate-400 mt-1">{SIGNAL_LABELS[type] || type}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Forecast summary */}
          {driftResult?.forecast_summary && (
            <div className="bg-indigo-50/20 dark:bg-indigo-950/10 border border-indigo-200 dark:border-indigo-900/40 rounded-2xl p-4 text-sm font-semibold text-indigo-950 dark:text-indigo-300 shadow-sm transition-all duration-300">
              <strong className="text-indigo-700 dark:text-indigo-400">Forecast:</strong> {driftResult.forecast_summary}
            </div>
          )}
        </div>
      )}

      {activeTab === 'signals' && (
        <div className="space-y-4">
          {allSignals.length === 0 ? (
            <div className="text-center py-16 text-slate-500 dark:text-slate-400">
              <CheckCircle2 className="h-16 w-16 mx-auto mb-4 text-green-500 opacity-80" />
              <p className="text-lg font-bold text-slate-800 dark:text-slate-100">No Drift Signals Detected</p>
              <p className="text-sm mt-1 font-medium">Your compliance posture is stable relative to baseline.</p>
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
                <div key={type} className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                    {SIGNAL_ICONS[type]}
                    {SIGNAL_LABELS[type] || type}
                    <span className="ml-1 px-2.5 py-0.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                      {signals.length}
                    </span>
                  </h3>
                  <div className="space-y-3 mb-5">
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
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-slate-155 text-lg font-bold">
                <Brain className="h-5 w-5 text-purple-600" />
                Shadow AI Governance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 leading-relaxed font-semibold">
                Detects unsanctioned AI models in the tech stack. Models with HIGH data sensitivity
                and UNSANCTIONED tier generate CRITICAL governance violations.
              </p>

              {shadowAI && shadowAI.count > 0 ? (
                <div className="space-y-3">
                  {shadowAI.has_critical && (
                    <div className="bg-red-50/20 dark:bg-red-950/10 border border-red-200 dark:border-red-900/40 rounded-2xl p-4 flex items-center gap-2.5 shadow-sm">
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="text-red-900 dark:text-red-300 font-extrabold">
                        CRITICAL: Unsanctioned AI processing sensitive data detected
                      </span>
                    </div>
                  )}
                  {shadowAI.shadow_ai_signals.map((signal, idx) => (
                    <SignalCard key={idx} signal={signal} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                  <CheckCircle2 className="h-16 w-16 mx-auto mb-4 text-green-500 opacity-80" />
                  <p className="text-lg font-bold text-slate-800 dark:text-slate-100">No Shadow AI Violations</p>
                  <p className="text-sm mt-1 font-medium">
                    All AI models in the tech stack are properly classified.
                    Add items with category &quot;AI Model&quot; to enable governance checks.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Model Tier Reference */}
          <Card className="shadow-sm bg-white/60 dark:bg-slate-950/20 transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700">
            <CardHeader>
              <CardTitle className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">AI Model Governance Tiers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-semibold">
                <div className="p-4 rounded-2xl bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/50 hover:scale-[1.01] transition-transform duration-200">
                  <div className="font-extrabold text-green-900 dark:text-green-300">Sanctioned</div>
                  <p className="text-green-700 dark:text-green-400 text-xs mt-1.5 leading-relaxed font-bold">Approved for production — vetted by security team</p>
                </div>
                <div className="p-4 rounded-2xl bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900/50 hover:scale-[1.01] transition-transform duration-200">
                  <div className="font-extrabold text-yellow-900 dark:text-yellow-300">Conditional</div>
                  <p className="text-yellow-700 dark:text-yellow-400 text-xs mt-1.5 leading-relaxed font-bold">Approved with restrictions — requires data classification review</p>
                </div>
                <div className="p-4 rounded-2xl bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900/50 hover:scale-[1.01] transition-transform duration-200">
                  <div className="font-extrabold text-orange-900 dark:text-orange-300">Unsanctioned</div>
                  <p className="text-orange-700 dark:text-orange-400 text-xs mt-1.5 leading-relaxed font-bold">Not approved — requires security review before deployment</p>
                </div>
                <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 hover:scale-[1.01] transition-transform duration-200">
                  <div className="font-extrabold text-red-900 dark:text-red-300">Banned</div>
                  <p className="text-red-700 dark:text-red-400 text-xs mt-1.5 leading-relaxed font-bold">Explicitly prohibited — violates organizational policy</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </motion.div>
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
