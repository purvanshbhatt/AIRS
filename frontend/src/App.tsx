import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import { DashboardLayout } from './components/layout';
import DocsLayout from './components/layout/DocsLayout';
import { EnvironmentHeader } from './components/layout/EnvironmentHeader';
import { ToastProvider } from './components/ui';
import { AuthProvider, DemoModeProvider, useDemoMode, PersonaProvider } from './contexts';
import { ProtectedRoute } from './components/ProtectedRoute';
import { isApiConfigured, apiBaseUrl, isDevelopment } from './config';
import { setUnauthorizedHandler } from './api';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Organizations from './pages/Organizations';
import Assessments from './pages/Assessments';
import AnalyticsPage from './pages/Analytics';
import Reports from './pages/Reports';
import NewOrg from './pages/NewOrg';
import NewAssessment from './pages/NewAssessment';
import QuickAssessment from './pages/QuickAssessment';
import Results from './pages/Results';
import Settings from './pages/Settings';
import Integrations from './pages/Integrations';
import About from './pages/About';
import SecurityPage from './pages/Security';
import PilotPage from './pages/Pilot';
import StatusPage from './pages/Status';
import GovernanceProfile from './pages/GovernanceProfile';
import AuditCalendar from './pages/AuditCalendar';
import TechnologyIntelligence from './pages/TechnologyIntelligence';
import AuditorView from './pages/AuditorView';
import ComplianceDrift from './pages/ComplianceDrift';
import ReliabilityDashboard from './pages/ReliabilityDashboard';
import RemediationLedger from './pages/RemediationLedger';
import ReadinessTimeline from './pages/ReadinessTimeline';
import BoardStory from './pages/BoardStory';
import DecisionEngine from './pages/DecisionEngine';
import BusinessUnits from './pages/BusinessUnits';
import { EvidenceNetwork } from './pages/EvidenceNetwork';
import AIAttackSimulationLab from './pages/AIAttackSimulationLab';

// Readiness Product Pages
import ReadinessLayout from './features/readiness/Layout';
import TodayPage from './features/readiness/TodayPage';
import NeedsAttentionPage from './features/readiness/NeedsAttentionPage';
import RecoveryReadinessPage from './features/readiness/RecoveryReadinessPage';
import ActivityPage from './features/readiness/ActivityPage';
import ReadinessSettingsPage from './features/readiness/SettingsPage';

// Docs pages
import { DocsOverview, DocsMethodology, DocsFrameworks, DocsSecurity, DocsApi } from './pages/docs';

const IS_READINESS_PRODUCT = true; // Feature flag

function ApiConfigBanner() {
  if (isApiConfigured) return null;

  return (
    <div className="bg-amber-500 text-white px-4 py-2 text-center text-sm font-medium">
      API base URL not configured. Set VITE_API_BASE_URL in your environment.
      <span className="ml-2 opacity-75">Currently using: {apiBaseUrl}</span>
    </div>
  );
}

function DashboardRoutes() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/organizations" element={<Organizations />} />
          <Route path="/org/new" element={<NewOrg />} />
          <Route path="/assessments" element={<Assessments />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/assessment/new" element={import.meta.env.VITE_APP_ENV === 'staging' ? <NewAssessment /> : <QuickAssessment />} />
          <Route path="/assessment/quick" element={<QuickAssessment />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />

          {/* Canonical Sprint 1.8 / Sprint 2 routes */}
          <Route path="/readiness-timeline" element={<ReadinessTimeline />} />
          <Route path="/board-story" element={<BoardStory />} />
          <Route path="/decision-engine" element={<DecisionEngine />} />
          <Route path="/business-units" element={<BusinessUnits />} />

          {/* Evidence Network — canonical path */}
          <Route path="/evidence-network" element={<EvidenceNetwork />} />

          {/* Legacy redirect — /integrations -> /evidence-network (F-003 / T-B01) */}
          <Route path="/integrations" element={<Integrations />} />

          {/* Retained pages */}
          <Route path="/governance" element={<GovernanceProfile />} />
          <Route path="/audit-calendar" element={<AuditCalendar />} />
          <Route path="/tech-stack" element={<TechnologyIntelligence />} />
          <Route path="/compliance-drift" element={<ComplianceDrift />} />
          <Route path="/reliability" element={<ReliabilityDashboard />} />
          <Route path="/remediation" element={<RemediationLedger />} />
          <Route path="/ai-attack-simulation-lab" element={<AIAttackSimulationLab />} />
        </Routes>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function ReadinessRoutes() {
  return (
    <ProtectedRoute>
      <Routes>
        <Route element={<ReadinessLayout />}>
          <Route index element={<TodayPage />} />
          <Route path="actions" element={<NeedsAttentionPage />} />
          <Route path="continuity" element={<RecoveryReadinessPage />} />
          <Route path="activity" element={<ActivityPage />} />
          <Route path="settings" element={<ReadinessSettingsPage />} />
        </Route>
      </Routes>
    </ProtectedRoute>
  );
}

function AuthRedirectHandler() {
  const navigate = useNavigate();

  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (isDevelopment) {
        console.log('[App] Handling 401 - navigating to /login');
      }
      navigate('/login', { replace: true });
    });
  }, [navigate]);

  return null;
}

export default function App() {
  useEffect(() => {
    const hostname = window.location.hostname;
    const isFirebaseDefaultDomain = hostname.endsWith('.web.app') || hostname.endsWith('.firebaseapp.com');
    if (isFirebaseDefaultDomain) {
      let targetDomain = '';
      if (hostname.includes('staging')) {
        targetDomain = 'staging.resilai.org';
      } else if (hostname.includes('demo') || hostname.includes('gen-lang-client-0384513977')) {
        targetDomain = 'demo.resilai.org';
      } else {
        targetDomain = 'resilai.org';
      }
      window.location.replace(`https://${targetDomain}${window.location.pathname}${window.location.search}${window.location.hash}`);
    }
  }, []);

  return (
    <AuthProvider>
      <DemoModeProvider>
        <PersonaProvider>
          <ToastProvider>
            <AuthRedirectHandler />
            <ApiConfigBanner />
            {!IS_READINESS_PRODUCT && <EnvironmentHeader />}
            <Routes>
            <Route path="/" element={IS_READINESS_PRODUCT ? <Navigate to="/readiness" replace /> : <Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/about" element={<About />} />
            <Route path="/security" element={<SecurityPage />} />
            <Route path="/pilot" element={<PilotPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/auditor" element={<AuditorView />} />

            <Route path="/dashboard/*" element={<DashboardRoutes />} />
            <Route path="/readiness/*" element={<ReadinessRoutes />} />

            {/* Legacy Backward-Compatible Redirects (S1.8-AUDIT-FIX-D01) */}
            <Route path="/assessment/new" element={<Navigate to="/dashboard/assessment/new" replace />} />
            <Route path="/assessment/quick" element={<Navigate to="/dashboard/assessment/quick" replace />} />
            <Route path="/org/new" element={<Navigate to="/dashboard/org/new" replace />} />
            <Route path="/results/:id" element={<Navigate to="/dashboard/results/:id" replace />} />
            <Route path="/settings/integrations" element={<Navigate to="/dashboard/evidence-network" replace />} />



            <Route path="/docs" element={<DocsLayout />}>
              <Route index element={<DocsOverview />} />
              <Route path="methodology" element={<DocsMethodology />} />
              <Route path="frameworks" element={<DocsFrameworks />} />
              <Route path="security" element={<DocsSecurity />} />
              <Route path="api" element={<DocsApi />} />
            </Route>
          </Routes>
        </ToastProvider>
        </PersonaProvider>
      </DemoModeProvider>
    </AuthProvider>
  );
}
