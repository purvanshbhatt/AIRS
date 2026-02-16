import { Routes, Route, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { DashboardLayout } from './components/layout';
import DocsLayout from './components/layout/DocsLayout';
import { ToastProvider } from './components/ui';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { isApiConfigured, apiBaseUrl, isDevelopment } from './config';
import { setUnauthorizedHandler, getSystemStatus } from './api';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Organizations from './pages/Organizations';
import Assessments from './pages/Assessments';
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

function DemoModeBanner() {
  const [isDemoMode, setIsDemoMode] = useState(false);

  useEffect(() => {
    getSystemStatus()
      .then((status) => setIsDemoMode(status.demo_mode))
      .catch(() => setIsDemoMode(false));
  }, []);

  if (!isDemoMode) return null;

  return (
    <div className="bg-blue-600 text-white px-4 py-2 text-center text-sm font-medium">
      Public Beta - Sample environment with synthetic data
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
          <Route path="/assessment/new" element={<NewAssessment />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/integrations" element={<Integrations />} />
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
      <ToastProvider>
        <AuthRedirectHandler />
        <ApiConfigBanner />
        <DemoModeBanner />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/about" element={<About />} />
          <Route path="/security" element={<SecurityPage />} />
          <Route path="/pilot" element={<PilotPage />} />
          <Route path="/status" element={<StatusPage />} />

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
    </AuthProvider>
  );
}
