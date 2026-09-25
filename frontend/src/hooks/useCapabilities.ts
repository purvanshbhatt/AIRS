import { useState, useEffect, useCallback } from 'react';
import { getCapabilities, type CapabilitiesResponse } from '../api';
import { useAuth } from '../contexts/AuthContext';

export interface UseCapabilitiesResult {
  capabilities: CapabilitiesResponse | null;
  loading: boolean;
  error: string | null;
  /** Check if a specific entitlement is granted */
  has: (entitlement: string) => boolean;
  /** True when org has an active paid plan */
  isPaid: boolean;
  /** Current plan name */
  plan: string;
  /** Refresh capabilities from backend */
  refresh: () => Promise<void>;
}

export function useCapabilities(orgId: string): UseCapabilitiesResult {
  const { user } = useAuth();
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdminEmail = (email?: string | null): boolean => {
    if (!email) return false;
    const clean = email.toLowerCase().trim();
    return (
      clean === 'purvansh95b@gmail.com' ||
      clean === 'purvansh@resilai.org' ||
      clean.endsWith('@resilai.org') ||
      clean.includes('purvansh')
    );
  };

  const fetchCapabilities = useCallback(async () => {
    if (!orgId) {
      setCapabilities(null);
      setLoading(false);
      return;
    }

    // Administrator / Testing Exemption
    if (isAdminEmail(user?.email)) {
      setCapabilities({
        plan: 'enterprise',
        status: 'active',
        is_paid: true,
        entitlements: {
          demo_access: true,
          simulated_data: true,
          public_product_preview: true,
          account_management: true,
          real_organization: true,
          telemetry_ingestion: true,
          evidence_collection: true,
          readiness_scoring: true,
          connectors_manage: true,
          executive_reports: true,
          api_keys: true,
          webhooks: true,
          advanced_reporting: true,
          additional_users: true,
          advanced_integrations: true,
          enterprise_controls: true,
          custom_frameworks: true,
        },
      });
      setLoading(false);
      return;
    }

    // Skip for demo sessions
    const isDemo = typeof window !== 'undefined' && (
      localStorage.getItem('resilai_demo_user') === 'true' ||
      window.location.search.includes('env=demo') ||
      window.location.hostname.includes('demo')
    );
    if (isDemo) {
      // Demo orgs get full demo-level entitlements
      setCapabilities({
        plan: 'demo',
        status: 'active',
        is_paid: false,
        entitlements: {
          demo_access: true,
          simulated_data: true,
          public_product_preview: true,
          account_management: true,
          real_organization: false,
          telemetry_ingestion: false,
          evidence_collection: false,
          readiness_scoring: false,
          connectors_manage: false,
          executive_reports: false,
          api_keys: false,
          webhooks: false,
          advanced_reporting: false,
          additional_users: false,
          advanced_integrations: false,
          enterprise_controls: false,
          custom_frameworks: false,
        },
      });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await getCapabilities(orgId);
      setCapabilities(data);
    } catch (err) {
      console.warn('[useCapabilities] Failed to fetch:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch capabilities');
      // On error, assume free plan for safety
      setCapabilities({
        plan: 'free',
        status: 'unpaid',
        is_paid: false,
        entitlements: {
          demo_access: true,
          simulated_data: true,
          public_product_preview: true,
          account_management: true,
        },
      });
    } finally {
      setLoading(false);
    }
  }, [orgId, user?.email]);

  useEffect(() => {
    fetchCapabilities();
  }, [fetchCapabilities]);

  const has = useCallback(
    (entitlement: string): boolean => {
      if (!capabilities) return false;
      return capabilities.entitlements[entitlement] === true;
    },
    [capabilities]
  );

  return {
    capabilities,
    loading,
    error,
    has,
    isPaid: capabilities?.is_paid ?? false,
    plan: capabilities?.plan ?? 'free',
    refresh: fetchCapabilities,
  };
}
