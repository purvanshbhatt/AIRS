import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot,
  Shield,
  Activity,
  AlertTriangle,
  Clock,
  Plus,
  ArrowRight,
  RefreshCw,
  Sparkles,
  Lock,
  ExternalLink,
  ChevronRight,
  Database,
  CheckCircle2,
} from 'lucide-react';
import { useActiveOrg } from '../hooks/useActiveOrg';
import {
  getAgentAudits,
  createAgentAudit,
  AgentAuditItem,
  ApiRequestError,
} from '../api';

export default function AgentAuditPage() {
  const navigate = useNavigate();
  const { orgId, isDemo } = useActiveOrg();
  const [audits, setAudits] = useState<AgentAuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paywallError, setPaywallError] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [agentName, setAgentName] = useState('');
  const [environment, setEnvironment] = useState('Production');
  const [sourceType, setSourceType] = useState('splunk');
  const [businessContext, setBusinessContext] = useState('');

  const fetchAudits = async () => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAgentAudits(orgId);
      setAudits(data);
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
      } else {
        setError(err.message || 'Failed to load live agent audits.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
  }, [orgId]);

  const handleCreateAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgId) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await createAgentAudit(orgId, {
        agent_name: agentName || 'Autonomous Care Assistant',
        environment,
        source_type: sourceType,
        business_context: businessContext || 'Live autonomous operations',
        audit_window: '48h',
      });
      setShowCreateModal(false);
      setAgentName('');
      setBusinessContext('');
      navigate(`/agent-audit/${created.id}`);
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
        setShowCreateModal(false);
      } else {
        setError(err.message || 'Failed to initiate agent observation window.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Evaluation Complete
          </span>
        );
      case 'INGESTING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            Ingesting Live Traces
          </span>
        );
      case 'EVALUATING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            Evaluating Blast Radius
          </span>
        );
      case 'EXPIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <Clock className="w-3.5 h-3.5" />
            Window Expired (48h)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" />
            Window Initialized
          </span>
        );
    }
  };

  const getRemainingTime = (expiresAt: string) => {
    const remaining = new Date(expiresAt).getTime() - new Date().getTime();
    if (remaining <= 0) return 'Window Closed';
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const mins = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${mins}m observation remaining`;
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight">48-Hour Live AI Agent Blast-Radius Audit</h1>
                {isDemo && (
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Sandbox Demo
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-sm mt-0.5">
                Deterministic, time-bounded telemetry evaluation of autonomous tool execution, lateral blast radius, and NIST AI RMF / OWASP LLM alignment.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchAudits}
            className="p-2.5 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl border border-slate-700 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            Start 48-Hour Audit
          </button>
        </div>
      </div>

      {/* Paywall Banner if 402 */}
      {paywallError && (
        <div className="p-6 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 rounded-2xl">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
              <Lock className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-white">Design Partner Subscription Required</h3>
              <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
                48-Hour Live AI Agent Blast-Radius Audits require an active ResilAI subscription or design partner enrollment to ingest production traces and generate compliance audit artifacts.
              </p>
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={() => navigate('/pricing')}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs uppercase tracking-wider rounded-lg transition-colors"
                >
                  View Plans & Enroll
                </button>
                <button
                  onClick={() => navigate('/pilot')}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
                >
                  Request 14-Day Pilot
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Content Area */}
      {loading ? (
        <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800/80">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400 font-medium">Loading agent observation sessions...</p>
        </div>
      ) : audits.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800/80 max-w-2xl mx-auto">
          <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 text-indigo-400">
            <Bot className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No Active Agent Audits</h2>
          <p className="text-sm text-slate-400 mb-6 leading-relaxed">
            Deploy a bounded 48-hour observation window to ingest agent execution telemetry from your MSP, SIEM, or directly via OpenTelemetry. The deterministic engine validates tool authorization, lateral blast radius, and unconstrained action execution.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" />
            Launch First 48-Hour Session
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {audits.map((audit) => {
            const isCompleted = audit.status === 'COMPLETE';
            const score = audit.readiness_score;

            return (
              <div
                key={audit.id}
                onClick={() => navigate(`/agent-audit/${audit.id}`)}
                className="group relative bg-slate-900/50 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 p-6 rounded-2xl cursor-pointer transition-all duration-200"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  {/* Left Column */}
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors">
                        {audit.agent_name || 'Autonomous Agent'}
                      </h3>
                      <span className="text-xs px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        {audit.environment}
                      </span>
                      <span className="text-xs px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono uppercase">
                        {audit.source_type}
                      </span>
                      {getStatusBadge(audit.status)}
                    </div>

                    <p className="text-sm text-slate-400 line-clamp-1">
                      {audit.business_context || 'Autonomous operational workflow'}
                    </p>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                      <span className="flex items-center gap-1.5 text-slate-400 font-medium">
                        <Clock className="w-3.5 h-3.5 text-indigo-400" />
                        {getRemainingTime(audit.expires_at)}
                      </span>
                      <span>•</span>
                      <span>{audit.telemetry_event_count.toLocaleString()} telemetry traces</span>
                      <span>•</span>
                      <span>{audit.tool_action_count.toLocaleString()} tool actions</span>
                      <span>•</span>
                      <span>{audit.findings?.length || 0} blast-radius findings</span>
                    </div>
                  </div>

                  {/* Right Column: Score & CTA */}
                  <div className="flex items-center gap-6 self-end lg:self-center">
                    {score !== null && score !== undefined ? (
                      <div className="text-right">
                        <div className="text-2xl font-extrabold text-white">
                          <span
                            className={
                              score >= 80
                                ? 'text-emerald-400'
                                : score >= 60
                                ? 'text-amber-400'
                                : 'text-rose-400'
                            }
                          >
                            {Math.round(score)}%
                          </span>
                        </div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                          Readiness Score
                        </div>
                      </div>
                    ) : (
                      <div className="text-right">
                        <div className="text-xs text-slate-400 font-medium bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
                          Awaiting Evaluation
                        </div>
                      </div>
                    )}

                    <div className="p-3 bg-slate-800/80 group-hover:bg-indigo-600/20 text-slate-400 group-hover:text-indigo-400 rounded-xl border border-slate-700/80 transition-all">
                      <ChevronRight className="w-5 h-5" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Audit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-white">Start 48-Hour Blast-Radius Audit</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Bounded time observation session. Automatically expires in 48 hours.
                </p>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAudit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  AI Agent Identifier / Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Triage AI Assistant or Client Document Vault Bot"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-800/70 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-800/70 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Production">Production</option>
                    <option value="Staging">Staging</option>
                    <option value="Sandbox">Sandbox</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Telemetry Source
                  </label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-800/70 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="splunk">Splunk MCP</option>
                    <option value="datadog">Datadog MCP</option>
                    <option value="cloudwatch">AWS CloudWatch</option>
                    <option value="agent_trace">OpenTelemetry Traces</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Business Scope & Mission
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe what data and tools this agent has access to..."
                  value={businessContext}
                  onChange={(e) => setBusinessContext(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-800/70 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="p-3.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                <div className="flex items-start gap-2.5 text-xs text-indigo-300">
                  <Shield className="w-4 h-4 flex-shrink-0 mt-0.5 text-indigo-400" />
                  <span>
                    Deterministic rules evaluate score and findings against NIST AI RMF. Gemini synthesizes executive explanations.
                  </span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
                >
                  {submitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                  Initialize 48h Window
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
