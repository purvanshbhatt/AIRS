/**
 * Suggested Questions Panel
 *
 * Displays AI-prioritised questions the organisation should address next,
 * based on current maturity, weakest control functions, and gap analysis.
 */

import { useEffect, useState } from 'react'
import {
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Filter,
  ArrowUpDown,
  Sparkles,
  Target,
  Zap,
  Shield,
} from 'lucide-react'
import { getSuggestedQuestions } from '../api'
import type { SuggestedQuestion, SuggestionsResponse } from '../types'

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface Props {
  orgId: string
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

const MATURITY_COLORS: Record<string, string> = {
  basic: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  managed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  advanced: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
}

const EFFORT_COLORS: Record<string, string> = {
  low: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  high: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
}

const IMPACT_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700 dark:bg-slate-700 dark:text-gray-300',
  medium: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  high: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
}

const FUNCTION_ICONS: Record<string, React.ReactNode> = {
  govern: <Shield className="w-3.5 h-3.5" />,
  identify: <Target className="w-3.5 h-3.5" />,
  protect: <Shield className="w-3.5 h-3.5" />,
  detect: <Zap className="w-3.5 h-3.5" />,
  respond: <Sparkles className="w-3.5 h-3.5" />,
  recover: <Lightbulb className="w-3.5 h-3.5" />,
}

type SortKey = 'impact' | 'effort' | 'maturity'

const LEVEL_ORDER: Record<string, number> = { low: 0, medium: 1, high: 2, basic: 0, managed: 1, advanced: 2 }

function sortQuestions(list: SuggestedQuestion[], key: SortKey, asc: boolean): SuggestedQuestion[] {
  return [...list].sort((a, b) => {
    const fieldMap: Record<SortKey, keyof SuggestedQuestion> = {
      impact: 'impact_level',
      effort: 'effort_level',
      maturity: 'maturity_level',
    }
    const field = fieldMap[key]
    const av = LEVEL_ORDER[a[field] as string] ?? 0
    const bv = LEVEL_ORDER[b[field] as string] ?? 0
    return asc ? av - bv : bv - av
  })
}

/* ------------------------------------------------------------------ */
/*  Badge                                                              */
/* ------------------------------------------------------------------ */

function Badge({ label, colorMap }: { label: string; colorMap: Record<string, string> }) {
  const cls = colorMap[label] ?? 'bg-gray-100 text-gray-700 dark:bg-slate-700 dark:text-gray-300'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label}
    </span>
  )
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function SuggestedQuestionsPanel({ orgId }: Props) {
  const [data, setData] = useState<SuggestionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)
  const [filterFunction, setFilterFunction] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('impact')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getSuggestedQuestions(orgId)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message ?? 'Failed to load suggestions')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [orgId])

  /* nothing to render while loading / error / empty  */
  if (loading) {
    return (
      <div className="my-4 p-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 animate-pulse">
        <div className="h-5 bg-gray-200 dark:bg-slate-700 rounded w-48 mb-3" />
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return null // silent fail — suggestions are non-critical
  }

  if (!data || data.suggestions.length === 0) {
    return null
  }

  /* Derive unique control functions for filter dropdown */
  const allFunctions = Array.from(new Set(data.suggestions.map((q) => q.control_function))).sort()

  /* Apply filter + sort */
  let visible = data.suggestions
  if (filterFunction) {
    visible = visible.filter((q) => q.control_function === filterFunction)
  }
  visible = sortQuestions(visible, sortKey, sortAsc)

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
  }

  return (
    <div className="my-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/60 transition-colors"
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-800 dark:text-gray-200">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          Suggested Next Questions
          <span className="ml-1 text-xs font-normal text-gray-500 dark:text-gray-400">
            ({data.total_count} available)
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {expanded && (
        <div className="px-5 pb-4">
          {/* Meta row: maturity + weakest functions */}
          {(data.org_maturity || (data.weakest_functions && data.weakest_functions.length > 0)) && (
            <div className="flex flex-wrap items-center gap-3 mb-3 text-xs text-gray-500 dark:text-gray-400">
              {data.org_maturity && (
                <span>
                  Org maturity: <strong className="text-gray-700 dark:text-gray-200">{data.org_maturity}</strong>
                </span>
              )}
              {data.weakest_functions && data.weakest_functions.length > 0 && (
                <span>
                  Weakest:{' '}
                  {data.weakest_functions.map((f) => (
                    <span
                      key={f}
                      className="inline-flex items-center gap-0.5 ml-1 capitalize text-gray-700 dark:text-gray-200 font-medium"
                    >
                      {FUNCTION_ICONS[f]}
                      {f}
                    </span>
                  ))}
                </span>
              )}
            </div>
          )}

          {/* Toolbar: filter + sort */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <Filter className="w-3.5 h-3.5" />
              <select
                value={filterFunction ?? ''}
                onChange={(e) => setFilterFunction(e.target.value || null)}
                className="bg-transparent border border-gray-200 dark:border-slate-700 rounded px-1.5 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
              >
                <option value="">All functions</option>
                {allFunctions.map((fn) => (
                  <option key={fn} value={fn}>
                    {fn}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <ArrowUpDown className="w-3.5 h-3.5" />
              {(['impact', 'effort', 'maturity'] as SortKey[]).map((k) => (
                <button
                  key={k}
                  onClick={() => toggleSort(k)}
                  className={`px-1.5 py-0.5 rounded text-xs capitalize ${
                    sortKey === k
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 font-medium'
                      : 'hover:bg-gray-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {k}
                  {sortKey === k && (sortAsc ? ' ↑' : ' ↓')}
                </button>
              ))}
            </div>
          </div>

          {/* Question list */}
          <div className="space-y-2">
            {visible.map((q) => (
              <div
                key={q.id}
                className="flex flex-col sm:flex-row sm:items-start gap-2 p-3 rounded-lg bg-gray-50 dark:bg-slate-800/60 border border-gray-100 dark:border-slate-700/60"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 dark:text-gray-200 leading-snug">
                    {q.question_text}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <Badge label={q.maturity_level} colorMap={MATURITY_COLORS} />
                    <Badge label={`effort: ${q.effort_level}`} colorMap={{ [`effort: ${q.effort_level}`]: EFFORT_COLORS[q.effort_level] }} />
                    <Badge label={`impact: ${q.impact_level}`} colorMap={{ [`impact: ${q.impact_level}`]: IMPACT_COLORS[q.impact_level] }} />
                    <span className="inline-flex items-center gap-0.5 text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {FUNCTION_ICONS[q.control_function]}
                      {q.control_function}
                    </span>
                  </div>
                  {q.framework_tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {q.framework_tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {visible.length === 0 && filterFunction && (
            <p className="text-xs text-gray-400 italic">No suggestions for "{filterFunction}" function.</p>
          )}
        </div>
      )}
    </div>
  )
}
