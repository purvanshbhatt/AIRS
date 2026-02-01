import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getAssessmentSummary, downloadReport, createReport, ApiRequestError } from '../api'
import type { AssessmentSummary } from '../types'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
} from '../components/ui'
import {
  Download,
  FileText,
  AlertTriangle,
  CheckCircle,
  Shield,
  ArrowLeft,
  Plus,
  Target,
  TrendingUp,
  AlertCircle,
  Copy,
  Check,
  Calendar,
  Building2,
  Clock,
  ChevronRight,
  Zap,
  Sparkles,
  Lightbulb,
  Bot,
  ShieldX,
  Home,
  Save,
} from 'lucide-react'

// Map tier color to Tailwind classes
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

// Domain score visual scale (0-5)
function getDomainScaleColor(score: number) {
  if (score >= 4) return 'bg-success-500'
  if (score >= 3) return 'bg-success-400'
  if (score >= 2) return 'bg-warning-400'
  if (score >= 1) return 'bg-warning-500'
  return 'bg-danger-500'
}

function getDomainScaleBg(score: number) {
  if (score >= 4) return 'bg-success-50 text-success-700 border-success-200'
  if (score >= 3) return 'bg-success-50/50 text-success-600 border-success-100'
  if (score >= 2) return 'bg-warning-50 text-warning-700 border-warning-200'
  if (score >= 1) return 'bg-warning-50/50 text-orange-600 border-orange-200'
  return 'bg-danger-50 text-danger-700 border-danger-200'
}

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [summary, setSummary] = useState<AssessmentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [isAccessDenied, setIsAccessDenied] = useState(false)
  const [selectedBaseline, setSelectedBaseline] = useState<string>('Typical SMB')

  useEffect(() => {
    getAssessmentSummary(id!)
      .then(setSummary)
      .catch((err) => {
        if (err instanceof ApiRequestError) {
          // Check for 404 or 403 - these indicate access denied
          if (err.status === 404 || err.status === 403) {
            setIsAccessDenied(true);
            setError("You don't have access to this assessment.");
          } else {
            setError(err.toDisplayMessage());
          }
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load assessment');
        }
      })
      .finally(() => setLoading(false))
  }, [id])

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const blob = await downloadReport(id!)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `AIRS_Report_${id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage())
      } else {
        setError(err instanceof Error ? err.message : 'Failed to download report')
      }
    } finally {
      setDownloading(false)
    }
  }

  const handleSaveReport = async () => {
    setSaving(true)
    try {
      await createReport(id!, { report_type: 'executive_pdf' })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage())
      } else {
        setError(err instanceof Error ? err.message : 'Failed to save report')
      }
    } finally {
      setSaving(false)
    }
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const input = document.createElement('input')
      input.value = window.location.href
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getSeverityVariant = (severity: string) => {
    const s = severity.toUpperCase()
    if (s === 'CRITICAL') return 'danger'
    if (s === 'HIGH') return 'warning'
    if (s === 'MEDIUM') return 'default'
    return 'outline'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading assessment results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    // Special UI for access denied (404/403)
    if (isAccessDenied) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <Card className="max-w-md w-full">
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 bg-danger-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <ShieldX className="h-8 w-8 text-danger-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Access Denied
              </h2>
              <p className="text-gray-600 mb-6">
                You don't have access to this assessment. It may belong to another user or no longer exist.
              </p>
              <Button
                onClick={() => navigate('/home')}
                className="inline-flex items-center gap-2"
              >
                <Home className="h-4 w-4" />
                Back to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      )
    }
    
    // Generic error UI
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="flex items-center gap-3 text-danger-600">
              <AlertCircle className="h-6 w-6" />
              <p className="text-lg">{error}</p>
            </div>
            <Button
              variant="outline"
              onClick={() => navigate('/home')}
              className="mt-2"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!summary) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Assessment Not Found</h2>
          <p className="text-gray-600 mb-6">The requested assessment could not be loaded</p>
          <Link to="/dashboard">
            <Button>Back to Dashboard</Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  const { tier, roadmap, domain_scores, findings, executive_summary } = summary
  const topFailures = findings.slice(0, 5)

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white rounded-xl border border-gray-200 p-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Building2 className="h-4 w-4" />
            <span>{summary.organization_name || 'Organization'}</span>
            <span className="text-gray-300">•</span>
            <Clock className="h-4 w-4" />
            <span>{formatDate(summary.created_at)}</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {summary.title || 'AI Readiness Assessment'}
          </h1>
          <p className="text-gray-600">Assessment ID: {id?.slice(0, 8)}...</p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyLink}
            className="gap-2"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? 'Copied!' : 'Copy Link'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleSaveReport}
            loading={saving}
            className="gap-2"
            disabled={saved}
          >
            {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
            {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Report'}
          </Button>
          <Button
            size="sm"
            onClick={handleDownload}
            loading={downloading}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {downloading ? 'Generating...' : 'Download PDF'}
          </Button>
        </div>
      </div>

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
                <span className="text-sm text-gray-500 mt-1">out of 100</span>
              </div>
            </div>

            {/* Tier & Stats */}
            <div className="text-center lg:text-left space-y-4">
              <div>
                <Badge
                  variant={tier.color as 'danger' | 'warning' | 'success' | 'default'}
                  className="text-lg px-4 py-1.5 mb-2"
                >
                  {tier.label}
                </Badge>
                <p className="text-gray-600 text-sm mt-2">
                  {tier.label === 'Critical' && 'Immediate action required to address security gaps'}
                  {tier.label === 'Needs Work' && 'Several areas require improvement before production'}
                  {tier.label === 'Good' && 'Solid foundation with room for enhancement'}
                  {tier.label === 'Strong' && 'Excellent security posture for AI incident readiness'}
                </p>
              </div>

              <div className="flex items-center justify-center lg:justify-start gap-8 pt-4 border-t border-gray-100">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1.5 text-primary-600 mb-1">
                    <Target className="h-4 w-4" />
                    <span className="text-2xl font-bold">{domain_scores.length}</span>
                  </div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Domains</span>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1.5 text-warning-600 mb-1">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-2xl font-bold">{summary.findings_count}</span>
                  </div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Findings</span>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1.5 text-danger-600 mb-1">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-2xl font-bold">{summary.critical_high_count}</span>
                  </div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Critical/High</span>
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
            <Sparkles className="h-5 w-5 text-primary-500" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 leading-relaxed">{executive_summary}</p>
        </CardContent>
      </Card>

      {/* AI Insights - Only shown when LLM is enabled */}
      {summary.llm_enabled && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-violet-500" />
                AI Insights
              </CardTitle>
              {summary.llm_mode === 'demo' && (
                <Badge variant="default" className="bg-violet-100 text-violet-700 border-violet-200">
                  <Lightbulb className="h-3 w-3 mr-1" />
                  AI-generated (demo)
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AI Executive Summary */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-violet-400" />
                Executive Summary
              </h4>
              {summary.executive_summary_text ? (
                <p className="text-gray-600 leading-relaxed bg-violet-50/50 p-4 rounded-lg border border-violet-100">
                  {summary.executive_summary_text}
                </p>
              ) : (
                <p className="text-gray-400 italic text-sm bg-gray-50 p-4 rounded-lg">
                  AI executive summary is not available for this assessment.
                </p>
              )}
            </div>

            {/* AI Roadmap Narrative */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-violet-400" />
                Roadmap Narrative
              </h4>
              {summary.roadmap_narrative_text ? (
                <p className="text-gray-600 leading-relaxed bg-violet-50/50 p-4 rounded-lg border border-violet-100 whitespace-pre-line">
                  {summary.roadmap_narrative_text}
                </p>
              ) : (
                <p className="text-gray-400 italic text-sm bg-gray-50 p-4 rounded-lg">
                  AI roadmap narrative is not available for this assessment.
                </p>
              )}
            </div>

            {/* LLM info footer */}
            {summary.llm_model && (
              <div className="flex items-center gap-2 pt-3 border-t border-gray-100 text-xs text-gray-400">
                <span>Powered by {summary.llm_provider || 'AI'}</span>
                <span>•</span>
                <span>{summary.llm_model}</span>
              </div>
            )}

            {/* Demo mode disclaimer */}
            {summary.llm_mode === 'demo' && (
              <div className="flex items-start gap-2 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <p>
                  This demo uses AI to generate narrative insights based on assessment results. 
                  Scores and findings are computed deterministically and are not modified by AI.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Domain Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-500" />
            Domain Scores
            <span className="text-sm font-normal text-gray-500 ml-2">(0-5 scale)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3">
            {domain_scores.map((ds) => (
              <div
                key={ds.domain_id}
                className="flex items-center gap-4 p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate">{ds.domain_name}</h4>
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${getDomainScaleColor(ds.score_5)}`}
                        style={{ width: `${(ds.score_5 / 5) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-10 text-right">{ds.weight}%</span>
                  </div>
                </div>
                <div
                  className={`flex items-center justify-center w-14 h-10 rounded-lg border font-bold text-lg ${getDomainScaleBg(ds.score_5)}`}
                >
                  {ds.score_5.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
          
          {/* Legend */}
          <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-gray-100">
            <span className="text-xs text-gray-500">Scale:</span>
            {[
              { label: '0-1', color: 'bg-danger-500' },
              { label: '1-2', color: 'bg-warning-500' },
              { label: '2-3', color: 'bg-warning-400' },
              { label: '3-4', color: 'bg-success-400' },
              { label: '4-5', color: 'bg-success-500' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded ${item.color}`} />
                <span className="text-xs text-gray-600">{item.label}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Benchmark Comparison */}
      {summary.baselines_available && summary.baselines_available.length > 0 && summary.baseline_profiles && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary-500" />
                Benchmark Comparison
              </CardTitle>
              <select
                value={selectedBaseline}
                onChange={(e) => setSelectedBaseline(e.target.value)}
                aria-label="Select baseline profile"
                className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
              >
                {summary.baselines_available.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 pr-4 font-medium text-gray-700">Domain</th>
                    <th className="text-center py-2 px-2 font-medium text-gray-700 w-20">Current</th>
                    <th className="text-center py-2 px-2 font-medium text-gray-700 w-20">Baseline</th>
                    <th className="text-left py-2 pl-4 font-medium text-gray-700 w-32">Comparison</th>
                  </tr>
                </thead>
                <tbody>
                  {domain_scores.map((ds) => {
                    const baselineScore = summary.baseline_profiles?.[selectedBaseline]?.[ds.domain_id] ?? null
                    const diff = baselineScore !== null ? ds.score_5 - baselineScore : null
                    return (
                      <tr key={ds.domain_id} className="border-b border-gray-100 last:border-0">
                        <td className="py-2.5 pr-4 text-gray-900">{ds.domain_name}</td>
                        <td className="py-2.5 px-2 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getDomainScaleBg(ds.score_5)}`}>
                            {ds.score_5.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 text-center">
                          {baselineScore !== null ? (
                            <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              {baselineScore.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="py-2.5 pl-4">
                          {diff !== null ? (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                                <div className="absolute inset-y-0 left-1/2 w-px bg-gray-300" />
                                {diff !== 0 && (
                                  <div
                                    className={`absolute inset-y-0 ${diff > 0 ? 'bg-success-500' : 'bg-danger-500'}`}
                                    style={{
                                      left: diff > 0 ? '50%' : `${50 + (diff / 5) * 50}%`,
                                      width: `${Math.abs(diff / 5) * 50}%`,
                                    }}
                                  />
                                )}
                              </div>
                              <span className={`text-xs font-medium w-10 text-right ${
                                diff > 0 ? 'text-success-600' : diff < 0 ? 'text-danger-600' : 'text-gray-500'
                              }`}>
                                {diff > 0 ? '+' : ''}{diff.toFixed(1)}
                              </span>
                            </div>
                          ) : (
                            <span className="text-gray-400 text-xs">N/A</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top 5 Failure Points */}
      {topFailures.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-danger-500" />
              Top {Math.min(5, topFailures.length)} Failure Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topFailures.map((finding, idx) => (
                <div
                  key={finding.id}
                  className="flex items-start gap-4 p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white border border-gray-200 text-sm font-bold text-gray-600">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={getSeverityVariant(finding.severity)} size="sm">
                        {finding.severity.toUpperCase()}
                      </Badge>
                      {finding.domain && (
                        <span className="text-xs text-gray-500">{finding.domain}</span>
                      )}
                    </div>
                    <h4 className="font-medium text-gray-900 mb-1">{finding.title}</h4>
                    {finding.recommendation && (
                      <p className="text-sm text-gray-600 flex items-start gap-1.5">
                        <ChevronRight className="h-4 w-4 text-primary-500 flex-shrink-0 mt-0.5" />
                        <span className="line-clamp-2">{finding.recommendation}</span>
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 30/60/90 Day Roadmap */}
      {(roadmap.day30.length > 0 || roadmap.day60.length > 0 || roadmap.day90.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary-500" />
              30/60/90 Day Remediation Roadmap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              {/* 30 Days */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-danger-200">
                  <div className="w-3 h-3 rounded-full bg-danger-500" />
                  <h4 className="font-semibold text-danger-700">30 Days</h4>
                  <span className="text-xs text-danger-500 ml-auto">Urgent</span>
                </div>
                {roadmap.day30.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No critical items</p>
                ) : (
                  roadmap.day30.map((item, idx) => (
                    <div key={idx} className="p-3 bg-danger-50 rounded-lg border border-danger-100">
                      <p className="text-sm font-medium text-danger-800 mb-1">{item.title}</p>
                      <p className="text-xs text-danger-600 line-clamp-2">{item.action}</p>
                    </div>
                  ))
                )}
              </div>

              {/* 60 Days */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-warning-200">
                  <div className="w-3 h-3 rounded-full bg-warning-500" />
                  <h4 className="font-semibold text-warning-700">60 Days</h4>
                  <span className="text-xs text-warning-500 ml-auto">High Priority</span>
                </div>
                {roadmap.day60.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No high priority items</p>
                ) : (
                  roadmap.day60.map((item, idx) => (
                    <div key={idx} className="p-3 bg-warning-50 rounded-lg border border-warning-100">
                      <p className="text-sm font-medium text-warning-800 mb-1">{item.title}</p>
                      <p className="text-xs text-warning-600 line-clamp-2">{item.action}</p>
                    </div>
                  ))
                )}
              </div>

              {/* 90 Days */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-primary-200">
                  <div className="w-3 h-3 rounded-full bg-primary-500" />
                  <h4 className="font-semibold text-primary-700">90 Days</h4>
                  <span className="text-xs text-primary-500 ml-auto">Planned</span>
                </div>
                {roadmap.day90.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No planned items</p>
                ) : (
                  roadmap.day90.map((item, idx) => (
                    <div key={idx} className="p-3 bg-primary-50 rounded-lg border border-primary-100">
                      <p className="text-sm font-medium text-primary-800 mb-1">{item.title}</p>
                      <p className="text-xs text-primary-600 line-clamp-2">{item.action}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Findings (Collapsed by default) */}
      {findings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-warning-500" />
                All Security Findings
              </span>
              <Badge variant={findings.length === 0 ? 'success' : 'default'}>
                {findings.length} total
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {findings.map((finding) => (
                <details
                  key={finding.id}
                  className="group border border-gray-200 rounded-lg overflow-hidden"
                >
                  <summary className="flex items-center gap-3 p-4 cursor-pointer hover:bg-gray-50 transition-colors">
                    <Badge variant={getSeverityVariant(finding.severity)} size="sm">
                      {finding.severity.toUpperCase()}
                    </Badge>
                    <span className="flex-1 font-medium text-gray-900">{finding.title}</span>
                    {finding.domain && (
                      <span className="text-xs text-gray-500 hidden sm:inline">{finding.domain}</span>
                    )}
                    <ChevronRight className="h-4 w-4 text-gray-400 transition-transform group-open:rotate-90" />
                  </summary>
                  <div className="px-4 pb-4 pt-2 border-t border-gray-100 bg-gray-50">
                    {finding.description && (
                      <p className="text-sm text-gray-700 mb-3">{finding.description}</p>
                    )}
                    {finding.evidence && (
                      <div className="bg-white rounded p-3 mb-3 border border-gray-200">
                        <p className="text-xs font-medium text-gray-500 mb-1">Evidence</p>
                        <p className="text-sm text-gray-700">{finding.evidence}</p>
                      </div>
                    )}
                    {finding.recommendation && (
                      <div className="bg-primary-50 rounded p-3 border border-primary-100">
                        <p className="text-xs font-medium text-primary-600 mb-1">Recommendation</p>
                        <p className="text-sm text-primary-800">{finding.recommendation}</p>
                      </div>
                    )}
                  </div>
                </details>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Findings State */}
      {findings.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-16 w-16 text-success-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-success-700 mb-2">
              No Security Findings
            </h3>
            <p className="text-gray-600">
              Excellent! Your AI incident readiness posture shows no identified gaps.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Actions Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 py-4">
        <Link to="/dashboard">
          <Button variant="secondary" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </Link>
        <Link to="/assessment/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Assessment
          </Button>
        </Link>
      </div>
    </div>
  )
}
