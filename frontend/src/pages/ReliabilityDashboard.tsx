/**
 * ReliabilityDashboard.tsx — Reliability Governance System (RRI v2)
 *
 * Staging-only page providing:
 *   - RRI Score gauge with Breach Exposure Heat Badge
 *   - Reliability Confidence Score (RCS) — two-axis resilience matrix
 *   - Five-dimension breakdown (SLA, Recovery, Redundancy, Monitoring, BCDR)
 *   - Autonomous Advisory Panel with severity-based remediation
 *   - Auto-detect recommendation banner (accept tier/SLA)
 *   - Live Downtime Budget Visualization (monthly/annual)
 *   - Smart SLA Advisor with industry-aware recommendations
 *   - Board Simulation Mode (upgrade + downgrade scenarios)
 *   - Reliability Maturity Timeline (90-day trend)
 *   - Top Gaps action list
 *
 * Positioning: Contractual Resilience Intelligence Platform for AI-Era Enterprises
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
  Info,
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
  getReliabilityConfidence,
  acceptRecommendation,
  getReliabilityHistory,
} from '../api';
import { useDemoMode } from '../contexts';
import type {
  Organization,
  RRIResponse,
  RRIDimension,
  DowntimeBudget,
  SLAAdvisor,
  BreachSimulationResponse,
  BreachExposureBadge,
  AdvisoryItem,
  ReliabilityConfidenceScore,
  AutoRecommendation,
  RRISnapshot,
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

function breachExposureDisplay(badge: BreachExposureBadge) {
  const colors: Record<string, string> = {
    green: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700',
    black: 'bg-gray-900 dark:bg-black text-white border-gray-700',
  };
  return colors[badge.severity] ?? colors.green;
}

function confidenceBandColor(band: string): string {
  switch (band) {
    case 'Verified': return 'text-green-600 dark:text-green-400';
    case 'Moderate': return 'text-yellow-600 dark:text-yellow-400';
    case 'Low': return 'text-orange-600 dark:text-orange-400';
    case 'Unvalidated': return 'text-red-600 dark:text-red-400';
    default: return 'text-gray-600 dark:text-gray-400';
  }
}

function rcsBarColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-500';
  if (score >= 20) return 'bg-orange-500';
  return 'bg-red-500';
}

function advisorySeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'border-l-red-600 bg-red-50 dark:bg-red-900/20';
    case 'high': return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20';
    case 'medium': return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
    case 'info': return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
    default: return 'border-l-gray-400 bg-gray-50 dark:bg-gray-800';
  }
}

function advisorySeverityBadge(severity: string) {
  switch (severity) {
    case 'critical': return <Badge variant="destructive">Critical</Badge>;
    case 'high': return <Badge variant="warning">High</Badge>;
    case 'medium': return <Badge variant="outline">Medium</Badge>;
    case 'info': return <Badge variant="outline">Info</Badge>;
    default: return <Badge variant="outline">{severity}</Badge>;
  }
}


// ═══════════════════════════════════════════════════════════════════════
// RRI Score Gauge (with Breach Exposure Heat Badge)
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
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
          SLA Commitment vs Operational Reality
        </p>
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
            {/* Breach Exposure Heat Badge */}
            {rri.breach_exposure && (
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${breachExposureDisplay(rri.breach_exposure)}`}>
                <span className="text-xl">{rri.breach_exposure.badge}</span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">
                    {rri.breach_exposure.level.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </p>
                  <p className="text-xs opacity-75 truncate">{rri.breach_exposure.explanation}</p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Risk Band:</span>
              <span className={`text-lg font-semibold ${riskBandColor(rri.risk_band)}`}>
                {rri.risk_band}
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
// Reliability Confidence Score (RCS) — Two-axis companion to RRI
// ═══════════════════════════════════════════════════════════════════════

function ReliabilityConfidenceCard({ rcs }: { rcs: ReliabilityConfidenceScore }) {
  const subDimensions = [
    { key: 'dr_test_recency', label: 'DR Test Recency', score: rcs.dr_test_recency },
    { key: 'backup_validation', label: 'Backup Validation', score: rcs.backup_validation },
    { key: 'ir_tabletop_recency', label: 'IR Tabletop', score: rcs.ir_tabletop_recency },
    { key: 'monitoring_coverage', label: 'Monitoring Coverage', score: rcs.monitoring_coverage },
    { key: 'architecture_redundancy', label: 'Arch. Redundancy', score: rcs.architecture_redundancy },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Reliability Confidence Score
          <Badge variant="outline" className="ml-2">RCS</Badge>
        </CardTitle>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
          RRI = Exposure · RCS = Confidence — Two-axis resilience matrix
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score display */}
        <div className="flex items-center gap-6">
          <div className="text-center">
            <span className={`text-4xl font-bold ${rcsBarColor(rcs.total_score).replace('bg-', 'text-')}`}>
              {rcs.total_score}
            </span>
            <p className="text-xs text-gray-400">/ 100</p>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm text-gray-500 dark:text-gray-400">Confidence Band:</span>
              <span className={`text-lg font-semibold ${confidenceBandColor(rcs.confidence_band)}`}>
                {rcs.confidence_band}
              </span>
            </div>
            <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${rcsBarColor(rcs.total_score)}`}
                style={{ width: `${rcs.total_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Sub-dimension bars */}
        <div className="space-y-2.5">
          {subDimensions.map((dim) => (
            <div key={dim.key} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">{dim.label}</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">{dim.score}/20</span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${rcsBarColor(dim.score * 5)}`}
                  style={{ width: `${(dim.score / 20) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Autonomous Advisory Panel
// ═══════════════════════════════════════════════════════════════════════

function AutonomousAdvisoryPanel({ advisories }: { advisories: AdvisoryItem[] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (advisories.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-green-600" />
            Autonomous Advisories
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 className="h-5 w-5" />
            <span className="text-sm">No advisories — all reliability controls aligned</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const criticalCount = advisories.filter(a => a.severity === 'critical').length;
  const highCount = advisories.filter(a => a.severity === 'high').length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5" />
          Autonomous Advisories
          <div className="ml-auto flex gap-1">
            {criticalCount > 0 && <Badge variant="destructive">{criticalCount} Critical</Badge>}
            {highCount > 0 && <Badge variant="warning">{highCount} High</Badge>}
          </div>
        </CardTitle>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
          Deterministic misalignment detection — no LLM required
        </p>
      </CardHeader>
      <CardContent className="space-y-2">
        {advisories.map((adv, i) => (
          <div
            key={i}
            className={`border-l-4 rounded-r-lg p-3 ${advisorySeverityColor(adv.severity)} cursor-pointer transition-all hover:shadow-sm`}
            onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {advisorySeverityBadge(adv.severity)}
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {adv.title}
                </span>
              </div>
              <span className="text-xs text-gray-400">
                {expandedIdx === i ? '▲' : '▼'}
              </span>
            </div>
            {expandedIdx === i && (
              <div className="mt-2 space-y-2 text-sm">
                <p className="text-gray-600 dark:text-gray-400">{adv.detail}</p>
                <div className="flex items-start gap-2 p-2 bg-white/60 dark:bg-gray-800/60 rounded">
                  <Lightbulb className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-blue-700 dark:text-blue-300">{adv.remediation}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Auto-Recommendation Banner
// ═══════════════════════════════════════════════════════════════════════

function AutoRecommendationBanner({
  recommendation,
  orgId,
  onAccepted,
}: {
  recommendation: AutoRecommendation;
  orgId: string;
  onAccepted: () => void;
}) {
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await acceptRecommendation(orgId, recommendation.recommended_tier, recommendation.recommended_sla);
      setAccepted(true);
      onAccepted();
    } catch {
      // Silently handle
    } finally {
      setAccepting(false);
    }
  };

  if (accepted) {
    return (
      <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <CheckCircle2 className="h-5 w-5 text-green-600" />
        <span className="text-sm font-medium text-green-700 dark:text-green-300">
          Recommendation accepted — tier and SLA updated
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
      <Info className="h-6 w-6 text-blue-600 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
          Auto-detected: {recommendation.recommended_tier.toUpperCase()} tier @ {recommendation.recommended_sla}% SLA
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
          {recommendation.rationale} (Source: {recommendation.source})
        </p>
      </div>
      <Button
        onClick={handleAccept}
        disabled={accepting}
        className="flex-shrink-0"
        variant="default"
      >
        {accepting ? (
          <RefreshCw className="h-4 w-4 animate-spin mr-1" />
        ) : (
          <CheckCircle2 className="h-4 w-4 mr-1" />
        )}
        Accept
      </Button>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Reliability Maturity Timeline (90-day trend)
// ═══════════════════════════════════════════════════════════════════════

function ReliabilityTimeline({ snapshots }: { snapshots: RRISnapshot[] }) {
  if (snapshots.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Reliability Maturity Timeline
            <Badge variant="outline" className="ml-2">90 Days</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-gray-500 dark:text-gray-400">
            <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">Insufficient data points for timeline.</p>
            <p className="text-xs text-gray-400 mt-1">
              RRI snapshots are recorded on each calculation. Check back soon.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // SVG chart dimensions
  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Normalize data
  const sorted = [...snapshots].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  const minTime = new Date(sorted[0].timestamp).getTime();
  const maxTime = new Date(sorted[sorted.length - 1].timestamp).getTime();
  const timeRange = maxTime - minTime || 1;

  function toX(ts: string) {
    return padding.left + ((new Date(ts).getTime() - minTime) / timeRange) * chartW;
  }
  function toYRri(score: number) {
    return padding.top + chartH - (Math.min(score, 100) / 100) * chartH;
  }
  function toYRcs(score: number) {
    return padding.top + chartH - (Math.min(score, 100) / 100) * chartH;
  }

  // Build path strings
  const rriPath = sorted.map((s, i) => `${i === 0 ? 'M' : 'L'}${toX(s.timestamp).toFixed(1)},${toYRri(s.rri_score).toFixed(1)}`).join(' ');
  const rcsPath = sorted.map((s, i) => `${i === 0 ? 'M' : 'L'}${toX(s.timestamp).toFixed(1)},${toYRcs(s.rcs_score).toFixed(1)}`).join(' ');

  // Latest vs first delta
  const rriDelta = sorted[sorted.length - 1].rri_score - sorted[0].rri_score;
  const rcsDelta = sorted[sorted.length - 1].rcs_score - sorted[0].rcs_score;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Reliability Maturity Timeline
          <Badge variant="outline" className="ml-2">90 Days</Badge>
        </CardTitle>
        <div className="flex gap-4 mt-1">
          <span className="text-xs flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-500 inline-block rounded" /> RRI (Exposure)
            <span className={`ml-1 font-semibold ${rriDelta < 0 ? 'text-green-600' : rriDelta > 0 ? 'text-red-600' : 'text-gray-400'}`}>
              {rriDelta > 0 ? '+' : ''}{rriDelta.toFixed(1)}
            </span>
          </span>
          <span className="text-xs flex items-center gap-1">
            <span className="w-3 h-0.5 bg-emerald-500 inline-block rounded" /> RCS (Confidence)
            <span className={`ml-1 font-semibold ${rcsDelta > 0 ? 'text-green-600' : rcsDelta < 0 ? 'text-red-600' : 'text-gray-400'}`}>
              {rcsDelta > 0 ? '+' : ''}{rcsDelta.toFixed(1)}
            </span>
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="xMidYMid meet">
          {/* Y-axis grid lines */}
          {[0, 25, 50, 75, 100].map((v) => (
            <g key={v}>
              <line
                x1={padding.left} y1={toYRri(v)}
                x2={width - padding.right} y2={toYRri(v)}
                stroke="currentColor" className="text-gray-200 dark:text-gray-700"
                strokeDasharray="4 4"
              />
              <text
                x={padding.left - 8} y={toYRri(v) + 4}
                textAnchor="end" fill="currentColor"
                className="text-gray-400 dark:text-gray-500"
                fontSize="10"
              >{v}</text>
            </g>
          ))}

          {/* RRI line */}
          <path d={rriPath} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          {/* RCS line */}
          <path d={rcsPath} fill="none" stroke="#10b981" strokeWidth="2" strokeDasharray="6 3" strokeLinecap="round" strokeLinejoin="round" />

          {/* Data points */}
          {sorted.map((s, i) => (
            <g key={i}>
              <circle cx={toX(s.timestamp)} cy={toYRri(s.rri_score)} r="3" fill="#3b82f6" />
              <circle cx={toX(s.timestamp)} cy={toYRcs(s.rcs_score)} r="3" fill="#10b981" />
            </g>
          ))}

          {/* X-axis labels (first and last) */}
          <text x={padding.left} y={height - 5} fontSize="9" fill="currentColor" className="text-gray-400">
            {new Date(sorted[0].timestamp).toLocaleDateString()}
          </text>
          <text x={width - padding.right} y={height - 5} textAnchor="end" fontSize="9" fill="currentColor" className="text-gray-400">
            {new Date(sorted[sorted.length - 1].timestamp).toLocaleDateString()}
          </text>
        </svg>
      </CardContent>
    </Card>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// Board Simulation Mode (with downgrade support)
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
          Simulate the impact of changing your SLA target — upgrade or downgrade — on downtime budget, required improvements, and reliability readiness.
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
            {/* Direction indicator */}
            {currentSla !== null && (
              <div className="flex items-center gap-2">
                <Badge variant={simSla > currentSla ? 'outline' : 'warning'}>
                  {simSla > currentSla ? '↑ Upgrade Scenario' : simSla < currentSla ? '↓ Downgrade Scenario' : '= No Change'}
                </Badge>
                <span className="text-xs text-gray-400">
                  {currentSla.toFixed(3)}% → {simSla.toFixed(3)}%
                </span>
              </div>
            )}

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
  const [history, setHistory] = useState<RRISnapshot[]>([]);
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

  // Load RRI + history when org changes
  useEffect(() => {
    if (!activeOrg) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    Promise.all([
      getReliabilityIndex(activeOrg),
      getReliabilityHistory(activeOrg).catch(() => []),
    ])
      .then(([rriData, historyData]) => {
        setRri(rriData);
        setHistory(historyData);
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
    Promise.all([
      getReliabilityIndex(activeOrg),
      getReliabilityHistory(activeOrg).catch(() => []),
    ])
      .then(([rriData, historyData]) => {
        setRri(rriData);
        setHistory(historyData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Refresh failed'))
      .finally(() => setLoading(false));
  }, [activeOrg]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Reliability Governance System
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
          Reliability Governance System
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
          Reliability Governance System
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
            Reliability Governance System
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Contractual Resilience Intelligence — SLA Commitment vs Operational Reality
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
          {/* Auto-recommendation banner (when tier/SLA missing) */}
          {rri.auto_recommendation && activeOrg && (
            <AutoRecommendationBanner
              recommendation={rri.auto_recommendation}
              orgId={activeOrg}
              onAccepted={handleRefresh}
            />
          )}

          {/* Row 1: RRI Score gauge + RCS (Two-axis resilience matrix) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RRIScoreGauge rri={rri} />
            {rri.reliability_confidence ? (
              <ReliabilityConfidenceCard rcs={rri.reliability_confidence} />
            ) : (
              <DimensionBreakdown dimensions={rri.dimensions} />
            )}
          </div>

          {/* Row 2: Dimension breakdown (if RCS present) + Advisory Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {rri.reliability_confidence && (
              <DimensionBreakdown dimensions={rri.dimensions} />
            )}
            <AutonomousAdvisoryPanel advisories={rri.advisories ?? []} />
          </div>

          {/* Row 3: Downtime Budget + SLA Advisor */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {rri.downtime_budget && (
              <DowntimeBudgetCard budget={rri.downtime_budget} />
            )}
            {rri.sla_advisor && (
              <SLAAdvisorCard advisor={rri.sla_advisor} />
            )}
          </div>

          {/* Row 4: Reliability Timeline (full width) */}
          {history.length > 0 && (
            <ReliabilityTimeline snapshots={history} />
          )}

          {/* Row 5: Top Gaps + Board Simulation */}
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
