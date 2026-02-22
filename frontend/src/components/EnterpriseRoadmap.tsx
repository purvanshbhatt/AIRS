// @ts-nocheck
/**
 * EnterpriseRoadmap — Phase 3: Graphical Executive Roadmap
 *
 * Features:
 *  1. Tiered timeline lanes: Immediate (0–30d) / Near-term (30–90d) / Strategic (90+d)
 *  2. Effort vs Impact 2×2 matrix with quadrant assignment
 *  3. Legend explaining assignment logic
 *  4. Graceful fallback when effort/impact data is absent
 */

import React, { useMemo } from 'react'
import { AlertTriangle, Zap, Clock, TrendingUp, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Badge } from './ui'
import type { DetailedRoadmapItem, AssessmentSummary } from '../types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TimelineLane = 'immediate' | 'near-term' | 'strategic'

interface EnrichedItem extends DetailedRoadmapItem {
  derivedLane: TimelineLane
  effortNum: number   // 1-5
  impactNum: number   // 1-5
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const EFFORT_MAP: Record<string, number> = {
  low: 1, minimal: 1,
  medium: 3, moderate: 3,
  high: 5, significant: 5,
}

const IMPACT_MAP: Record<string, number> = {
  low: 1, minimal: 1,
  medium: 3, moderate: 3, 'critical risk reduction': 5,
  high: 4, critical: 5, significant: 4,
}

function parseEffort(item: DetailedRoadmapItem): number {
  const raw = (item.effort || item.effort_estimate || '').toLowerCase()
  for (const [k, v] of Object.entries(EFFORT_MAP)) {
    if (raw.includes(k)) return v
  }
  // fallback from phase
  if (item.phase === '30') return 1
  if (item.phase === '60') return 3
  return 5
}

function parseImpact(item: DetailedRoadmapItem): number {
  const raw = (item.risk_impact || '').toLowerCase()
  for (const [k, v] of Object.entries(IMPACT_MAP)) {
    if (raw.includes(k)) return v
  }
  // severity-based fallback
  const sev = (item.severity || item.priority || '').toLowerCase()
  if (sev === 'critical') return 5
  if (sev === 'high') return 4
  if (sev === 'medium') return 3
  return 2
}

function deriveLane(effort: number, impact: number, item: DetailedRoadmapItem): TimelineLane {
  // Explicit timeline_label wins
  const tl = (item.timeline_label || '').toLowerCase()
  if (tl.includes('immediate')) return 'immediate'
  if (tl.includes('near')) return 'near-term'
  if (tl.includes('strategic')) return 'strategic'

  // Matrix logic from spec: impact≥4 && effort≤2 → Immediate; impact≥4 && effort≥3 → Near-term; else → Strategic
  if (impact >= 4 && effort <= 2) return 'immediate'
  if (impact >= 4 && effort >= 3) return 'near-term'
  return 'strategic'
}

function getSeverityVariant(sev: string): 'danger' | 'warning' | 'default' | 'outline' {
  const s = (sev || '').toUpperCase()
  if (s === 'CRITICAL') return 'danger'
  if (s === 'HIGH') return 'warning'
  if (s === 'MEDIUM') return 'default'
  return 'outline'
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TimelineLaneCard({
  lane,
  items,
  icon,
  color,
}: {
  lane: string
  items: EnrichedItem[]
  icon: React.ReactNode
  color: string
}) {
  if (items.length === 0) return null
  return (
    <div className={`rounded-xl border-2 ${color} overflow-hidden`}>
      <div className={`px-5 py-3 flex items-center justify-between ${color.replace('border', 'bg').replace('-200', '-100').replace('-800', '-900/50')}`}>
        <div className="flex items-center gap-2 font-semibold text-sm">
          {icon}
          {lane}
        </div>
        <span className="text-xs opacity-70">{items.length} item{items.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="p-4 space-y-3 bg-white dark:bg-gray-900">
        {items.map((item, i) => (
          <div
            key={item.finding_id || item.id || i}
            className="p-3 rounded-lg border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition-colors"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-1.5 mb-1">
                  <Badge variant={getSeverityVariant(item.severity || item.priority)}>
                    {item.severity || item.priority}
                  </Badge>
                  {item.nist_category && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                      NIST CSF: {item.nist_category}
                    </span>
                  )}
                  {item.risk_impact && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800">
                      {item.risk_impact}
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                {item.action && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.action}</p>
                )}
              </div>
              {/* Impact vs Effort mini-indicator */}
              <div className="flex-shrink-0 text-right">
                <div className="text-[10px] text-gray-400 dark:text-gray-500">Impact</div>
                <div className="text-xs font-semibold text-gray-700 dark:text-gray-300">{item.impactNum}/5</div>
                <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">Effort</div>
                <div className="text-xs font-semibold text-gray-700 dark:text-gray-300">{item.effortNum}/5</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Effort vs Impact Matrix
// ---------------------------------------------------------------------------

function EffortImpactMatrix({ items }: { items: EnrichedItem[] }) {
  // Quadrant labels (Impact on Y, Effort on X)
  const quadrants = [
    {
      id: 'q1',
      label: 'Quick Wins',
      sub: 'High Impact, Low Effort',
      color: 'bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800',
      titleColor: 'text-success-700 dark:text-success-300',
      filter: (it: EnrichedItem) => it.impactNum >= 4 && it.effortNum <= 2,
    },
    {
      id: 'q2',
      label: 'Strategic Bets',
      sub: 'High Impact, High Effort',
      color: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
      titleColor: 'text-blue-700 dark:text-blue-300',
      filter: (it: EnrichedItem) => it.impactNum >= 4 && it.effortNum >= 3,
    },
    {
      id: 'q3',
      label: 'Fill Ins',
      sub: 'Low Impact, Low Effort',
      color: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
      titleColor: 'text-gray-600 dark:text-gray-300',
      filter: (it: EnrichedItem) => it.impactNum < 4 && it.effortNum <= 2,
    },
    {
      id: 'q4',
      label: 'Deprioritize',
      sub: 'Low Impact, High Effort',
      color: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
      titleColor: 'text-amber-700 dark:text-amber-300',
      filter: (it: EnrichedItem) => it.impactNum < 4 && it.effortNum >= 3,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="h-5 w-5 text-primary-500" />
          Effort vs. Risk Reduction Impact
        </CardTitle>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Each remediation item is classified by estimated implementation effort (X) and
          risk reduction impact (Y). Focus on Quick Wins first, then Strategic Bets.
        </p>
      </CardHeader>
      <CardContent>
        {/* 2×2 grid */}
        <div className="grid grid-cols-2 gap-3">
          {quadrants.map((q) => {
            const qItems = items.filter(q.filter)
            return (
              <div
                key={q.id}
                className={`rounded-lg border p-4 ${q.color} min-h-[100px]`}
              >
                <div className={`text-sm font-semibold mb-0.5 ${q.titleColor}`}>{q.label}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 mb-2">{q.sub}</div>
                {qItems.length === 0 ? (
                  <p className="text-xs text-gray-400 dark:text-gray-500 italic">No items</p>
                ) : (
                  <div className="space-y-1">
                    {qItems.slice(0, 4).map((it, i) => (
                      <div key={i} className="text-xs text-gray-700 dark:text-gray-300 truncate" title={it.title}>
                        • {it.title}
                      </div>
                    ))}
                    {qItems.length > 4 && (
                      <div className="text-[10px] text-gray-400 dark:text-gray-500">+{qItems.length - 4} more</div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Axis labels */}
        <div className="flex items-center justify-between mt-3 px-1 text-[10px] text-gray-400 dark:text-gray-500">
          <span>← Low Effort</span>
          <span>High Effort →</span>
        </div>
        <div className="flex justify-center mt-0.5">
          <div className="text-[10px] text-gray-400 dark:text-gray-500">
            ↕ Risk Reduction Impact (Low bottom → High top)
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
            <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-700 dark:text-blue-300">
              <strong>Assignment logic:</strong> Items with Impact ≥ 4 and Effort ≤ 2 are
              classified as <em>Immediate</em>. Items with Impact ≥ 4 and Effort ≥ 3 are
              classified as <em>Near-term</em>. Remaining items are classified as{' '}
              <em>Strategic</em>. Scores are derived from severity, NIST impact area, and
              explicit risk_impact/effort fields when present.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface EnterpriseRoadmapProps {
  summary: AssessmentSummary
}

export function EnterpriseRoadmap({ summary }: EnterpriseRoadmapProps) {
  const detailedRoadmap = summary.detailed_roadmap

  /** Flatten all items from all phases */
  const rawItems: DetailedRoadmapItem[] = useMemo(() => {
    if (!detailedRoadmap?.phases) return []
    // detailed_roadmap.phases is a dict keyed by "day30" etc.
    return Object.values(detailedRoadmap.phases).flatMap((phase: any) =>
      Array.isArray(phase?.items) ? phase.items : []
    )
  }, [detailedRoadmap])

  const enriched: EnrichedItem[] = useMemo(
    () =>
      rawItems.map((it) => {
        const effortNum = parseEffort(it)
        const impactNum = parseImpact(it)
        return {
          ...it,
          effortNum,
          impactNum,
          derivedLane: deriveLane(effortNum, impactNum, it),
        }
      }),
    [rawItems]
  )

  if (enriched.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <TrendingUp className="h-14 w-14 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No Roadmap Items
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Score the assessment to generate an enterprise-grade remediation roadmap.
          </p>
        </CardContent>
      </Card>
    )
  }

  const immediate = enriched.filter((it) => it.derivedLane === 'immediate')
  const nearTerm = enriched.filter((it) => it.derivedLane === 'near-term')
  const strategic = enriched.filter((it) => it.derivedLane === 'strategic')

  return (
    <div className="space-y-6">
      {/* Header stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 text-center">
          <div className="text-3xl font-bold text-danger-600 dark:text-danger-400">{immediate.length}</div>
          <div className="text-sm text-danger-700 dark:text-danger-300 mt-0.5">Immediate</div>
          <div className="text-[10px] text-danger-500 dark:text-danger-400">0–30 days</div>
        </div>
        <div className="p-4 rounded-xl bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 text-center">
          <div className="text-3xl font-bold text-warning-600 dark:text-warning-400">{nearTerm.length}</div>
          <div className="text-sm text-warning-700 dark:text-warning-300 mt-0.5">Near-term</div>
          <div className="text-[10px] text-warning-500 dark:text-warning-400">30–90 days</div>
        </div>
        <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 text-center">
          <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">{strategic.length}</div>
          <div className="text-sm text-primary-700 dark:text-primary-300 mt-0.5">Strategic</div>
          <div className="text-[10px] text-primary-500 dark:text-primary-400">90+ days</div>
        </div>
      </div>

      {/* Effort vs Impact Matrix */}
      <EffortImpactMatrix items={enriched} />

      {/* Timeline lanes */}
      <div className="space-y-4">
        <TimelineLaneCard
          lane="Immediate (0–30 days)"
          items={immediate}
          icon={<Zap className="h-4 w-4 text-danger-600 dark:text-danger-400" />}
          color="border-danger-200 dark:border-danger-800"
        />
        <TimelineLaneCard
          lane="Near-term (30–90 days)"
          items={nearTerm}
          icon={<Clock className="h-4 w-4 text-warning-600 dark:text-warning-400" />}
          color="border-warning-200 dark:border-warning-800"
        />
        <TimelineLaneCard
          lane="Strategic (90+ days)"
          items={strategic}
          icon={<TrendingUp className="h-4 w-4 text-primary-600 dark:text-primary-400" />}
          color="border-primary-200 dark:border-primary-800"
        />
      </div>
    </div>
  )
}

export default EnterpriseRoadmap
