import { Routes, Route, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import { DashboardLayout } from './components/layout';
import DocsLayout from './components/layout/DocsLayout';
import { ToastProvider } from './components/ui';
import { AuthProvider, DemoModeProvider, useDemoMode } from './contexts';
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
import Results from './pages/Results';
import Settings from './pages/Settings';
import Integrations from './pages/Integrations';
import About from './pages/About';
import SecurityPage from './pages/Security';
import PilotPage from './pages/Pilot';
import StatusPage from './pages/Status';
import GovernanceProfile from './pages/GovernanceProfile';
import AuditCalendar from './pages/AuditCalendar';
import TechStack from './pages/TechStack';
import PilotDashboard from './pages/PilotDashboard';
import AuditorView from './pages/AuditorView';
import ComplianceDrift from './pages/ComplianceDrift';
import ReliabilityDashboard from './pages/ReliabilityDashboard';
import RemediationLedger from './pages/RemediationLedger';

// Docs pages
import { DocsOverview, DocsMethodology, DocsFrameworks, DocsSecurity, DocsApi } from './pages/docs';

function ApiConfigBanner() {
  if (isApiConfigured) return null;

  return (
    <div className="bg-amber-500 text-white px-4 py-2 text-center text-sm font-medium">
      API base URL not configured. Set VITE_API_BASE_URL in your environment.
      <span className="ml-2 opacity-75">Currently using: {apiBaseUrl}</span>
    </div>
  );
}

function EnvironmentBanner() {
  const { systemStatus } = useDemoMode();
  const host = typeof window !== 'undefined' ? window.location.hostname : '';
  const isStaging = systemStatus?.environment === 'staging' || 
                    host.includes('staging') || 
                    import.meta.env.MODE === 'staging';

  const isDemo = systemStatus?.environment === 'demo' || 
                 host.includes('demo') || 
                 import.meta.env.MODE === 'demo';

  if (isStaging) {
    return (
      <div className="bg-amber-500/10 border-b border-amber-500/50 text-amber-600 dark:text-amber-400 py-2 px-4 text-center text-xs font-semibold flex items-center justify-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
        <span>STAGING ENVIRONMENT - GOVERNANCE SPRINT ACTIVE. DATA MAY BE FLUSHED.</span>
      </div>
    );
  }

  if (isDemo) {
    return (
      <div className="bg-blue-500/10 border-b border-blue-500/50 text-blue-600 dark:text-blue-400 py-2 px-4 text-center text-xs font-semibold flex items-center justify-center gap-2">
        <Lock className="w-4 h-4 text-blue-500 shrink-0" />
        <span>DEMO ENVIRONMENT - LOCKED AT NIST CSF 2.0 MILESTONE.</span>
      </div>
    );
  }

  return null;
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
          <Route path="/assessment/new" element={<NewAssessment />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/governance" element={<GovernanceProfile />} />
          <Route path="/audit-calendar" element={<AuditCalendar />} />
          <Route path="/tech-stack" element={<TechStack />} />
          <Route path="/pilot-program" element={<PilotDashboard />} />
          <Route path="/compliance-drift" element={<ComplianceDrift />} />
          <Route path="/reliability" element={<ReliabilityDashboard />} />
          <Route path="/remediation" element={<RemediationLedger />} />
        </Routes>
      </DashboardLayout>
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
  return (
    <AuthProvider>
      <DemoModeProvider>
        <ToastProvider>
          <AuthRedirectHandler />
          <ApiConfigBanner />
          <EnvironmentBanner />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/about" element={<About />} />
            <Route path="/security" element={<SecurityPage />} />
            <Route path="/pilot" element={<PilotPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/auditor" element={<AuditorView />} />

            <Route path="/dashboard/*" element={<DashboardRoutes />} />

            <Route
              path="/assessment/new"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <NewAssessment />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/org/new"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <NewOrg />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:id"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Results />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings/integrations"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Integrations />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route path="/docs" element={<DocsLayout />}>
              <Route index element={<DocsOverview />} />
              <Route path="methodology" element={<DocsMethodology />} />
              <Route path="frameworks" element={<DocsFrameworks />} />
              <Route path="security" element={<DocsSecurity />} />
              <Route path="api" element={<DocsApi />} />
            </Route>
          </Routes>
        </ToastProvider>
      </DemoModeProvider>
    </AuthProvider>
  );
}
