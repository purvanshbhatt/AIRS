import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDailyReadinessReport, getIntegrationStatus } from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';

interface SystemEvent {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERR' | 'FATAL';
  source: string;
  message: string;
}

export default function ITWorkspacePage() {
  const navigate = useNavigate();
  const { orgId, isDemo } = useActiveOrg();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [integrationStatus, setIntegrationStatus] = useState<any>(null);
  const [logFilter, setLogFilter] = useState<'ALL' | 'ERRORS'>('ALL');

  const systemEvents: SystemEvent[] = useMemo(() => {
    if (!isDemo) {
      return [];
    }
    const now = new Date();
    const fmt = (offsetSec: number) => {
      const d = new Date(now.getTime() - offsetSec * 1000);
      return d.toTimeString().split(' ')[0] + '.' + String(d.getMilliseconds()).padStart(3, '0');
    };
    return [
      { timestamp: fmt(10), level: 'ERR', source: 'auth_svc', message: 'Failed authentication attempt from IP 192.168.1.104 - Invalid signature' },
      { timestamp: fmt(22), level: 'WARN', source: 'db_sync', message: 'High latency detected on replica region-us-east-1 (420ms)' },
      { timestamp: fmt(45), level: 'INFO', source: 'node_mgr', message: 'Node wkr-04 successfully re-registered to cluster' },
      { timestamp: fmt(68), level: 'FATAL', source: 'policy_enf', message: 'Policy violation: Unauthorized lateral movement attempt detected source=wkr-02 dest=db-master' },
      { timestamp: fmt(95), level: 'INFO', source: 'sys_mon', message: 'Routine memory garbage collection completed (freed 4.2GB)' },
      { timestamp: fmt(120), level: 'INFO', source: 'wazuh_agent', message: 'Wazuh active response sweep completed on 14 endpoints' },
      { timestamp: fmt(180), level: 'INFO', source: 'splunk_mcp', message: 'Splunk MCP query search execution: 4 searches returned 0 critical findings' },
    ];
  }, [isDemo]);

  useEffect(() => {
    async function loadWorkspace() {
      if (!orgId) {
        setLoading(false);
        return;
      }
      try {
        const [rep, integ] = await Promise.all([
          getDailyReadinessReport(orgId).catch(() => null),
          getIntegrationStatus(orgId).catch(() => null),
        ]);
        setReport(rep);
        setIntegrationStatus(integ);
      } catch (err) {
        console.error('Failed to load IT workspace telemetry:', err);
      } finally {
        setLoading(false);
      }
    }
    loadWorkspace();
  }, [orgId]);

  const filteredEvents = logFilter === 'ERRORS' 
    ? systemEvents.filter(e => e.level === 'ERR' || e.level === 'FATAL')
    : systemEvents;

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/40 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">Operations & Telemetry</h1>
            {isDemo && (
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/10 text-amber-500 border border-amber-500/30">
                SANDBOX SIMULATION
              </span>
            )}
          </div>
          <p className="text-base text-on-surface-variant max-w-2xl">
            Deep-dive technical workspace for IT administrators and MSPs. Real-time system logs, forensic snapshots, and network telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => {
              if (isDemo) {
                alert('Exporting PCAP telemetry stream (simulated)...');
              } else {
                alert('No telemetry stream connected yet. Connect your systems in Connectors.');
              }
            }}
            className="px-4 py-2 bg-surface-container-high border border-outline-variant/50 text-on-surface hover:text-ready-emerald text-xs font-mono rounded-lg transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm" data-icon="download">
              download
            </span>
            Export Telemetry PCAP
          </button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">Ingress Rate</span>
            <span className="text-3xl font-bold text-on-surface font-mono">
              {isDemo ? '42.8' : '0.0'} <span className="text-sm text-ready-emerald">MB/s</span>
            </span>
          </div>
          <span className="material-symbols-outlined text-ready-emerald text-3xl" data-icon="swap_calls">
            swap_calls
          </span>
        </div>

        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">Active Blocks</span>
            <span className="text-3xl font-bold text-on-surface font-mono">
              {isDemo ? '1,204' : '0'}
            </span>
          </div>
          <span className="material-symbols-outlined text-critical-red text-3xl" data-icon="shield_locked">
            shield_locked
          </span>
        </div>

        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">EDR Endpoints</span>
            <span className="text-3xl font-bold text-ready-emerald font-mono">
              {isDemo ? '14/14' : '0/0'}
            </span>
          </div>
          <span className="material-symbols-outlined text-ready-emerald text-3xl" data-icon="computer">
            computer
          </span>
        </div>
      </div>

      {/* Bottom Grid: Live System Events & Forensic Snapshots */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Live System Events (Span 7) */}
        <div className="lg:col-span-7 bg-surface-container-low border border-surface-bright rounded-xl flex flex-col overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-bright flex justify-between items-center bg-surface-container">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-ready-emerald text-lg" data-icon="list_alt">
                list_alt
              </span>
              <h3 className="text-sm font-semibold text-on-surface">Live System Telemetry Stream</h3>
            </div>
            {filteredEvents.length > 0 && (
              <div className="flex gap-2">
                <button 
                  onClick={() => setLogFilter(logFilter === 'ALL' ? 'ERRORS' : 'ALL')}
                  className={`px-2.5 py-1 rounded text-xs font-mono border transition-all ${logFilter === 'ERRORS' ? 'bg-critical-red/20 text-critical-red border-critical-red/40' : 'bg-surface-container-high text-on-surface-variant border-outline-variant/40'}`}
                >
                  {logFilter === 'ERRORS' ? 'ERRORS ONLY' : 'ALL LOGS'}
                </button>
              </div>
            )}
          </div>

          <div className="p-4 font-mono text-xs space-y-2 overflow-y-auto max-h-[400px]">
            {filteredEvents.length > 0 ? (
              filteredEvents.map((evt, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded bg-surface-container/50 hover:bg-surface-container transition-colors">
                  <span className="text-on-surface-variant shrink-0">{evt.timestamp}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                    evt.level === 'FATAL' || evt.level === 'ERR' ? 'bg-critical-red/20 text-critical-red border border-critical-red/40' :
                    evt.level === 'WARN' ? 'bg-drift-amber/20 text-drift-amber border border-drift-amber/40' :
                    'bg-ready-emerald/20 text-ready-emerald border border-ready-emerald/40'
                  }`}>
                    [{evt.level}]
                  </span>
                  <span className="text-ready-emerald font-semibold shrink-0">{evt.source}</span>
                  <span className="text-on-surface truncate">{evt.message}</span>
                </div>
              ))
            ) : (
              <div className="py-12 px-6 text-center flex flex-col items-center justify-center font-sans">
                <div className="w-12 h-12 rounded-xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-on-surface-variant mb-3">
                  <span className="material-symbols-outlined text-2xl">sensors_off</span>
                </div>
                <h4 className="text-sm font-bold text-on-surface mb-1">Awaiting Live Telemetry Stream</h4>
                <p className="text-xs text-on-surface-variant max-w-md leading-relaxed mb-4">
                  Nothing is connected yet. Connect your security platforms (Microsoft 365, Veeam, CrowdStrike, or SentinelOne) to stream verified telemetry events.
                </p>
                <button
                  onClick={() => navigate('/connectors')}
                  className="px-4 py-2 bg-ready-emerald text-slate-950 font-bold text-xs rounded-lg hover:brightness-110 flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-sm">add_link</span>
                  Connect a System
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Forensic Snapshots (Span 5) */}
        <div className="lg:col-span-5 bg-surface-container-low border border-surface-bright rounded-xl flex flex-col overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-bright flex justify-between items-center bg-surface-container">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-ready-emerald text-lg" data-icon="shield_with_heart">
                shield_with_heart
              </span>
              <h3 className="text-sm font-semibold text-on-surface">Forensic Snapshots</h3>
            </div>
          </div>

          <div className="p-4 space-y-3">
            {isDemo ? (
              <>
                <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-992-A</span>
                    <span className="text-xs text-on-surface-variant">Policy Breach Sweep Snapshot</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-critical-red/10 text-critical-red border border-critical-red/30">
                    Breach Audit
                  </span>
                </div>

                <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-991-B</span>
                    <span className="text-xs text-on-surface-variant">Routine Overnight Ledger Snapshot</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30">
                    Verified
                  </span>
                </div>

                <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-990-C</span>
                    <span className="text-xs text-on-surface-variant">Wazuh EDR Endpoint Telemetry Snapshot</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30">
                    Verified
                  </span>
                </div>
              </>
            ) : (
              <div className="py-12 px-4 text-center flex flex-col items-center justify-center font-sans">
                <div className="w-12 h-12 rounded-xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-on-surface-variant mb-3">
                  <span className="material-symbols-outlined text-2xl">history</span>
                </div>
                <h4 className="text-sm font-bold text-on-surface mb-1">No Forensic Snapshots</h4>
                <p className="text-xs text-on-surface-variant max-w-xs leading-relaxed">
                  Forensic ledger snapshots are generated automatically once active connectors report evidence.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
