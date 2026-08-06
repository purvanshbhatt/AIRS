import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import DocsLayout from './components/layout/DocsLayout';
import { EnvironmentHeader } from './components/layout/EnvironmentHeader';
import { ToastProvider } from './components/ui';
import { AuthProvider, DemoModeProvider, useDemoMode, PersonaProvider } from './contexts';
import { ProtectedRoute } from './components/ProtectedRoute';
import { isApiConfigured, apiBaseUrl, isDevelopment } from './config';
import { setUnauthorizedHandler } from './api';

// Public Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import About from './pages/About';
import SecurityPage from './pages/Security';
import PilotPage from './pages/Pilot';
import StatusPage from './pages/Status';
import AuditorView from './pages/AuditorView';

// MORNING OPERATIONS
import TodayPage from './features/readiness/TodayPage';
import NeedsAttentionPage from './features/readiness/NeedsAttentionPage';
import RecoveryReadinessPage from './features/readiness/RecoveryReadinessPage';
import ActivityPage from './features/readiness/ActivityPage';

// TECHNOLOGY OPERATIONS DOMAIN MINI-PRODUCTS
import IdentityPage from './pages/technology/IdentityPage';
import DevicesPage from './pages/technology/DevicesPage';
import BackupsPage from './pages/technology/BackupsPage';
import EmailPage from './pages/technology/EmailPage';
import NetworkPage from './pages/technology/NetworkPage';
import CloudPage from './pages/technology/CloudPage';
import AIPage from './pages/technology/AIPage';

// LEGACY & PLATFORM
import { EvidenceNetwork } from './pages/EvidenceNetwork';
import ComplianceDrift from './pages/ComplianceDrift';
import ReliabilityDashboard from './pages/ReliabilityDashboard';
import TechnologyIntelligence from './pages/TechnologyIntelligence';
import AuditCalendar from './pages/AuditCalendar';
import Settings from './pages/Settings';
import Integrations from './pages/Integrations';

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

function MainAppRoutes() {
  return (
    <ProtectedRoute>
      <Routes>
        <Route element={<AppLayout />}>
          {/* MORNING OPERATIONS */}
          <Route path="/morning-brief" element={<TodayPage />} />
          <Route path="/needs-attention" element={<NeedsAttentionPage />} />
          <Route path="/recovery" element={<RecoveryReadinessPage />} />
          <Route path="/yesterday" element={<ActivityPage />} />
          
          {/* TECHNOLOGY OPERATIONS DOMAIN MINI-PRODUCTS */}
          <Route path="/identity" element={<IdentityPage />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/backups" element={<BackupsPage />} />
          <Route path="/email" element={<EmailPage />} />
          <Route path="/network" element={<NetworkPage />} />
          <Route path="/cloud" element={<CloudPage />} />
          <Route path="/ai" element={<AIPage />} />

          {/* PLATFORM */}
          <Route path="/connectors" element={<Integrations />} />
          <Route path="/activity" element={<EvidenceNetwork />} />
          <Route path="/activity/compliance-drift" element={<ComplianceDrift />} />
          <Route path="/technology/intelligence" element={<TechnologyIntelligence />} />
          <Route path="/audit" element={<AuditCalendar />} />
          <Route path="/settings" element={<Settings />} />

          {/* BACKWARD-COMPATIBLE REDIRECTS FOR LEGACY PATHS */}
          <Route path="/dashboard/today" element={<Navigate to="/morning-brief" replace />} />
          <Route path="/dashboard/attention" element={<Navigate to="/needs-attention" replace />} />
          <Route path="/dashboard/recovery" element={<Navigate to="/recovery" replace />} />
          <Route path="/dashboard/activity" element={<Navigate to="/yesterday" replace />} />
          
          <Route path="/explore/verification" element={<Navigate to="/activity" replace />} />
          <Route path="/explore/evidence" element={<Navigate to="/activity" replace />} />
          <Route path="/explore/systems" element={<Navigate to="/identity" replace />} />
          <Route path="/explore/integrations" element={<Navigate to="/ai" replace />} />
          <Route path="/explore/history" element={<Navigate to="/yesterday" replace />} />

          <Route path="/admin/integrations" element={<Navigate to="/connectors" replace />} />
          <Route path="/admin/audit" element={<Navigate to="/audit" replace />} />
          <Route path="/admin/settings" element={<Navigate to="/settings" replace />} />
          <Route path="/admin/team" element={<Navigate to="/settings" replace />} />

          {/* INCIDENTS (Placeholder) */}
          <Route path="/incidents/*" element={<div className="p-8 text-center text-slate-500">Incident workspace coming soon</div>} />

          {/* Fallback to Morning Brief */}
          <Route path="*" element={<Navigate to="/morning-brief" replace />} />
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
  return (
    <AuthProvider>
      <DemoModeProvider>
        <PersonaProvider>
          <ToastProvider>
            <AuthRedirectHandler />
            <ApiConfigBanner />
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/readiness" element={<Navigate to="/morning-brief" replace />} />
              <Route path="/login" element={<Login />} />
              <Route path="/about" element={<About />} />
              <Route path="/security" element={<SecurityPage />} />
              <Route path="/pilot" element={<PilotPage />} />
              <Route path="/status" element={<StatusPage />} />
              <Route path="/auditor" element={<AuditorView />} />

              {/* Main Application Routes */}
              <Route path="/*" element={<MainAppRoutes />} />

              {/* Docs */}
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
