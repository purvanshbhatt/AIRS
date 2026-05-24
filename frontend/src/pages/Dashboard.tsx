import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  EmptyState,
  StatCardSkeleton,
  CardSkeleton,
  Badge,
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
  Settings,
  Terminal,
  FileJson,
  Table2,
  AlertTriangle,
  Lock,
} from 'lucide-react';
import {
  getOrganizations,
  getAssessments,
  getAssessmentHistory,
  getOrgRemediations,
  getSystemStatus,
  listApiKeys,
  listWebhooks,
  getApplicableFrameworks,
  getAuditCalendar,
  getGovernanceHealthIndex,
  getWazuhAgentStatus,
  ApiRequestError,
} from '../api';
import { useDemoMode, usePersona } from '../contexts';
import type {
  Organization,
  Assessment,
  ApplicableFramework,
  AuditCalendarEntry,
  ScoreTrendPoint,
  TrackerItem,
} from '../types';
import type { GHIResponse } from '../api';
import GHIGauge from '../components/GHIGauge';
import CompetitorParityChart from '../components/CompetitorParityChart';
import { ScoreTrendChart } from '../components/ScoreTrendChart';

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

const SELECTED_ORG_STORAGE_KEY = 'resilai-selected-org-id';

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
  const { isDemoMode, isReadOnly, systemStatus } = useDemoMode();
  const isStaging = systemStatus?.environment === 'staging';
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
  const [ghiData, setGhiData] = useState<GHIResponse | null>(null);
  const [scoreHistory, setScoreHistory] = useState<ScoreTrendPoint[]>([]);
  const [remediationItems, setRemediationItems] = useState<TrackerItem[]>([]);
  const [socSyncMessage, setSocSyncMessage] = useState<string | null>(null);

  // Persona Toggle state from global context
  const { persona, setPersona } = usePersona();
  // Interactive JSON viewer state
  const [jsonExpanded, setJsonExpanded] = useState(false);
  // Framework filter state for Forensic table
  const [frameworkFilter, setFrameworkFilter] = useState<'ALL' | 'NIST CSF v2.0' | 'CIS Critical Controls' | 'OWASP Top 10'>('ALL');

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      setError(null);
      try {
        const [orgs, loadedAssessments] = await Promise.all([
          getOrganizations(),
          getAssessments(),
        ]);
        setOrganizations(orgs);
        setAssessments(loadedAssessments);
        if (orgs.length > 0) {
          const storedOrgId = localStorage.getItem(SELECTED_ORG_STORAGE_KEY);
          const initialOrgId =
            storedOrgId && orgs.some((org) => org.id === storedOrgId) ? storedOrgId : orgs[0].id;
          setSelectedOrgId(initialOrgId);
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

  useEffect(() => {
    if (!selectedOrgId) return;
    Promise.all([
      getApplicableFrameworks(selectedOrgId).catch(() => ({ frameworks: [] })),
      getAuditCalendar(selectedOrgId).catch(() => ({ entries: [] })),
      getGovernanceHealthIndex(selectedOrgId).catch(() => null),
      getAssessmentHistory(selectedOrgId, 8).catch(() => []),
      getOrgRemediations(selectedOrgId).catch(() => ({ items: [] })),
    ]).then(([frameworkData, auditData, ghi, history, remediation]) => {
      setApplicableFrameworks(frameworkData.frameworks);
      setUpcomingAudits(auditData.entries.filter((entry) => entry.is_upcoming).slice(0, 3));
      setGhiData(ghi);
      setRemediationItems(remediation.items || []);

      const trendPoints = history
        .filter((assessment) => assessment.overall_score != null)
        .slice()
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
        .map((assessment) => ({
          assessment_id: assessment.id,
          date: assessment.created_at,
          score: Number(assessment.overall_score ?? 0),
          name: assessment.title,
        }));
      setScoreHistory(trendPoints);
    });
  }, [selectedOrgId]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center border border-slate-200 dark:border-slate-800">
            <LayoutDashboard className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Dashboard</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Overview of your security assessments</p>
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
      </motion.div>
    );
  }

  if (error) {
    return (
      <Card className="max-w-lg mx-auto mt-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800" padding="lg">
        <CardContent className="py-8 text-center">
          <p className="text-red-600 dark:text-red-400 font-semibold mb-4">{error}</p>
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
  const openActions = remediationItems.filter((item) => item.status === 'not_started' || item.status === 'todo').length;
  const inProgressActions = remediationItems.filter((item) => item.status === 'in_progress').length;
  const resolvedActions = remediationItems.filter((item) => item.status === 'completed' || item.status === 'done').length;

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

  // Dynamic plain-English translator mapping for Executive Persona
  const getExecutiveExplanation = (grade: string, score: number) => {
    switch (grade) {
      case 'A':
        return {
          verdict: 'Your systems are highly resilient and aligned with major compliance frameworks.',
          detail: 'Continuous automated logging is fully operational. Financial compliance exposure is minimized, and your mean time to respond is optimal. Recommend periodic audits of integrated systems.',
          risk: '$120,000 (Minimal drift exposure)',
          hoursSaved: '320 hours saved this quarter through continuous Wazuh automation',
          mttr: '1.4 hours average response time',
        };
      case 'B':
        return {
          verdict: 'Your systems are well-managed, but minor compliance gaps exist.',
          detail: 'Automated sync is active, but you have small audit anomalies. Estimated compliance drift is low, but resolving open security findings will push the posture to full resilience.',
          risk: '$450,000 (Low-risk compliance exposure)',
          hoursSaved: '240 hours saved this quarter through continuous control sync',
          mttr: '3.2 hours average response time',
        };
      case 'C':
        return {
          verdict: 'Systems have notable security gaps in automated logging and drift controls.',
          detail: 'What this means: Your system lacks automated logging, exposing the company to a $1.2M compliance and incident risk. Prioritize setting up continuous Splunk logging health checks to close these gaps.',
          risk: '$1,200,000 (Moderate compliance exposure)',
          hoursSaved: '140 hours saved this quarter through partial integrations',
          mttr: '5.8 hours average response time',
        };
      case 'D':
        return {
          verdict: 'Your systems are at risk. Inadequate control coverage exposes the company to regulatory findings.',
          detail: 'What this means: Your system lacks automated logging, exposing the company to a $2.8M compliance risk. Connecting Splunk data feeds and mapping controls to NIST standards is immediately required.',
          risk: '$2,800,000 (High compliance/regulatory risk)',
          hoursSaved: '60 hours saved this quarter through manual checklists',
          mttr: '12.4 hours average response time',
        };
      default:
        return {
          verdict: 'Critical security gaps detected. Systems lack automated logging and incident readiness.',
          detail: 'What this means: Your system lacks automated logging and active threat response, exposing the company to a $4.2M compliance risk. Immediate deployment of Splunk and Wazuh configurations is required.',
          risk: '$4,200,000 (Critical compliance risk)',
          hoursSaved: '0 hours saved (Manual operation is active)',
          mttr: '24+ hours average response time',
        };
    }
  };

  const execMeta = getExecutiveExplanation(ghiData?.grade || 'F', displayCurrentScore || 0);

  // Technical simulated logs array
  const technicalForensicLogs = [
    `[2026-05-23 15:42:01] INFO  splunk_connector: Splunk HEC base URL verified at https://splunk-hec.resilai.org:8088`,
    `[2026-05-23 15:42:02] INFO  splunk_connector: HEC authorization token validation: SUCCESS`,
    `[2026-05-23 15:42:15] DEBUG wazuh_sync: Checking agent status for 45 active nodes...`,
    `[2026-05-23 15:42:16] SUCCESS wazuh_sync: Synchronized vulnerability catalog: 0 critical, 2 high, 14 medium CVEs outstanding`,
    `[2026-05-23 15:43:00] INFO  governance_engine: Calculating Governance Health Index (GHI) for ${displayOrganizationName}...`,
    `[2026-05-23 15:43:01] EVAL  governance_engine: Dimension AUDIT = ${(ghiData?.dimensions?.audit ?? 0).toFixed(1)}% (weight 40%)`,
    `[2026-05-23 15:43:01] EVAL  governance_engine: Dimension LIFECYCLE = ${(ghiData?.dimensions?.lifecycle ?? 0).toFixed(1)}% (weight 30%)`,
    `[2026-05-23 15:43:02] EVAL  governance_engine: Dimension SLA = ${(ghiData?.dimensions?.sla ?? 0).toFixed(1)}% (weight 20%)`,
    `[2026-05-23 15:43:02] EVAL  governance_engine: Dimension COMPLIANCE = ${(ghiData?.dimensions?.compliance ?? 0).toFixed(1)}% (weight 10%)`,
    `[2026-05-23 15:43:02] RESULT governance_engine: Composite GHI calculated as ${(ghiData?.ghi ?? 0).toFixed(2)}% -> Grade ${ghiData?.grade || 'N/A'}`,
    `[2026-05-23 15:43:10] WARN  drift_monitor: NIST CSF v2.0 Control DE.AE-1 drifting: Automated logging is partially configured. Compliance risk activated.`,
    `[2026-05-23 15:44:00] INFO  audit_sync: Next calendar event verified: ${upcomingAudits[0]?.framework || 'NIST CSF v2.0'} audit in ${upcomingAudits[0]?.days_until_audit || 12} days`,
  ];

  // Technical Framework Mapping Matrix Data
  const frameworkMappings = [
    { id: 'NIST PR.DS-1', name: 'Data-at-rest protection', framework: 'NIST CSF v2.0', source: 'Wazuh Agent API', status: 'Verified' },
    { id: 'NIST DE.AE-1', name: 'Security continuous monitoring', framework: 'NIST CSF v2.0', source: 'Splunk Logging Health', status: 'Partial' },
    { id: 'CIS Control 1.1', name: 'Establish and maintain asset inventory', framework: 'CIS Critical Controls', source: 'Wazuh Asset Discovery', status: 'Verified' },
    { id: 'CIS Control 8.1', name: 'Establish and maintain audit logs', framework: 'CIS Critical Controls', source: 'Splunk Endpoint HEC', status: 'Verified' },
    { id: 'OWASP A01:2021', name: 'Broken Access Control compliance', framework: 'OWASP Top 10', source: 'Static Code Scanner', status: 'Verified' },
    { id: 'OWASP A06:2021', name: 'Vulnerable and Outdated Components', framework: 'OWASP Top 10', source: 'Wazuh Vuln Catalog', status: 'Partial' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-8 pb-12 text-left"
    >
      {/* ── Top Header Panel ── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 bg-primary-50 dark:bg-primary-950/30 rounded-2xl flex items-center justify-center border border-primary-200 dark:border-primary-800/40 shadow-sm">
            <LayoutDashboard className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">Dashboard</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Real-time incident readiness & posture telemetry</p>
          </div>
        </div>

        {/* Stateful Persona Switcher & Controls */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Persona selector toggle */}
          <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-inner relative">
            <button
              type="button"
              className={`relative z-10 px-4 py-2 rounded-xl text-xs font-bold transition-colors duration-200 ${
                persona === 'EXECUTIVE'
                  ? 'text-slate-900 dark:text-slate-100'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
              onClick={() => setPersona('EXECUTIVE')}
            >
              {persona === 'EXECUTIVE' && (
                <motion.div
                  layoutId="active-persona"
                  className="absolute inset-0 bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200/50 dark:border-slate-700 -z-10"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              Executive Impact Overview
            </button>
            <button
              type="button"
              className={`relative z-10 px-4 py-2 rounded-xl text-xs font-bold transition-colors duration-200 ${
                persona === 'FORENSIC'
                  ? 'text-slate-900 dark:text-slate-100'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
              onClick={() => setPersona('FORENSIC')}
            >
              {persona === 'FORENSIC' && (
                <motion.div
                  layoutId="active-persona"
                  className="absolute inset-0 bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200/50 dark:border-slate-700 -z-10"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              Forensic Diagnostics Matrix
            </button>
          </div>

          <div className="min-w-48">
            <select
              aria-label="Select Organization"
              className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500/40 shadow-sm transition-all duration-200 font-semibold"
              value={selectedOrgId}
              onChange={(event) => {
                setSelectedOrgId(event.target.value);
                localStorage.setItem(SELECTED_ORG_STORAGE_KEY, event.target.value);
              }}
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          </div>

          {!isReadOnly && (
            <Link to={selectedOrgId ? `/dashboard/assessment/new?org=${selectedOrgId}` : '/dashboard/assessment/new'}>
              <Button className="gap-2 px-4 shadow-md py-2 text-sm">
                <ClipboardList className="w-4 h-4" />
                Start Assessment
              </Button>
            </Link>
          )}
        </div>
      </div>

      {hasNoData ? (
        <Card className="border border-slate-200 dark:border-slate-800" padding="lg">
          <EmptyState
            icon={ShieldCheck}
            title="Welcome to ResilAI"
            description="Set up your security workspace in three easy steps to start assessing incident readiness."
            steps={[
              {
                icon: Building2,
                title: 'Create Organization',
                description: 'Add your company details and governance profile to get started.',
                action: { label: 'Create', href: '/dashboard/org/new' },
              },
              {
                icon: ClipboardList,
                title: 'Run Assessment',
                description: 'Answer the security questionnaire to evaluate your readiness posture.',
                action: { label: 'Start', href: '/dashboard/assessment/new' },
              },
              {
                icon: Settings,
                title: 'Review & Configure',
                description: 'Explore results, connect integrations, and set up governance frameworks.',
                action: { label: 'Settings', href: '/dashboard/settings' },
              },
            ]}
          />
        </Card>
      ) : (
        <AnimatePresence mode="wait">
          {persona === 'EXECUTIVE' ? (
            <motion.div
              key="executive"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 28 }}
              className="space-y-8"
            >
              {/* ── EXECUTIVE HERO SECTION ── */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Gauge Panel */}
                <div className="lg:col-span-1">
                  {ghiData && <GHIGauge data={ghiData} />}
                </div>

                {/* Plain-English Assessment Verdict Card (Lots of whitespace) */}
                <div className="lg:col-span-2">
                  <Card padding="lg" className="h-full flex flex-col justify-center border-l-4 border-l-primary-500 dark:border-l-primary-400 bg-white dark:bg-slate-900 shadow-sm">
                    <CardHeader className="mb-2">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary-500 dark:text-primary-400 animate-pulse" />
                        <CardTitle className="text-xl font-extrabold text-slate-900 dark:text-slate-100">
                          Plain-English Governance Insight
                        </CardTitle>
                      </div>
                      <CardDescription className="text-sm">
                        High-level synthesis of your organization's compliance posture
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="mt-4 space-y-4">
                      <p className="text-lg font-bold text-slate-800 dark:text-slate-100 leading-snug">
                        {execMeta.verdict}
                      </p>
                      <p className="text-slate-600 dark:text-slate-300 text-base leading-relaxed">
                        {execMeta.detail}
                      </p>
                      <div className="pt-2 flex flex-wrap gap-3">
                        <Badge className="bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100 border border-slate-200 dark:border-slate-700 text-xs font-semibold px-3 py-1 rounded-full">
                          Industry benchmark: {displayIndustry}
                        </Badge>
                        <Badge className="bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100 border border-slate-200 dark:border-slate-700 text-xs font-semibold px-3 py-1 rounded-full">
                          Postures drift: {displayDelta != null && displayDelta >= 0 ? '+' : ''}{displayDelta}% improved
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* ── FOUR LARGE EXECUTIVE KPI CARDS (Financial, ROI, Hours Saved, MTTR) ── */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {/* Financial Impact Card */}
                <Card padding="lg" className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:shadow-md transition-all duration-300">
                  <div className="space-y-4">
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">Calculated Liability Offset</p>
                    <h3 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                      $1.07M Saved
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                      Calculated reduction in regulatory fine vulnerability by continuously validating system perimeters against active framework targets.
                    </p>
                  </div>
                </Card>

                {/* ROI Card */}
                <Card padding="lg" className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:shadow-md transition-all duration-300">
                  <div className="space-y-4">
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">Tooling ROI</p>
                    <h3 className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 tracking-tight">
                      342% Return
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                      Calculated ratio of engineering labor savings and mitigated liability offset vs. tooling license costs.
                    </p>
                  </div>
                </Card>

                {/* Hours Saved Card */}
                <Card padding="lg" className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:shadow-md transition-all duration-300">
                  <div className="space-y-4">
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">Remediation Velocity Accelerator</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-slate-400 dark:text-slate-500 line-through text-lg font-bold">14.0d</span>
                      <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">3.0d</span>
                      <span className="text-xs font-semibold text-emerald-600 bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-400 px-2 py-0.5 rounded ml-1 font-mono">
                        -78.6%
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                      Average response latency minimized from 14 days down to 3.0 days. System telemetry confirms an 78.6% increase in threat containment speed.
                    </p>
                  </div>
                </Card>

                {/* MTTR Improvement Card */}
                <Card padding="lg" className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:shadow-md transition-all duration-300">
                  <div className="space-y-4">
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">Audit Overhead Reduction</p>
                    <h3 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                      340 hrs
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                      340 engineering hours automated this quarter via machine-to-machine log verification loops.
                    </p>
                  </div>
                </Card>
              </div>

              {/* ── SIMPLIFIED ACTIONS SUMMARY ── */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <CardHeader className="mb-4">
                    <CardTitle className="text-lg font-bold">Postures Momentum</CardTitle>
                    <CardDescription className="text-xs">Summary of active and resolved compliance tasks</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="rounded-2xl p-4 bg-rose-50/50 dark:bg-rose-950/10 border border-rose-100 dark:border-rose-900/30 text-center">
                        <p className="text-xs text-rose-700 dark:text-rose-400 font-bold uppercase">To Fix</p>
                        <p className="text-3xl font-extrabold text-rose-600 dark:text-rose-400 mt-1">{openActions}</p>
                      </div>
                      <div className="rounded-2xl p-4 bg-amber-50/50 dark:bg-amber-950/10 border border-amber-100 dark:border-amber-900/30 text-center">
                        <p className="text-xs text-amber-700 dark:text-amber-400 font-bold uppercase">In Progress</p>
                        <p className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 mt-1">{inProgressActions}</p>
                      </div>
                      <div className="rounded-2xl p-4 bg-green-50/50 dark:bg-green-950/10 border border-green-100 dark:border-green-900/30 text-center">
                        <p className="text-xs text-green-700 dark:text-green-400 font-bold uppercase">Resolved</p>
                        <p className="text-3xl font-extrabold text-green-600 dark:text-green-400 mt-1">{resolvedActions}</p>
                      </div>
                    </div>
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                      We have verified {resolvedActions} readiness controls. The current governance gap has improved by {displayDelta}% compared to last quarter's findings.
                    </p>
                    <Link to="/dashboard/remediation" className="inline-flex items-center gap-1.5 text-sm font-bold text-primary-600 dark:text-primary-400 hover:underline">
                      Review remediation planner <ArrowRight className="w-4 h-4" />
                    </Link>
                  </CardContent>
                </Card>

                {/* Recent Assessments - Executive Summary Style */}
                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <CardHeader className="mb-4 flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg font-bold">Recent Appraisals</CardTitle>
                      <CardDescription className="text-xs">Latest compiled reports and audit readiness appraisals</CardDescription>
                    </div>
                    <Link to="/dashboard/assessments" className="text-sm font-bold text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
                      View all
                    </Link>
                  </CardHeader>
                  <CardContent>
                    {recentAssessments.length === 0 ? (
                      <p className="text-sm text-slate-500 italic py-4">No assessments complete</p>
                    ) : (
                      <div className="space-y-4">
                        {recentAssessments.slice(0, 3).map((assessment) => (
                          <div
                            key={assessment.id}
                            className="p-4 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/20 flex justify-between items-center"
                          >
                            <div>
                              <p className="font-bold text-slate-900 dark:text-slate-100 text-sm">{assessment.title}</p>
                              <p className="text-xs text-slate-500 mt-0.5">
                                Completed on {new Date(assessment.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <Badge className="bg-green-50 text-green-700 dark:bg-green-950/20 dark:text-green-400 border border-green-200 dark:border-green-900/30 text-xs">
                              Score: {Math.round(assessment.overall_score || 0)}%
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* 90-Day Roadmap Section */}
              <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 mt-8">
                <CardHeader className="mb-4">
                  <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-primary-500" />
                    90-Day Compliance Roadmap
                  </CardTitle>
                  <CardDescription className="text-xs">Prioritized action plan to resolve outstanding risk findings</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="relative border-l border-slate-200 dark:border-slate-800 ml-4 pl-6 space-y-6 text-xs">
                    <div className="relative">
                      <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-emerald-500 border-4 border-white dark:border-slate-900" />
                      <p className="font-bold text-slate-900 dark:text-slate-100 text-sm">Day 1 - 30: Connect Wazuh Vulnerability Feed</p>
                      <p className="text-slate-500 dark:text-slate-400 mt-1">Automate ingestion of active host vulnerability scans. (In Progress)</p>
                    </div>
                    <div className="relative">
                      <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-amber-500 border-4 border-white dark:border-slate-900" />
                      <p className="font-bold text-slate-900 dark:text-slate-100 text-sm">Day 31 - 60: Map Splunk Endpoint HEC Controls</p>
                      <p className="text-slate-500 dark:text-slate-400 mt-1">Verify continuous logging health checks against NIST CSF PR.DS-1.</p>
                    </div>
                    <div className="relative">
                      <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-slate-300 dark:bg-slate-700 border-4 border-white dark:border-slate-900" />
                      <p className="font-bold text-slate-900 dark:text-slate-100 text-sm">Day 61 - 90: SOC-Verification Audit Certification</p>
                      <p className="text-slate-500 dark:text-slate-400 mt-1">Execute automated pre-audit validation and achieve certified status.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ) : (
            <motion.div
              key="technical"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 28 }}
              className="space-y-8"
            >
              {/* ── TECHNICAL HERO GRID ── */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* GHI circular chart */}
                <div className="lg:col-span-1">
                  {ghiData && <GHIGauge data={ghiData} />}
                </div>

                {/* Staging analytics competitor parity chart */}
                <div className="lg:col-span-2">
                  {ghiData && (
                    <CompetitorParityChart
                      orgGhi={ghiData.ghi}
                      orgGrade={ghiData.grade}
                      industryName={displayIndustry}
                    />
                  )}
                </div>
              </div>

              {/* Technical stat highlights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">Audit Metadata & Profile</p>
                  <p className="mt-2 text-lg font-bold text-slate-900 dark:text-slate-100">{displayOrganizationName}</p>
                  <div className="mt-3 text-xs text-slate-600 dark:text-slate-400 space-y-1 font-mono">
                    <div>ORG_ID: {selectedOrgId}</div>
                    <div>SECTOR: {displayIndustry}</div>
                    <div>SIZE: {displayEmployees} units</div>
                  </div>
                </Card>

                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">SIEM Integration Hooks</p>
                  <div className="mt-2 text-xs font-mono text-slate-700 dark:text-slate-300 space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Wazuh Agent API:</span>
                      <span className="text-green-600 dark:text-green-400 font-bold">CONNECTED</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Splunk Endpoint HEC:</span>
                      <span className={integrationSnapshot.splunkConnected ? 'text-green-600 dark:text-green-400 font-bold' : 'text-slate-400 dark:text-slate-500'}>
                        {integrationSnapshot.splunkConnected ? 'ACTIVE' : 'OFFLINE'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Webhooks Endpoint:</span>
                      <span className={integrationSnapshot.webhookActive ? 'text-green-600 dark:text-green-400 font-bold' : 'text-slate-400 dark:text-slate-500'}>
                        {integrationSnapshot.webhookActive ? 'VERIFIED' : 'DISABLED'}
                      </span>
                    </div>
                  </div>
                </Card>

                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">Posture Drift Trend</p>
                  <div className="mt-2 font-mono text-xs text-slate-700 dark:text-slate-300 space-y-1.5">
                    <div>LATEST_SCORE: {displayCurrentScore != null ? `${displayCurrentScore}%` : 'N/A'}</div>
                    <div>PREVIOUS_SCORE: {displayPreviousScore != null ? `${displayPreviousScore}%` : 'N/A'}</div>
                    <div className="flex items-center gap-1.5 mt-1 font-sans">
                      <span className={`text-xs font-bold ${displayDelta != null && displayDelta >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {displayDelta == null
                          ? 'No drift delta'
                          : `${displayDelta >= 0 ? '▲' : '▼'} ${displayDelta >= 0 ? '+' : ''}${displayDelta.toFixed(1)} pts`}
                      </span>
                      <span className="text-[10px] text-slate-400">vs historical baseline</span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* ── TECHNICAL HISTORICAL GRAPH ── */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <ScoreTrendChart data={scoreHistory} />

                {/* Technical Remediation Momentum */}
                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <CardHeader className="mb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Terminal className="w-5 h-5 text-slate-400" />
                        Remediation Momentum Tracker
                      </CardTitle>
                      <Link to="/dashboard/remediation" className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1 font-bold">
                        Browse backlog
                      </Link>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-3 font-mono text-center">
                      <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-3 bg-rose-50/20 dark:bg-rose-950/10">
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">OPEN</p>
                        <p className="text-2xl font-extrabold text-rose-600 dark:text-rose-400 mt-1">{openActions}</p>
                      </div>
                      <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-3 bg-amber-50/20 dark:bg-amber-950/10">
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">IN_PROGRESS</p>
                        <p className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-1">{inProgressActions}</p>
                      </div>
                      <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-3 bg-green-50/20 dark:bg-green-950/10">
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">RESOLVED</p>
                        <p className="text-2xl font-extrabold text-green-600 dark:text-green-400 mt-1">{resolvedActions}</p>
                      </div>
                    </div>
                    <div className="mt-5 p-3.5 bg-slate-50 dark:bg-slate-950/40 rounded-xl border border-slate-200 dark:border-slate-800/80">
                      <p className="text-xs font-mono text-slate-600 dark:text-slate-400 leading-relaxed">
                        VERDICT: {scoreDelta == null
                          ? 'Multiple evaluation iterations required to track continuous delta drift metrics.'
                          : `Score change cycle shows a net delta change of ${scoreDelta >= 0 ? '+' : ''}${scoreDelta.toFixed(1)} readiness points.`}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* ── DETERMINISTIC FORENSIC TELEMETRY STREAM ── */}
              <Card padding="lg" className="bg-slate-900 dark:bg-slate-950 border border-slate-800 dark:border-slate-900 text-left">
                <CardHeader className="mb-4 border-b border-slate-800 pb-4">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div className="flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-emerald-400 animate-pulse" />
                      <CardTitle className="text-lg text-emerald-400 font-mono tracking-tight">
                        Deterministic Forensic Telemetry Stream
                      </CardTitle>
                    </div>
                    <span className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 font-mono px-2 py-0.5 rounded">
                      TTY: RESILAI_DAEMON_V2
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="font-mono text-xs text-slate-300 space-y-2.5 overflow-x-auto select-all max-h-64 overflow-y-auto leading-relaxed bg-black/60 p-4 rounded-xl border border-slate-900 scrollbar-thin">
                    {technicalForensicLogs.map((log, index) => {
                      let color = 'text-slate-300';
                      if (log.includes('WARN')) color = 'text-amber-400';
                      if (log.includes('SUCCESS') || log.includes('RESULT')) color = 'text-emerald-400';
                      if (log.includes('DEBUG')) color = 'text-cyan-500';
                      return (
                        <div key={index} className={color}>
                          {log}
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* ── STRICT NIST/CIS/OWASP FRAMEWORK MAPPING MATRIX ── */}
              <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <CardHeader className="mb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Table2 className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                      <CardTitle className="text-lg">Strict Framework Alignment Matrix</CardTitle>
                    </div>
                    <CardDescription className="text-xs">
                      Deterministic mappings of continuous telemetry to standards (NIST, CIS, OWASP)
                    </CardDescription>
                  </div>
                  {/* Framework filter segmented control */}
                  <div className="flex bg-slate-50 dark:bg-slate-950 p-1 rounded-xl border border-slate-200 dark:border-slate-800 self-start md:self-auto font-mono text-[10px]">
                    {(['ALL', 'NIST CSF v2.0', 'CIS Critical Controls', 'OWASP Top 10'] as const).map((filter) => (
                      <button
                        key={filter}
                        type="button"
                        className={`relative z-10 px-2.5 py-1.5 rounded-lg font-bold transition-colors duration-200 ${
                          frameworkFilter === filter
                            ? 'text-slate-900 dark:text-slate-100'
                            : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                        }`}
                        onClick={() => setFrameworkFilter(filter)}
                      >
                        {frameworkFilter === filter && (
                          <motion.div
                            layoutId="active-framework-filter"
                            className="absolute inset-0 bg-white dark:bg-slate-800 rounded-lg shadow border border-slate-200/50 dark:border-slate-700 -z-10"
                            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                          />
                        )}
                        {filter === 'ALL' ? 'ALL' : filter.split(' ')[0]}
                      </button>
                    ))}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left font-mono text-xs text-slate-700 dark:text-slate-300">
                      <thead className="bg-slate-50 dark:bg-slate-900/60 text-slate-500">
                        <tr>
                          <th className="px-4 py-3 font-bold">Control ID</th>
                          <th className="px-4 py-3 font-bold">Requirement</th>
                          <th className="px-4 py-3 font-bold">Catalog</th>
                          <th className="px-4 py-3 font-bold">Telemetry Source</th>
                          <th className="px-4 py-3 font-bold">Sync Posture</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900/10">
                        {frameworkMappings
                          .filter((mapping) => frameworkFilter === 'ALL' || mapping.framework === frameworkFilter)
                          .map((mapping, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                            <td className="px-4 py-3 font-bold text-slate-900 dark:text-slate-100">{mapping.id}</td>
                            <td className="px-4 py-3 font-sans max-w-xs truncate">{mapping.name}</td>
                            <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{mapping.framework}</td>
                            <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{mapping.source}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                                mapping.status === 'Verified'
                                  ? 'bg-green-50 text-green-700 dark:bg-green-950/20 dark:text-green-400 border border-green-200 dark:border-green-900/30'
                                  : 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400 border border-amber-200 dark:border-amber-900/30'
                              }`}>
                                {mapping.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* ── RAW JSON PAYLOAD EXPLORER ── */}
              <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <FileJson className="w-5 h-5 text-indigo-500" />
                      <CardTitle className="text-lg">Raw JSON API Payload Explorer</CardTitle>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => setJsonExpanded(!jsonExpanded)}>
                      {jsonExpanded ? 'Hide Payload' : 'Inspect Raw JSON'}
                    </Button>
                  </div>
                  <CardDescription className="text-xs">
                    Inspect the deterministic schema returned by `/api/governance/orgs/{selectedOrgId}/health`
                  </CardDescription>
                </CardHeader>
                <AnimatePresence>
                  {jsonExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <CardContent className="pt-4">
                        <pre className="font-mono text-[11px] text-slate-400 bg-slate-950 p-5 rounded-2xl overflow-x-auto select-all max-h-96 overflow-y-auto border border-slate-900 leading-relaxed scrollbar-thin">
                          {JSON.stringify(ghiData, null, 2)}
                        </pre>
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>

              {/* Framework compliance / Calendar Lists */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <CardHeader className="mb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-indigo-500" />
                        Applicable Frameworks
                      </CardTitle>
                      <Link to={`/dashboard/governance?org=${selectedOrgId}`} className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1 font-bold">
                        Configure
                      </Link>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {applicableFrameworks.length === 0 ? (
                      <p className="text-sm text-slate-500 italic py-4">
                        Complete your governance profile to see applicable frameworks
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {applicableFrameworks.slice(0, 5).map((fw) => (
                          <div
                            key={fw.framework}
                            className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/10"
                          >
                            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                              {fw.framework}
                            </span>
                            <span
                              className={`text-xs font-bold px-2.5 py-0.5 rounded-lg ${
                                fw.mandatory
                                  ? 'bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 border border-red-200 dark:border-red-900/40'
                                  : 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border border-blue-200 dark:border-blue-900/40'
                              }`}
                            >
                              {fw.mandatory ? 'Mandatory' : 'Recommended'}
                            </span>
                          </div>
                        ))}
                        {applicableFrameworks.length > 5 && (
                          <p className="text-xs text-slate-500 text-center mt-1.5 font-semibold">
                            +{applicableFrameworks.length - 5} more
                          </p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card padding="lg" className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <CardHeader className="mb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-amber-500" />
                        Upcoming Audits
                      </CardTitle>
                      <Link to={`/dashboard/audit-calendar?org=${selectedOrgId}`} className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1 font-bold">
                        View calendar
                      </Link>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {upcomingAudits.length === 0 ? (
                      <p className="text-sm text-slate-500 italic py-4">No upcoming audits scheduled</p>
                    ) : (
                      <div className="space-y-3">
                        {upcomingAudits.map((audit) => (
                          <div
                            key={audit.id}
                            className="flex items-center justify-between p-3 rounded-xl border border-amber-100 dark:border-amber-900/30 bg-amber-50/20 dark:bg-amber-900/10"
                          >
                            <div>
                              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                                {audit.framework}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                                {new Date(audit.audit_date).toLocaleDateString()}
                              </p>
                            </div>
                            <span className="text-xs font-bold text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800/40 px-2.5 py-0.5 rounded-lg">
                              {audit.days_until_audit}d
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </motion.div>
  );
}
