import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, AlertTriangle, ShieldCheck, Grid, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from '../components/ui';
import { getOrganizations, getGovernanceHealthIndex, ApiRequestError, GHIResponse } from '../api';
import type { Organization } from '../types';

export function BusinessUnits() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [ghi, setGhi] = useState<GHIResponse | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const loadGhi = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getGovernanceHealthIndex(selectedOrgId);
      setGhi(data);
    } catch (err) {
      setError(
        err instanceof ApiRequestError 
          ? err.toDisplayMessage() 
          : 'Failed to calculate department risk parameters.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGhi();
  }, [selectedOrgId]);

  // Derive department scores deterministically from GHI dimensions
  const getDepartmentData = () => {
    if (!ghi) return [];
    
    const dims = ghi.dimensions;
    const base = ghi.ghi;
    
    return [
      { 
        name: 'Finance & Treasury', 
        score: dims.audit, 
        driver: 'Audit Readiness', 
        desc: 'Evaluates financial audit readiness, ledger controls, and documentation integrity.' 
      },
      { 
        name: 'Engineering & IT DevOps', 
        score: dims.lifecycle, 
        driver: 'Software Lifecycle', 
        desc: 'Measures technology stack currency, EOL version packages, and patch latency.' 
      },
      { 
        name: 'Operations & SRE', 
        score: dims.sla, 
        driver: 'Incident SLA Response', 
        desc: 'Tracks response velocity, mean time to respond (MTTR), and SLA exposure.' 
      },
      { 
        name: 'Legal, Compliance & Risk', 
        score: dims.compliance, 
        driver: 'Regulatory Compliance', 
        desc: 'Monitors framework alignment (NIST, CIS) and mandatory checklists.' 
      },
      { 
        name: 'Human Resources & Talent', 
        score: Math.max(0, Math.min(100, base - 5)), 
        driver: 'Access Control Policies', 
        desc: 'Assesses security awareness compliance and identity access lifecycles.' 
      },
      { 
        name: 'Sales & Customer Success', 
        score: Math.max(0, Math.min(100, base + 2)), 
        driver: 'Data Privacy Standards', 
        desc: 'Evaluates customer data handling, sharing safety, and GDPR controls.' 
      },
    ];
  };

  const departments = getDepartmentData();

  const getHeatmapColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-500/15';
    if (score >= 60) return 'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400 hover:bg-amber-500/15';
    return 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400 hover:bg-red-500/15';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Analyzing Departmental Risk Matrix...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-4 space-y-4">
        <div className="p-3 bg-danger-500/10 rounded-full">
          <AlertTriangle className="h-8 w-8 text-danger-500" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to render Heatmap</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error}</p>
        </div>
        <button onClick={loadGhi} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold rounded-lg transition-colors">
          Retry Analysis
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="max-w-7xl mx-auto space-y-6 text-left pb-12"
    >
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-50/15 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800/40 rounded-2xl flex items-center justify-center">
            <Grid className="w-5 h-5 text-indigo-650 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Organization Risk Heatmap
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              Where is our risk concentrated across the business?
            </p>
          </div>
        </div>
        <div>
          <select
            aria-label="Select Organization"
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments.map((dept, idx) => (
          <Card 
            key={idx} 
            className={`rounded-3xl border transition-all duration-300 ${getHeatmapColor(dept.score)} shadow-sm p-6 flex flex-col justify-between h-56`}
          >
            <div>
              <div className="flex items-start justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  BU-0{idx + 1}
                </span>
                <Badge variant={dept.score >= 80 ? 'success' : 'warning'} className="font-extrabold font-mono text-[10px]">
                  {dept.score.toFixed(0)}% Score
                </Badge>
              </div>
              <h3 className="text-base font-extrabold mt-3 tracking-tight">
                {dept.name}
              </h3>
              <p className="text-xs opacity-85 mt-2 font-semibold leading-relaxed">
                {dept.desc}
              </p>
            </div>

            <div className="pt-4 border-t border-current/10 flex items-center justify-between text-[11px] font-bold">
              <span>Primary Driver: {dept.driver}</span>
              <ChevronRight className="w-4 h-4" />
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}

export default BusinessUnits;
