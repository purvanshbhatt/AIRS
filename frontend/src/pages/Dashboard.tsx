import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  EmptyState,
  StatCardSkeleton,
  CardSkeleton,
} from '../components/ui';
import {
  LayoutDashboard,
  Building2,
  ClipboardList,
  FileCheck,
  Plus,
  ArrowRight,
  TrendingUp,
  Clock,
  Sparkles,
  ShieldCheck,
  Calendar,
} from 'lucide-react';
import {
  getOrganizations,
  getAssessments,
  getSystemStatus,
  listApiKeys,
  listWebhooks,
  getApplicableFrameworks,
  getAuditCalendar,
  ApiRequestError,
} from '../api';
import type { Organization, Assessment, ApplicableFramework, AuditCalendarEntry } from '../types';

interface DashboardStats {
  totalOrgs: number;
  totalAssessments: number;
  completedAssessments: number;
  draftAssessments: number;
  averageScore: number | null;
}

interface IntegrationStatus {
  splunk?: {
    connected?: boolean;
  };
}

function safeParseIntegrationStatus(raw: string | undefined): IntegrationStatus | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as IntegrationStatus;
  } catch {
    return null;
  }
}

function getReadinessLevel(score: number | null): string {
  if (score == null) return 'Unavailable';
  if (score <= 40) return 'Critical';
  if (score <= 60) return 'At Risk';
  if (score <= 80) return 'Managed';
  return 'Resilient';
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [exampleAssessmentId, setExampleAssessmentId] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [integrationSnapshot, setIntegrationSnapshot] = useState({
    splunkConnected: false,
    webhookActive: false,
    apiKeyEnabled: false,
  });
  const [stats, setStats] = useState<DashboardStats>({
    totalOrgs: 0,
    totalAssessments: 0,
    completedAssessments: 0,
    draftAssessments: 0,
    averageScore: null,
  });
  const [recentAssessments, setRecentAssessments] = useState<Assessment[]>([]);
  const [recentOrgs, setRecentOrgs] = useState<Organization[]>([]);
  const [applicableFrameworks, setApplicableFrameworks] = useState<ApplicableFramework[]>([]);
  const [upcomingAudits, setUpcomingAudits] = useState<AuditCalendarEntry[]>([]);

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      setError(null);
      try {
        const [orgs, loadedAssessments, systemStatus] = await Promise.all([
          getOrganizations(),
          getAssessments(),
          getSystemStatus().catch(() => null),
        ]);
        setIsDemoMode(Boolean(systemStatus?.demo_mode));
        setOrganizations(orgs);
        setAssessments(loadedAssessments);
        if (orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }

        const completed = loadedAssessments.filter((assessment) => assessment.status === 'completed');
        const drafts = loadedAssessments.filter((assessment) => assessment.status !== 'completed');
        const scoresWithValues = completed.filter((assessment) => assessment.overall_score != null);
        const avgScore =
          scoresWithValues.length > 0
            ? scoresWithValues.reduce((sum, assessment) => sum + (assessment.overall_score ?? 0), 0) /
              scoresWithValues.length
            : null;

        setStats({
          totalOrgs: orgs.length,
          totalAssessments: loadedAssessments.length,
          completedAssessments: completed.length,
          draftAssessments: drafts.length,
          averageScore: avgScore,
        });

        setRecentAssessments(
          loadedAssessments
            .slice()
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 5)
        );
        const completedForExample = loadedAssessments.filter((assessment) => assessment.status === 'completed');
        setExampleAssessmentId(completedForExample[0]?.id || loadedAssessments[0]?.id || null);
        setRecentOrgs(
          orgs
            .slice()
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 3)
        );
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  useEffect(() => {
    const loadOrgIntegrationSnapshot = async () => {
      if (!selectedOrgId) return;

      try {
        const selectedOrg = organizations.find((org) => org.id === selectedOrgId);
        const integrationStatus = safeParseIntegrationStatus(selectedOrg?.integration_status);
        const [apiKeys, webhooks] = await Promise.all([listApiKeys(selectedOrgId), listWebhooks(selectedOrgId)]);
        const betaDefault = isDemoMode;
        setIntegrationSnapshot({
          splunkConnected: betaDefault ? true : Boolean(integrationStatus?.splunk?.connected),
          webhookActive: betaDefault ? true : webhooks.length > 0,
          apiKeyEnabled: betaDefault ? true : apiKeys.some((key) => key.is_active),
        });
      } catch {
        setIntegrationSnapshot({
          splunkConnected: isDemoMode,
          webhookActive: isDemoMode,
          apiKeyEnabled: isDemoMode,
        });
      }
    };

    loadOrgIntegrationSnapshot();
  }, [selectedOrgId, organizations, isDemoMode]);

  // Load governance widgets when org changes
  useEffect(() => {
    if (!selectedOrgId) return;
    getApplicableFrameworks(selectedOrgId)
      .then((data) => setApplicableFrameworks(data.frameworks))
      .catch(() => setApplicableFrameworks([]));
    getAuditCalendar(selectedOrgId)
      .then((data) => setUpcomingAudits(data.entries.filter((e) => e.is_upcoming).slice(0, 3)))
      .catch(() => setUpcomingAudits([]));
  }, [selectedOrgId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gray-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-gray-600 dark:text-slate-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Dashboard</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">Overview of your security assessments</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="max-w-lg mx-auto mt-12">
        <CardContent className="py-8 text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  const hasNoData = stats.totalOrgs === 0 && stats.totalAssessments === 0;
  const selectedOrgAssessments = selectedOrgId
    ? assessments.filter((assessment) => assessment.organization_id === selectedOrgId)
    : assessments;
  const completedForSelectedOrg = selectedOrgAssessments
    .filter((assessment) => assessment.status === 'completed' && assessment.overall_score != null)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  const latestCompleted = completedForSelectedOrg[0] || null;
  const previousCompleted = completedForSelectedOrg[1] || null;
  const scoreDelta =
    latestCompleted && previousCompleted
      ? (latestCompleted.overall_score ?? 0) - (previousCompleted.overall_score ?? 0)
      : null;

  const selectedOrganization = organizations.find((org) => org.id === selectedOrgId);
  const displayOrganizationName = selectedOrganization?.name || 'Acme Health Systems';
  const displayIndustry = selectedOrganization?.industry || 'Healthcare';
  const displayEmployees = isDemoMode ? '850' : selectedOrganization?.size || 'N/A';
  const displayCurrentScore = isDemoMode
    ? 72
    : latestCompleted
      ? Math.round(latestCompleted.overall_score || 0)
      : null;
  const displayPreviousScore = isDemoMode
    ? 58
    : previousCompleted
      ? Math.round(previousCompleted.overall_score || 0)
      : null;
  const displayDelta = isDemoMode ? 14 : scoreDelta;
  const displayReadinessLevel = getReadinessLevel(displayCurrentScore);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Dashboard</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">Overview of your security assessments</p>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="min-w-[220px]">
            <label className="block text-xs text-gray-500 dark:text-slate-400 mb-1">Organization</label>
            <select
              className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100"
              value={selectedOrgId}
              onChange={(event) => setSelectedOrgId(event.target.value)}
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          </div>
          <Link to="/dashboard/org/new">
            <Button variant="outline" className="gap-2">
              <Plus className="w-4 h-4" />
              New Organization
            </Button>
          </Link>
          <Link to="/dashboard/assessment/new">
            <Button className="gap-2">
              <ClipboardList className="w-4 h-4" />
              New Assessment
            </Button>
          </Link>
        </div>
      </div>

      {hasNoData ? (
        <Card>
          <EmptyState
            icon={ClipboardList}
            title="Welcome to ResilAI"
            description="Get started by creating your first organization, then run a security assessment to evaluate your incident readiness."
            action={{
              label: 'Create Organization',
              href: '/dashboard/org/new',
            }}
          />
        </Card>
      ) : (
        <>
          {isDemoMode && exampleAssessmentId && (
            <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
              <CardContent className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="text-sm text-blue-900 dark:text-blue-200">
                  Public Beta environment contains synthetic example data.
                </div>
                <Button size="sm" className="gap-2" onClick={() => navigate(`/dashboard/results/${exampleAssessmentId}`)}>
                  <Sparkles className="w-4 h-4" />
                  View Executive Report
                </Button>
              </CardContent>
            </Card>
          )}

          <Card padding="md">
            <p className="text-sm text-gray-500 dark:text-slate-400">Organization Profile</p>
            <p className="mt-1 text-lg font-semibold text-gray-900 dark:text-slate-100">{displayOrganizationName}</p>
            <div className="mt-2 text-sm text-gray-700 dark:text-slate-300">Industry: {displayIndustry}</div>
            <div className="text-sm text-gray-700 dark:text-slate-300">Employees: {displayEmployees}</div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card padding="md">
              <p className="text-sm text-gray-500 dark:text-slate-400">Integration Status</p>
              <div className="mt-2 text-sm text-gray-800 dark:text-slate-200 space-y-1">
                <div>Splunk: {integrationSnapshot.splunkConnected ? 'Connected (Last sync: 5 min ago)' : 'Not connected'}</div>
                <div>Webhook: {integrationSnapshot.webhookActive ? 'Active (Last delivery check: 2 min ago)' : 'Inactive'}</div>
                <div>API Key: {integrationSnapshot.apiKeyEnabled ? 'Active' : 'Not generated'}</div>
              </div>
              <Link to="/dashboard/integrations" className="inline-flex mt-3 text-sm text-primary-600 hover:text-primary-700">
                Open Integrations
              </Link>
            </Card>
            <Card padding="md">
              <p className="text-sm text-gray-500 dark:text-slate-400">Last Assessment</p>
              <p className="mt-2 text-base font-semibold text-gray-900 dark:text-slate-100">
                {isDemoMode
                  ? 'Last evaluated: 2 hours ago'
                  : latestCompleted
                    ? new Date(latestCompleted.created_at).toLocaleString()
                    : 'No completed run yet'}
              </p>
              <p className="text-sm text-gray-600 dark:text-slate-300 mt-1">
                Readiness Level: {displayReadinessLevel}
              </p>
            </Card>
            <Card padding="md">
              <p className="text-sm text-gray-500 dark:text-slate-400">Risk Trend</p>
              <p className="mt-2 text-base font-semibold text-gray-900 dark:text-slate-100">
                {displayCurrentScore != null ? `Current: ${displayCurrentScore}%` : 'Current: N/A'}
              </p>
              <p className="text-sm text-gray-600 dark:text-slate-300">
                {displayPreviousScore != null ? `Previous: ${displayPreviousScore}%` : 'Previous: N/A'}
              </p>
              <p className={`text-sm font-medium ${displayDelta != null && displayDelta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {displayDelta == null
                  ? 'Trend unavailable'
                  : `${displayDelta >= 0 ? '^' : 'v'} ${displayDelta >= 0 ? '+' : '-'}${Math.abs(displayDelta).toFixed(0)} ${displayDelta >= 0 ? 'improvement' : 'change'}`}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Organizations</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{stats.totalOrgs}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <ClipboardList className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Total Assessments</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{stats.totalAssessments}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <FileCheck className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Completed</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{stats.completedAssessments}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Avg. Score</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">
                    {stats.averageScore != null ? `${Math.round(stats.averageScore)}%` : '-'}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Clock className="w-5 h-5 text-gray-400" />
                    Recent Assessments
                  </CardTitle>
                  <Link
                    to="/dashboard/assessments"
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    View all <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentAssessments.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-slate-400 italic py-4">No assessments yet</p>
                ) : (
                  <div className="space-y-3">
                    {recentAssessments.map((assessment) => (
                      <Link
                        key={assessment.id}
                        to={
                          assessment.status === 'completed'
                            ? `/dashboard/results/${assessment.id}`
                            : `/dashboard/assessment/new?resume=${assessment.id}`
                        }
                        className="block p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-slate-100">{assessment.title}</p>
                            <p className="text-xs text-gray-500 dark:text-slate-400">
                              {assessment.organization_name || 'Unknown org'} |{' '}
                              {new Date(assessment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              assessment.status === 'completed'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {assessment.status === 'completed' ? 'Completed' : 'Draft'}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-gray-400" />
                    Recent Organizations
                  </CardTitle>
                  <Link
                    to="/dashboard/organizations"
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    View all <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentOrgs.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-slate-400 italic py-4">No organizations yet</p>
                ) : (
                  <div className="space-y-3">
                    {recentOrgs.map((org) => (
                      <div
                        key={org.id}
                        className="p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        <p className="font-medium text-gray-900 dark:text-slate-100">{org.name}</p>
                        <p className="text-xs text-gray-500 dark:text-slate-400">
                          {org.industry || 'No industry'} | {new Date(org.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Governance Quick Glance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-indigo-500" />
                    Applicable Frameworks
                  </CardTitle>
                  <Link
                    to={`/dashboard/governance?org=${selectedOrgId}`}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    Configure <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {applicableFrameworks.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-slate-400 italic py-4">
                    Complete your governance profile to see applicable frameworks
                  </p>
                ) : (
                  <div className="space-y-2">
                    {applicableFrameworks.slice(0, 5).map((fw) => (
                      <div
                        key={fw.framework}
                        className="flex items-center justify-between p-2 rounded-lg border border-gray-100 dark:border-slate-800"
                      >
                        <span className="text-sm font-medium text-gray-900 dark:text-slate-100">
                          {fw.framework}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            fw.mandatory
                              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                              : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          }`}
                        >
                          {fw.mandatory ? 'Mandatory' : 'Recommended'}
                        </span>
                      </div>
                    ))}
                    {applicableFrameworks.length > 5 && (
                      <p className="text-xs text-gray-500 text-center mt-1">
                        +{applicableFrameworks.length - 5} more
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-amber-500" />
                    Upcoming Audits
                  </CardTitle>
                  <Link
                    to={`/dashboard/audit-calendar?org=${selectedOrgId}`}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    View calendar <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {upcomingAudits.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-slate-400 italic py-4">
                    No upcoming audits scheduled
                  </p>
                ) : (
                  <div className="space-y-3">
                    {upcomingAudits.map((audit) => (
                      <div
                        key={audit.id}
                        className="flex items-center justify-between p-2 rounded-lg border border-amber-100 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-900/10"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-slate-100">
                            {audit.framework}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-slate-400">
                            {new Date(audit.audit_date).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 px-2 py-1 rounded-full">
                          {audit.days_until_audit}d
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
