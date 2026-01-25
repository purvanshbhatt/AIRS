import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getAssessmentSummary, getOrganization, downloadReport, downloadReportById, createReport, getReportsForAssessment, ApiRequestError, refreshNarrative } from '../api'
import type { AssessmentSummary, Report } from '../types'
import {
  Card,
  CardContent,
  Button,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  useToast,
  ApiDiagnosticsPanel,
  ResultsOverviewSkeleton,
  ResultsTabSkeleton,
  ResultsFrameworkSkeleton,
  ResultsAnalyticsSkeleton,
} from '../components/ui'
import {
  Download,
  FileText,
  ArrowLeft,
  Target,
  AlertCircle,
  Copy,
  Check,
  Clock,
  Building2,
  ShieldX,
  Home,
  Save,
  AlertTriangle,
  Shield,
  Calendar,
  Route,
  FolderOpen,
} from 'lucide-react'
import {
  OverviewTab,
  FindingsTab,
  RESULT_TABS,
  type ResultTabId,
} from '../components/ResultsTabs'

// Lazy load heavy tabs for better initial render
const FrameworkTab = lazy(() => import('../components/ResultsTabs').then(m => ({ default: m.FrameworkTab })))
const RoadmapTab = lazy(() => import('../components/ResultsTabs').then(m => ({ default: m.RoadmapTab })))
const AnalyticsTab = lazy(() => import('../components/ResultsTabs').then(m => ({ default: m.AnalyticsTab })))

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { addToast } = useToast()
  const [summary, setSummary] = useState<AssessmentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)
  const [savedReports, setSavedReports] = useState<Report[]>([])
  const [reportsLoading, setReportsLoading] = useState(true)
  const [error, setError] = useState('')
  const [errorObject, setErrorObject] = useState<Error | null>(null)
  const [isAccessDenied, setIsAccessDenied] = useState(false)
  const [selectedBaseline, setSelectedBaseline] = useState<string>('Typical SMB')
  const [suggestedBaseline, setSuggestedBaseline] = useState<string | undefined>()
  const [activeTab, setActiveTab] = useState<ResultTabId>('overview')
  const [isRefreshingNarrative, setIsRefreshingNarrative] = useState(false)

  // Load saved reports for this assessment
  const loadSavedReports = useCallback(async () => {
    if (!id) return
    setReportsLoading(true)
    try {
      const response = await getReportsForAssessment(id)
      setSavedReports(response.reports)
    } catch {
      // Silently fail - reports indicator is not critical
      console.log('Could not load saved reports')
    } finally {
      setReportsLoading(false)
    }
  }, [id])

  useEffect(() => {
    getAssessmentSummary(id!)
      .then(async (data) => {
        setSummary(data)

        // Fetch organization to check for suggested baseline
        if (data.organization_id) {
          try {
            const org = await getOrganization(data.organization_id);
            if (org.baseline_suggestion) {
              setSuggestedBaseline(org.baseline_suggestion.replace('_', ' ')); // Normalize
            }
          } catch (err) {
            console.log('Could not load organization details');
          }
        }
      })
      .catch((err) => {
        setErrorObject(err instanceof Error ? err : new Error(String(err)));
        if (err instanceof ApiRequestError) {
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

    // Also load saved reports
    loadSavedReports()
  }, [id, loadSavedReports])

  // Handle refresh AI narrative
  const handleRefreshNarrative = useCallback(async () => {
    if (!id || isRefreshingNarrative) return
    
    setIsRefreshingNarrative(true)
    try {
      const result = await refreshNarrative(id)
      
      // Update the summary with the new narratives
      if (summary && result.llm_status === 'ready') {
        setSummary({
          ...summary,
          executive_summary_text: result.executive_summary_text || undefined,
          roadmap_narrative_text: result.roadmap_narrative_text || undefined,
          llm_status: result.llm_status,
        })
        addToast({
          title: 'AI Insights Ready',
          message: 'AI-generated insights have been loaded.',
          type: 'success',
        })
      } else if (result.llm_status === 'pending') {
        // Still pending, show toast
        addToast({
          title: 'Still Generating',
          message: 'AI insights are still being generated. Try again in a few seconds.',
          type: 'info',
        })
      }
    } catch (err) {
      addToast({
        title: 'Refresh Failed',
        message: 'Could not refresh AI insights. Please try again.',
        type: 'error',
      })
    } finally {
      setIsRefreshingNarrative(false)
    }
  }, [id, isRefreshingNarrative, summary, addToast])

  const handleDownload = async () => {
    setDownloading(true)
    try {
      let blob: Blob
      let filename: string

      // If we have a saved report, download it; otherwise generate on the fly
      if (savedReports.length > 0) {
        const latestReport = savedReports[0]
        blob = await downloadReportById(latestReport.id)
        const safeTitle = (latestReport.title || 'Report').replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '')
        filename = `AIRS_Report_${safeTitle}.pdf`
      } else {
        blob = await downloadReport(id!)
        filename = `AIRS_Report_${id}.pdf`
      }

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
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
      const newReport = await createReport(id!, { report_type: 'full' })
      setSaved(true)

      // Add to local state immediately
      setSavedReports(prev => [newReport, ...prev])

      // Show success toast
      addToast({
        type: 'success',
        title: 'Report Saved!',
        message: 'Your report has been saved and is available in Reports.',
      })

      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage())
        addToast({
          type: 'error',
          title: 'Failed to save report',
          message: err.toDisplayMessage(),
        })
      } else {
        setError(err instanceof Error ? err.message : 'Failed to save report')
        addToast({
          type: 'error',
          title: 'Failed to save report',
          message: err instanceof Error ? err.message : 'Unknown error',
        })
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

  // Loading state - show skeleton for better perceived performance
  if (loading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header skeleton */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="animate-pulse flex items-center gap-4">
            <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
            <div className="flex-1">
              <div className="h-4 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
              <div className="h-6 w-64 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          </div>
        </div>
        {/* Tabs skeleton */}
        <div className="flex gap-2 mb-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
          ))}
        </div>
        {/* Content skeleton */}
        <ResultsOverviewSkeleton />
      </div>
    )
  }

  // Access denied
  if (isAccessDenied) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md w-full">
          <CardContent className="py-12 text-center">
            <div className="w-16 h-16 bg-danger-100 dark:bg-danger-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <ShieldX className="h-8 w-8 text-danger-600 dark:text-danger-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              You don't have access to this assessment. It may belong to another user or no longer exist.
            </p>
            <Button
              onClick={() => navigate('/dashboard')}
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

  // Error state
  if (error) {
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
              onClick={() => navigate('/dashboard')}
              className="mt-2"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
          {/* Show API Diagnostics for network/CORS errors */}
          {errorObject && (
            <ApiDiagnosticsPanel error={errorObject} autoRun={true} compact={false} />
          )}
        </CardContent>
      </Card>
    )
  }

  // Not found
  if (!summary) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-16 w-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Assessment Not Found</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">The requested assessment could not be loaded</p>
          <Link to="/dashboard">
            <Button>Back to Dashboard</Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  // Tab icons map
  const tabIcons: Record<ResultTabId, typeof Target> = {
    overview: Target,
    findings: AlertTriangle,
    framework: Shield,
    roadmap: Calendar,
    analytics: Route,
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Saved Reports Indicator */}
      {!reportsLoading && savedReports.length > 0 && (
        <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-4 py-3">
          <div className="flex items-center gap-3">
            <FolderOpen className="h-5 w-5 text-green-600" />
            <span className="text-green-800 font-medium">
              {savedReports.length} saved report{savedReports.length !== 1 ? 's' : ''}
            </span>
            <span className="text-green-600 text-sm">
              Latest: {formatDate(savedReports[0].created_at)}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/dashboard/reports')}
            className="text-green-700 border-green-300 hover:bg-green-100"
          >
            View All Reports
          </Button>
        </div>
      )}

      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Building2 className="h-4 w-4" />
            <span>{summary.organization_name || 'Organization'}</span>
            <span className="text-gray-300 dark:text-gray-600">•</span>
            <Clock className="h-4 w-4" />
            <span>{formatDate(summary.created_at)}</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {summary.title || 'AI Readiness Assessment'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">Assessment ID: {id?.slice(0, 8)}...</p>
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

      {/* Tabs Navigation */}
      <Tabs defaultValue="overview" value={activeTab} onValueChange={(v) => setActiveTab(v as ResultTabId)}>
        <TabsList className="flex-wrap">
          {RESULT_TABS.map((tab) => {
            const Icon = tabIcons[tab.id]
            return (
              <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
                <Icon className="h-4 w-4" />
                {tab.label}
              </TabsTrigger>
            )
          })}
        </TabsList>

        {/* Tab Content */}
        <div className="mt-6">
          <TabsContent value="overview">
            <OverviewTab
              summary={summary}
              selectedBaseline={selectedBaseline}
              setSelectedBaseline={setSelectedBaseline}
              suggestedBaseline={suggestedBaseline}
              onRefreshNarrative={handleRefreshNarrative}
              isRefreshingNarrative={isRefreshingNarrative}
            />
          </TabsContent>

          <TabsContent value="findings">
            <FindingsTab summary={summary} />
          </TabsContent>

          <TabsContent value="framework">
            <Suspense fallback={<ResultsFrameworkSkeleton />}>
              <FrameworkTab summary={summary} />
            </Suspense>
          </TabsContent>

          <TabsContent value="roadmap">
            <Suspense fallback={<ResultsTabSkeleton />}>
              <RoadmapTab summary={summary} />
            </Suspense>
          </TabsContent>

          <TabsContent value="analytics">
            <Suspense fallback={<ResultsAnalyticsSkeleton />}>
              <AnalyticsTab summary={summary} />
            </Suspense>
          </TabsContent>
        </div>
      </Tabs>

      {/* Actions Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <Button variant="outline" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => navigate(`/assessment/${summary.id}`)}
          >
            <FileText className="h-4 w-4 mr-2" />
            Edit Assessment
          </Button>
          <Button onClick={handleDownload} loading={downloading}>
            <Download className="h-4 w-4 mr-2" />
            Export PDF Report
          </Button>
        </div>
      </div>
    </div>
  )
}
