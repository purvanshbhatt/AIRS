import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getAssessmentSummary,
  downloadReport,
  downloadExecutiveSummary,
  exportAssessmentForSiem,
  createReport,
  ApiRequestError,
} from '../api'
import type { AssessmentSummary } from '../types'
import {
  Card,
  CardContent,
  Button,
  Badge,
} from '../components/ui'
import {
  Download,
  FileText,
  ArrowLeft,
  Plus,
  Copy,
  Check,
  Clock,
  Building2,
  Home,
  Save,
  BarChart3,
  Shield,
  Route,
  TrendingUp,
  AlertTriangle,
  Map,
} from 'lucide-react'
import { clsx } from 'clsx'
import ProgressSteps from '../components/ProgressSteps'
import { useMockTrustData } from '../hooks/useMockTrustData'
import TrustScore from '../components/dashboard/TrustScore'
import VerificationSummaryGrid from '../components/dashboard/VerificationSummaryGrid'
import EvidenceTimeline from '../components/dashboard/EvidenceTimeline'

function getReadinessLevel(score: number): { label: string; variant: 'danger' | 'warning' | 'primary' | 'success' } {
  if (score <= 40) return { label: 'Critical', variant: 'danger' }
  if (score <= 60) return { label: 'At Risk', variant: 'warning' }
  if (score <= 80) return { label: 'Managed', variant: 'primary' }
  return { label: 'Resilient', variant: 'success' }
}

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const [summary, setSummary] = useState<AssessmentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [executiveDownloading, setExecutiveDownloading] = useState(false)
  const [exportingSiem, setExportingSiem] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [isAccessDenied, setIsAccessDenied] = useState(false)

  const { data: trustData, loading: trustLoading } = useMockTrustData(id)

  useEffect(() => {
    getAssessmentSummary(id!)
      .then(setSummary)
      .catch((err) => {
        if (err instanceof ApiRequestError) {
          if (err.status === 404 || err.status === 403) {
            setIsAccessDenied(true)
            setError("You don't have access to this assessment.")
          } else {
            setError(err.toDisplayMessage())
          }
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load assessment')
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
      link.download = `ResilAI_Report_${id}.pdf`
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

  const handleDownloadExecutiveSummary = async () => {
    setExecutiveDownloading(true)
    try {
      const blob = await downloadExecutiveSummary(id!)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ResilAI_Executive_Risk_Summary_${id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage())
      } else {
        setError(err instanceof Error ? err.message : 'Failed to download executive summary')
      }
    } finally {
      setExecutiveDownloading(false)
    }
  }

  const handleExportForSiem = async () => {
    setExportingSiem(true)
    try {
      const payload = await exportAssessmentForSiem(id!)
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ResilAI_SIEM_Export_${id}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage())
      } else {
        setError(err instanceof Error ? err.message : 'Failed to export findings')
      }
    } finally {
      setExportingSiem(false)
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



  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading || trustLoading) {
    return <ProgressSteps />
  }

  if (error) {
    if (isAccessDenied) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <Card className="max-w-md w-full">
            <CardContent className="py-12 text-center">
              <Shield className="h-16 w-16 text-warning-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Access Denied</h2>
              <p className="text-gray-600 dark:text-slate-300 mb-6">{error}</p>
              <div className="flex flex-col gap-3">
                <Link to="/dashboard">
                  <Button className="w-full gap-2">
                    <Home className="h-4 w-4" />
                    Go to Dashboard
                  </Button>
                </Link>
                <Link to="/dashboard/assessments">
                  <Button variant="secondary" className="w-full">
                    View Your Assessments
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md w-full">
          <CardContent className="py-12 text-center">
            <FileText className="h-16 w-16 text-danger-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Error Loading Assessment</h2>
            <p className="text-gray-600 dark:text-slate-300 mb-6">{error}</p>
            <Link to="/dashboard">
              <Button>Back to Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!summary) {
    return (
      <Card className="max-w-md mx-auto mt-12">
        <CardContent className="py-12 text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Assessment Not Found</h2>
          <p className="text-gray-600 dark:text-slate-300 mb-6">The requested assessment could not be loaded</p>
          <Link to="/dashboard">
            <Button>Back to Dashboard</Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  const readinessLevel = getReadinessLevel(summary.overall_score)

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-slate-400">
            <Building2 className="h-4 w-4" />
            <span>{summary.organization_name || 'Organization'}</span>
            <span className="text-gray-300 dark:text-slate-600">|</span>
            <Clock className="h-4 w-4" />
            <span>{formatDate(summary.created_at)}</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">
            {summary.title || 'AI Readiness Assessment'}
          </h1>
          <div className="flex items-center gap-2">
            <Badge variant={readinessLevel.variant}>Readiness Level: {readinessLevel.label}</Badge>
            <Badge variant="outline">Readiness Score: {Math.round(summary.overall_score)}</Badge>
          </div>
          <p className="text-gray-600 dark:text-slate-300">Assessment ID: {id?.slice(0, 8)}...</p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyLink}
            className="gap-2"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? 'Copied!' : 'Share Link'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleSaveReport}
            disabled={saving || saved}
            className="gap-2"
          >
            <Save className="h-4 w-4" />
            {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Report'}
          </Button>
          <Button
            size="sm"
            onClick={handleDownload}
            disabled={downloading}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {downloading ? 'Downloading...' : 'Download PDF'}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleDownloadExecutiveSummary}
            disabled={executiveDownloading}
            className="gap-2"
          >
            <FileText className="h-4 w-4" />
            {executiveDownloading ? 'Downloading...' : 'Download Board Briefing (1-Page)'}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleExportForSiem}
            disabled={exportingSiem}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {exportingSiem ? 'Exporting...' : 'Export for SIEM'}
          </Button>
        </div>
      </div>
      <div className="text-[10px] text-indigo-600/80 dark:text-indigo-400/80 font-medium mb-6">
        The Board Briefing is AI-synthesized strictly from deterministic findings and telemetry. AI does not calculate readiness scores or assess compliance.
      </div>

      {/* Trust Score Hero breakdown */}
      <TrustScore
        score={trustData?.overallScore ?? Math.round(summary.overall_score)}
        verifiedTelemetryPct={trustData?.verifiedTelemetryPct ?? 65}
        selfAttestedPct={trustData?.selfAttestedPct ?? 35}
      />

      {/* Verification summary counts grid */}
      <VerificationSummaryGrid
        verified={trustData?.verificationSummary.verified ?? 22}
        partiallyVerified={trustData?.verificationSummary.partiallyVerified ?? 14}
        selfAttested={trustData?.verificationSummary.selfAttested ?? 12}
        notVerified={trustData?.verificationSummary.notVerified ?? 8}
      />

      {/* Historical trend charting and evidence transition activity logs */}
      <EvidenceTimeline
        trendData={trustData?.trendData ?? []}
        events={trustData?.events ?? []}
      />

      {/* Actions Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 py-4">
        <Link to="/dashboard">
          <Button variant="secondary" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </Link>
        <Link to={summary.organization_id ? `/assessment/new?org=${summary.organization_id}` : '/assessment/new'}>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Start New Assessment
          </Button>
        </Link>
      </div>
    </div>
  )
}


