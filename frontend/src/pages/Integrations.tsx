/**
 * S1.8-AUDIT-FIX-B01: Explicit redirect from legacy /integrations to canonical /dashboard/evidence-network.
 * Using a silent alias (export default EvidenceNetwork) hid the rename from users and broke deep-link UX.
 * React Router Navigate with replace preserves browser history correctly.
 */
import { Navigate, useLocation } from 'react-router-dom';

export default function IntegrationsRedirect() {
  const location = useLocation();
  // Forward any query-string the caller may have appended (e.g. ?org=...)
  return <Navigate to={`/dashboard/evidence-network${location.search}`} replace />;
}