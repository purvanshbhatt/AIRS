import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { DashboardLayout, DocsLayout } from './components/layout';
import { ToastProvider } from './components/ui';
import { AuthProvider, ThemeProvider, useAuth } from './contexts';
import { ProtectedRoute } from './components/ProtectedRoute';
import { isApiConfigured, apiBaseUrl, isDevelopment } from './config';
import { setUnauthorizedHandler } from './api';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Organizations from './pages/Organizations';
import Assessments from './pages/Assessments';
import Assessment from './pages/Assessment';
import Reports from './pages/Reports';
import NewOrg from './pages/NewOrg';
import NewAssessment from './pages/NewAssessment';
import Results from './pages/Results';
import Settings from './pages/Settings';

// Docs Pages
import { DocsOverview, DocsMethodology, DocsFrameworks, DocsSecurity, DocsApi } from './pages/docs';

/**
 * Root redirect - sends authenticated users to dashboard, others to login
 */
function RootRedirect() {
  const { user, loading, isConfigured } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-gray-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // If Firebase not configured (dev mode) or user is authenticated, go to dashboard
  if (!isConfigured || user) {
    return <Navigate to="/dashboard" replace />;
  }

  // Not authenticated - show landing page
  return <Landing />;
}

/**
 * Catch-all redirect for unknown routes
 */
function CatchAllRedirect() {
  const { user, loading, isConfigured } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-gray-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // If Firebase not configured (dev mode) or user is authenticated, go to dashboard
  if (!isConfigured || user) {
    return <Navigate to="/dashboard" replace />;
  }

  // Not authenticated - go to login
  return <Navigate to="/login" replace />;
}

// API Configuration Warning Banner (dev only when not configured)
function ApiConfigBanner() {
  if (isApiConfigured) return null;

  return (
    <div className="bg-amber-500 text-white px-4 py-2 text-center text-sm font-medium">
      ⚠️ API base URL not configured. Set VITE_API_BASE_URL in your environment.
      <span className="ml-2 opacity-75">Currently using: {apiBaseUrl}</span>
    </div>
  );
}

// Dashboard wrapper component (protected)
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
          <Route path="/assessment/:id" element={<Assessment />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          {/* Catch unknown dashboard paths - redirect to main dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

// Component to set up 401 redirect handler
function AuthRedirectHandler() {
  const navigate = useNavigate();

  useEffect(() => {
    // Register the 401 handler with the API client
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
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <AuthRedirectHandler />
          <ApiConfigBanner />
          <Routes>
            {/* Root - redirects based on auth state */}
            <Route path="/" element={<RootRedirect />} />

            {/* /home redirects to /dashboard */}
            <Route path="/home" element={<Navigate to="/dashboard" replace />} />

            {/* Public routes */}
            <Route path="/login" element={<Login />} />

            {/* Public docs routes */}
            <Route path="/docs" element={<DocsLayout />}>
              <Route index element={<DocsOverview />} />
              <Route path="methodology" element={<DocsMethodology />} />
              <Route path="frameworks" element={<DocsFrameworks />} />
              <Route path="security" element={<DocsSecurity />} />
              <Route path="api" element={<DocsApi />} />
            </Route>

            {/* Protected dashboard routes */}
            <Route path="/dashboard/*" element={<DashboardRoutes />} />

            {/* Protected assessment flow routes (legacy paths) */}
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
              path="/assessment/:id"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Assessment />
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

            {/* Catch-all route - redirects based on auth state */}
            <Route path="*" element={<CatchAllRedirect />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
