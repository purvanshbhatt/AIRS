import { Routes, Route } from 'react-router-dom';
import { DashboardLayout } from './components/layout';
import { ToastProvider } from './components/ui';
import { AuthProvider } from './contexts/AuthContext';

// Pages
import Landing from './pages/Landing';
import Home from './pages/Home';
import NewOrg from './pages/NewOrg';
import NewAssessment from './pages/NewAssessment';
import Results from './pages/Results';

// Dashboard wrapper component
function DashboardRoutes() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/organizations" element={<Home />} />
        <Route path="/org/new" element={<NewOrg />} />
        <Route path="/assessments" element={<Home />} />
        <Route path="/assessment/new" element={<NewAssessment />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/reports" element={<Home />} />
        <Route path="/settings" element={<Home />} />
      </Routes>
    </DashboardLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
        {/* Public landing page */}
        <Route path="/" element={<Landing />} />

        {/* Dashboard routes */}
        <Route path="/dashboard/*" element={<DashboardRoutes />} />

        {/* Assessment flow (within dashboard) */}
        <Route
          path="/assessment/new"
          element={
            <DashboardLayout>
              <NewAssessment />
            </DashboardLayout>
          }
        />
        <Route
          path="/org/new"
          element={
            <DashboardLayout>
              <NewOrg />
            </DashboardLayout>
          }
        />
        <Route
          path="/results/:id"
          element={
            <DashboardLayout>
              <Results />
            </DashboardLayout>
          }
        />
      </Routes>
    </ToastProvider>
  </AuthProvider>
  );
}
