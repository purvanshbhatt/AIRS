import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Settings, CheckSquare, Square, TrendingUp, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge } from '../components/ui';
import { getOrganizations, getRecommendedActions, projectDecisions, ApiRequestError, RecommendedAction, ProjectReadinessResponse, DecisionAction } from '../api';
import type { Organization } from '../types';

export function DecisionEngine() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  
  // Data States
  const [recommendations, setRecommendations] = useState<RecommendedAction[]>([]);
  const [projection, setProjection] = useState<ProjectReadinessResponse | null>(null);
  
  // Selection State
  const [selectedActions, setSelectedActions] = useState<DecisionAction[]>([]);
  
  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [projecting, setProjecting] = useState(false);
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

  const loadRecommendations = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendedActions(selectedOrgId);
      setRecommendations(data);
      // Reset selections when org changes
      setSelectedActions([]);
      
      // Get baseline projection (empty actions list)
      const baseline = await projectDecisions(selectedOrgId, { actions: [] });
      setProjection(baseline);
    } catch (err) {
      setError(
        err instanceof ApiRequestError 
          ? err.toDisplayMessage() 
          : 'Failed to load recommended decision actions.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [selectedOrgId]);

  // Run projection when selection changes
  useEffect(() => {
    if (!selectedOrgId || loading) return;

    const runProjection = async () => {
      setProjecting(true);
      try {
        const data = await projectDecisions(selectedOrgId, { actions: selectedActions });
        setProjection(data);
      } catch (err) {
        console.error('Failed to project decisions', err);
      } finally {
        setProjecting(false);
      }
    };

    // Debounce projection calls by 300ms
    const timer = setTimeout(runProjection, 300);
    return () => clearTimeout(timer);
  }, [selectedActions, selectedOrgId]);

  const toggleAction = (rec: RecommendedAction) => {
    const actionKey = (act: DecisionAction) => 
      `${act.type}-${act.software_name || ''}`;
      
    const isSelected = selectedActions.some(
      a => actionKey(a) === actionKey(rec.action)
    );

    if (isSelected) {
      setSelectedActions(selectedActions.filter(a => actionKey(a) !== actionKey(rec.action)));
    } else {
      setSelectedActions([...selectedActions, rec.action]);
    }
  };

  const getActionTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'verify_control':
        return <ShieldCheck className="w-4 h-4 text-emerald-500" />;
      case 'remediate_exposure':
      case 'remediate_lifecycle':
        return <Settings className="w-4 h-4 text-indigo-500" />;
      default:
        return <HelpCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Initializing Boardroom Decision Simulator...</p>
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
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to load Decision Engine</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error}</p>
        </div>
        <button onClick={loadRecommendations} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold rounded-lg transition-colors">
          Retry Connection
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
            <TrendingUp className="w-5 h-5 text-indigo-650 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Postural ROI & Decision Simulator
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              Which security investments will yield the highest risk reduction?
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: List of recommended actions */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-2">Prioritized Recommendations</h3>
          {recommendations.length === 0 ? (
            <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 p-8 text-center">
              <p className="text-sm text-slate-550 dark:text-slate-400 font-semibold">No recommended actions found.</p>
              <p className="text-xs text-slate-450 dark:text-slate-500 mt-1">Your posture has no outstanding exposure or lifecycle warnings.</p>
            </Card>
          ) : (
            recommendations.map((rec, idx) => {
              const actionKey = (act: DecisionAction) => 
                `${act.type}-${act.software_name || ''}`;
              const isSelected = selectedActions.some(
                a => actionKey(a) === actionKey(rec.action)
              );

              return (
                <div
                  key={idx}
                  onClick={() => toggleAction(rec)}
                  className={`p-4 rounded-2xl border cursor-pointer flex items-start justify-between gap-4 transition-all duration-200 ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-500/5 dark:bg-indigo-950/20 shadow-sm'
                      : 'border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <button className="pt-0.5 text-slate-400 dark:text-slate-650 hover:text-indigo-500 transition-colors">
                      {isSelected ? (
                        <CheckSquare className="w-5 h-5 text-indigo-500" />
                      ) : (
                        <Square className="w-5 h-5" />
                      )}
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="p-1 bg-slate-100 dark:bg-slate-900 rounded-lg">
                          {getActionTypeIcon(rec.action.type)}
                        </span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                          {rec.action.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <h4 className="text-sm font-black text-slate-905 dark:text-slate-100 mt-2">
                        {rec.description}
                      </h4>
                      <p className="text-xs text-slate-550 dark:text-slate-450 mt-1.5 font-semibold leading-relaxed">
                        Remediating this {rec.action.software_name || 'asset'} modifier directly offsets systemic concentration risk factors.
                      </p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="success" className="font-bold font-mono">
                      +{rec.projected_delta.toFixed(1)} pts
                    </Badge>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right column: Simulation projections */}
        <div className="lg:col-span-1 space-y-6">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-2">Simulation Impact Summary</h3>
          <Card className="rounded-3xl border border-slate-220 dark:border-slate-800/80 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md p-6">
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Baseline Posture</span>
                  <span className="text-3xl font-extrabold text-slate-400 dark:text-slate-500 font-mono mt-1 block">
                    {projection ? `${Math.round(projection.assessment_score)}%` : '—'}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Projected Posture</span>
                  <span className="text-3xl font-black text-indigo-500 font-mono mt-1 block">
                    {projection ? `${Math.round(projection.final_readiness)}%` : '—'}
                  </span>
                </div>
              </div>              {/* projected delta badge */}
              {projection && projection.readiness_delta !== null && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between text-xs text-[#00C853] font-bold font-sans">
                  <span>Net Posture Increase</span>
                  <span className="font-mono text-sm">+{projection.readiness_delta.toFixed(1)} Points</span>
                </div>
              )}

              {/* Simulation metrics breakdown */}
              {projection && (
                <div className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-3 font-mono text-[11px]">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-sans mb-1">Scoring Modifier Details</h4>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Telemetry Verification</span>
                    <span className="text-[#00C853] font-bold">+{projection.modifiers.verification_modifier.toFixed(1)}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Framework Coverage</span>
                    <span className="text-slate-800 dark:text-slate-200 font-bold">+{projection.modifiers.coverage_modifier.toFixed(1)}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Software Lifecycle (EOL)</span>
                    <span className={`font-bold ${projection.modifiers.lifecycle_modifier < 0 ? 'text-red-500' : 'text-slate-500'}`}>
                      {projection.modifiers.lifecycle_modifier.toFixed(1)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Exploit Exposure (KEVs)</span>
                    <span className={`font-bold ${projection.modifiers.exposure_modifier < 0 ? 'text-red-500' : 'text-slate-500'}`}>
                      {projection.modifiers.exposure_modifier.toFixed(1)}
                    </span>
                  </div>
                </div>
              )}

              {/* Actions detail list */}
              {selectedActions.length > 0 && (
                <div className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-2">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Simulated Actions ({selectedActions.length})</h4>
                  <div className="space-y-1.5">
                    {selectedActions.map((act, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-805/50 text-[10px] font-semibold text-slate-650 dark:text-slate-400">
                        {getActionTypeIcon(act.type)}
                        <span className="truncate max-w-[170px]">
                          {act.type === 'remediate_lifecycle' ? 'Upgrade ' : 'Remediate '}
                          {act.software_name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}

export default DecisionEngine;
