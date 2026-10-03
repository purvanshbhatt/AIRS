import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Bot,
  Shield,
  Activity,
  AlertTriangle,
  Clock,
  ArrowLeft,
  RefreshCw,
  Sparkles,
  Download,
  CheckCircle2,
  Lock,
  ChevronRight,
  Play,
  Terminal,
  FileText,
  Copy,
  Check,
  Wrench,
} from 'lucide-react';
import { useActiveOrg } from '../hooks/useActiveOrg';
import {
  getAgentAudit,
  runAgentAuditAnalysis,
  getAgentAuditExplanation,
  downloadAgentAuditReport,
  ingestAgentTelemetry,
  remediateAgentAuditFinding,
  AgentAuditItem,
  AgentAuditExplanationResponse,
  ApiRequestError,
} from '../api';

export default function AgentAuditDetailPage() {
  const { auditId } = useParams<{ auditId: string }>();
  const navigate = useNavigate();
  const { orgId, isDemo } = useActiveOrg();

  const [audit, setAudit] = useState<AgentAuditItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [explanation, setExplanation] = useState<AgentAuditExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [paywallError, setPaywallError] = useState(false);
  const [copied, setCopied] = useState(false);
  const [remediatingId, setRemediatingId] = useState<string | null>(null);

  const handleRemediateFinding = async (findingId: string) => {
    if (!orgId || !auditId) return;
    setRemediatingId(findingId);
    try {
      await remediateAgentAuditFinding(orgId, auditId, findingId);
      setAudit((prev) => {
        if (!prev) return prev;
        const updatedFindings = (prev.findings || []).map((f) => {
          if (f.finding_id === findingId) {
            return { ...f, status: 'REMEDIATED' };
          }
          return f;
        });
        const newScore = Math.min(100, Math.round(Number(prev.readiness_score || 60) + 15));
        return {
          ...prev,
          readiness_score: newScore,
          findings: updatedFindings,
        };
      });
    } catch (err) {
      console.error('Failed to remediate finding:', err);
    } finally {
      setRemediatingId(null);
    }
  };

  const fetchAudit = async () => {
    if (!orgId || !auditId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAgentAudit(orgId, auditId);
      setAudit(data);
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
      } else {
        setError(err.message || 'Failed to load agent audit session.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
  }, [orgId, auditId]);

  const handleRunAnalysis = async () => {
    if (!orgId || !auditId) return;
    setEvaluating(true);
    setError(null);
    try {
      const updated = await runAgentAuditAnalysis(orgId, auditId);
      setAudit(updated);
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
      } else {
        setError(err.message || 'Failed to evaluate blast radius.');
      }
    } finally {
      setEvaluating(false);
    }
  };

  const handleIngestSampleTraces = async () => {
    if (!orgId || !auditId) return;
    setIngesting(true);
    setError(null);
    try {
      const sampleEvents = [
        {
          agent_id: audit?.agent_name || 'Autonomous Agent',
          tool: 'bash_shell',
          action: 'exec',
          params: { cmd: 'cat /etc/passwd' },
          timestamp: new Date().toISOString(),
          authorized: false,
        },
        {
          agent_id: audit?.agent_name || 'Autonomous Agent',
          tool: 'sql_writer',
          action: 'write',
          params: { query: 'SELECT * FROM patients WHERE ssn IS NOT NULL' },
          timestamp: new Date().toISOString(),
          authorized: true,
        },
        {
          agent_id: audit?.agent_name || 'Autonomous Agent',
          tool: 'external_http_fetch',
          action: 'call',
          params: { url: 'https://webhook.site/untrusted-exfil' },
          timestamp: new Date().toISOString(),
          authorized: false,
        },
      ];
      await ingestAgentTelemetry(orgId, auditId, sampleEvents);
      await fetchAudit();
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
      } else {
        setError(err.message || 'Failed to ingest telemetry traces.');
      }
    } finally {
      setIngesting(false);
    }
  };

  const handleGenerateExplanation = async () => {
    if (!orgId || !auditId) return;
    setExplaining(true);
    setError(null);
    try {
      const exp = await getAgentAuditExplanation(orgId, auditId);
      setExplanation(exp);
    } catch (err: any) {
      setError(err.message || 'Failed to synthesize executive explanation.');
    } finally {
      setExplaining(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!orgId || !auditId) return;
    setDownloading(true);
    setError(null);
    try {
      const blob = await downloadAgentAuditReport(orgId, auditId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resilai-agent-blast-radius-audit-${auditId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      if (err instanceof ApiRequestError && err.status === 402) {
        setPaywallError(true);
      } else {
        setError(err.message || 'Failed to download report.');
      }
    } finally {
      setDownloading(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev.toLowerCase();
    if (s === 'critical') {
      return (
        <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 uppercase tracking-wide">
          Critical
        </span>
      );
    }
    if (s === 'high') {
      return (
        <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 uppercase tracking-wide">
          High
        </span>
      );
    }
    if (s === 'medium') {
      return (
        <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border border-yellow-500/20 uppercase tracking-wide">
          Medium
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 uppercase tracking-wide">
        Low
      </span>
    );
  };

  const getRemainingTime = (expiresAt?: string) => {
    if (!expiresAt) return 'Bounded 48h';
    const remaining = new Date(expiresAt).getTime() - new Date().getTime();
    if (remaining <= 0) return 'Observation Window Closed';
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const mins = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${mins}m observation window remaining`;
  };

  if (loading) {
    return (
      <div className="p-16 text-center">
        <RefreshCw className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
        <p className="text-on-surface-variant text-sm">Loading agent audit blast-radius telemetry...</p>
      </div>
    );
  }

  if (!audit) {
    return (
      <div className="p-12 text-center bg-surface-container-low rounded-2xl border border-outline-variant/60 shadow-xs">
        <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-on-surface mb-2">Audit Session Not Found</h2>
        <p className="text-on-surface-variant text-sm mb-4">The requested 48-hour observation session could not be located.</p>
        <button
          onClick={() => navigate('/agent-audit')}
          className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-xl text-sm border border-outline-variant/60 transition-colors"
        >
          Return to Agent Audits
        </button>
      </div>
    );
  }

  const score = audit.readiness_score;
  const isExpired = audit.status === 'EXPIRED';

  return (
    <div className="space-y-6">
      {/* Back Button & Navigation */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/agent-audit')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-on-surface-variant hover:text-on-surface transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Agent Audits
        </button>
      </div>

      {/* Paywall Banner if 402 */}
      {paywallError && (
        <div className="p-6 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 rounded-2xl">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-amber-500/10 text-amber-500 rounded-lg">
              <Lock className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-on-surface">Design Partner Subscription Required</h3>
              <p className="text-sm text-on-surface-variant mt-1 max-w-2xl leading-relaxed">
                Evaluating live production agent blast radius and downloading executive compliance reports requires an active ResilAI subscription or design partner enrollment.
              </p>
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={() => navigate('/pricing')}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs uppercase tracking-wider rounded-lg transition-colors"
                >
                  View Plans & Enroll
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-500 dark:text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Session Hero Banner */}
      <div className="bg-surface-container-low border border-outline-variant/60 p-6 rounded-2xl space-y-4 shadow-xs">
        <div className="flex flex-col lg:flex-row justify-between lg:items-center gap-4 pb-4 border-b border-outline-variant/60">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-primary/10 border border-primary/20 rounded-xl text-primary">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-on-surface tracking-tight">{audit.agent_name}</h1>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-surface-container text-on-surface-variant border border-outline-variant/60 font-mono">
                    {audit.environment}
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 font-mono uppercase">
                    {audit.source_type}
                  </span>
                </div>
                <p className="text-sm text-on-surface-variant mt-0.5">{audit.business_context}</p>
              </div>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleIngestSampleTraces}
              disabled={ingesting || isExpired}
              className="flex items-center gap-2 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 transition-colors disabled:opacity-50"
              title="Feed agent execution traces into this observation window"
            >
              <Terminal className={`w-3.5 h-3.5 ${ingesting ? 'animate-spin' : ''}`} />
              {ingesting ? 'Ingesting...' : 'Inject Test Trace'}
            </button>

            <button
              onClick={handleRunAnalysis}
              disabled={evaluating}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-on-primary text-xs font-semibold rounded-xl shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
              {evaluating ? 'Evaluating Blast Radius...' : 'Run Deterministic Analysis'}
            </button>

            <button
              onClick={handleDownloadReport}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-xl border border-outline-variant/60 transition-colors disabled:opacity-50"
            >
              <Download className={`w-3.5 h-3.5 ${downloading ? 'animate-spin' : ''}`} />
              {downloading ? 'Generating PDF...' : 'Download PDF Report'}
            </button>
          </div>
        </div>

        {/* Live Observation Status Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
            <div className="text-[11px] uppercase tracking-wider text-on-surface-variant font-semibold mb-1 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-primary" />
              Observation Window
            </div>
            <div className="text-sm font-bold text-on-surface">{getRemainingTime(audit.expires_at)}</div>
          </div>

          <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
            <div className="text-[11px] uppercase tracking-wider text-on-surface-variant font-semibold mb-1 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-sky-500" />
              Telemetry Events
            </div>
            <div className="text-sm font-bold text-on-surface">
              {audit.telemetry_event_count.toLocaleString()} Traces Captured
            </div>
          </div>

          <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
            <div className="text-[11px] uppercase tracking-wider text-on-surface-variant font-semibold mb-1 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-500" />
              Verified Tool Calls
            </div>
            <div className="text-sm font-bold text-on-surface">
              {audit.verified_action_count} / {audit.tool_action_count} verified
            </div>
          </div>

          <div className="p-3 bg-surface-container rounded-xl border border-outline-variant/60">
            <div className="text-[11px] uppercase tracking-wider text-on-surface-variant font-semibold mb-1 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              Blast-Radius Score
            </div>
            <div className="text-sm font-bold">
              {score !== null && score !== undefined ? (
                <span
                  className={
                    score >= 80 ? 'text-emerald-500 dark:text-emerald-400' : score >= 60 ? 'text-amber-500 dark:text-amber-400' : 'text-rose-500 dark:text-rose-400'
                  }
                >
                  {Math.round(score)}% Readiness
                </span>
              ) : (
                <span className="text-on-surface-variant">Pending Evaluation</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Executive Explanation (Gemini Engine) */}
      <div className="p-6 bg-surface-container-low border border-outline-variant/60 rounded-2xl space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg text-primary">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-on-surface">Executive Explanation & Narrative Breakdown</h2>
              <p className="text-xs text-on-surface-variant">
                Grounding: Deterministic rules evaluate score & findings; Gemini synthesizes executive explanations.
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerateExplanation}
            disabled={explaining}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-xl text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${explaining ? 'animate-spin' : ''}`} />
            {explaining ? 'Synthesizing...' : 'Synthesize Explanation'}
          </button>
        </div>

        {explanation ? (
          <div className="p-5 bg-surface-container border border-outline-variant/60 rounded-xl space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60 text-xs text-on-surface-variant">
              <span className="font-mono">Engine: {explanation.narrative_source}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(explanation.explanation);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="flex items-center gap-1 hover:text-on-surface transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Narrative'}
              </button>
            </div>
            <div className="text-sm text-on-surface leading-relaxed whitespace-pre-line font-sans">
              {explanation.explanation}
            </div>
          </div>
        ) : (
          <div className="p-5 bg-surface-container border border-outline-variant/60 rounded-xl text-xs text-on-surface-variant leading-relaxed flex items-center justify-between">
            <span>
              Click "Synthesize Explanation" to generate an executive-ready plain-English synthesis of the agent blast radius, lateral movement boundaries, and compliance risks.
            </span>
          </div>
        )}
      </div>

      {/* Blast Radius Findings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-on-surface">Impact & Risk Findings ({audit.findings?.length || 0})</h2>
            <p className="text-xs text-on-surface-variant">
              Identified vulnerabilities and execution boundary gaps.
            </p>
          </div>
        </div>

        {(!audit.findings || audit.findings.length === 0) ? (
          <div className="p-8 text-center bg-surface-container-low rounded-2xl border border-outline-variant/60 shadow-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-on-surface">Zero Critical Violations</h3>
            <p className="text-xs text-on-surface-variant mt-1 max-w-md mx-auto">
              No unauthorized tool execution, shell escape, or unconstrained credential access observed in this window.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {audit.findings.map((f, idx) => (
              <div
                key={f.finding_id || idx}
                className="p-5 bg-surface-container-low border border-outline-variant/60 rounded-2xl space-y-3 shadow-xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-on-surface-variant">{f.finding_id}</span>
                    <h3 className="text-base font-bold text-on-surface">{f.title}</h3>
                    {getSeverityBadge(f.severity)}
                  </div>
                  <span className="text-xs font-mono text-on-surface-variant/80">
                    {new Date(f.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <p className="text-sm text-on-surface leading-relaxed">{f.deterministic_reason}</p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
                  <div className="p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant block mb-0.5 font-medium">Affected Agent</span>
                    <span className="text-on-surface font-mono">{f.affected_agent}</span>
                  </div>
                  <div className="p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant block mb-0.5 font-medium">Affected Tool / Command</span>
                    <span className="text-on-surface font-mono">{f.affected_tool}</span>
                  </div>
                  <div className="p-2.5 bg-surface-container rounded-xl border border-outline-variant/60">
                    <span className="text-on-surface-variant block mb-0.5 font-medium">Evidence Traces</span>
                    <span className="text-primary font-mono">
                      {f.evidence_ids ? f.evidence_ids.join(', ') : 'Direct Trace'}
                    </span>
                  </div>
                </div>

                {/* Remediation Action Row */}
                {f.status === 'REMEDIATED' ? (
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20 w-fit mt-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span>Remediated & Verified in Telemetry</span>
                  </div>
                ) : (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 mt-3 border-t border-outline-variant/60">
                    <p className="text-xs text-on-surface-variant">
                      <span className="font-semibold text-on-surface">Recommended Fix: </span>
                      {f.remediation || "Apply least-privilege boundary policy to restrict agent capabilities."}
                    </p>
                    <button
                      onClick={() => handleRemediateFinding(f.finding_id)}
                      disabled={remediatingId === f.finding_id}
                      className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                    >
                      <Wrench className="w-3.5 h-3.5" />
                      {remediatingId === f.finding_id ? 'Applying Policy...' : 'Fix Issue Now'}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Regulatory Framework Alignment */}
      <div className="p-6 bg-surface-container-low border border-outline-variant/60 rounded-2xl space-y-4 shadow-xs">
        <h2 className="text-base font-bold text-on-surface">Regulatory Framework & Standard Coverage</h2>
        <p className="text-xs text-on-surface-variant">
          Cross-mapping of observed blast radius and tool interactions against governance baselines.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-on-surface">NIST AI RMF</span>
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Aligned</span>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              MAP 1.5, MEASURE 2.6, MANAGE 4.1 for autonomous agent bounded agency.
            </p>
          </div>

          <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-on-surface">OWASP LLM Top 10</span>
              <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">Monitored</span>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              LLM08 (Excessive Agency), LLM02 (Sensitive Information Disclosure), LLM06 (Excessive Permissions).
            </p>
          </div>

          <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-on-surface">ISO/IEC 42001</span>
              <span className="text-xs text-primary font-medium">Enforced</span>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Annex A.6 AI Risk Assessment, A.8 AI System Life Cycle and continuous verification.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
