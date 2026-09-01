import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getOrganizations } from '../api';
import type { Organization } from '../types';

export interface ActiveOrgState {
  orgId: string;
  orgName: string;
  org: Organization | null;
  orgs: Organization[];
  isDemo: boolean;
  hasOrg: boolean;
  tier?: string;
  loading: boolean;
  selectOrg: (id: string) => void;
  resetOrg: () => void;
  refresh: () => Promise<void>;
}

export function useActiveOrg(): ActiveOrgState {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(() => {
    if (typeof window === 'undefined') return '';
    return localStorage.getItem('resilai_selected_org_id') || '';
  });

  const isDemo = typeof window !== 'undefined' && (
    localStorage.getItem('resilai_demo_user') === 'true' ||
    localStorage.getItem('resilai_demo_session') === 'true' ||
    window.location.search.includes('env=demo') ||
    window.location.hostname.includes('demo')
  );

  const fetchOrgs = useCallback(async () => {
    if (isDemo) {
      const demoOrg = {
        id: 'demo-health-org',
        name: 'Acme Health Systems (Demo)',
        industry: 'Healthcare',
        created_at: new Date().toISOString(),
        owner_uid: 'demo-executive-uid',
      } as unknown as Organization;
      setOrgs([demoOrg]);
      setSelectedOrgId('demo-health-org');
      setLoading(false);
      return;
    }

    if (!user) {
      setOrgs([]);
      setSelectedOrgId('');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getOrganizations();
      const orgList = data || [];
      setOrgs(orgList);
      
      if (orgList.length > 0) {
        const currentSaved = localStorage.getItem('resilai_selected_org_id');
        const found = orgList.find(o => o.id === currentSaved);
        if (found) {
          setSelectedOrgId(found.id);
        } else {
          // Stale, deleted, or unselected ID — automatically self-heal to first valid org
          const defaultId = orgList[0].id;
          localStorage.setItem('resilai_selected_org_id', defaultId);
          setSelectedOrgId(defaultId);
        }
      } else {
        localStorage.removeItem('resilai_selected_org_id');
        setSelectedOrgId('');
      }
    } catch (err) {
      console.warn('[useActiveOrg] Failed to fetch organizations:', err);
    } finally {
      setLoading(false);
    }
  }, [user, isDemo]);

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  const selectOrg = useCallback((id: string) => {
    localStorage.setItem('resilai_selected_org_id', id);
    setSelectedOrgId(id);
    window.location.reload();
  }, []);

  const resetOrg = useCallback(() => {
    localStorage.removeItem('resilai_selected_org_id');
    setSelectedOrgId('');
    fetchOrgs();
  }, [fetchOrgs]);

  const activeOrg = orgs.find(o => o.id === selectedOrgId) || (orgs.length > 0 ? orgs[0] : null);

  const orgId = activeOrg?.id || (isDemo ? 'demo-health-org' : '');
  const orgName = isDemo
    ? 'Acme Health Systems'
    : (activeOrg?.name || (user?.email ? `${user.email.split('@')[0]}'s Workspace` : ''));

  return {
    orgId,
    orgName,
    org: activeOrg || null,
    orgs,
    isDemo,
    hasOrg: Boolean(activeOrg || isDemo),
    loading,
    selectOrg,
    resetOrg,
    refresh: fetchOrgs,
  };
}
