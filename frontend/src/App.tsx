import { Routes, Route, useNavigate } from 'react-router-dom';
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
            <EnvironmentHeader />
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
        </PersonaProvider>
      </DemoModeProvider>
    </AuthProvider>
  );
}
