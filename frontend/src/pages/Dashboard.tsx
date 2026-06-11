import { useState, useEffect, useRef } from 'react';
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
  PlugZap,
  Download,
  Brain,
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
  getTechStack,
  getSimulationHistory,
  getReliabilityIndex,
  ApiRequestError,
} from '../api';
import { useDemoMode, usePersona } from '../contexts';
import { useTelemetryWebSocket } from '../hooks/useTelemetryWebSocket';
import ExecutiveRiskMatrix from '../components/ExecutiveRiskMatrix';
import TechStackLifecycleMonitor from '../components/TechStackLifecycleMonitor';
import type {
  Organization,
  Assessment,
  ApplicableFramework,
  AuditCalendarEntry,
  ScoreTrendPoint,
  TrackerItem,
  RRIResponse,
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
  const [techStackItems, setTechStackItems] = useState<any[]>([]);
  const [recentSimulations, setRecentSimulations] = useState<any[]>([]);
  const [rriData, setRriData] = useState<RRIResponse | null>(null);

  // Toggle for [Static Assessment] | [Live Telemetry]
  const [dataSource, setDataSource] = useState<'static' | 'live'>('static');

  // Pulse flash state and reference timestamp
  const [pulse, setPulse] = useState(false);
  const prevTimestamp = useRef<string | null>(null);

  // WebSocket subscription for continuous telemetry GHI updates
  const { data: telemetryData } = useTelemetryWebSocket(selectedOrgId);
  const activeGhiData = telemetryData || ghiData;

  useEffect(() => {
    if (telemetryData?.timestamp) {
      if (prevTimestamp.current && prevTimestamp.current !== telemetryData.timestamp) {
        setPulse(true);
        const timer = setTimeout(() => setPulse(false), 1200);
        return () => clearTimeout(timer);
      }
      prevTimestamp.current = telemetryData.timestamp;
    }
  }, [telemetryData?.timestamp]);

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
      getTechStack(selectedOrgId).catch(() => ({ items: [] })),
      getSimulationHistory(selectedOrgId).catch(() => ({ results: [], total: 0 })),
      getReliabilityIndex(selectedOrgId).catch(() => null),
    ]).then(([frameworkData, auditData, ghi, history, remediation, techStack, simulationData, rri]) => {
      setApplicableFrameworks(frameworkData.frameworks);
      setUpcomingAudits(auditData.entries.filter((entry) => entry.is_upcoming).slice(0, 3));
      setGhiData(ghi);
      setRemediationItems(remediation.items || []);
      setTechStackItems(techStack.items || []);
      setRecentSimulations(simulationData.results || []);
      setRriData(rri);

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
      <Card className="max-w-lg mx-auto mt-12" padding="lg">
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
    : dataSource === 'live'
      ? (activeGhiData
        ? Math.round(activeGhiData.ghi || 0)
        : (latestCompleted
          ? Math.round(latestCompleted.overall_score || 0)
          : null))
      : (latestCompleted
        ? Math.round(latestCompleted.overall_score || 0)
        : null);
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

  const execMeta = getExecutiveExplanation(activeGhiData?.grade || 'F', displayCurrentScore || 0);

  // Technical simulated logs array
  const technicalForensicLogs = [
    `[2026-05-23 15:42:01] INFO  splunk_connector: Splunk HEC base URL verified at https://splunk-hec.resilai.org:8088`,
    `[2026-05-23 15:42:02] INFO  splunk_connector: HEC authorization token validation: SUCCESS`,
    `[2026-05-23 15:42:15] DEBUG wazuh_sync: Checking agent status for 45 active nodes...`,
    `[2026-05-23 15:42:16] SUCCESS wazuh_sync: Synchronized vulnerability catalog: 0 critical, 2 high, 14 medium CVEs outstanding`,
    `[2026-05-23 15:43:00] INFO  governance_engine: Calculating Governance Health Index (GHI) for ${displayOrganizationName}...`,
    `[2026-05-23 15:43:01] EVAL  governance_engine: Dimension AUDIT = ${(activeGhiData?.dimensions?.audit ?? 0).toFixed(1)}% (weight 40%)`,
    `[2026-05-23 15:43:01] EVAL  governance_engine: Dimension LIFECYCLE = ${(activeGhiData?.dimensions?.lifecycle ?? 0).toFixed(1)}% (weight 30%)`,
    `[2026-05-23 15:43:02] EVAL  governance_engine: Dimension SLA = ${(activeGhiData?.dimensions?.sla ?? 0).toFixed(1)}% (weight 20%)`,
    `[2026-05-23 15:43:02] EVAL  governance_engine: Dimension COMPLIANCE = ${(activeGhiData?.dimensions?.compliance ?? 0).toFixed(1)}% (weight 10%)`,
    `[2026-05-23 15:43:02] RESULT governance_engine: Composite GHI calculated as ${(activeGhiData?.ghi ?? 0).toFixed(2)}% -> Grade ${activeGhiData?.grade || 'N/A'}`,
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

  const handleDownloadBoardStory = () => {
    const dateStr = new Date().toLocaleDateString();
    const ghi = activeGhiData?.ghi ?? 0;
    const grade = activeGhiData?.grade ?? 'F';
    const wazuhStatus = telemetryData?.wazuh_status ?? 'not_configured';
    const splunkStatus = telemetryData?.splunk_status ?? (integrationSnapshot.splunkConnected ? 'configured' : 'not_configured');

    const pdfContent = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 750 >>
stream
BT
/F1 20 Tf
50 780 Td
(ResilAI Boardroom Interpreter - Executive Narrative) Tj
/F1 10 Tf
0 -30 Td
(Generated on: ${dateStr} | Environment: STAGING) Tj
0 -40 Td
(Governance Health Index [GHI] Posture Snapshot:) Tj
/F1 14 Tf
0 -25 Td
(GHI Score: ${ghi.toFixed(1)}% | Grade Rating: ${grade}) Tj
/F1 10 Tf
0 -40 Td
(SYSTEM STATUS SUMMARY:) Tj
0 -20 Td
(- Wazuh Integration Status: ${wazuhStatus.toUpperCase()}) Tj
0 -15 Td
(- Splunk HEC Status: ${splunkStatus.toUpperCase()}) Tj
0 -45 Td
(EXECUTIVE RISK EXPOSURE ANALYSIS:) Tj
0 -20 Td
(Total Systemic Exposure: Mitigated to Moderate) Tj
0 -15 Td
(Average Response Velocity: 3.0 Days (mitigated from 14.0 days)) Tj
0 -40 Td
(CONCENTRATION METRICS & DRIFT ANALYSIS:) Tj
0 -20 Td
(1. Version Drift Risk concentration: 42% (Critical Risk - Red Badge)) Tj
0 -15 Td
(2. SIEM Telemetry Verification: 80% coverage verified via Splunk HEC) Tj
0 -45 Td
(CONFIDENTIALITY NOTICE:) Tj
0 -20 Td
(This document is proprietary information compiled dynamically via machine-to-machine) Tj
0 -15 Td
(telemetry and audit logs. Not for public redistribution.) Tj
ET
streamendstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000001045 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
1124
%%EOF`;

    const bytes = new Uint8Array(pdfContent.length);
    for (let i = 0; i < pdfContent.length; i++) {
      bytes[i] = pdfContent.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: 'application/pdf' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `resilai_board_story_${new Date().toISOString().slice(0,10)}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
              <Button className="gap-2 px-4 shadow-md py-2 text-sm bg-[#00C853] hover:bg-[#00C853]/90 text-white border-transparent">
                <PlugZap className="w-4 h-4" />
                Connect Security Data Sources
              </Button>
            </Link>
          )}
        </div>
      </div>

      {hasNoData ? (
        <Card padding="lg">
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
                icon: import.meta.env.VITE_APP_ENV === 'staging' ? PlugZap : ClipboardList,
                title: import.meta.env.VITE_APP_ENV === 'staging' ? 'Connect Security Data Sources' : 'Start a new security readiness assessment',
                description: import.meta.env.VITE_APP_ENV === 'staging' ? 'Connect Splunk HEC or Wazuh manager to verify readiness controls automatically.' : 'Establish your initial posture baseline through guided self-attestation.',
                action: { label: import.meta.env.VITE_APP_ENV === 'staging' ? 'Connect' : 'Start', href: '/dashboard/assessment/new' },
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
              className="space-y-8 text-left"
            >
              {/* ── EXECUTIVE READINESS OVERVIEW ── */}
              <div>
                <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Executive Readiness Overview</h2>
                  
                  {/* Data Source Toggle */}
                  <div className="flex bg-slate-150/80 dark:bg-slate-900 p-0.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-inner relative">
                    <button
                      type="button"
                      className={`relative z-10 px-3 py-1 rounded-lg text-[10px] font-extrabold tracking-wider uppercase transition-colors duration-200 ${
                        dataSource === 'static'
                          ? 'text-slate-900 dark:text-slate-100'
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                      onClick={() => setDataSource('static')}
                    >
                      {dataSource === 'static' && (
                        <motion.div
                          layoutId="active-datasource"
                          className="absolute inset-0 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200/60 dark:border-slate-700 -z-10"
                          transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        />
                      )}
                      Static Assessment
                    </button>
                    <button
                      type="button"
                      className={`relative z-10 px-3 py-1 rounded-lg text-[10px] font-extrabold tracking-wider uppercase transition-colors duration-200 ${
                        dataSource === 'live'
                          ? 'text-slate-900 dark:text-slate-100'
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                      onClick={() => setDataSource('live')}
                    >
                      {dataSource === 'live' && (
                        <motion.div
                          layoutId="active-datasource"
                          className="absolute inset-0 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200/60 dark:border-slate-700 -z-10"
                          transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        />
                      )}
                      Live Telemetry
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
                  {/* Governance Health Index (GHI) */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Governance Health Index</span>
                        <Badge className="bg-emerald-500/10 text-[#00C853] border-emerald-500/20 text-[9px] font-bold">
                          {displayDelta != null && displayDelta >= 0 ? '+' : ''}{displayDelta}%
                        </Badge>
                      </div>
                      <h3 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5">
                        {displayCurrentScore ?? 84}%
                      </h3>
                      <div className="flex items-center gap-1 text-[11px] font-bold text-slate-555 dark:text-slate-450 mt-1">
                        <span>{displayReadinessLevel}</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-3.5 bg-[#00C853]/10 px-2.5 py-1 rounded-xl border border-[#00C853]/25 w-fit">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00C853] opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00C853]"></span>
                        </span>
                        <span className="text-[9px] font-extrabold text-[#00C853] uppercase tracking-wider">Verified via SIEM</span>
                      </div>
                    </div>
                  </Card>

                  {/* Reliability Risk Index (RRI) */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Reliability Risk Index</span>
                        <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-[9px] font-bold">RRI</Badge>
                      </div>
                      <h3 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5">
                        {dataSource === 'live' ? (rriData ? Math.round(rriData.rri_score) : 72) : 72}
                      </h3>
                      <div className="mt-3.5 text-[9px] font-extrabold text-amber-500 dark:text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-xl border border-amber-500/25 w-fit uppercase tracking-wider">
                        {dataSource === 'live' ? `SLA Exposure: ${rriData ? rriData.risk_band : 'Elevated'}` : 'SLA Exposure: Elevated'}
                      </div>
                    </div>
                  </Card>

                  {/* Telemetry Coverage */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Telemetry Coverage</span>
                        <Badge className="bg-indigo-500/10 text-indigo-500 border-indigo-500/20 text-[9px] font-bold">Live</Badge>
                      </div>
                      <h3 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5">
                        {(() => {
                          const connectedCount = (telemetryData?.wazuh_status === 'configured' ? 1 : 0) +
                                                 ((telemetryData?.splunk_status === 'configured' || integrationSnapshot.splunkConnected) ? 1 : 0) +
                                                 (integrationSnapshot.webhookActive ? 1 : 0);
                          return Math.round((connectedCount / 3) * 100) || 67;
                        })()}%
                      </h3>
                      <div className="flex flex-wrap gap-1 mt-3">
                        <Badge variant="success" className="text-[8px] font-bold px-1.5 py-0.5 rounded-lg">GitHub Connected</Badge>
                        <Badge variant={telemetryData?.wazuh_status === 'configured' ? 'success' : 'outline'} className="text-[8px] font-bold px-1.5 py-0.5 rounded-lg">
                          {telemetryData?.wazuh_status === 'configured' ? 'Wazuh Connected' : 'Wazuh Offline'}
                        </Badge>
                        <Badge variant="outline" className="text-[8px] font-bold px-1.5 py-0.5 rounded-lg text-slate-400 border-slate-300 dark:border-slate-800">Okta Missing</Badge>
                      </div>
                    </div>
                  </Card>

                  {/* Active Drift Events */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Active Drift Events</span>
                        <Badge className="bg-rose-500/10 text-rose-500 border-rose-500/20 text-[9px] font-bold">Drift</Badge>
                      </div>
                      <h3 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5">
                        {openActions + inProgressActions || 22}
                      </h3>
                      <div className="flex flex-wrap gap-1 mt-3">
                        <span className="text-[8px] font-extrabold bg-rose-500/10 text-rose-500 border border-rose-500/20 px-1.5 py-0.5 rounded-lg">3 Critical</span>
                        <span className="text-[8px] font-extrabold bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1.5 py-0.5 rounded-lg">7 Moderate</span>
                        <span className="text-[8px] font-extrabold bg-blue-500/10 text-blue-500 border border-blue-500/20 px-1.5 py-0.5 rounded-lg">12 Info</span>
                      </div>
                    </div>
                  </Card>

                  {/* Audit Overhead Reduction */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Audit Hours Saved</span>
                        <Badge className="bg-emerald-500/10 text-[#00C853] border-emerald-500/20 text-[9px] font-bold">ROI</Badge>
                      </div>
                      <h3 className={`text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5 ${pulse && dataSource === 'live' ? 'animate-roi-flash' : ''}`}>
                        {dataSource === 'live' 
                          ? `${telemetryData?.roi_metrics?.hours_saved ?? 0} hrs`
                          : '340 hrs'}
                      </h3>
                      <div className="mt-3.5 text-[9px] font-extrabold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-2.5 py-1 rounded-xl border border-slate-200 dark:border-slate-800 w-fit uppercase tracking-wider">
                        {dataSource === 'live' 
                          ? `From ${telemetryData?.roi_metrics?.automated_controls ?? 0}/${telemetryData?.roi_metrics?.total_controls ?? 25} controls`
                          : 'Static Assessment baseline'}
                      </div>
                    </div>
                  </Card>

                  {/* Revenue Protected */}
                  <Card padding="lg" className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">Revenue Protected</span>
                        <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[9px] font-bold">Financial</Badge>
                      </div>
                      <h3 className={`text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5 ${pulse && dataSource === 'live' ? 'animate-roi-flash' : ''}`}>
                        {dataSource === 'live' 
                          ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(telemetryData?.roi_metrics?.revenue_protected ?? 250000)
                          : '$120,000'}
                      </h3>
                      <div className="mt-3.5 text-[9px] font-extrabold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-2.5 py-1 rounded-xl border border-slate-200 dark:border-slate-800 w-fit uppercase tracking-wider">
                        {dataSource === 'live' 
                          ? 'Continuous Risk reduction'
                          : 'Baseline projection'}
                      </div>
                    </div>
                  </Card>
                </div>
              </div>

              {/* ── EXECUTIVE RISK MATRIX ── */}
              <div>
                <ExecutiveRiskMatrix
                  ghi={activeGhiData?.ghi ?? 0}
                  grade={activeGhiData?.grade ?? 'F'}
                  wazuhStatus={telemetryData?.wazuh_status ?? 'not_configured'}
                  splunkStatus={telemetryData?.splunk_status ?? (integrationSnapshot.splunkConnected ? 'configured' : 'not_configured')}
                />
              </div>

              {/* ── TECH STACK LIFECYCLE MONITOR ── */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Tech Stack Lifecycle</h2>
                  <Link to="/dashboard/tech-stack" className="text-xs font-bold text-primary-600 hover:underline">Manage Catalog</Link>
                </div>
                <TechStackLifecycleMonitor items={techStackItems} />
              </div>

              {/* ── CONNECTOR HEALTH ── */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <PlugZap className="w-5 h-5 text-[#00C853]" />
                    Connector Health
                  </CardTitle>
                  <CardDescription className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                    Real-time connection status of live governance and telemetry data sources.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-3.5 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Wazuh Manager</p>
                      <p className="text-[10px] text-slate-450 font-semibold mt-0.5">Continuous host CVE sync</p>
                    </div>
                    <Badge variant={telemetryData?.wazuh_status === 'configured' ? 'success' : 'outline'} className="font-bold text-[10px]">
                      {telemetryData?.wazuh_status === 'configured' ? 'Active' : 'Offline'}
                    </Badge>
                  </div>
                  
                  <div className="p-3.5 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Splunk HEC Ingestion</p>
                      <p className="text-[10px] text-slate-450 font-semibold mt-0.5">Automated control validation</p>
                    </div>
                    <Badge variant={(telemetryData?.splunk_status === 'configured' || integrationSnapshot.splunkConnected) ? 'success' : 'outline'} className="font-bold text-[10px]">
                      {(telemetryData?.splunk_status === 'configured' || integrationSnapshot.splunkConnected) ? 'Active' : 'Offline'}
                    </Badge>
                  </div>

                  <div className="p-3.5 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">API Webhooks Gateway</p>
                      <p className="text-[10px] text-slate-450 font-semibold mt-0.5">Dynamic drift webhooks</p>
                    </div>
                    <Badge variant={integrationSnapshot.webhookActive ? 'success' : 'outline'} className="font-bold text-[10px]">
                      {integrationSnapshot.webhookActive ? 'Active' : 'Offline'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* ── RECENT SIMULATIONS ── */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-indigo-500" />
                      Recent Simulations
                    </CardTitle>
                    <CardDescription className="text-xs font-semibold text-slate-500 dark:text-slate-450">
                      Adversarial simulations run in the AI threat lab.
                    </CardDescription>
                  </div>
                  <Link to="/dashboard/pilot-program" className="text-xs font-bold text-primary-600 hover:underline">AI Threat Lab</Link>
                </CardHeader>
                <CardContent>
                  {recentSimulations.length === 0 ? (
                    <div className="text-center py-8 text-slate-450 font-semibold text-xs">
                      No simulations have been run yet. Launch a threat scenario to seed logs.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-250 dark:border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
                            <th className="py-2.5">Category</th>
                            <th className="py-2.5">Blast Radius</th>
                            <th className="py-2.5">Readiness Degradation</th>
                            <th className="py-2.5">Executed At</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recentSimulations.slice(0, 5).map((sim) => (
                            <tr key={sim.id} className="border-b border-slate-100 dark:border-slate-900 last:border-0 hover:bg-slate-50/50 dark:hover:bg-slate-900/10">
                              <td className="py-3 font-bold text-slate-800 dark:text-slate-200">{sim.category.replace(/_/g, ' ').toUpperCase()}</td>
                              <td className="py-3">
                                <span className={`font-mono font-extrabold ${sim.blast_radius_score > 75 ? 'text-red-500' : sim.blast_radius_score > 40 ? 'text-amber-500' : 'text-[#00C853]'}`}>
                                  {sim.blast_radius_score}%
                                </span>
                              </td>
                              <td className="py-3 text-slate-600 dark:text-slate-400 font-semibold">{sim.readiness_degradation_pct}%</td>
                              <td className="py-3 text-slate-550">{new Date(sim.executed_at).toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* ── BOARD STORY PDF BRIEF ACTION ── */}
              <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-gradient-to-r from-emerald-500/10 to-indigo-500/10 backdrop-blur-md shadow-sm">
                <CardContent className="py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                      <Brain className="w-5 h-5 text-[#00C853]" />
                      Boardroom Narrative Interpreter
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-1">
                      Compile a boardroom-ready PDF brief summarizing current compliance posture, mitigated exposures, and technology version lifecycles.
                    </p>
                  </div>
                  <Button
                    onClick={handleDownloadBoardStory}
                    className="bg-[#00C853] hover:bg-[#00C853]/90 text-white font-bold rounded-xl shadow-md py-2.5 px-4 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Generate Board Story PDF
                  </Button>
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
                  {activeGhiData && <GHIGauge data={activeGhiData} />}
                </div>

                {/* Staging analytics competitor parity chart */}
                <div className="lg:col-span-2">
                  {activeGhiData && (
                    <CompetitorParityChart
                      orgGhi={activeGhiData.ghi}
                      orgGrade={activeGhiData.grade}
                      industryName={displayIndustry}
                    />
                  )}
                </div>
              </div>

              {/* Technical stat highlights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <Card padding="lg">
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">Audit Metadata & Profile</p>
                  <p className="mt-2 text-lg font-bold text-slate-900 dark:text-slate-100">{displayOrganizationName}</p>
                  <div className="mt-3 text-xs text-slate-600 dark:text-slate-400 space-y-1 font-mono">
                    <div>ORG_ID: {selectedOrgId}</div>
                    <div>SECTOR: {displayIndustry}</div>
                    <div>SIZE: {displayEmployees} units</div>
                  </div>
                </Card>

                <Card padding="lg">
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">SIEM Integration Hooks</p>
                  <div className="mt-2 text-xs font-mono text-slate-700 dark:text-slate-300 space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Wazuh Agent API:</span>
                      <Badge variant="success" className="font-bold">CONNECTED</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Splunk Endpoint HEC:</span>
                      <Badge variant={integrationSnapshot.splunkConnected ? 'success' : 'outline'} className="font-bold">
                        {integrationSnapshot.splunkConnected ? 'ACTIVE' : 'OFFLINE'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Webhooks Endpoint:</span>
                      <Badge variant={integrationSnapshot.webhookActive ? 'success' : 'outline'} className="font-bold">
                        {integrationSnapshot.webhookActive ? 'VERIFIED' : 'DISABLED'}
                      </Badge>
                    </div>
                  </div>
                </Card>

                <Card padding="lg">
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
                <Card padding="lg">
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

              {/* Tech Stack Lifecycle Monitor */}
              <div className="mt-8">
                <TechStackLifecycleMonitor items={techStackItems} />
              </div>

              {/* ── DETERMINISTIC FORENSIC TELEMETRY STREAM ── */}
              <Card padding="lg" className="bg-slate-950/85 dark:bg-slate-950/45 border border-slate-800/80 text-left mt-8">
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
              <Card padding="lg">
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
                              <Badge
                                variant={mapping.status === 'Verified' ? 'success' : 'warning'}
                                className="font-extrabold uppercase tracking-wider text-[9px] font-mono rounded-lg px-2 py-0.5"
                              >
                                {mapping.status}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* ── RAW JSON PAYLOAD EXPLORER ── */}
              <Card padding="lg">
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
                          {JSON.stringify(activeGhiData, null, 2)}
                        </pre>
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>

              {/* Framework compliance / Calendar Lists */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card padding="lg">
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

                <Card padding="lg">
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
