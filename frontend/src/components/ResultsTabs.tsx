// @ts-nocheck
/**
 * Results Tab Components for AIRS Assessment Results
 * 
 * Tab structure:
 * - Overview: Score ring, tier, executive summary, domain heatmap
 * - Findings: All findings with filtering and severity badges
 * - Framework Mapping: MITRE ATT&CK, CIS Controls, OWASP references
 * - Roadmap: Detailed 30/60/90 day remediation plan
 * - Analytics: Attack paths, detection gaps, response gaps
 */

import {
  AlertTriangle,
  CheckCircle,
  Shield,
  Target,
  TrendingUp,
  Calendar,
  Clock,
  ChevronRight,
  Zap,
  Sparkles,
  Lightbulb,
  Bot,
  ExternalLink,
  Route,
  Lock,
  FileWarning,
  Plus,
  ShieldAlert,
} from 'lucide-react'
import React from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../components/ui'
import type {
  AssessmentSummary,
  AttackPath,
  AttackStep,
  DetailedRoadmapItem,
  FrameworkMappedFinding,
  FrameworkRef,
} from '../types'
import { createRoadmapItem } from '../api'

// Helper functions
function getTierBg(color: string) {
  const map: Record<string, string> = {
    danger: 'bg-danger-500',
    warning: 'bg-warning-500',
    primary: 'bg-primary-500',
    success: 'bg-success-500',
  }
  return map[color] || 'bg-gray-500'
}

function getTierStroke(color: string) {
  const map: Record<string, string> = {
    danger: 'stroke-danger-500',
    warning: 'stroke-warning-500',
    primary: 'stroke-primary-500',
    success: 'stroke-success-500',
  }
  return map[color] || 'stroke-gray-500'
}

function getTierText(color: string) {
  const map: Record<string, string> = {
    danger: 'text-danger-600',
    warning: 'text-warning-600',
    primary: 'text-primary-600',
    success: 'text-success-600',
  }
  return map[color] || 'text-gray-600'
}

function getDomainScaleColor(score: number) {
  if (score >= 4) return 'bg-success-500'
  if (score >= 3) return 'bg-success-400'
  if (score >= 2) return 'bg-warning-400'
  if (score >= 1) return 'bg-warning-500'
  return 'bg-danger-500'
}

function getDomainScaleBg(score: number) {
  if (score >= 4) return 'bg-success-50 dark:bg-success-900/30 text-success-700 dark:text-success-300 border-success-200 dark:border-success-800'
  if (score >= 3) return 'bg-success-50/50 dark:bg-success-900/20 text-success-600 dark:text-success-400 border-success-100 dark:border-success-800/50'
  if (score >= 2) return 'bg-warning-50 dark:bg-warning-900/30 text-warning-700 dark:text-warning-300 border-warning-200 dark:border-warning-800'
  if (score >= 1) return 'bg-warning-50/50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800'
  return 'bg-danger-50 dark:bg-danger-900/30 text-danger-700 dark:text-danger-300 border-danger-200 dark:border-danger-800'
}

function getSeverityVariant(severity: string): 'danger' | 'warning' | 'default' | 'outline' | 'success' | 'primary' {
  const s = severity.toUpperCase()
  if (s === 'CRITICAL') return 'danger'
  if (s === 'HIGH') return 'warning'
  if (s === 'MEDIUM') return 'default'
  return 'outline'
}

function getLikelihoodColor(likelihood: string) {
  if (likelihood === 'high' || likelihood === 'High') return 'text-danger-700 dark:text-danger-300 bg-danger-50 dark:bg-danger-900/30'
  if (likelihood === 'medium' || likelihood === 'Medium') return 'text-warning-700 dark:text-warning-300 bg-warning-50 dark:bg-warning-900/30'
  return 'text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700'
}

// ============================================================================
// OVERVIEW TAB
// ============================================================================
interface OverviewTabProps {
  summary: AssessmentSummary;
  selectedBaseline: string;
  setSelectedBaseline: (baseline: string) => void;
  suggestedBaseline?: string;
  onRefreshNarrative?: () => void;
  isRefreshingNarrative?: boolean;
}

export function OverviewTab({ summary, selectedBaseline, setSelectedBaseline, suggestedBaseline, onRefreshNarrative, isRefreshingNarrative }: OverviewTabProps) {
  const { tier, domain_scores, findings, executive_summary } = summary
  const topFailures = findings.slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Hero Card - Overall Score */}
      <Card className="overflow-hidden">
        <div className={`h-2 ${getTierBg(tier.color)}`} />
        <CardContent className="py-8">
          <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16">
            {/* Score Ring */}
            <div className="relative w-48 h-48">
              <svg viewBox="0 0 100 100" className="-rotate-90">
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  className="stroke-gray-100"
                  strokeWidth="12"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  className={getTierStroke(tier.color)}
                  strokeWidth="12"
                  strokeDasharray={2 * Math.PI * 42}
                  strokeDashoffset={2 * Math.PI * 42 * (1 - summary.overall_score / 100)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-5xl font-bold ${getTierText(tier.color)}`}>
                  {Math.round(summary.overall_score)}
                </span>
                <span className="text-gray-500 dark:text-gray-400 text-sm mt-1">out of 100</span>
              </div>
            </div>

            {/* Tier & Stats */}
            <div className="text-center lg:text-left space-y-4">
              <div>
                <div className="text-gray-500 dark:text-gray-400 uppercase text-xs tracking-wider mb-1">Readiness Tier</div>
                <div className={`text-4xl font-bold ${getTierText(tier.color)}`}>
                  {tier.label}
                </div>
              </div>
              <div className="flex flex-wrap justify-center lg:justify-start gap-4">
                <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <Target className="h-5 w-5 text-primary-500" />
                  <div>
                    <div className="text-lg font-semibold dark:text-gray-100">{summary.findings_count}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Total Findings</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-danger-50 dark:bg-danger-900/30 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-danger-500" />
                  <div>
                    <div className="text-lg font-semibold text-danger-600 dark:text-danger-400">{summary.critical_high_count}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Critical + High</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-success-50 dark:bg-success-900/30 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-success-500" />
                  <div>
                    <div className="text-lg font-semibold text-success-600 dark:text-success-400">
                      {5 - (summary.findings_count > 0 ? Math.min(5, summary.findings_count) : 0)}/5
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Domains OK</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileWarning className="h-5 w-5 text-primary-500" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{executive_summary}</p>
        </CardContent>
      </Card>

      {/* AI Insights - Only shown when LLM is enabled */}
      {summary.llm_enabled && (summary.executive_summary_text || summary.llm_status === 'pending') && (
        <Card className="border-primary-100 dark:border-primary-800 bg-gradient-to-br from-primary-50/50 dark:from-primary-900/20 to-white dark:to-gray-900">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary-700">
              <Sparkles className="h-5 w-5" />
              AI-Generated Insights
              <Badge variant="outline" className="ml-2 text-xs">
                <Bot className="h-3 w-3 mr-1" />
                {summary.llm_model || 'AI'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Show pending state */}
            {summary.llm_status === 'pending' && !summary.executive_summary_text && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                {isRefreshingNarrative ? (
                  <>
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mb-4"></div>
                    <p className="text-gray-600 dark:text-gray-300 font-medium">Generating AI insights...</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">This may take a few seconds</p>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-8 w-8 text-primary-400 mb-4 animate-pulse" />
                    <p className="text-gray-600 dark:text-gray-300 font-medium">AI insights are being generated</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 mb-4">Click refresh to check if they're ready</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onRefreshNarrative}
                      className="gap-2"
                    >
                      <TrendingUp className="h-4 w-4" />
                      Refresh AI Insights
                    </Button>
                  </>
                )}
              </div>
            )}

            {/* AI Executive Summary */}
            {summary.executive_summary_text && (
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">
                  <Lightbulb className="h-4 w-4" />
                  AI Executive Analysis
                </div>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {summary.executive_summary_text}
                </p>
              </div>
            )}

            {/* AI Roadmap Narrative */}
            {summary.roadmap_narrative_text && (
              <div className="pt-4 border-t border-primary-100 dark:border-primary-800">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">
                  <TrendingUp className="h-4 w-4" />
                  AI Remediation Strategy
                </div>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {summary.roadmap_narrative_text}
                </p>
              </div>
            )}

            {/* LLM info footer */}
            <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500 pt-2 border-t border-gray-100 dark:border-gray-700">
              <span>Powered by {summary.llm_provider || 'AI'}</span>
              {summary.llm_mode === 'demo' && (
                <span className="text-warning-500 font-medium">Demo Mode</span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Domain Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-500" />
            Domain Scores
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {domain_scores.map((ds) => {
              const score5 = ds.score_5 || ds.score / 20
              return (
                <div
                  key={ds.domain_id}
                  className={`p-4 rounded-xl border ${getDomainScaleBg(score5)} transition-all hover:scale-[1.02]`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold truncate pr-2">{ds.domain_name}</div>
                    <div className={`w-10 h-10 rounded-full ${getDomainScaleColor(score5)} flex items-center justify-center text-white font-bold`}>
                      {score5.toFixed(1)}
                    </div>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getDomainScaleColor(score5)} transition-all duration-500`}
                      style={{ width: `${(score5 / 5) * 100}%` }}
                    />
                  </div>
                  <div className="text-xs mt-2 opacity-75">
                    Weight: {Math.round(ds.weight * 100)}%
                  </div>
                </div>
              )
            })}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-4 mt-6 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-success-500"></div>
              <span>Excellent (4-5)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-success-400"></div>
              <span>Good (3-4)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-warning-400"></div>
              <span>Needs Work (2-3)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-warning-500"></div>
              <span>Poor (1-2)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-danger-500"></div>
              <span>Critical (0-1)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top 5 Findings */}
      {topFailures.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-danger-500" />
              Top Priority Findings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topFailures.map((f, i) => (
                <div
                  key={f.id || i}
                  className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-danger-100 dark:bg-danger-900/30 flex items-center justify-center text-danger-600 dark:text-danger-400 font-bold text-sm">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">{f.title}</h4>
                      <Badge variant={getSeverityVariant(f.severity)}>{f.severity}</Badge>
                    </div>
                    {f.recommendation && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{f.recommendation}</p>
                    )}
                    {f.domain && (
                      <div className="text-xs text-gray-400 dark:text-gray-500 mt-2">{f.domain}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Benchmark Comparison */}
      {summary.baseline_profiles && Object.keys(summary.baseline_profiles).length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary-500" />
                Benchmark Comparison
              </CardTitle>
              <div className="flex items-center gap-2">
                {suggestedBaseline && suggestedBaseline !== selectedBaseline && (
                  <button
                    onClick={() => setSelectedBaseline(suggestedBaseline)}
                    className="text-xs flex items-center gap-1 px-2 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 hover:bg-primary-100 dark:hover:bg-primary-800/30 transition-colors"
                    title={`Apply suggested baseline: ${suggestedBaseline}`}
                  >
                    <Sparkles className="w-3 h-3" />
                    Apply Suggested
                  </button>
                )}
                <select
                  value={selectedBaseline}
                  onChange={(e) => setSelectedBaseline(e.target.value)}
                  className="text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 dark:text-gray-100"
                >
                  {summary.baselines_available?.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {domain_scores.map((ds) => {
                const baselineScore = summary.baseline_profiles?.[selectedBaseline]?.[ds.domain_id] || 0
                const score5 = ds.score_5 || ds.score / 20
                const diff = score5 - baselineScore
                const isAbove = diff >= 0

                return (
                  <div key={ds.domain_id} className="flex items-center gap-4">
                    <div className="w-40 text-sm font-medium truncate">{ds.domain_name}</div>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="flex-1 h-3 bg-gray-100 rounded-full relative overflow-hidden">
                        {/* Baseline marker */}
                        <div
                          className="absolute top-0 bottom-0 w-0.5 bg-gray-400 z-10"
                          style={{ left: `${(baselineScore / 5) * 100}%` }}
                        />
                        {/* Actual score */}
                        <div
                          className={`h-full rounded-full ${getDomainScaleColor(score5)}`}
                          style={{ width: `${(score5 / 5) * 100}%` }}
                        />
                      </div>
                      <div className={`w-16 text-right text-sm font-medium ${isAbove ? 'text-success-600' : 'text-danger-600'}`}>
                        {isAbove ? '+' : ''}{diff.toFixed(1)}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-gray-400 dark:bg-gray-500"></div>
                <span>Baseline ({selectedBaseline})</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ============================================================================
// FINDINGS TAB
// ============================================================================
interface FindingsTabProps {
  summary: AssessmentSummary;
}

export function FindingsTab({ summary }: FindingsTabProps) {
  const { findings } = summary

  if (findings.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <CheckCircle className="h-16 w-16 text-success-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Findings</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Excellent! The assessment did not identify any gaps in your security posture.
          </p>
        </CardContent>
      </Card>
    )
  }

  // Group findings by severity
  const findingsBySeverity: Record<string, typeof findings> = {
    critical: findings.filter(f => f.severity.toLowerCase() === 'critical'),
    high: findings.filter(f => f.severity.toLowerCase() === 'high'),
    medium: findings.filter(f => f.severity.toLowerCase() === 'medium'),
    low: findings.filter(f => f.severity.toLowerCase() === 'low'),
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-danger-50 dark:bg-danger-900/30 rounded-lg border border-danger-200 dark:border-danger-800">
          <div className="text-3xl font-bold text-danger-600 dark:text-danger-400">{findingsBySeverity.critical.length}</div>
          <div className="text-sm text-danger-700 dark:text-danger-300">Critical</div>
        </div>
        <div className="p-4 bg-warning-50 dark:bg-warning-900/30 rounded-lg border border-warning-200 dark:border-warning-800">
          <div className="text-3xl font-bold text-warning-600 dark:text-warning-400">{findingsBySeverity.high.length}</div>
          <div className="text-sm text-warning-700 dark:text-warning-300">High</div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="text-3xl font-bold text-gray-600 dark:text-gray-300">{findingsBySeverity.medium.length}</div>
          <div className="text-sm text-gray-700 dark:text-gray-400">Medium</div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="text-3xl font-bold text-gray-600 dark:text-gray-300">{findingsBySeverity.low.length}</div>
          <div className="text-sm text-gray-700 dark:text-gray-400">Low</div>
        </div>
      </div>

      {/* All Findings */}
      <Card>
        <CardHeader>
          <CardTitle>All Findings ({findings.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {findings.map((f, i) => (
              <div
                key={f.id || i}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={getSeverityVariant(f.severity)}>{f.severity}</Badge>
                      {f.domain && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">{f.domain}</span>
                      )}
                    </div>
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">{f.title}</h4>
                    {f.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{f.description}</p>
                    )}
                    {f.recommendation && (
                      <div className="mt-3 p-3 bg-primary-50 dark:bg-primary-900/30 rounded-lg">
                        <div className="text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Recommendation</div>
                        <p className="text-sm text-primary-900 dark:text-primary-200">{f.recommendation}</p>
                      </div>
                    )}
                    {f.evidence && (
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        <strong>Evidence:</strong> {f.evidence}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ============================================================================
// FRAMEWORK MAPPING TAB
// ============================================================================
interface FrameworkTabProps {
  summary: AssessmentSummary;
}

export function FrameworkTab({ summary }: FrameworkTabProps) {
  const mapping = summary.framework_mapping

  if (!mapping || mapping.findings.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Shield className="h-16 w-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Framework Mappings</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Framework mappings will appear here once the assessment is scored.
          </p>
        </CardContent>
      </Card>
    )
  }

  const { findings, coverage } = mapping
  
  // Compute unique framework refs from findings (source of truth)
  const uniqueMitre = new Set<string>()
  const uniqueCIS = new Set<string>()
  const uniqueOWASP = new Set<string>()
  const mitreTechniqueNames: Record<string, string> = {}
  const cisTechniqueNames: Record<string, string> = {}
  const owaspNames: Record<string, string> = {}
  
  findings.forEach((f: FrameworkMappedFinding) => {
    f.mitre_refs?.forEach((ref: FrameworkRef) => {
      uniqueMitre.add(ref.id)
      mitreTechniqueNames[ref.id] = ref.name
    })
    f.cis_refs?.forEach((ref: FrameworkRef) => {
      uniqueCIS.add(ref.id)
      cisTechniqueNames[ref.id] = ref.name
    })
    f.owasp_refs?.forEach((ref: FrameworkRef) => {
      uniqueOWASP.add(ref.id)
      owaspNames[ref.id] = ref.name
    })
  })
  
  // Use computed values as source of truth
  const mitreCount = uniqueMitre.size
  const mitreTotal = coverage?.mitre_techniques_total || 40
  const mitrePct = mitreTotal > 0 ? (mitreCount / mitreTotal * 100) : 0
  const mitreList = Array.from(uniqueMitre).slice(0, 5)
  
  const cisCount = uniqueCIS.size
  const cisTotal = coverage?.cis_controls_total || 56
  const cisList = Array.from(uniqueCIS).slice(0, 5)
  
  const owaspCount = uniqueOWASP.size
  const owaspTotal = coverage?.owasp_total || 10
  const owaspPct = owaspTotal > 0 ? (owaspCount / owaspTotal * 100) : 0
  const owaspList = Array.from(uniqueOWASP).slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Coverage Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* MITRE Coverage */}
        <Card>
          <CardContent className="py-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <Target className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">MITRE ATT&CK</div>
                <div className="text-2xl font-bold dark:text-gray-100">{mitrePct.toFixed(0)}%</div>
              </div>
            </div>

            {/* Count from computed values */}
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              <span className="font-medium text-gray-700 dark:text-gray-300">{mitreCount}</span> of <span className="font-medium text-gray-700 dark:text-gray-300">{mitreTotal}</span> techniques referenced
            </div>

            {/* Top Techniques List */}
            {mitreList.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-[10px] uppercase font-bold text-gray-400 dark:text-gray-500 mb-1">Top Referenced</p>
                <div className="flex flex-wrap gap-1">
                  {mitreList.map((tid: string) => (
                    <Badge key={tid} variant="outline" className="text-[10px] px-1.5 py-0 h-5 bg-white dark:bg-gray-800" title={mitreTechniqueNames[tid]}>
                      {tid}
                    </Badge>
                  ))}
                  {uniqueMitre.size > 5 && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 flex items-center">+{uniqueMitre.size - 5} more</span>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* CIS Controls Coverage */}
        <Card>
          <CardContent className="py-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">CIS Controls v8</div>
                <div className="text-2xl font-bold dark:text-gray-100">{cisCount} referenced</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              <span className="font-medium text-gray-700 dark:text-gray-300">{cisCount}</span> of <span className="font-medium text-gray-700 dark:text-gray-300">{cisTotal}</span> controls referenced
            </div>
            {coverage && (
              <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400 mt-2">
                <div>IG1: {coverage.ig1_coverage_pct?.toFixed(0) || 0}%</div>
                <div>IG2: {coverage.ig2_coverage_pct?.toFixed(0) || 0}%</div>
                <div>IG3: {coverage.ig3_coverage_pct?.toFixed(0) || 0}%</div>
              </div>
            )}
            {/* Top Controls List */}
            {cisList.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-[10px] uppercase font-bold text-gray-400 dark:text-gray-500 mb-1">Top Referenced</p>
                <div className="flex flex-wrap gap-1">
                  {cisList.map((cid: string) => (
                    <Badge key={cid} variant="outline" className="text-[10px] px-1.5 py-0 h-5 bg-white dark:bg-gray-800" title={cisTechniqueNames[cid]}>
                      {cid}
                    </Badge>
                  ))}
                  {uniqueCIS.size > 5 && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 flex items-center">+{uniqueCIS.size - 5} more</span>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* OWASP */}
        <Card>
          <CardContent className="py-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Lock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">OWASP Top 10</div>
                <div className="text-2xl font-bold dark:text-gray-100">{owaspCount} referenced</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              <span className="font-medium text-gray-700 dark:text-gray-300">{owaspCount}</span> of <span className="font-medium text-gray-700 dark:text-gray-300">{owaspTotal}</span> categories referenced ({owaspPct.toFixed(0)}%)
            </div>
            {/* Top OWASP List */}
            {owaspList.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-[10px] uppercase font-bold text-gray-400 dark:text-gray-500 mb-1">Referenced</p>
                <div className="flex flex-wrap gap-1">
                  {owaspList.map((oid: string) => (
                    <Badge key={oid} variant="outline" className="text-[10px] px-1.5 py-0 h-5 bg-white dark:bg-gray-800" title={owaspNames[oid]}>
                      {oid}
                    </Badge>
                  ))}
                  {uniqueOWASP.size > 5 && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 flex items-center">+{uniqueOWASP.size - 5} more</span>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Findings with Framework References */}
      <Card>
        <CardHeader>
          <CardTitle>Findings with Framework References</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {findings.map((f: FrameworkMappedFinding, i: number) => (
              <div key={f.finding_id || i} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={getSeverityVariant(f.severity)}>{f.severity}</Badge>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{f.domain}</span>
                    </div>
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">{f.title}</h4>
                  </div>
                </div>

                {/* MITRE ATT&CK References */}
                {f.mitre_refs && f.mitre_refs.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-red-700 dark:text-red-400 mb-2 flex items-center gap-1">
                      <Target className="h-3 w-3" />
                      MITRE ATT&CK
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {f.mitre_refs.map((ref: FrameworkRef) => (
                        <a
                          key={ref.id}
                          href={ref.url || '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 py-1 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
                        >
                          {ref.id}: {ref.name}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* CIS Controls References */}
                {f.cis_refs && f.cis_refs.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-1">
                      <Shield className="h-3 w-3" />
                      CIS Controls v8
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {f.cis_refs.map((ref: FrameworkRef) => (
                        <span
                          key={ref.id}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs"
                        >
                          {ref.id}{ref.ig_level ? ` (IG${ref.ig_level})` : ''}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* OWASP References */}
                {f.owasp_refs && f.owasp_refs.length > 0 && (
                  <div>
                    <div className="text-xs font-medium text-purple-700 dark:text-purple-400 mb-2 flex items-center gap-1">
                      <Lock className="h-3 w-3" />
                      OWASP Top 10
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {f.owasp_refs.map((ref: FrameworkRef) => (
                        <span
                          key={ref.id}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs"
                        >
                          {ref.id}: {ref.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ============================================================================
// ROADMAP TAB
// ============================================================================
interface RoadmapTabProps {
  summary: AssessmentSummary;
}

export function RoadmapTab({ summary }: RoadmapTabProps) {
  const detailedRoadmap = summary.detailed_roadmap
  const basicRoadmap = summary.roadmap

  // If we have detailed roadmap, show that
  if (detailedRoadmap && detailedRoadmap.phases) {
    const { summary: stats, phases } = detailedRoadmap

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="p-4 bg-primary-50 dark:bg-primary-900/30 rounded-lg border border-primary-200 dark:border-primary-800">
            <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">{stats.total_items}</div>
            <div className="text-sm text-primary-700 dark:text-primary-300">Total Items</div>
          </div>
          <div className="p-4 bg-danger-50 dark:bg-danger-900/30 rounded-lg border border-danger-200 dark:border-danger-800">
            <div className="text-3xl font-bold text-danger-600 dark:text-danger-400">{stats.critical_items}</div>
            <div className="text-sm text-danger-700 dark:text-danger-300">Critical</div>
          </div>
          <div className="p-4 bg-success-50 dark:bg-success-900/30 rounded-lg border border-success-200 dark:border-success-800">
            <div className="text-3xl font-bold text-success-600 dark:text-success-400">{stats.quick_wins}</div>
            <div className="text-sm text-success-700 dark:text-success-300">Quick Wins</div>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-3xl font-bold text-gray-600 dark:text-gray-300">{stats.total_effort_hours}h</div>
            <div className="text-sm text-gray-700 dark:text-gray-400">Est. Effort</div>
          </div>
          <div className="p-4 bg-warning-50 dark:bg-warning-900/30 rounded-lg border border-warning-200 dark:border-warning-800">
            <div className="text-3xl font-bold text-warning-600 dark:text-warning-400">{stats.total_risk_reduction}</div>
            <div className="text-sm text-warning-700 dark:text-warning-300">Risk Reduction</div>
          </div>
        </div>

        {/* Phase Cards */}
        {['day30', 'day60', 'day90', 'beyond'].map((phaseKey) => {
          const phase = phases[phaseKey as keyof typeof phases]
          if (!phase || phase.items.length === 0) return null

          const phaseColors: Record<string, string> = {
            day30: 'border-danger-200 dark:border-danger-800 bg-danger-50/30 dark:bg-danger-900/20',
            day60: 'border-warning-200 dark:border-warning-800 bg-warning-50/30 dark:bg-warning-900/20',
            day90: 'border-primary-200 dark:border-primary-800 bg-primary-50/30 dark:bg-primary-900/20',
            beyond: 'border-gray-200 dark:border-gray-700 bg-gray-50/30 dark:bg-gray-800/30',
          }

          const headerColors: Record<string, string> = {
            day30: 'bg-danger-100 dark:bg-danger-900/50 text-danger-800 dark:text-danger-200',
            day60: 'bg-warning-100 dark:bg-warning-900/50 text-warning-800 dark:text-warning-200',
            day90: 'bg-primary-100 dark:bg-primary-900/50 text-primary-800 dark:text-primary-200',
            beyond: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200',
          }

          return (
            <Card key={phaseKey} className={`overflow-hidden ${phaseColors[phaseKey]}`}>
              <div
                className={`px-6 py-3 ${headerColors[phaseKey]} flex items-center justify-between`}
              >
                <div className="flex items-center gap-2 font-semibold">
                  <Calendar className="h-4 w-4" />
                  {phase.name}
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span>{phase.item_count} items</span>
                  <span>{phase.effort_hours}h effort</span>
                </div>
              </div>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{phase.description}</p>
                <div className="space-y-3">
                  {phase.items.map((item: DetailedRoadmapItem, i: number) => {
                    // Tracking state
                    const [added, setAdded] = React.useState(false)
                    const [tracking, setTracking] = React.useState(false)

                    const handleAddToTracker = async () => {
                      if (added || tracking) return
                      setTracking(true)
                      try {
                        await createRoadmapItem(summary.organization_id, {
                          title: item.title,
                          description: item.action,
                          status: 'todo',
                          priority: ['critical', 'high'].includes(
                            item.severity.toLowerCase()
                          )
                            ? 'high'
                            : 'medium',
                          effort: item.effort.toLowerCase() as any,
                        })
                        setAdded(true)
                      } catch (e) {
                        console.error('Failed to add roadmap item', e)
                      } finally {
                        setTracking(false)
                      }
                    }

                    return (
                      <div
                        key={item.finding_id || i}
                        className="p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant={getSeverityVariant(item.severity)}>
                                {item.severity}
                              </Badge>
                              <Badge variant="outline">{item.effort} effort</Badge>
                              <span className="text-xs text-gray-500 dark:text-gray-400">{item.domain}</span>
                            </div>
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">{item.title}</h4>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 gap-1"
                            onClick={handleAddToTracker}
                            disabled={added || tracking}
                          >
                            {added ? (
                              <CheckCircle className="w-3 h-3 text-green-600" />
                            ) : (
                              <Plus className="w-3 h-3" />
                            )}
                            {added ? 'Tracked' : 'Track'}
                          </Button>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{item.action}</p>

                        {item.milestones && item.milestones.length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Milestones:
                            </div>
                            <ul className="space-y-1">
                              {item.milestones.map((m: string, mi: number) => (
                                <li
                                  key={mi}
                                  className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400"
                                >
                                  <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                                  {m}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {item.success_criteria && (
                          <div className="text-xs text-success-700 dark:text-success-300 bg-success-50 dark:bg-success-900/30 rounded p-2">
                            <strong>Success:</strong> {item.success_criteria}
                          </div>
                        )}

                        <div className="mt-2 text-xs text-gray-400 dark:text-gray-500">Owner: {item.owner}</div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    )
  }

  // Fallback to basic roadmap
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary-500" />
            30/60/90 Day Remediation Roadmap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 30 Days */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-danger-200 dark:border-danger-800">
                <div className="w-10 h-10 rounded-full bg-danger-100 dark:bg-danger-900/30 flex items-center justify-center">
                  <Zap className="h-5 w-5 text-danger-600 dark:text-danger-400" />
                </div>
                <div>
                  <div className="font-semibold text-danger-700 dark:text-danger-300">Day 30</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Critical Actions</div>
                </div>
              </div>
              {basicRoadmap.day30.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">No critical items</p>
              ) : (
                basicRoadmap.day30.map((item, i) => (
                  <div key={i} className="p-3 bg-danger-50 dark:bg-danger-900/30 rounded-lg border border-danger-100 dark:border-danger-800">
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-100">{item.title}</div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{item.action}</p>
                  </div>
                ))
              )}
            </div>

            {/* 60 Days */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-warning-200 dark:border-warning-800">
                <div className="w-10 h-10 rounded-full bg-warning-100 dark:bg-warning-900/30 flex items-center justify-center">
                  <Clock className="h-5 w-5 text-warning-600 dark:text-warning-400" />
                </div>
                <div>
                  <div className="font-semibold text-warning-700 dark:text-warning-300">Day 60</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">High Priority</div>
                </div>
              </div>
              {basicRoadmap.day60.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">No high priority items</p>
              ) : (
                basicRoadmap.day60.map((item, i) => (
                  <div key={i} className="p-3 bg-warning-50 dark:bg-warning-900/30 rounded-lg border border-warning-100 dark:border-warning-800">
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-100">{item.title}</div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{item.action}</p>
                  </div>
                ))
              )}
            </div>

            {/* 90 Days */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-primary-200 dark:border-primary-800">
                <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <div className="font-semibold text-primary-700 dark:text-primary-300">Day 90</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Medium Priority</div>
                </div>
              </div>
              {basicRoadmap.day90.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">No medium priority items</p>
              ) : (
                basicRoadmap.day90.map((item, i) => (
                  <div key={i} className="p-3 bg-primary-50 dark:bg-primary-900/30 rounded-lg border border-primary-100 dark:border-primary-800">
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-100">{item.title}</div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{item.action}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ============================================================================
// ANALYTICS TAB
// ============================================================================
interface AnalyticsTabProps {
  summary: AssessmentSummary;
}

export function AnalyticsTab({ summary }: AnalyticsTabProps) {
  const analytics = summary.analytics

  if (!analytics) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Route className="h-16 w-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Analytics Available</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Advanced analytics will appear here once the assessment is scored and findings are generated.
          </p>
        </CardContent>
      </Card>
    )
  }

  const { attack_paths, detection_gaps, response_gaps, identity_gaps, risk_summary } = analytics

  // Safe checks for empty lists
  const hasAttackPaths = attack_paths && attack_paths.length > 0
  const hasDetectionGaps = detection_gaps && detection_gaps.categories && detection_gaps.categories.length > 0
  const hasResponseGaps = response_gaps && response_gaps.categories && response_gaps.categories.length > 0
  const hasIdentityGaps = identity_gaps && identity_gaps.categories && identity_gaps.categories.length > 0

  const hasAnyContent = hasAttackPaths || hasDetectionGaps || hasResponseGaps || hasIdentityGaps

  if (!hasAnyContent) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Critical Risks Detected</h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-lg mx-auto">
            Great job! Our analysis did not identify any major attack paths or critical security gaps based on the current assessment findings.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-8">

      {/* Risk Summary Cards */}
      {risk_summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-red-800 dark:text-red-300">Critical Risks</div>
              <div className="text-2xl font-bold text-red-900 dark:text-red-200">{risk_summary.severity_counts?.critical || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-orange-50 dark:bg-orange-900/20 border-orange-100 dark:border-orange-800">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-orange-800 dark:text-orange-300">High Risks</div>
              <div className="text-2xl font-bold text-orange-900 dark:text-orange-200">{risk_summary.severity_counts?.high || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Findings</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{risk_summary.findings_count || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-100 dark:border-blue-800">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-blue-800 dark:text-blue-300">Risk Score</div>
              <div className="text-2xl font-bold text-blue-900 dark:text-blue-200">{risk_summary.total_risk_score || 0}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Attack Paths */}
      {hasAttackPaths && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Route className="h-5 w-5 text-danger-500" />
              Top Attack Paths Enabled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Based on the identified gaps, the following attack paths may be exploitable:
            </p>
            <div className="space-y-4">
              {attack_paths.map((path: AttackPath) => (
                <div
                  key={path.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-danger-200 dark:hover:border-danger-700 transition-colors bg-white dark:bg-gray-800"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">{path.name}</h4>
                        <Badge className={getLikelihoodColor(path.likelihood)}>
                          {path.likelihood || 'Medium'} likelihood
                        </Badge>
                        <Badge className={getLikelihoodColor(path.impact)}>
                          {path.impact || 'High'} impact
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{path.description}</p>
                    </div>
                  </div>

                  {/* Attack Steps (Techniques) */}
                  {path.steps && path.steps.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Attack Progression:</div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {path.steps.map((step: AttackStep, i: number) => (
                          <div key={i} className="flex items-center gap-2">
                            <div className="px-2 py-1 bg-danger-50 dark:bg-danger-900/30 text-danger-700 dark:text-danger-300 rounded text-xs">
                              {step.step ? `${step.step}. ` : ''}{step.action}
                            </div>
                            {i < path.steps.length - 1 && (
                              <ChevronRight className="h-4 w-4 text-gray-400" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Techniques (if steps not available but techniques list is) */}
                  {/* @ts-ignore - handling backend payload variation */}
                  {path.techniques && path.techniques.length > 0 && !path.steps && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Techniques Used:</div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* @ts-ignore */}
                        {path.techniques.map((tech: { id: string; name: string }, i: number) => (
                          <div key={i} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs border border-gray-200 dark:border-gray-600">
                            {tech.name || tech.id}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Enabling Gaps */}
                  {path.enabling_gaps && path.enabling_gaps.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Enabled by these gaps:</div>
                      <div className="flex flex-wrap gap-2">
                        {path.enabling_gaps.map((gap: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs border border-red-100 dark:border-red-800">
                            {gap}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gap Analysis Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Gaps */}
        {hasDetectionGaps && (
          <GapAnalysisCard
            title="Detection Gaps"
            icon={<ShieldAlert className="h-5 w-5 text-orange-500" />}
            categories={detection_gaps.categories}
          />
        )}

        {/* Response Gaps */}
        {hasResponseGaps && (
          <GapAnalysisCard
            title="Response Gaps"
            icon={<Zap className="h-5 w-5 text-blue-500" />}
            categories={response_gaps.categories}
          />
        )}

        {/* Identity Gaps */}
        {hasIdentityGaps && (
          <GapAnalysisCard
            title="Identity & Access Gaps"
            icon={<AlertTriangle className="h-5 w-5 text-purple-500" />}
            categories={identity_gaps.categories}
          />
        )}
      </div>
    </div>
  )
}

function GapAnalysisCard({ title, icon, categories }: { title: string, icon: React.ReactNode, categories: any[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {categories.map((cat, i) => (
            <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-100 dark:border-gray-700">
              <div className="flex justify-between items-start mb-1">
                <div className="font-medium text-sm text-gray-900 dark:text-gray-100">{cat.category}</div>
                <Badge variant="outline" className={cat.is_critical ? "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800" : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"}>
                  {cat.gap_count} gaps
                </Badge>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{cat.description}</p>

              {cat.findings && cat.findings.length > 0 && (
                <div className="space-y-1 pl-2 border-l-2 border-gray-200 dark:border-gray-600">
                  {cat.findings.map((f: any, j: number) => (
                    <div key={j} className="text-xs text-gray-700 dark:text-gray-300 truncate" title={f.title}>
                      • {f.title}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Re-export from config file for backward compatibility
export { RESULT_TABS, type ResultTabId } from './ResultsTabsConfig'
