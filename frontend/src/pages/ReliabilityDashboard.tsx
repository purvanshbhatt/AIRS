/**
 * ReliabilityDashboard.tsx — Reliability Risk Index (RRI) Dashboard
 *
 * Staging-only page providing:
 *   - RRI Score gauge with risk band visualization
 *   - Five-dimension breakdown (SLA, Recovery, Redundancy, Monitoring, BCDR)
 *   - Architecture Alignment badge (🟢/🟡/🔴)
 *   - Live Downtime Budget Visualization (monthly/annual)
 *   - Smart SLA Advisor with industry-aware recommendations
 *   - Board Simulation Mode ("What if we upgrade SLA?")
 *   - Top Gaps action list
 *
 * Gated: only renders when systemStatus.environment === 'staging'
 */

import { useState, useEffect, useCallback } from 'react';
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
  ArrowDown,
  ArrowUp,
  BarChart3,
  CheckCircle2,
  Clock,
  Gauge,
  Lightbulb,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Target,
  TrendingDown,
  TrendingUp,
  XCircle,
  Zap,
} from 'lucide-react';
import {
  getOrganizations,
  getReliabilityIndex,
  simulateReliability,
  getSlaAdvisor,
  getDowntimeBudget,
} from '../api';
import { useDemoMode } from '../contexts';
import type {
  Organization,
  RRIResponse,
  RRIDimension,
  DowntimeBudget,
  SLAAdvisor,
  BreachSimulationResponse,
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
          Reliability Risk Index is only available in staging environments.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}


// ═══════════════════════════════════════════════════════════════════════
// Helper: risk-band color classes
// ═══════════════════════════════════════════════════════════════════════

function riskBandColor(band: string): string {
  switch (band) {
    case 'Low': return 'text-green-600 dark:text-green-400';
    case 'Moderate': return 'text-yellow-600 dark:text-yellow-400';
    case 'High': return 'text-orange-600 dark:text-orange-400';
    case 'Critical': return 'text-red-600 dark:text-red-400';
    default: return 'text-gray-600 dark:text-gray-400';
  }
}

function riskBandBg(band: string): string {
  switch (band) {
    case 'Low': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
    case 'Moderate': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300';
    case 'High': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300';
    case 'Critical': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
    default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-300';
  }
}

function alignmentBadge(alignment: string) {
  switch (alignment) {
    case 'aligned':
      return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" /> Aligned</Badge>;
    case 'partial':
      return <Badge variant="warning"><AlertTriangle className="h-3 w-3 mr-1" /> Partial</Badge>;
    case 'high_risk':
      return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" /> High Risk</Badge>;
    default:
      return <Badge variant="outline">Unknown</Badge>;
  }
}

function scoreColor(score: number): string {
  if (score <= 25) return 'text-green-600 dark:text-green-400';
  if (score <= 50) return 'text-yellow-600 dark:text-yellow-400';
  if (score <= 75) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
}

function scoreBarColor(score: number): string {
  if (score <= 25) return 'bg-green-500';
  if (score <= 50) return 'bg-yellow-500';
  if (score <= 75) return 'bg-orange-500';
  return 'bg-red-500';
}

function confidenceBadge(confidence: string) {
  switch (confidence) {
    case 'high':
      return <Badge variant="success">High Confidence</Badge>;
    case 'medium':
      return <Badge variant="warning">Medium Confidence</Badge>;
    case 'low':
      return <Badge variant="outline">Low Confidence</Badge>;
    default:
      return <Badge variant="outline">{confidence}</Badge>;
  }
}


// ═══════════════════════════════════════════════════════════════════════
// RRI Score Gauge
// ═══════════════════════════════════════════════════════════════════════

function RRIScoreGauge({ rri }: { rri: RRIResponse }) {
  const circumference = 2 * Math.PI * 60;
  const progress = (rri.rri_score / 100) * circumference;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Gauge className="h-5 w-5" />
          Reliability Risk Index™
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-8">
          {/* Circular gauge */}
          <div className="relative flex-shrink-0">
            <svg width="150" height="150" viewBox="0 0 150 150">
              <circle
                cx="75" cy="75" r="60"
                fill="none"
                stroke="currentColor"
                className="text-gray-200 dark:text-gray-700"
                strokeWidth="12"
              />
              <circle
                cx="75" cy="75" r="60"
                fill="none"
                stroke="currentColor"
                className={scoreColor(rri.rri_score)}
                strokeWidth="12"
                strokeDasharray={circumference}
                strokeDashoffset={circumference - progress}
                strokeLinecap="round"
                transform="rotate(-90 75 75)"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-3xl font-bold ${scoreColor(rri.rri_score)}`}>
                {rri.rri_score.toFixed(1)}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">/ 100</span>
            </div>
          </div>

          {/* Score details */}
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Risk Band:</span>
              <span className={`text-lg font-semibold ${riskBandColor(rri.risk_band)}`}>
                {rri.risk_band}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Breach Probability:</span>
              <span className={`font-medium ${riskBandBg(rri.breach_probability)} px-2 py-0.5 rounded text-sm`}>
                {rri.breach_probability}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Application Tier:</span>
              <Badge variant="outline">{rri.application_tier.replace('_', ' ').toUpperCase()}</Badge>
              <span className="text-xs text-gray-400">×{rri.tier_multiplier.toFixed(2)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Architecture:</span>
              {alignmentBadge(rri.architecture_alignment)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Dimension Breakdown
// ═══════════════════════════════════════════════════════════════════════

function DimensionBreakdown({ dimensions }: { dimensions: RRIDimension[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Dimension Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {dimensions.map((dim) => (
          <div key={dim.key} className="space-y-1">
            <button
              onClick={() => setExpanded(expanded === dim.key ? null : dim.key)}
              className="w-full flex items-center justify-between text-left"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {dim.name}
                </span>
                <span className="text-xs text-gray-400">
                  (×{dim.weight.toFixed(2)})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${scoreColor(dim.score)}`}>
                  {dim.score.toFixed(0)}
                </span>
                <span className="text-xs text-gray-400">
                  → {dim.weighted_score.toFixed(1)}
                </span>
              </div>
            </button>

            {/* Progress bar */}
            <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${scoreBarColor(dim.score)}`}
                style={{ width: `${Math.min(dim.score, 100)}%` }}
              />
            </div>

            {/* Expanded details */}
            {expanded === dim.key && (
              <div className="mt-2 ml-2 space-y-2 text-sm">
                {dim.signals.length > 0 && (
                  <div>
                    <p className="font-medium text-gray-600 dark:text-gray-400 mb-1">Signals:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      {dim.signals.map((s, i) => (
                        <li key={i} className="text-gray-500 dark:text-gray-400">{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {dim.gaps.length > 0 && (
                  <div>
                    <p className="font-medium text-orange-600 dark:text-orange-400 mb-1">Gaps:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      {dim.gaps.map((g, i) => (
                        <li key={i} className="text-orange-500 dark:text-orange-400">{g}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Downtime Budget Visualization
// ═══════════════════════════════════════════════════════════════════════

function DowntimeBudgetCard({ budget }: { budget: DowntimeBudget }) {
  const usedPercent = Math.min(100, (budget.monthly_minutes / budget.annual_minutes) * 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Downtime Budget
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
              {budget.annual_display}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Annual Budget</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              ({budget.annual_minutes.toFixed(2)} min)
            </p>
          </div>
          <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
              {budget.monthly_display}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Monthly Budget</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              ({budget.monthly_minutes.toFixed(2)} min)
            </p>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>SLA Target: {budget.sla_target}%</span>
            <span>{(100 - budget.sla_target).toFixed(4)}% downtime allowed</span>
          </div>
          <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-full transition-all"
              style={{ width: `${usedPercent}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Smart SLA Advisor
// ═══════════════════════════════════════════════════════════════════════

function SLAAdvisorCard({ advisor }: { advisor: SLAAdvisor }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Smart SLA Advisor
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">Recommended Tier</span>
          <Badge variant="outline" className="text-base font-semibold">
            {advisor.recommended_tier}
          </Badge>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">SLA Range</span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {advisor.sla_range[0]}% – {advisor.sla_range[1]}%
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">Industry</span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
            {advisor.industry}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">Confidence</span>
          {confidenceBadge(advisor.confidence)}
        </div>
        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <Lightbulb className="h-4 w-4 inline mr-1" />
            {advisor.rationale}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Top Gaps
// ═══════════════════════════════════════════════════════════════════════

function TopGapsCard({ gaps }: { gaps: string[] }) {
  if (gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Top Gaps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 className="h-5 w-5" />
            <span className="text-sm">No critical gaps identified</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Top Gaps
          <Badge variant="destructive" className="ml-auto">{gaps.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {gaps.map((gap, i) => (
            <li key={i} className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-700 dark:text-gray-300">{gap}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Board Simulation Mode
// ═══════════════════════════════════════════════════════════════════════

function BoardSimulation({
  orgId,
  currentSla,
}: {
  orgId: string;
  currentSla: number | null;
}) {
  const [simSla, setSimSla] = useState(currentSla ?? 99.9);
  const [result, setResult] = useState<BreachSimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await simulateReliability(orgId, simSla);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setLoading(false);
    }
  }, [orgId, simSla]);

  const SLA_PRESETS = [99.0, 99.5, 99.9, 99.95, 99.99, 99.999];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sliders className="h-5 w-5" />
          Board Simulation Mode
          <Badge variant="outline" className="ml-2">What If?</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Simulate the impact of changing your SLA target on downtime budget, required improvements, and reliability readiness.
        </p>

        {/* SLA Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <label className="font-medium text-gray-700 dark:text-gray-300">
              Simulated SLA Target
            </label>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {simSla.toFixed(3)}%
            </span>
          </div>
          <input
            type="range"
            min="95"
            max="99.999"
            step="0.001"
            value={simSla}
            onChange={(e) => setSimSla(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex flex-wrap gap-1">
            {SLA_PRESETS.map((preset) => (
              <button
                key={preset}
                onClick={() => setSimSla(preset)}
                className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                  Math.abs(simSla - preset) < 0.001
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                {preset}%
              </button>
            ))}
          </div>
        </div>

        <Button onClick={runSimulation} disabled={loading} className="w-full">
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Zap className="h-4 w-4 mr-2" />
          )}
          Run Simulation
        </Button>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Simulation Results */}
        {result && (
          <div className="space-y-4 border-t pt-4 dark:border-gray-700">
            {/* Delta banner */}
            <div className={`p-3 rounded-lg flex items-center gap-3 ${
              result.readiness_delta < 0
                ? 'bg-green-50 dark:bg-green-900/20'
                : result.readiness_delta > 0
                ? 'bg-red-50 dark:bg-red-900/20'
                : 'bg-gray-50 dark:bg-gray-800'
            }`}>
              {result.readiness_delta < 0 ? (
                <ArrowDown className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : result.readiness_delta > 0 ? (
                <ArrowUp className="h-5 w-5 text-red-600 dark:text-red-400" />
              ) : (
                <Activity className="h-5 w-5 text-gray-400" />
              )}
              <div>
                <p className={`font-bold ${
                  result.readiness_delta < 0
                    ? 'text-green-700 dark:text-green-300'
                    : result.readiness_delta > 0
                    ? 'text-red-700 dark:text-red-300'
                    : 'text-gray-700 dark:text-gray-300'
                }`}>
                  Readiness Delta: {result.readiness_delta > 0 ? '+' : ''}{result.readiness_delta.toFixed(1)} points
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {result.current_sla}% → {result.simulated_sla}%
                </p>
              </div>
              <Badge variant="outline" className="ml-auto">{result.cost_impact}</Badge>
            </div>

            {/* Budget comparison */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Budget</p>
                <p className="font-bold text-gray-700 dark:text-gray-300">
                  {result.current_budget.annual_display}
                </p>
                <p className="text-xs text-gray-400">/ year</p>
              </div>
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Simulated Budget</p>
                <p className="font-bold text-blue-700 dark:text-blue-300">
                  {result.simulated_budget.annual_display}
                </p>
                <p className="text-xs text-gray-400">/ year</p>
              </div>
            </div>

            {/* Required improvements */}
            {result.required_improvements.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Required Improvements
                </p>
                <ul className="space-y-1">
                  {result.required_improvements.map((imp, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <TrendingUp className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-400">{imp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Control gaps */}
            {result.control_gaps.length > 0 && (
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400 mb-2">
                  Control Gaps
                </p>
                <ul className="space-y-1">
                  {result.control_gaps.map((gap, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-400">{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════

function ReliabilityContent() {
  const [searchParams] = useSearchParams();
  const selectedOrgId = searchParams.get('org');

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [activeOrg, setActiveOrg] = useState<string | null>(null);
  const [rri, setRri] = useState<RRIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load organizations
  useEffect(() => {
    getOrganizations()
      .then((data) => {
        setOrgs(data);
        if (selectedOrgId) {
          setActiveOrg(selectedOrgId);
        } else if (data.length > 0) {
          setActiveOrg(data[0].id);
        }
      })
      .catch(() => setError('Failed to load organizations'));
  }, [selectedOrgId]);

  // Load RRI when org changes
  useEffect(() => {
    if (!activeOrg) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    getReliabilityIndex(activeOrg)
      .then((data) => {
        setRri(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load RRI');
        setLoading(false);
      });
  }, [activeOrg]);

  const handleRefresh = useCallback(() => {
    if (!activeOrg) return;
    setLoading(true);
    getReliabilityIndex(activeOrg)
      .then(setRri)
      .catch((err) => setError(err instanceof Error ? err.message : 'Refresh failed'))
      .finally(() => setLoading(false));
  }, [activeOrg]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Reliability Risk Index™
          </h1>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Reliability Risk Index™
        </h1>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <XCircle className="h-12 w-12 text-red-400 mx-auto mb-3" />
              <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
              <Button onClick={handleRefresh} variant="outline" className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (orgs.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Reliability Risk Index™
        </h1>
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            <Shield className="h-12 w-12 mx-auto mb-3 text-gray-400" />
            <p>No organizations found. Create an organization first.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="h-7 w-7 text-blue-600" />
            Reliability Risk Index™
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Deterministic reliability exposure scoring — SLA + Recovery + Redundancy + Monitoring + BCDR
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Org selector */}
          {orgs.length > 1 && (
            <select
              value={activeOrg ?? ''}
              onChange={(e) => setActiveOrg(e.target.value)}
              className="text-sm border rounded-md px-3 py-1.5 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
            >
              {orgs.map((org) => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
          )}
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {rri && (
        <>
          {/* Row 1: Score gauge + Dimension breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RRIScoreGauge rri={rri} />
            <DimensionBreakdown dimensions={rri.dimensions} />
          </div>

          {/* Row 2: Downtime Budget + SLA Advisor */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {rri.downtime_budget && (
              <DowntimeBudgetCard budget={rri.downtime_budget} />
            )}
            {rri.sla_advisor && (
              <SLAAdvisorCard advisor={rri.sla_advisor} />
            )}
          </div>

          {/* Row 3: Top Gaps + Board Simulation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TopGapsCard gaps={rri.top_gaps} />
            {activeOrg && (
              <BoardSimulation
                orgId={activeOrg}
                currentSla={rri.downtime_budget?.sla_target ?? null}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Export
// ═══════════════════════════════════════════════════════════════════════

export default function ReliabilityDashboard() {
  return (
    <StagingGate>
      <ReliabilityContent />
    </StagingGate>
  );
}
